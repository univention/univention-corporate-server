#!/usr/share/ucs-test/runner python3
## desc: check if radius mac whitelisting is working
## tags: [apptest, radius]
## packages:
##   - univention-radius
## join: true
## exposure: dangerous

import subprocess
import tempfile

import univention.config_registry
import univention.testing.ucr as ucr_test
import univention.testing.udm as udm_test
from univention.testing import strings, utils


def eapol_test(username, client_mac,):
    testdata = '''network={{
        key_mgmt=WPA-EAP
        eap=PEAP
        identity="{}"
        anonymous_identity="anonymous"
        password="univention"
        phase2="autheap=MSCHAPV2"
}}
'''.format(username)
    with tempfile.NamedTemporaryFile() as fd:
        fd.write(testdata.encode('UTF-8'))
        fd.flush()
        subprocess.check_call(['/usr/sbin/eapol_test', '-c', fd.name, '-M', client_mac, '-s', 'testing123'])


def main():
    with ucr_test.UCSTestConfigRegistry(), udm_test.UCSTestUDM() as udm:
        client_mac = strings.random_mac()
        userdn, username = udm.create_user(networkAccess=1)
        clientdn = udm.create_object(
            'computers/ipmanagedclient',
            set={
                'name': strings.random_name(),
                'mac': client_mac,
                'networkAccess': 0,
            },)
        univention.config_registry.handler_set(['radius/mac/whitelisting=true'])

        # try authentication with disabled client
        try:
            eapol_test(username, client_mac,)
        except subprocess.CalledProcessError:
            pass
        else:
            utils.fail('User could authenticate on client with disabled network!')

        # try authentication with enabled client
        udm.modify_object(
            'computers/ipmanagedclient',
            dn=clientdn,
            set={
                'networkAccess': 1,
            },)

        try:
            eapol_test(username, client_mac,)
        except subprocess.CalledProcessError:
            utils.fail('User could not authenticate on client with enabled network!')

        # try authentication with unknown client
        try:
            eapol_test(username, strings.random_mac(),)
        except subprocess.CalledProcessError:
            pass
        else:
            utils.fail('User could authenticate on client with unknown mac address!')


if __name__ == '__main__':
    main()
