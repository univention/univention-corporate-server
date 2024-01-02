#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Management Console
# Univention Configuration Registry Module to rewrite SAML SP configuration for UMC
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2015-2024 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

from __future__ import print_function

import os
from glob import glob
from subprocess import call
from time import sleep

from defusedxml import ElementTree, lxml
from saml2 import BINDING_SOAP
from saml2.md import NAMESPACE
from six.moves.urllib_parse import urlparse


workaround = set()


def handler(config_registry, changes):
    if not isinstance(changes.get('umc/saml/idp-server'), (list, tuple)):
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
    except (IOError, OSError):
        pass


if __name__ == '__main__':
    from univention.config_registry import ucr
    handler(ucr, {'umc/saml/idp-server': []})
