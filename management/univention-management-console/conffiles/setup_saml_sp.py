#!/usr/bin/python3
#
# Univention Management Console
# Univention Configuration Registry Module to rewrite SAML SP configuration for UMC
#
# SPDX-FileCopyrightText: 2015-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


import os
from glob import glob
from subprocess import call
from time import sleep
from urllib.parse import urlparse

from defusedxml import ElementTree, lxml
from saml2 import BINDING_SOAP
from saml2.md import NAMESPACE


workaround = set()


def handler(config_registry, changes):
    if not isinstance(changes.get('umc/saml/idp-server'), list | tuple):
        # workaround for Bug #39444
        print('skipping UCR registration')
        return
    if workaround:
        return  # Bug #39443
    workaround.add(True)
    cleanup()
    metadata_download_failed = []
    metadata_validation_failed = []
    saml_idp = config_registry.get('umc/saml/idp-server')
    if not saml_idp:
        print('umc/saml/idp-server not set, nothing to do')
        return
    if not download_idp_metadata(saml_idp):
        metadata_download_failed.append(saml_idp)
    elif not valid_metadata(saml_idp):
        metadata_validation_failed.append(saml_idp)
    remove_saml_logout_soap_binding(config_registry, saml_idp)
    reload_webserver()
    if not rewrite_sasl_configuration():
        raise SystemExit('Could not rewrite SASL configuration for UMC.')
    if metadata_download_failed:
        raise SystemExit('Could not download IDP metadata for %s' % (', '.join(metadata_download_failed),))
    if metadata_validation_failed:
        raise SystemExit('IDP metadata not valid for %s' % (', '.join(metadata_validation_failed),))


def remove_saml_logout_soap_binding(config_registry, saml_idp):
    """Remove the saml logout SOAP binding from the IDP metadata"""
    if not config_registry.is_true("umc/saml/idp-server/remove-soap-logout", True):
        return
    idp = str(urlparse(saml_idp).netloc)
    filename = '/usr/share/univention-management-console/saml/idp/%s.xml' % (idp,)
    with open(filename) as xmlfile:
        dom_xml = lxml.fromstring(xmlfile.read())
    slo_endpoints = dom_xml.findall('.//{%s}SingleLogoutService' % NAMESPACE)
    modified = False
    for endpoint in slo_endpoints:
        if endpoint.get('Binding') == BINDING_SOAP:
            endpoint.getparent().remove(endpoint)
            modified = True
    if modified:
        with open(filename, 'wb') as xmlfile:
            xmlfile.write(lxml.tostring(dom_xml))


def cleanup():
    for metadata in glob('/usr/share/univention-management-console/saml/idp/*.xml'):
        os.remove(metadata)


def valid_metadata(saml_idp):
    idp = str(urlparse(saml_idp).netloc)
    filename = '/usr/share/univention-management-console/saml/idp/%s.xml' % (idp,)
    try:
        ElementTree.parse(filename)
    except ElementTree.ParseError:
        os.remove(filename)
        return False
    return True


def download_idp_metadata(metadata):
    idp = str(urlparse(metadata).netloc)
    filename = '/usr/share/univention-management-console/saml/idp/%s.xml' % (idp,)
    for i in range(60):
        print('Try to download idp metadata (%s/60)' % (i + 1))
        rc = call([
            '/usr/bin/curl',
            '--fail',
            '--cacert', '/etc/univention/ssl/ucsCA/CAcert.pem',
            '-o', filename,
            metadata,
        ])
        if rc and os.path.exists(filename):
            os.remove(filename)
        if rc == 0:
            return True
        sleep(1)
    return False


def rewrite_sasl_configuration():
    # rewrite UMC-PAM configuration to include every IDP entry
    rc = call(['/usr/sbin/ucr', 'commit', '/etc/pam.d/univention-management-console'])
    # enable saml sasl module
    rc += call(['/usr/sbin/ucr', 'commit', '/etc/ldap/sasl2/slapd.conf'])
    return rc == 0


def reload_webserver():
    try:
        call(['systemctl', 'reload', 'univention-management-console-server'])
    except OSError:
        pass


if __name__ == '__main__':
    from univention.config_registry import ucr
    handler(ucr, {'umc/saml/idp-server': []})
