#!/usr/share/ucs-test/runner pytest-3 -s -vvv
## desc: check if MAC is returned correctly in radius response
## tags: [apptest, radius]
## packages:
##   - univention-radius
## join: true
## exposure: dangerous

import re
import subprocess
from io import StringIO
from tempfile import NamedTemporaryFile

import pyrad.packet
import pytest
from pyrad.client import Client
from pyrad.dictionary import Dictionary

from univention.testing import strings


RE_VLAN_ID = re.compile('Tunnel-Private-Group-Id:0 = "(.*?)"')
RE_MAC = re.compile("([0-9a-f]{2})[^0-9a-f]?([0-9a-f]{2})[^0-9a-f]?([0-9a-f]{2})[^0-9a-f]?([0-9a-f]{2})[^0-9a-f]?([0-9a-f]{2})[^0-9a-f]?([0-9a-f]{2})")
mac_formats = [
    "{}:{}:{}:{}:{}:{}",
    "{}-{}-{}-{}-{}-{}",
    "{}{}.{}{}.{}{}",
    "{}.{}.{}.{}.{}.{}",
    "{}{}{}{}{}{}",
]


def restart_service(service):
    subprocess.call(['systemctl', 'restart', service])


def default_vlan_id(ucr, vlan_id, restart_freeradius):
    if not vlan_id:
        ucr.handler_unset(['freeradius/vlan-id'])
    else:
        ucr.handler_set([f'freeradius/vlan-id={vlan_id}'])
    if restart_freeradius:
        restart_service('freeradius')


@pytest.fixture(scope='module')
def pyrad_client():
    dictionary_text = """
# -*- text -*-
# Copyright (C) 2015 The FreeRADIUS Server project and contributors
#
#       Attributes and values defined in RFC 2865.
#       http://www.ietf.org/rfc/rfc2865.txt
#
#       $Id: b800f754257b91c455ebcf9601343e933ce4ccd8 $
#
ATTRIBUTE       NAS-IP-Address                          4       ipaddr
ATTRIBUTE       User-Name                                       1       string
ATTRIBUTE       Called-Station-Id                       30      string
ATTRIBUTE       Calling-Station-Id                      31      string
ATTRIBUTE       User-Password                           2       string encrypt=1
ATTRIBUTE       NAS-Port                                        5       integer
ATTRIBUTE       NAS-Port-Type                           61      integer
ATTRIBUTE       Framed-MTU                              12      integer
ATTRIBUTE      Service-Type                            6       integer
ATTRIBUTE      Reply-Message                           18      string
ATTRIBUTE      Tunnel-Medium-Type                      65      integer has_tag
ATTRIBUTE      Tunnel-Private-Group-Id                 81      string  has_tag
ATTRIBUTE      Tunnel-Type                             64      integer has_tag
VALUE  Tunnel-Type                     PPTP                    1
VALUE  Tunnel-Type                     L2F                     2
VALUE  Tunnel-Type                     L2TP                    3
VALUE  Tunnel-Type                     ATMP                    4
VALUE  Tunnel-Type                     VTP                     5
VALUE  Tunnel-Type                     AH                      6
VALUE  Tunnel-Type                     IP                      7
VALUE  Tunnel-Type                     MIN-IP                  8
VALUE  Tunnel-Type                     ESP                     9
VALUE  Tunnel-Type                     GRE                     10
VALUE  Tunnel-Type                     DVS                     11
VALUE  Tunnel-Type                     IP-in-IP                12
VALUE  Tunnel-Type                     VLAN                    13
VALUE  Tunnel-Medium-Type              IP                      1
VALUE  Tunnel-Medium-Type              IPv4                    1
VALUE  Tunnel-Medium-Type              IPv6                    2
VALUE  Tunnel-Medium-Type              NSAP                    3
VALUE  Tunnel-Medium-Type              HDLC                    4
VALUE  Tunnel-Medium-Type              BBN-1822                5
VALUE  Tunnel-Medium-Type              IEEE-802                6
VALUE  Tunnel-Medium-Type              E.163                   7
VALUE  Tunnel-Medium-Type              E.164                   8
VALUE  Tunnel-Medium-Type              F.69                    9
VALUE  Tunnel-Medium-Type              X.121                   10
VALUE  Tunnel-Medium-Type              IPX                     11
VALUE  Tunnel-Medium-Type              Appletalk               12
VALUE  Tunnel-Medium-Type              DecNet-IV               13
VALUE  Tunnel-Medium-Type              Banyan-Vines            14
VALUE  Tunnel-Medium-Type              E.164-NSAP              15
"""
    IO = StringIO(dictionary_text)
    server = "localhost"
    server = "localhost"
    secret = b"testing123"
    # Crea un cliente RADIUS
    radius_client = Client(server=server, secret=secret, dict=Dictionary(IO))
    return radius_client


def radius_mab_auth(radius_client, mac_as_username, mac):
    req = radius_client.CreateAuthPacket(code=pyrad.packet.AccessRequest)
    req["User-Name"] = mac_as_username
    req["Calling-Station-Id"] = mac
    req["Service-Type"] = 10
    reply = radius_client.SendPacket(req)
    if reply.code == pyrad.packet.AccessAccept:
        try:
            return str(reply["Tunnel-Private-Group-Id"][0])
        except KeyError:
            return None
    else:
        raise ValueError(f"Access denied: {reply.code}")


def find_vlanid(message):
    search = RE_VLAN_ID.search(message)
    if search:
        return search[1].strip()


def get_wpa_config(username):
    wpa_config = f'''network={{
    key_mgmt=IEEE8021X
    eap=MD5
    identity="{username}"
    password="{username}"
    eapol_flags=3
}}
'''
    return wpa_config


def eap_find_vlanid(stdout):
    lines = stdout.splitlines()
    for i, line in enumerate(lines):
        if 'Tunnel-Private-Group-Id' in line:
            return bytes.fromhex(lines[i + 1].split(':')[1].strip()).decode('utf-8')


def radius_auth(username, password, user_type, auth_method, mac=None, radius_client=None):
    if user_type == 'computer':
        if auth_method == 'pap':
            if radius_client is None:
                raise ValueError("radius_client is required for pap")
            if mac is None:
                raise ValueError("mac is required for pap")
            return radius_mab_auth(radius_client, username, mac)
        if auth_method == 'mschap':
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
        elif auth_method == 'eap':
            if mac is None:
                raise ValueError("mac is required for eap")
            with NamedTemporaryFile() as tmp_file:
                wpa_config = get_wpa_config(username)
                tmp_file.write(wpa_config.encode("UTF-8"))
                tmp_file.seek(0)
                p = subprocess.run([
                    'eapol_test',
                    '-c',
                    tmp_file.name,
                    '-a',
                    '127.0.0.1',
                    '-p',
                    '1812',
                    '-M',
                    mac,
                    '-s',
                    'testing123',
                    '-r0',
                    "-n",
                ], capture_output=True, text=True, check=True)
                return eap_find_vlanid(p.stdout)
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


def all_mac_format_supported(mac):
    mac_ = RE_MAC.match(mac)
    assert mac_

    for mac_format in mac_formats:
        yield mac_format.format(*mac_.groups())


@pytest.mark.parametrize('vlg1, vlg2, ucr_vlan_id, expected_vlan_id, restart_freeradius, mac_auth, add_to_groups, expected_access', [
    ('1', '', '2', '1', True, True, [1, 2], True),
    ('', '3', '2', '3', True, True, [1, 2], True),
    ('', '', '2', '2', True, True, [1, 2], True),
    ('', '', '', None, True, True, [1, 2], True),
    ('', '', '', None, True, False, [], False),
    ('', '', '', None, True, True, [], True),
    ('', '', '', None, True, True, [], False),
])
def test_computer_mac(udm, ucr_session, pyrad_client, vlg1, vlg2, ucr_vlan_id, expected_vlan_id, restart_freeradius, mac_auth, add_to_groups, expected_access):
    ucr_session.handler_set([f'freeradius/conf/allow-mac-address-authentication={"yes" if mac_auth else "no"}'])
    default_vlan_id(ucr_session, ucr_vlan_id, restart_freeradius)
    computername = strings.random_name()
    username = strings.random_username()
    mac = strings.random_mac()
    password = "univention"
    hostdn = udm.create_object('computers/linux', set={
        'name': computername,
        'mac': [mac],
        'password': password,
        "networkAccess": 1 if expected_access and len(add_to_groups) == 0 else 0,
    })
    userdn = udm.create_object('users/user', set={
        'username': username,
        'lastname': username,
        'password': password,
        "networkAccess": 1 if expected_access and len(add_to_groups) == 0 else 0,
    })
    if 1 in add_to_groups:
        data = {
            'networkAccess': 1,
            'hosts': hostdn,
            'users': userdn,
        }
        if vlg1:
            data['vlanId'] = vlg1
        _group1dn, _group1name = udm.create_group(set=data)
    if 2 in add_to_groups:
        data = {
            'networkAccess': 1,
            'hosts': hostdn,
            'users': userdn,
        }
        if vlg2:
            data['vlanId'] = vlg2
        _group2dn, _group2name = udm.create_group(set=data)
    for mac_as_username in all_mac_format_supported(mac):
        if expected_access:
            vlanid = radius_auth(mac_as_username, "", 'computer', 'pap', mac, pyrad_client)
            assert vlanid == expected_vlan_id, f"PAP authentication failed for computer {mac_as_username!r}"
            vlanid = radius_auth(mac_as_username, "", 'computer', 'eap', mac, pyrad_client)
            assert vlanid == expected_vlan_id, f"EAP authentication failed for computer {mac_as_username!r}"
        else:
            with pytest.raises(ValueError):
                radius_auth(mac_as_username, "", 'computer', 'pap', mac, pyrad_client)
            with pytest.raises(subprocess.CalledProcessError):
                radius_auth(mac_as_username, "", 'computer', 'eap', mac, pyrad_client)

    if expected_access:
        vlanid = radius_auth(f"{computername}$", password, 'computer', 'mschap')
        assert vlanid == expected_vlan_id, f"MSCHAP authentication failed for computer {computername!r}"
        vlanid = radius_auth(username, password, 'user', 'mschap')
        assert vlanid == expected_vlan_id, f"MSCHAP authentication failed for username {username!r}"
    else:
        with pytest.raises(subprocess.CalledProcessError):
            radius_auth(username, password, 'user', 'mschap')
        with pytest.raises(subprocess.CalledProcessError):
            radius_auth(f"{computername}$", password, 'computer', 'mschap')
