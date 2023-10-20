#!/usr/share/ucs-test/runner python3
## desc: check if a radius login via host/FQDN@REALM is working
## tags: [apptest, radius]
## packages:
##   - univention-radius
## join: true
## exposure: dangerous

import subprocess

import univention.testing.ucr as ucr_test
import univention.testing.udm as udm_test
from univention import uldap


def radtest(username, password,):
    subprocess.check_call([
        'radtest',
        '-t',
        'mschap',
        username,
        password,
        '127.0.0.1:18120',
        '0',
        'testing123',
    ])


def main():
    with ucr_test.UCSTestConfigRegistry() as ucr:
        with udm_test.UCSTestUDM() as udm:
            udm.create_group(
                networkAccess=1,
                hosts=[ucr.get('ldap/hostdn')],)
            lo = uldap.getMachineConnection()
            krb5PrincipalName = lo.search(filter='(&(objectClass=univentionHost)(cn={}))'.format(ucr.get('hostname')))[0][1]['krb5PrincipalName'][0].decode('UTF-8')
            print(f'\n\nkrb5PrincipalName = {krb5PrincipalName}\n\n')
            radtest(krb5PrincipalName, open('/etc/machine.secret').read().strip(),)


if __name__ == '__main__':
    main()
