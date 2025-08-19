#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Include CNames as SANs in certificates
## roles: [domaincontroller_master]
## exposure: dangerous
## bugs: [44469]

from cryptography import x509
from cryptography.x509.oid import ExtensionOID

from univention.testing import strings


def test_san(udm, ucr):
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

    with open('/etc/univention/ssl/%s/cert.pem' % membername, 'rb') as f:
        cert = x509.load_pem_x509_certificate(f.read())
    san_ext = cert.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
    san_names = [name.value for name in san_ext.value]

    assert "www.%(domainname)s" % ucr in san_names


def test_san_different_network(udm, ucr):
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

    with open('/etc/univention/ssl/%s/cert.pem' % membername, 'rb') as f:
        cert = x509.load_pem_x509_certificate(f.read())
    san_ext = cert.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
    san_names = [name.value for name in san_ext.value]

    assert "www.%s" % (zonename,) in san_names
