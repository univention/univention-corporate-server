#!/usr/share/ucs-test/runner python3
## desc: s4connector check if dNSTombstoned is removed on DNS A record (ucs -> AD) sync
## exposure: dangerous
## packages:
##   - univention-config
##   - univention-directory-manager-tools
##   - univention-s4-connector
##   - bind9-dnsutils

import sys
import time

from samba.auth import system_session
from samba.credentials import Credentials
from samba.dcerpc import dnsp
from samba.ndr import ndr_unpack
from samba.param import LoadParm
from samba.samdb import SamDB

import univention.testing.strings as uts
import univention.testing.udm as udm_test

import dnstests
import s4connector


def find_host_record(samdb, dc):
    # cross-ncs
    controls = ['search_options:1:2']

    ldap_filter = f'(&(objectClass=dnsNode)(dc={dc}))'

    wait = 0
    timeout = 10
    res = None
    while wait < timeout and (res is None or len(res) == 0):
        if res is not None:
            time.sleep(1)
            wait += 1

        res = samdb.search(expression=ldap_filter, controls=controls, attrs=['dNSTombstoned', 'dnsRecord'])

    assert len(res) == 1, 'Failed to find host_record {dc} in samba'
    return res[0]


def extract_a_record(ldap_message):
    for record in ldap_message:
        record = ndr_unpack(dnsp.DnssrvRpcRecord, record)
        if record.wType == dnsp.DNS_TYPE_A:
            return record.data

    return None


if __name__ == '__main__':
    s4connector.exit_if_connector_not_running()

    lp = LoadParm()
    lp.load_default()

    samba_machine_creds = Credentials()
    samba_machine_creds.guess(lp)
    samba_machine_creds.set_machine_account(lp)

    samdb = SamDB(url='/var/lib/samba/private/sam.ldb', session_info=system_session(), credentials=samba_machine_creds, lp=lp)

    with udm_test.UCSTestUDM() as udm:
        res = udm.list_objects('dns/forward_zone')
        zone_dn = res[0][0]

        # cerate new host_record
        host_record_name = uts.random_string()
        ip = dnstests.make_random_ip()
        host_record_dn = udm.create_object('dns/host_record', superordinate=zone_dn, name=host_record_name, a=ip)
        dnstests.check_ldap_object(host_record_dn, 'A Record', 'aRecord', ip)

        s4connector.wait_for_sync()

        ldap_message = find_host_record(samdb, host_record_name)
        samba_ip = extract_a_record(ldap_message['dnsRecord'])
        assert samba_ip == ip, 'false dnsRecord attribute {samba_ip}'
        assert 'dNSTombstoned' not in ldap_message, f"dNSTombstoned attribute set when it shouldn't {ldap_message['dNSTombstoned']}"

        # add dNSTombstoned attribute in AD
        add_dns_tombstoned = f"""
dn: {ldap_message.dn}
changetype: modify
add: dNSTombstoned
dNSTombstoned: TRUE
"""
        samdb.modify_ldif(add_dns_tombstoned)

        ldap_message = find_host_record(samdb, host_record_name)
        assert 'dNSTombstoned' in ldap_message, 'dNSTombstoned attribute unset when it should be set'
        assert ldap_message['dNSTombstoned'][0] == b'TRUE', f'dNSTombstoned has wrong value {ldap_message["dNSTombstoned"]}'

        # change IP in udm and check if dNSTombstoned is removed in AD
        changed_ip = dnstests.make_random_ip()
        udm.modify_object('dns/host_record', dn=host_record_dn, a=changed_ip)
        dnstests.check_ldap_object(host_record_dn, 'A Record', 'aRecord', changed_ip)

        s4connector.wait_for_sync()

        ldap_message = find_host_record(samdb, host_record_name)
        samba_ip = extract_a_record(ldap_message['dnsRecord'])
        assert samba_ip == changed_ip, 'false dnsRecord attribute {samba_ip}'
        assert 'dNSTombstoned' not in ldap_message, f"dNSTombstoned attribute set when it shouldn't {ldap_message['dNSTombstoned']}"

    sys.stdout.flush()
