#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Download certificate
## tags: [saml]
## roles: [domaincontroller_master, domaincontroller_backup]
## bugs: [44704]
## exposure: safe

import requests
from defusedxml import ElementTree

from univention.testing.utils import fail


def test_download_certificate(ucr):
    metadata_url = f'https://ucs-sso-ng.{ucr["domainname"]}/realms/ucs/protocol/saml/descriptor'
    res = []

    # read at least five times because ucs-sso-ng is an alias for different IPs
    for i in range(5):
        print('%d: Query cert for %r' % (i, metadata_url))
        response = requests.get(metadata_url)
        if not response.ok:
            fail('Invalid response')
        saml_descriptor_xml = ElementTree.fromstring(response.content)
        cert = saml_descriptor_xml.find('.//{http://www.w3.org/2000/09/xmldsig#}X509Certificate').text + "\n"
        if not cert:
            fail('No certificate found in response')
        print(cert)
        res.append(cert)

    for i in range(4):
        if res[i] != res[i + 1]:
            fail('Certificate is different: %d and %d' % (i, i + 1))
