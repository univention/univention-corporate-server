# -*- coding: utf-8 -*-
#
# Copyright 2022-2024 Univention GmbH
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

"""|UDM| pki X.509 DER certificate handling"""

import base64

from M2Crypto import X509

import univention.admin
import univention.admin.localization
import univention.admin.mapping
import univention.admin.syntax
import univention.debug as ud
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin')
_ = translation.translate


def pki_option():
    return univention.admin.option(
        short_description=_('Public key infrastructure account'),
        default=False,
        editable=True,
        objectClasses=['pkiUser'],
    )


def pki_properties():
    return {
        'userCertificate': univention.admin.property(
            short_description=_("PKI certificate (DER format)"),
            long_description=_('Public key infrastructure - certificate'),
            syntax=univention.admin.syntax.Base64Upload,
            dontsearch=True,
            options=['pki'],
        ),
        'certificateIssuerCountry': univention.admin.property(
            short_description=_('Issuer Country'),
            long_description=_('Certificate Issuer Country'),
            syntax=univention.admin.syntax.string,
            dontsearch=True,
            editable=False,
            options=['pki'],
        ),
        'certificateIssuerState': univention.admin.property(
            short_description=_('Issuer State'),
            long_description=_('Certificate Issuer State'),
            syntax=univention.admin.syntax.string,
            dontsearch=True,
            editable=False,
            options=['pki'],
        ),
        'certificateIssuerLocation': univention.admin.property(
            short_description=_('Issuer Location'),
            long_description=_('Certificate Issuer Location'),
            syntax=univention.admin.syntax.string,
            dontsearch=True,
            editable=False,
            options=['pki'],
        ),
        'certificateIssuerOrganisation': univention.admin.property(
            short_description=_('Issuer Organisation'),
            long_description=_('Certificate Issuer Organisation'),
            syntax=univention.admin.syntax.string,
            dontsearch=True,
            editable=False,
            options=['pki'],
        ),
        'certificateIssuerOrganisationalUnit': univention.admin.property(
            short_description=_('Issuer Organisational Unit'),
            long_description=_('Certificate Issuer Organisational Unit'),
            syntax=univention.admin.syntax.string,
            dontsearch=True,
            editable=False,
            options=['pki'],
        ),
        'certificateIssuerCommonName': univention.admin.property(
            short_description=_('Issuer Common Name'),
            long_description=_('Certificate Issuer Common Name'),
            syntax=univention.admin.syntax.string,
            dontsearch=True,
            editable=False,
            options=['pki'],
        ),
        'certificateIssuerMail': univention.admin.property(
            short_description=_('Issuer Mail'),
            long_description=_('Certificate Issuer Mail'),
            syntax=univention.admin.syntax.string,
            dontsearch=True,
            editable=False,
            options=['pki'],
        ),
        'certificateSubjectCountry': univention.admin.property(
            short_description=_('Subject Country'),
            long_description=_('Certificate Subject Country'),
            syntax=univention.admin.syntax.string,
            dontsearch=True,
            editable=False,
            options=['pki'],
        ),
        'certificateSubjectState': univention.admin.property(
            short_description=_('Subject State'),
            long_description=_('Certificate Subject State'),
            syntax=univention.admin.syntax.string,
            dontsearch=True,
            editable=False,
            options=['pki'],
        ),
        'certificateSubjectLocation': univention.admin.property(
            short_description=_('Subject Location'),
            long_description=_('Certificate Subject Location'),
            syntax=univention.admin.syntax.string,
            dontsearch=True,
            editable=False,
            options=['pki'],
        ),
        'certificateSubjectOrganisation': univention.admin.property(
            short_description=_('Subject Organisation'),
            long_description=_('Certificate Subject Organisation'),
            syntax=univention.admin.syntax.string,
            dontsearch=True,
            editable=False,
            options=['pki'],
        ),
        'certificateSubjectOrganisationalUnit': univention.admin.property(
            short_description=_('Subject Organisational Unit'),
            long_description=_('Certificate Subject Organisational Unit'),
            syntax=univention.admin.syntax.string,
            dontsearch=True,
            editable=False,
            options=['pki'],
        ),
        'certificateSubjectCommonName': univention.admin.property(
            short_description=_('Subject Common Name'),
            long_description=_('Certificate Subject Common Name'),
            syntax=univention.admin.syntax.string,
            dontsearch=True,
            editable=False,
            options=['pki'],
        ),
        'certificateSubjectMail': univention.admin.property(
            short_description=_('Subject Mail'),
            long_description=_('Certificate Subject Mail'),
            syntax=univention.admin.syntax.string,
            dontsearch=True,
            editable=False,
            options=['pki'],
        ),
        'certificateDateNotBefore': univention.admin.property(
            short_description=_('Valid from'),
            long_description=_('Certificate valid from'),
            syntax=univention.admin.syntax.date,
            dontsearch=True,
            editable=False,
            options=['pki'],
        ),
        'certificateDateNotAfter': univention.admin.property(
            short_description=_('Valid until'),
            long_description=_('Certificate valid until'),
            syntax=univention.admin.syntax.date,
            dontsearch=True,
            editable=False,
            options=['pki'],
        ),
        'certificateVersion': univention.admin.property(
            short_description=_('Version'),
            long_description=_('Certificate Version'),
            syntax=univention.admin.syntax.string,
            dontsearch=True,
            editable=False,
            options=['pki'],
        ),
        'certificateSerial': univention.admin.property(
            short_description=_('Serial'),
            long_description=_('Certificate Serial'),
            syntax=univention.admin.syntax.string,
            dontsearch=True,
            editable=False,
            options=['pki'],
        ),
    }


def register_pki_mapping(mapping):
    mapping.register('userCertificate', 'userCertificate;binary', univention.admin.mapping.mapBase64, univention.admin.mapping.unmapBase64)


def pki_tab():
    return Tab(_('Certificate'), _('Certificate'), advanced=True, layout=[
        Group(_('General'), '', [
            'userCertificate',
        ]),
        Group(_('Subject'), '', [
            ['certificateSubjectCommonName', 'certificateSubjectMail'],
            ['certificateSubjectOrganisation', 'certificateSubjectOrganisationalUnit'],
            'certificateSubjectLocation',
            ['certificateSubjectState', 'certificateSubjectCountry'],
        ]),
        Group(_('Issuer'), '', [
            ['certificateIssuerCommonName', 'certificateIssuerMail'],
            ['certificateIssuerOrganisation', 'certificateIssuerOrganisationalUnit'],
            'certificateIssuerLocation',
            ['certificateIssuerState', 'certificateIssuerCountry'],
        ]),
        Group(_('Validity'), '', [
            ['certificateDateNotBefore', 'certificateDateNotAfter'],
        ]),
        Group(_('Misc'), '', [
            ['certificateVersion', 'certificateSerial'],
        ]),
    ])


def register_pki_integration(property_descriptions, mapping, options, layout):
    """
    Register the PKI integration for the given object type.

    .. deprecated: 5.0-3
         Warning: Using this function the property descriptions, mapping, options and layout are updated without atomicity.
    """
    options['pki'] = pki_option()
    property_descriptions.update(pki_properties())
    layout.append(pki_tab())
    register_pki_mapping(mapping)


def load_certificate(user_certificate):
    """Import a certificate in DER format"""
    if not user_certificate:
        return {}
    try:
        certificate = base64.b64decode(user_certificate)
    except base64.binascii.Error:
        return {}
    try:
        x509 = X509.load_cert_string(certificate, X509.FORMAT_DER)

        values = {
            'certificateDateNotBefore': x509.get_not_before().get_datetime().date().isoformat(),
            'certificateDateNotAfter': x509.get_not_after().get_datetime().date().isoformat(),
            'certificateVersion': str(x509.get_version()),
            'certificateSerial': str(x509.get_serial_number()),
        }
        X509.m2.XN_FLAG_SEP_MULTILINE & ~X509.m2.ASN1_STRFLGS_ESC_MSB | X509.m2.ASN1_STRFLGS_UTF8_CONVERT
        for entity, prefix in (
                (x509.get_issuer(), "certificateIssuer"),
                (x509.get_subject(), "certificateSubject"),
        ):
            for key, attr in load_certificate.ATTR.items():
                try:
                    value = getattr(entity, key)
                except TypeError:  # not expecting type '<class 'NoneType'>'
                    value = None
                values[prefix + attr] = value
    except (X509.X509Error, AttributeError):
        return {}

    ud.debug(ud.ADMIN, ud.INFO, 'value=%s' % values)
    return values


load_certificate.ATTR = {
    "C": "Country",
    "ST": "State",
    "L": "Location",
    "O": "Organisation",
    "OU": "OrganisationalUnit",
    "CN": "CommonName",
    "emailAddress": "Mail",
}


class PKIIntegration(object):

    def pki_open(self):
        if self.exists():
            self.reload_certificate()

    def reload_certificate(self):
        """Reload user certificate."""
        if 'pki' not in self.options:
            return
        self.info['certificateSubjectCountry'] = ''
        self.info['certificateSubjectState'] = ''
        self.info['certificateSubjectLocation'] = ''
        self.info['certificateSubjectOrganisation'] = ''
        self.info['certificateSubjectOrganisationalUnit'] = ''
        self.info['certificateSubjectCommonName'] = ''
        self.info['certificateSubjectMail'] = ''
        self.info['certificateIssuerCountry'] = ''
        self.info['certificateIssuerState'] = ''
        self.info['certificateIssuerLocation'] = ''
        self.info['certificateIssuerOrganisation'] = ''
        self.info['certificateIssuerOrganisationalUnit'] = ''
        self.info['certificateIssuerCommonName'] = ''
        self.info['certificateIssuerMail'] = ''
        self.info['certificateDateNotBefore'] = ''
        self.info['certificateDateNotAfter'] = ''
        self.info['certificateVersion'] = ''
        self.info['certificateSerial'] = ''
        _certificate = self.info.get('userCertificate')
        certificate = _certificate[0] if isinstance(_certificate, list) else _certificate
        values = load_certificate(certificate)
        if values:
            self.info.update(values)
        else:
            self.info['userCertificate'] = ''
