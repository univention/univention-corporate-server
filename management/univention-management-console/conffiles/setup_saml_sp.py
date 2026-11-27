#!/usr/bin/python3
#
# Univention Management Console
# Univention Configuration Registry Module to rewrite SAML SP configuration for UMC
#
# SPDX-FileCopyrightText: 2015-2026 Univention GmbH
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
    metadata_download_failed = []
    metadata_validation_failed = []
    saml_idp = config_registry.get('umc/saml/idp-server')
    if not saml_idp:
        cleanup()
        print('umc/saml/idp-server not set, nothing to do')
        return
    # The UMC server reads the metadata whenever it (re)starts. Download to a
    # temporary file and replace the metadata in one step, so that a running or
    # restarting UMC never sees it missing or half written.
    filename = metadata_filename(saml_idp)
    tmp_filename = '%s.tmp' % (filename,)
    if not download_idp_metadata(saml_idp, tmp_filename):
        metadata_download_failed.append(saml_idp)
    elif not valid_metadata(tmp_filename):
        metadata_validation_failed.append(saml_idp)
    if metadata_download_failed or metadata_validation_failed:
        # no usable metadata: remove all, like before, so that callers notice
        if os.path.exists(tmp_filename):
            os.remove(tmp_filename)
        cleanup()
    else:
        remove_saml_logout_soap_binding(config_registry, tmp_filename)
        os.replace(tmp_filename, filename)
        cleanup(keep=filename)
    reload_webserver()
    if not rewrite_sasl_configuration():
        raise SystemExit('Could not rewrite SASL configuration for UMC.')
    if metadata_download_failed:
        raise SystemExit('Could not download IDP metadata for %s' % (', '.join(metadata_download_failed),))
    if metadata_validation_failed:
        raise SystemExit('IDP metadata not valid for %s' % (', '.join(metadata_validation_failed),))


def metadata_filename(saml_idp):
    idp = str(urlparse(saml_idp).netloc)
    return '/usr/share/univention-management-console/saml/idp/%s.xml' % (idp,)


def remove_saml_logout_soap_binding(config_registry, filename):
    """Remove the saml logout SOAP binding from the IDP metadata file"""
    if not config_registry.is_true("umc/saml/idp-server/remove-soap-logout", True):
        return
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


def cleanup(keep=None):
    """Remove the metadata of all IDPs (except the file `keep`)"""
    for metadata in glob('/usr/share/univention-management-console/saml/idp/*.xml'):
        if metadata != keep:
            os.remove(metadata)


def valid_metadata(filename):
    try:
        ElementTree.parse(filename)
    except ElementTree.ParseError:
        return False
    return True


def download_idp_metadata(metadata, filename):
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
