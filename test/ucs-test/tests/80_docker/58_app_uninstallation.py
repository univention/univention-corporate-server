#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test the Docker App uninstallation
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import os

import pytest

from univention.testing.utils import fail, get_ldap_connection

from dockertest import tiny_app


@pytest.mark.exposure('dangerous')
def test_app_uninstallation(appcenter):
    app = tiny_app()

    try:
        app.set_ini_parameter(
            DockerScriptSetup='/usr/sbin/%s-setup' % app.app_name,
        )

        app.add_script(setup='''#!/bin/sh
set -x -e
echo "Test 123 Data" >/var/lib/univention-appcenter/apps/%(app_name)s/data/test123
echo "Test 123 Conf" >/var/lib/univention-appcenter/apps/%(app_name)s/conf/test123
''' % {'app_name': app.app_name})
        app.add_to_local_appcenter()

        appcenter.update()

        app.install()
        app.verify()

        lo = get_ldap_connection()
        print(lo.searchDn(filter=f'(&(cn={app.app_name[:5]}-*)(objectClass=univentionMemberServer)(!(aRecord=*))(!(macAddress=*)))', unique=True, required=True))

    finally:
        app.uninstall()
        app.remove()

    assert os.path.exists(f'/var/lib/univention-appcenter/apps/{app.app_name}/data/test123')
    assert not os.path.exists(f'/var/lib/univention-appcenter/apps/{app.app_name}/conf/test123')
    assert not os.path.exists(f'/var/lib/univention-appcenter/apps/{app.app_name}/conf/base.conf')

    found_conf = False
    backup_dir = '/var/lib/univention-appcenter/backups/'
    for d in os.listdir(backup_dir):
        if d.startswith(f'appcenter-backup-{app.app_name}:'):
            conffile = os.path.join(backup_dir, d, 'conf', 'test123')
            if os.path.exists(conffile):
                f = open(conffile)
                res = f.readlines()
                if res == ['Test 123 Conf\n']:
                    found_conf = True
    if not found_conf:
        fail('Conf backup file not found')

    lo = get_ldap_connection()
    res = lo.searchDn(filter=f'(&(cn={app.app_name[:5]}-*)(objectClass=univentionMemberServer))')
    if res:
        fail(f'The LDAP object has not been removed: {res}')
