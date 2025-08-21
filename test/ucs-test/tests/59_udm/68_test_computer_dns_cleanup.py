#!/usr/share/ucs-test/runner pytest-3 -s
## desc: Check UDM computer DNS cleanup
## tags: [udm,udm-dns,bug-31926]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import univention.testing.strings as uts
from univention.config_registry import ucr
from univention.testing import utils


class TestComputerDNSCleanup:
    def test_computer_ns_record_cleanup_single_nameserver(self, udm):
        """Check that DNS zones are removed when the only nameserver computer is removed"""
        # Create a domain controller
        dc_name = uts.random_name()
        dc = udm.create_object(
            'computers/domaincontroller_master',
            name=dc_name,
            ip=uts.random_ip(),
            wait_for=True,
        )
        domain = ucr.get('domainname')

        # Create a forward zone with only this DC as nameserver
        forward_zone_name = '%s.%s' % (uts.random_name(), uts.random_dns_record())
        forward_zone = udm.create_object(
            'dns/forward_zone',
            zone=forward_zone_name,
            nameserver=f'{dc_name}.{domain}',
            wait_for=True,
        )

        # Check that the NS record exists
        utils.verify_ldap_object(forward_zone, {'nSRecord': [f'{dc_name}.{domain}.']})

        # Remove the domain controller
        udm.remove_object(
            'computers/domaincontroller_master',
            dn=dc,
        )

        # Check that the entire forward zone is removed (since it was the only nameserver)
        utils.verify_ldap_object(forward_zone, should_exist=False)

    def test_computer_ns_record_cleanup_multiple_nameservers(self, udm):
        """Check that only the NS record is removed when there are multiple nameservers"""
        # Create two domain controllers
        dc1_name = uts.random_name()
        dc1 = udm.create_object(
            'computers/domaincontroller_master',
            name=dc1_name,
            ip=uts.random_ip(),
            wait_for=True,
        )

        dc2_name = uts.random_name()
        _ = udm.create_object(
            'computers/domaincontroller_backup',
            name=dc2_name,
            ip=uts.random_ip(),
            wait_for=True,
        )

        domain = ucr.get('domainname')

        # Create a forward zone with both DCs as nameservers
        forward_zone_name = '%s.%s' % (uts.random_name(), uts.random_dns_record())
        forward_zone = udm.create_object(
            'dns/forward_zone',
            zone=forward_zone_name,
            append={'nameserver': [f'{dc1_name}.{domain}', f'{dc2_name}.{domain}']},
            wait_for=True,
        )

        # Check that both NS records exist
        utils.verify_ldap_object(forward_zone, {
            'nSRecord': [f'{dc1_name}.{domain}.', f'{dc2_name}.{domain}.'],
        })

        # Remove the first domain controller
        udm.remove_object(
            'computers/domaincontroller_master',
            dn=dc1,
        )

        # Check that the zone still exists but only has the second nameserver
        utils.verify_ldap_object(forward_zone, {
            'nSRecord': [f'{dc2_name}.{domain}.'],
        })
