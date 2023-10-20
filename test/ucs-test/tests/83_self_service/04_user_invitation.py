#!/usr/share/ucs-test/runner python3
## desc: Tests the Univention Self Service Invitation
## tags: [apptest]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##  - univention-self-service-invitation

import subprocess
import time

import univention.testing.udm as udm_test
from univention.testing import utils


def main():
    subprocess.call(['service', 'postfix', 'restart'], close_fds=True,)
    subprocess.call(['service', 'univention-self-service-invitation', 'restart'], close_fds=True,)
    time.sleep(3)
    with udm_test.UCSTestUDM() as udm:
        username = udm.create_user(pwdChangeNextLogin='1', PasswordRecoveryEmail='root@localhost',)[1]
        utils.wait_for_replication_and_postrun()
        time.sleep(45)
        expected = f'Dear user {username}'
        with open('/var/spool/mail/systemmail', 'rb',) as f:
            for line in f.readlines():
                if expected.lower() in line.decode('UTF-8', 'replace',).lower():
                    break
            else:
                utils.fail(f'Expected user invitation "{expected}" not found in /var/spool/mail/systemmail')


if __name__ == '__main__':
    main()
