#!/usr/share/ucs-test/runner pytest-3
## desc: Include CNames as SANs in certificates
## roles: [domaincontroller_master]
## exposure: dangerous
## bugs: [44469]

from M2Crypto import X509

import univention.testing.ucr as ucr_test
import univention.testing.udm as udm_test
from univention.testing import strings, utils


def test_san():
    with udm_test.UCSTestUDM() as udm, ucr_test.UCSTestConfigRegistry() as ucr:
        membername = strings.random_string()
        udm.create_object(
            'computers/memberserver',
            position='cn=memberserver,cn=computers,%(ldap/base)s' % ucr,
            set={
                'name': membername,
                'password': 'univention',
                'network': 'cn=default,cn=networks,%(ldap/base)s' % ucr,
                'dnsEntryZoneAlias': '%(domainname)s zoneName=%(domainname)s,cn=dns,%(ldap/base)s www' % ucr,
            },
        )

        x509 = X509.load_cert('/etc/univention/ssl/%s/cert.pem' % membername)
        san = x509.get_ext('subjectAltName').get_value()

        expected = "www.%(domainname)s" % ucr
        if expected not in san:
            utils.fail('Missing SAN %r in certificate of default network: %r' % (expected, san))


def test_san_different_network():
    with udm_test.UCSTestUDM() as udm, ucr_test.UCSTestConfigRegistry() as ucr:
        zonename = strings.random_string(length=5) + '.' + strings.random_string(length=5)

        forwardzonedn = udm.create_object(
            'dns/forward_zone',
            position='cn=dns,%(ldap/base)s' % ucr,
            set={
                'nameserver': ucr.get('hostname'),
                'zone': zonename,
            },
        )

        membername = strings.random_string()
        udm.create_object(
            'computers/memberserver',
            position='cn=memberserver,cn=computers,%(ldap/base)s' % ucr,
            set={
                'name': membername,
                'password': 'univention',
                'network': 'cn=default,cn=networks,%(ldap/base)s' % ucr,
                'dnsEntryZoneAlias': '%s %s www' % (ucr.get('domainname'), forwardzonedn),
            },
        )

        x509 = X509.load_cert('/etc/univention/ssl/%s/cert.pem' % membername)
        san = x509.get_ext('subjectAltName').get_value()

        expected = "www.%s" % (zonename,)
        if expected not in san:
            utils.fail('Missing SAN %r in certificate of non-default network: %r' % (expected, san))
