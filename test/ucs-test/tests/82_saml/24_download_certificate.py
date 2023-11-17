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
    # TODO where to get the sso_fqdn from, ucs/server/sso/fqdn or keycloak/server/sso/fqdn
    sso_fqdn = f'ucs-sso-ng.{ucr["domainname"]}'
    metadata_url = f'https://{sso_fqdn}/realms/ucs/protocol/saml/descriptor'
    response = requests.get(metadata_url)
    if not response.ok:
        fail('Invalid response')
    saml_descriptor_xml = ElementTree.fromstring(response.content)
    cert = saml_descriptor_xml.find('.//{http://www.w3.org/2000/09/xmldsig#}X509Certificate')
    if cert is None or not cert.text:
        fail('No certificate found in response')
    print(cert.text)
