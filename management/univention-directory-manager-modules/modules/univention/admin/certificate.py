# SPDX-FileCopyrightText: 2022-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| pki X.509 DER certificate handling"""

import base64
import datetime

from cryptography import x509
from cryptography.x509.oid import NameOID

import univention.admin
import univention.admin.localization
import univention.admin.mapping
import univention.admin.syntax
from univention.admin.layout import Group, Tab
from univention.admin.log import log


translation = univention.admin.localization.translation('univention.admin')
_ = translation.translate

_CRYPT_HAS_UTC = hasattr(x509.Certificate, 'not_valid_after_utc')  # > Debian bookworm


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
            short_description=_('PKI certificate (DER format)'),
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
    ])  # fmt: skip


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
    """Import a certificate in DER format."""
    if not user_certificate:
        return {}
    try:
        certificate = base64.b64decode(user_certificate)
    except base64.binascii.Error:
        return {}
    try:
        cert = x509.load_der_x509_certificate(certificate)

        not_before = cert.not_valid_before_utc if _CRYPT_HAS_UTC else cert.not_valid_before.replace(tzinfo=datetime.UTC)
        not_after = cert.not_valid_after_utc if _CRYPT_HAS_UTC else cert.not_valid_after.replace(tzinfo=datetime.UTC)
        values = {
            'certificateDateNotBefore': not_before.date().isoformat(),
            'certificateDateNotAfter': not_after.date().isoformat(),
            'certificateVersion': str(cert.version.value),
            'certificateSerial': str(cert.serial_number),
        }
        for entity, prefix in (
            (cert.issuer, 'certificateIssuer'),
            (cert.subject, 'certificateSubject'),
        ):
            for oid, attr in load_certificate.ATTR_MAP.items():
                try:
                    attrs = entity.get_attributes_for_oid(oid)
                    value = attrs[0].value if attrs else None
                except (IndexError, AttributeError, ValueError):
                    value = None
                values[prefix + attr] = value
    except (ValueError, TypeError, AttributeError):
        return {}

    log.trace('certificate', value=values)
    return values


load_certificate.ATTR_MAP = {
    NameOID.COUNTRY_NAME: 'Country',
    NameOID.STATE_OR_PROVINCE_NAME: 'State',
    NameOID.LOCALITY_NAME: 'Location',
    NameOID.ORGANIZATION_NAME: 'Organisation',
    NameOID.ORGANIZATIONAL_UNIT_NAME: 'OrganisationalUnit',
    NameOID.COMMON_NAME: 'CommonName',
    NameOID.EMAIL_ADDRESS: 'Mail',
}


class PKIIntegration:
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
