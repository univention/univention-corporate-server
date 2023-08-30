#!/usr/share/ucs-test/runner python3
## desc: Test appcenter listener/converter
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import glob
import json
import os
import subprocess
import time
from typing import Any, Optional

import univention.testing.udm as udm_test

from dockertest import App, Appcenter


APP_NAME = 'my-listener-test-app'
DB_FILE = f'/var/lib/univention-appcenter/apps/{APP_NAME}/data/db.json'
LISTENER_DIR = f'/var/lib/univention-appcenter/apps/{APP_NAME}/data/listener/'
LISTENER_TIMEOUT = 10
DOCKER_IMAGE_OLD = 'docker-test.software-univention.de/python:3.7-slim-buster'
DOCKER_IMAGE_NEW = 'docker-test.software-univention.de/python:3.7-slim-bullseye'


def dump_db() -> Any:
    with open(DB_FILE) as fd:
        return json.load(fd)


def obj_exists(obj_type: str, dn: str) -> bool:
    db = dump_db()
    return any(dn.lower() == obj.get('dn').lower() for obj_id, obj in db[obj_type].items())


def user_exists(dn: str) -> bool:
    return obj_exists('users/user', dn)


def group_exists(dn: str) -> bool:
    return obj_exists('groups/group', dn)


def get_attr(obj_type: str, dn: str, attr: str) -> Optional[Any]:
    db = dump_db()
    for _obj_id, obj in db[obj_type].items():
        if dn.lower() == obj.get('dn').lower():
            return obj['obj'].get(attr)
    return None


def test_listener() -> None:
    with udm_test.UCSTestUDM() as udm:
        # create
        u1 = udm.create_user(username='litest1')
        u2 = udm.create_user(username='litest2')
        u3 = udm.create_user(username='litest3')
        g1 = udm.create_group(name='ligroup1')
        g2 = udm.create_group(name='ligroup2')
        time.sleep(LISTENER_TIMEOUT)
        assert user_exists(u1[0])
        assert user_exists(u2[0])
        assert user_exists(u3[0])
        assert group_exists(g1[0])
        assert group_exists(g2[0])
        # modify
        udm.modify_object('users/user', dn=u1[0], description='abcde')
        udm.modify_object('users/user', dn=u2[0], description='xyz')
        udm.modify_object('users/user', dn=u3[0], description='öäü????ßßßß!')
        udm.modify_object('groups/group', dn=g1[0], description='lkjalkhlÄÖ#üäööäö')
        udm.modify_object('groups/group', dn=g2[0], users=u1[0])
        time.sleep(LISTENER_TIMEOUT)
        assert get_attr('users/user', u1[0], 'description') == 'abcde'
        assert get_attr('users/user', u2[0], 'description') == 'xyz'
        assert get_attr('users/user', u3[0], 'description') == 'öäü????ßßßß!'
        assert get_attr('users/user', u1[0], 'description')
        assert get_attr('users/user', u1[0], 'disabled') is False
        assert get_attr('users/user', u1[0], 'displayName')
        assert get_attr('users/user', u1[0], 'gidNumber')
        assert get_attr('users/user', u1[0], 'groups')
        assert get_attr('users/user', u1[0], 'lastname')
        assert get_attr('users/user', u1[0], 'sambaRID')
        assert get_attr('groups/group', g1[0], 'description') == 'lkjalkhlÄÖ#üäööäö'
        assert get_attr('groups/group', g2[0], 'users') == [u1[0]]
        assert get_attr('groups/group', g2[0], 'users')
        assert get_attr('groups/group', g2[0], 'gidNumber')
        assert get_attr('groups/group', g2[0], 'name')
        assert get_attr('groups/group', g2[0], 'sambaRID')
        # remove
        udm.remove_object('users/user', dn=u1[0])
        udm.remove_object('users/user', dn=u2[0])
        udm.remove_object('users/user', dn=u3[0])
        udm.remove_object('groups/group', dn=g1[0])
        udm.remove_object('groups/group', dn=g2[0])
        time.sleep(LISTENER_TIMEOUT)
        assert not user_exists(u1[0])
        assert not user_exists(u2[0])
        assert not user_exists(u3[0])
        assert not group_exists(g1[0])
        assert not group_exists(g2[0])
        # listener dir should be empty at this point
        assert not glob.glob(os.path.join(LISTENER_DIR, '*.json'))


def get_pid_for_name(name: str) -> Optional[str]:
    o = subprocess.check_output(['ps', 'aux'], text=True)
    for line in o.split('\n'):
        if name in line:
            return line.split()[1]
    return None


def systemd_service_active(service: str) -> bool:
    return subprocess.call(['systemctl', '--quiet', 'is-active', service]) == 0


def systemd_service_enabled(service: str) -> bool:
    return subprocess.call(['systemctl', '--quiet', 'is-enabled', service]) == 0


if __name__ == '__main__':
    name = APP_NAME
    systemd_service = f'univention-appcenter-listener-converter@{name}.service'

    setup = '#!/bin/sh'
    store_data = '#!/bin/sh'
    preinst = f'''#!/bin/sh
ucr set appcenter/apps/{name}/docker/params=' -t'
exit 0
'''

    listener_trigger = f'''#!/usr/bin/env python3
import glob
import json
import os

DATA_DIR = '/var/lib/univention-appcenter/apps/{name}/data/listener'
DB = '/var/lib/univention-appcenter/apps/{name}/data/db.json'

try:
    with open(DB) as fd:
        db = json.load(fd)
except (FileNotFoundError, json.decoder.JSONDecodeError):
    db = {{}}

for i in sorted(glob.glob(os.path.join(DATA_DIR, '*.json'))):
    with open(i) as fd:
        dumped = json.load(fd)

    obj = dumped.get('object')
    obj_type = dumped.get('udm_object_type')
    entries = db.setdefault(obj_type, {{}})
    id_ = dumped.get('id')
    if obj is None:
        entries.pop(id_, None)
    else:
        entries[id_] = dict(
            id=id_,
            dn=dumped.get('dn'),
            obj=obj,
        )

    with open(DB, 'w') as fd:
        json.dump(db, fd, sort_keys=True, indent=4)

    os.remove(i)
'''

    with Appcenter() as appcenter:
        app = App(name=name, version='1', build_package=False, call_join_scripts=False)
        app.set_ini_parameter(
            DockerImage=DOCKER_IMAGE_OLD,
            DockerScriptSetup='/setup',
            DockerScriptStoreData='/store_data',
            DockerScriptInit='/bin/sh',
            ListenerUdmModules='users/user, groups/group',
        )
        app.add_script(
            setup=setup,
            store_data=store_data,
            preinst=preinst,
            listener_trigger=listener_trigger,
        )
        app.add_to_local_appcenter()
        appcenter.update()
        app.install()
        appcenter.apps.append(app)
        app.verify()

        subprocess.check_call(['docker', 'image', 'inspect', DOCKER_IMAGE_OLD])

        very_old_con_pid = get_pid_for_name('univention-appcenter-listener-converter %s' % name)
        time.sleep(10)
        with open('/var/lib/univention-directory-listener/handlers/%s' % name) as f:
            status = f.readline()
            assert status == '3'
        test_listener()

        # check listener/converter restart during update
        old_li_pid = get_pid_for_name(' /usr/sbin/univention-directory-listener')
        old_con_pid = get_pid_for_name('univention-appcenter-listener-converter %s' % name)
        assert very_old_con_pid == old_con_pid  # should be the same until now
        app = App(name=name, version='2', build_package=False, call_join_scripts=False)
        app.set_ini_parameter(
            DockerImage=DOCKER_IMAGE_NEW,
            DockerScriptSetup='/setup',
            DockerScriptStoreData='/store_data',
            DockerScriptInit='/bin/sh',
            ListenerUdmModules='users/user, groups/group',
        )
        app.add_script(
            setup=setup,
            store_data=store_data,
            preinst=preinst,
            listener_trigger=listener_trigger,
        )
        app.add_to_local_appcenter()
        appcenter.update()
        app.upgrade()
        app.verify()

        li_pid = get_pid_for_name(' /usr/sbin/univention-directory-listener')
        con_pid = get_pid_for_name('univention-appcenter-listener-converter %s' % name)
        assert old_li_pid == li_pid  # app update does not require listener restart
        assert old_con_pid != con_pid

        # check handler file/listener restart during remove
        app.uninstall()
        new_li_pid = get_pid_for_name(' /usr/sbin/univention-directory-listener')
        assert not systemd_service_enabled(systemd_service)
        assert not os.path.isfile('/var/lib/univention-directory-listener/handlers/%s' % name)
        assert li_pid != new_li_pid
