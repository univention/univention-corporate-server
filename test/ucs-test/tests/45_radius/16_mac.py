#!/usr/share/ucs-test/runner pytest-3 -s -vvv
## desc: check if MAC is returned correctly in radius response
## tags: [apptest, radius]
## packages:
##   - univention-radius
## join: true
## exposure: dangerous

import re
import subprocess

import pytest

from univention.testing import strings


RE_VLAN_ID = re.compile('Tunnel-Private-Group-Id:0 = "(.*?)"')


def restart_service(service):
    subprocess.call(['systemctl', 'restart', service])


def default_vlan_id(ucr, vlan_id, restart_freeradius):
    if not vlan_id:
        ucr.handler_unset(['freeradius/vlan-id'])
    else:
        ucr.handler_set([f'freeradius/vlan-id={vlan_id}'])
    if restart_freeradius:
        restart_service('freeradius')


def find_vlanid(message):
    search = RE_VLAN_ID.search(message)
    if search:
        return search[1].strip()


def radius_auth(username, password, user_type, auth_method):
    if user_type == 'computer':
        p = subprocess.run([
            'radtest',
            '-x',
            '-t',
            'mschap',
            username,
            password,
            '127.0.0.1',
            '0',
            'testing123',
        ], capture_output=True, text=True, check=True)
    elif user_type == 'user':
        if auth_method in ('pap', 'mschap'):
            p = subprocess.run(['radtest', '-x', '-t', auth_method, username, password, 'localhost', '0', 'testing123'], capture_output=True, text=True, check=True)
        elif auth_method == 'eap':
            credentials = f'user-name={username}, user-password={password}'
            echo_username_password = subprocess.Popen(('echo', credentials), stdout=subprocess.PIPE)
            p = subprocess.run(['radeapclient', '-x', 'localhost', 'auth', 'testing123'], stdin=echo_username_password.stdout, capture_output=True, text=True, check=True)
            echo_username_password.wait()
        else:
            raise ValueError(f"Unexpected radius authmethod {auth_method!r}")
    else:
        raise ValueError(f"Unexpected user_type {user_type!r}")
    return find_vlanid(p.stdout)


@pytest.mark.parametrize('vlg1, vlg2, ucr_vlan_id, expected_vlan_id, restart_freeradius, mac_auth, add_to_groups, expected_access', [
    ('1', '', '2', '1', True, True, [1, 2], True),
    ('', '3', '2', '3', True, True, [1, 2], True),
    ('', '', '2', '2', True, True, [1, 2], True),
    ('', '', '', None, True, True, [1, 2], True),
    ('', '', '', None, True, False, [], False),
    ('', '', '', None, True, True, [], True),
    ('', '', '', None, True, True, [], False),
])
def test_computer_mac(udm, ucr_session, vlg1, vlg2, ucr_vlan_id, expected_vlan_id, restart_freeradius, mac_auth, add_to_groups, expected_access):
    ucr_session.handler_set([f'freeradius/conf/allow-mac-address-authentication={"yes" if mac_auth else "no"}'])
    default_vlan_id(ucr_session, ucr_vlan_id, restart_freeradius)
    name = "testcomputer"
    mac = strings.random_mac()
    password = "univention"
    hostdn = udm.create_object('computers/linux', set={
        'name': name,
        'mac': [mac],
        'password': password,
        "networkAccess": 1 if expected_access and len(add_to_groups) == 0 else 0,
    })
    if 1 in add_to_groups:
        group1dn, group1name = udm.create_group(set={
            'networkAccess': 1,
            'hosts': hostdn,
            'vlanId': vlg1,
        })
    if 2 in add_to_groups:
        group2dn, group2name = udm.create_group(set={
            'networkAccess': 1,
            'hosts': hostdn,
            'vlanId': vlg2,
        })

    if expected_access:
        vlanid = radius_auth(mac, password, 'computer', None)
        assert vlanid == expected_vlan_id
    else:
        with pytest.raises(subprocess.CalledProcessError):
            radius_auth(mac, password, 'computer', None)
