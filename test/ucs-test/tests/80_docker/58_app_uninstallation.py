#!/usr/share/ucs-test/runner python3
## desc: Test the Docker App uninstallation
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import os

from univention.testing.utils import fail, get_ldap_connection

from dockertest import Appcenter, tiny_app


def fail_if_file_exists(f,):
    if os.path.exists(f):
        fail('%s still exists' % f)


def fail_if_file_does_not_exist(f,):
    if not os.path.exists(f):
        fail('%s still exists' % f)


if __name__ == '__main__':

    with Appcenter() as appcenter:
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
            app.verify(joined=False)

            lo = get_ldap_connection()
            print(lo.searchDn(filter='(&(cn=%s-*)(objectClass=univentionMemberServer)(!(aRecord=*))(!(macAddress=*)))' % app.app_name[:5], unique=True, required=True,))

        finally:
            app.uninstall()
            app.remove()

        fail_if_file_does_not_exist('/var/lib/univention-appcenter/apps/%s/data/test123' % app.app_name)
        fail_if_file_exists('/var/lib/univention-appcenter/apps/%s/conf/test123' % app.app_name)
        fail_if_file_exists('/var/lib/univention-appcenter/apps/%s/conf/base.conf' % app.app_name)

        found_conf = False
        backup_dir = '/var/lib/univention-appcenter/backups/'
        for d in os.listdir(backup_dir):
            if d.startswith('appcenter-backup-%s:' % app.app_name):
                conffile = os.path.join(backup_dir, d, 'conf', 'test123',)
                if os.path.exists(conffile):
                    f = open(conffile)
                    res = f.readlines()
                    if res == ['Test 123 Conf\n']:
                        found_conf = True
        if not found_conf:
            fail('Conf backup file not found')

        lo = get_ldap_connection()
        res = lo.searchDn(filter='(&(cn=%s-*)(objectClass=univentionMemberServer))' % app.app_name[:5])
        if res:
            fail('The LDAP object has not been removed: %s' % res)
