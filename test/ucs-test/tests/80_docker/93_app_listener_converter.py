#!/usr/share/ucs-test/runner pytest-3 -s -vvv
## desc: test univention-appcenter-listener-converter
## tags: [appcenter]
## packages:
##   - univention-appcenter
## join: true
## exposure: dangerous

import pytest
import os
import subprocess
import time
import json
from glob import glob

import univention.testing.udm as udm_test
from univention.config_registry import handler_set as ucr_set
from univention.config_registry import handler_unset as ucr_unset
from univention.appcenter.app_cache import Apps
from dockertest import App, Appcenter
from univention.appcenter.docker import Docker

SYSTEMCTL_RESTART_TIME = 5
APP_NAME = 'list-conv-test-app'
DB_FILE = '/var/lib/univention-appcenter/apps/{0}/data/db.json'.format(APP_NAME)
LISTENER_DIR = '/var/lib/univention-appcenter/apps/{0}/data/listener/'.format(APP_NAME)
LISTENER_TIMEOUT = 10
LISTENER_PROCESS = '/usr/bin/python3 /usr/share/univention-appcenter-listener-converter {0}'.format(APP_NAME)


def restart_service(service):
	subprocess.call(['systemctl', 'restart', service])


def systemd_service_enabled(service):
	cmd = ['systemctl', 'is-enabled', service]
	try:
		out = subprocess.check_output(cmd, text=True)
	except subprocess.CalledProcessError:
		out = ''
	return 'enabled' in out


def set_wait_time(wtime):
	lwt_ucr = '%s/listener-wait-time' % APP_NAME
	if wtime:
		ucr_set([lwt_ucr + '={:d}'.format(wtime)])
	else:
		ucr_unset([lwt_ucr])
	restart_service('univention-appcenter-listener-converter@%s.service' % APP_NAME)
	while os.system('service univention-appcenter-listener-converter@%s status' % APP_NAME) != 0:
		time.sleep(1)


def check_wait_time(wtime=None):
	set_wait_time(wtime)
	pid1 = get_pid_for_name(LISTENER_PROCESS)
	if not wtime:
		wtime = 600		# The default value
	if wtime > 2:
		time.sleep(wtime - 2)
	if pid1 != get_pid_for_name(LISTENER_PROCESS):
		return False
	time.sleep(4)
	return pid1 != get_pid_for_name(LISTENER_PROCESS)


def get_pid_for_name(name):
	o = subprocess.check_output(['ps', 'aux'], text=True)
	for line in o.split('\n'):
		if name in line:
			return line.split()[1]
	return None


def dump_db():
	with open(DB_FILE, 'r') as f:
		db = json.load(f)
	return db


def obj_exists(obj_type, dn):
	found = False
	db = dump_db()
	for obj_id, obj in db[obj_type].items():
		if dn.lower() == obj.get('dn').lower():
			found = True
	return found


def user_exists(dn):
	return obj_exists('users/user', dn)


def check_listener():
	with udm_test.UCSTestUDM() as udm:
		u1 = udm.create_user(username='litest1')
		time.sleep(2)
		assert user_exists(u1[0])
		# listener dir should be empty at this point
		assert not glob.glob(os.path.join(LISTENER_DIR, '*.json'))


def test_app():
	name = APP_NAME
	systemd_service = 'univention-appcenter-listener-converter@%s.service' % name

	setup = '''#!/bin/bash
export DEBIAN_FRONTEND=noninteractive
apt-get -y update
apt-get -y install python
exit 0
'''
	store_data = '#!/bin/sh'
	preinst = '''#!/bin/bash
ucr set appcenter/apps/{0}/docker/params=' -t'
exit 0
'''.format(name)

	listener_trigger = '''#!/usr/bin/python

import glob
import os
import json

DATA_DIR='/var/lib/univention-appcenter/apps/%s/data/listener'
DB='/var/lib/univention-appcenter/apps/%s/data/db.json'

if not os.path.isfile(DB):
	with open(DB, 'wb') as f:
		json.dump({'users/user':dict(), 'groups/group':dict()}, f, sort_keys=True, indent=4)

for i in sorted(glob.glob(os.path.join(DATA_DIR, '*.json'))):

	with open(DB, 'r') as f:
		db = json.load(f)

	with open(i, 'r') as f:
		dumped = json.load(f)
		action = 'add/modify'
		if dumped.get('object') is None:
			action = 'delete'

		if action == 'delete':
			if dumped.get('id') in db[dumped.get('udm_object_type')]:
				del db[dumped.get('udm_object_type')][dumped.get('id')]
		else:
			db[dumped.get('udm_object_type')][dumped.get('id')] = dict(
				id=dumped.get('id'),
				dn=dumped.get('dn'),
				obj=dumped.get('object'),
			)

	with open(DB, 'wb') as f:
		json.dump(db, f, sort_keys=True, indent=4)

	os.remove(i)
''' % (name, name)

	with Appcenter() as appcenter:
		app = App(name=name, version='1', build_package=False, call_join_scripts=False)
		app.set_ini_parameter(
			DockerImage='docker-test.software-univention.de/debian:stable',
			DockerScriptSetup='/setup',
			DockerScriptStoreData='/store_data',
			DockerScriptInit='/bin/bash',
			ListenerUdmModules='users/user, groups/group',
		)
		app.add_script(setup=setup)
		app.add_script(store_data=store_data)
		app.add_script(preinst=preinst)
		app.add_script(listener_trigger=listener_trigger)
		app.add_to_local_appcenter()
		appcenter.update()
		app.install()
		appcenter.apps.append(app)
		app.verify(joined=False)
		images = subprocess.check_output(['docker', 'images'], text=True)
		assert 'stable' in images, images
		time.sleep(10)
		with open('/var/lib/univention-directory-listener/handlers/%s' % name, 'r') as f:
			status = f.readline()
			assert status == '3'

		check_listener()
		# assert check_wait_time()
		assert check_wait_time(10)

		# check listener/converter restart during update
		set_wait_time(600)

		old_con_pid = get_pid_for_name('univention-appcenter-listener-converter %s' % name)
		app = App(name=name, version='2', build_package=False, call_join_scripts=False)
		app.set_ini_parameter(
			DockerImage='docker-test.software-univention.de/debian:testing',
			DockerScriptSetup='/setup',
			DockerScriptStoreData='/store_data',
			DockerScriptInit='/bin/bash',
			ListenerUdmModules='users/user, groups/group',
		)
		app.add_script(setup=setup)
		app.add_script(store_data=store_data)
		app.add_script(preinst=preinst)
		app.add_script(listener_trigger=listener_trigger)
		app.add_to_local_appcenter()
		appcenter.update()
		app.upgrade()
		app.verify(joined=False)

		check_listener()

		images = subprocess.check_output(['docker', 'images'], text=True)
		assert 'stable' not in images, images

		li_pid = get_pid_for_name(' /usr/sbin/univention-directory-listener')
		assert not old_con_pid == get_pid_for_name('univention-appcenter-listener-converter %s' % name)

		# check handler file/listener restart during remove
		app.uninstall()
		new_li_pid = get_pid_for_name(' /usr/sbin/univention-directory-listener')
		assert not systemd_service_enabled(systemd_service)
		assert not os.path.isfile('/var/lib/univention-directory-listener/handlers/%s' % name)
		assert not li_pid == new_li_pid



