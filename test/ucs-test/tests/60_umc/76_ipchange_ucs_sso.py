#!/usr/share/ucs-test/runner python3
## desc: Check if ip_change also changes the ucs-sso entry
## roles-not: [basesystem]
## exposure: dangerous

import atexit
from ldap.filter import filter_format

import univention.testing.strings as uts
import univention.testing.udm as udm_test
from univention.config_registry import ConfigRegistry
from univention.testing import utils
from univention.testing.umc import Client


if __name__ == '__main__':
    ucr = ConfigRegistry()
    ucr.load()

    # Since the S4 connector uses a object based synchronization,
    # it is a problem to change the same object in short intervals,
    # see https://forge.univention.org/bugzilla/show_bug.cgi?id=35336
    if utils.s4connector_present():
        # stopping is a no-op if the connector doesn't run on this host
        atexit.register(utils.start_s4connector)
        utils.stop_s4connector()

    with udm_test.UCSTestUDM() as udm:
        role = ucr.get('server/role')
        sso_prefix = ucr.get('keycloak/server/sso/fqdn', 'ucs-sso-ng').split('.', 1)[0]

        # Don't create a new Master object
        if role == 'domaincontroller_master':
            role = 'domaincontroller_backup'
        computerName = uts.random_string()
        computer = udm.create_object(
            'computers/%s' % role, name=computerName,
            password='univention',
            network='cn=default,cn=networks,%s' % ucr.get('ldap/base'),
            univentionService='univention-saml',
            check_for_drs_replication=False,
        )

        lo = utils.get_ldap_connection()
        computer_object = lo.get(computer)
        print(computer_object)

        iface = ucr.get('interfaces/primary', 'eth0')

        # Bug #59759: the host records of the Keycloak and Samba 4 services must not be
        # modified for a server they don't belong to, i.e. if they don't contain its
        # current IP address. This uses its own computer object with a freshly allocated
        # IP address, and runs before the tests below, which put the IP address of their
        # computer object into the ucs-sso record on purpose.
        foreignName = uts.random_string()
        foreign_computer = udm.create_object(
            'computers/%s' % role, name=foreignName,
            password='univention',
            network='cn=default,cn=networks,%s' % ucr.get('ldap/base'),
            check_for_drs_replication=False,
        )
        foreign_records = {
            record_dn: record.get('aRecord', [])
            for name in [sso_prefix, 'gc._msdcs', 'DomainDnsZones', 'ForestDnsZones']
            for record_dn, record in lo.search(filter_format('(&(objectClass=dNSZone)(relativeDomainName=%s))', [name]))
        }
        assert foreign_records, 'no host record found which could be modified erroneously.'

        foreign_ip = lo.get(foreign_computer)['aRecord'][0]
        for record_dn, addresses in foreign_records.items():
            assert foreign_ip not in addresses, f'{record_dn} already contains {foreign_ip!r}, the just allocated IP address of {foreign_computer}.'

        try:
            new_ip = '1.2.3.11'

            client = Client(ucr.get('ldap/master'), '%s$' % foreignName, 'univention')
            client.umc_command('ip/change', {'ip': new_ip, 'oldip': foreign_ip.decode('UTF-8'), 'netmask': ucr.get('interfaces/%s/netmask' % iface), 'role': role})

            utils.wait_for_replication()
            utils.verify_ldap_object(foreign_computer, {'aRecord': [new_ip]}, strict=True)
            # the host records are modified before the computer object, so no further waiting is required
            for record_dn, addresses in foreign_records.items():
                utils.verify_ldap_object(record_dn, {'aRecord': addresses}, strict=True, retry_count=0)
        finally:
            for record_dn, addresses in foreign_records.items():
                lo.modify(record_dn, [('aRecord', lo.get(record_dn).get('aRecord', []), addresses)])

        # Test change IPv4 address
        ip = computer_object['aRecord']
        utils.verify_ldap_object(computer, {'aRecord': ip})

        for ucs_sso_dn, ucs_sso_object in lo.search(filter_format('relativeDomainName=%s', [sso_prefix]), unique=True, required=True):
            ips = ucs_sso_object.get('aRecord')
            break
        else:
            raise ValueError(f'no {sso_prefix} host found.')

        lo.modify(ucs_sso_dn, [('aRecord', ips, ips + ip)])
        try:
            new_ip = '1.2.3.10'

            client = Client(ucr.get('ldap/master'), '%s$' % computerName, 'univention')
            client.umc_command('ip/change', {'ip': new_ip, 'oldip': ip[0].decode('UTF-8'), 'netmask': ucr.get('interfaces/%s/netmask' % iface), 'role': role})

            utils.wait_for_replication()
            utils.verify_ldap_object(computer, {'aRecord': [new_ip]}, strict=True)
            utils.verify_ldap_object(ucs_sso_dn, {'aRecord': [*ips, new_ip]}, strict=True)
        finally:
            lo.modify(ucs_sso_dn, [('aRecord', lo.get(ucs_sso_dn).get('aRecord'), ips)])

        # Test change IPv6 address
        if ucr.get('interfaces/%s/ipv6/default/prefix' % iface):
            ip = computer_object['aAAARecord']
            utils.verify_ldap_object(computer, {'aAAARecord': ip})

            for ucs_sso_dn, ucs_sso_object in lo.search(filter_format('relativeDomainName=%s', [sso_prefix]), unique=True, required=True):
                ips = ucs_sso_object.get('aAAARecord')
                break
            else:
                raise ValueError('no ucs-sso host found.')

            lo.modify(ucs_sso_dn, [('aAAARecord', ips, ips + ip)])
            try:
                new_ip = 'fdff:1:2:3:10'
                new_ip = 'fdff:0001:0002:0003:0000:0000:0000:0010'

                client = Client(ucr.get('ldap/master'), '%s$' % computerName, 'univention')
                client.umc_command('ip/change', {'ip': new_ip, 'oldip': ip[0].decode('UTF-8'), 'netmask': ucr.get('interfaces/%s/ipv6/default/prefix' % iface), 'role': role})

                utils.wait_for_replication()
                utils.verify_ldap_object(computer, {'aAAARecord': [new_ip]}, strict=True)
                utils.verify_ldap_object(ucs_sso_dn, {'aAAARecord': [*ips, new_ip]}, strict=True)
            finally:
                lo.modify(ucs_sso_dn, [('aAAARecord', lo.get(ucs_sso_dn).get('aAAARecord'), ips)])
