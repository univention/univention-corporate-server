#!/usr/share/ucs-test/runner python3
## desc: test automatic reconnect of uldap.py
## tags: [skip_admember,reconnect]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - python3-univention-directory-manager
##   - python3-univention

import subprocess
import time
import traceback
from _thread import start_new_thread

from ldap import INSUFFICIENT_ACCESS, UNAVAILABLE
from ldap.filter import filter_format

import univention.admin.uexceptions
import univention.admin.uldap
import univention.testing.strings as uts
import univention.testing.ucr
import univention.testing.ucr as ucr_test
import univention.testing.udm
import univention.uldap
from univention.testing import utils


def delayed_slapd_restart():
    global restart_finished
    subprocess.call(['systemctl', 'daemon-reload'])
    time.sleep(3)
    print('Restarting slapd')
    subprocess.call(['service', 'slapd', 'stop'])
    subprocess.call(['service', 'slapd', 'start'])
    time.sleep(5)
    print('Restarting slapd again')
    subprocess.call(['service', 'slapd', 'stop'])
    subprocess.call(['service', 'slapd', 'start'])
    time.sleep(3)
    print('Restart finished')
    restart_finished = True


restart_finished = False


def main():
    global restart_finished
    with ucr_test.UCSTestConfigRegistry() as ucr, univention.testing.udm.UCSTestUDM() as udm:
        account = utils.UCSTestDomainAdminCredentials()

        user_dn, username = udm.create_user()

        # test with univention.uldap and univention.admin.uldap connection objects
        for access in (univention.uldap.access, univention.admin.uldap.access):
            follow_referral = False  # TODO: implement a truish variant?
            # get connection
            lo = access(
                host=ucr['hostname'],
                base=ucr.get('ldap/base'),
                binddn=account.binddn,
                bindpw=account.bindpw,
                start_tls=2,
                follow_referral=follow_referral)

            if isinstance(lo, tuple):
                lo = lo[0]

            print(f'Starting test set with connection {lo!r}')

            print('Testing lo.search operation...')
            restart_finished = False
            start_new_thread(delayed_slapd_restart, ())
            filter_s = filter_format('(uid=%s)', (account.username,))
            count = 0
            try:
                while not restart_finished:
                    try:
                        res = lo.search(filter=filter_s)[0][0]
                        assert res == account.binddn
                        count += 1
                    except UNAVAILABLE:
                        # ignore ldap.UNAVAILABLE, slapd is started but database backend not yet available
                        # python3-ldap reconnect does not handle this situation
                        print('ignore UNAVAILABLE')
                    except univention.admin.uexceptions.ldapError as exc:
                        if 'Server is unavailable'.lower() not in str(exc).lower():
                            raise
                        print('ignore univention.admin.uexceptions.ldapError Server is unavailable')
                print(f'LDAP search finished successfully {count} times.')
            except Exception as exc:
                print(f'LDAP modify failed after succeeding {count} times.')
                print(traceback.format_exc())
                utils.fail(f'lo.search() is not restart-safe with {lo!r} follow_referral={follow_referral!r}: {exc}')

            # test lo.modify operation
            restart_finished = False
            start_new_thread(delayed_slapd_restart, ())
            count = 0
            try:
                old_description = b''
                while not restart_finished:
                    try:
                        new_description = f'Foo bar {uts.random_string(5)}'.encode()
                        res = lo.modify(user_dn, [['description', old_description, new_description]])
                        assert res == user_dn
                        old_description = new_description
                        count += 1
                    except UNAVAILABLE:
                        # ignore ldap.UNAVAILABLE, slapd is started but database backend not yet available
                        # python3-ldap reconnect does not handle this situation
                        pass
                    except univention.admin.uexceptions.ldapError as exc:
                        if 'Server is unavailable'.lower() not in str(exc).lower():
                            raise
                        print('ignore univention.admin.uexceptions.ldapError Server is unavailable')
                print(f'LDAP modify finished successfully {count} times.')
            except (INSUFFICIENT_ACCESS, univention.admin.uexceptions.permissionDenied):
                pass  # On DC Slaves no objects can be modified
            except Exception as exc:
                print(f'LDAP modify failed after succeeding {count} times.')
                print(traceback.format_exc())
                utils.fail(f'lo.modify() is not restart-safe with {lo!r} follow_referral={follow_referral!r}: {exc}')

            # TODO: add a check for rename() and add()


if __name__ == '__main__':
    main()
