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
from univention.appcenter.docker import Docker

SYSTEMCTL_RESTART_TIME = 5


def restart_service(service):
	subprocess.call(['systemctl', 'restart', service])


def update_wait_time(wtime=None, rtime=None):
	if wtime:
		ucr_set(['owncloud/listener-wait-time={:d}'.format(wtime)])
	else:
		ucr_unset(['owncloud/listener-wait-time'])
	if not rtime:
		restart_service('univention-appcenter-listener-converter@owncloud.service')
		while os.system('service univention-appcenter-listener-converter@owncloud status') != 0:
			time.sleep(1)
	else:
		time.sleep(rtime)
	time.sleep(1)
	with open("/var/log/univention/listener_modules/owncloud.log", "r") as file:
		for line in file:
			pass
	return line


@pytest.fixture(scope="session")
def udm_session():
	with udm_test.UCSTestUDM() as udm:
		yield udm


@pytest.fixture(scope='module')
def app_and_docker():
	app = Apps().find('owncloud')
	if not app:
		print('App unknown')
		raise ValueError
	docker = Docker(app, None)
	yield app, docker
	docker.unpause()


def install_owncloud():
	pass


def test_wait_time():
	assert update_wait_time().find('Wait Time = 600') != -1
	assert update_wait_time(5).find('Wait Time = 5') != -1
	assert update_wait_time(10, 5 + SYSTEMCTL_RESTART_TIME).find('Wait Time = 10') != -1


def test_new_user(app_and_docker, udm_session):
	app, docker = app_and_docker
	if not app.is_installed():
		install_owncloud()
	dest = os.path.join(app.get_data_dir(), 'listener', '*.json')
	files = glob(dest)
	for file in files:
		os.unlink(file)
	docker.pause()
	userdn, username = udm_session.create_user()
	time.sleep(5)
	files = glob(dest)
	assert len(files) == 1
	jout = json.load(open(files[0]))
	assert jout['dn'] == userdn
	assert jout['object']['username'] == username
	docker.unpause()
	time.sleep(10 + SYSTEMCTL_RESTART_TIME)
	files = glob(dest)
	assert len(files) == 0
	docker.pause()
	udm_session.remove_user(username, False)
	time.sleep(5)
	files = glob(dest)
	assert len(files) == 1
	jout = json.load(open(files[0]))
	assert jout['dn'] == userdn
	assert jout['object'] is None
	docker.unpause()






