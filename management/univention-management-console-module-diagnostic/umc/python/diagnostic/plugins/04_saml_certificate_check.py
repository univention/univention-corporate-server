#!/usr/bin/python3
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2017-2024 Univention GmbH
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

import glob
import socket
from base64 import b64decode
from subprocess import call
from typing import Any, Callable, Dict, Iterator, List, Tuple

import requests
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from defusedxml.ElementTree import fromstring, parse
from ldap.filter import filter_format

import univention.uldap
from univention.config_registry import ucr_live as ucr
from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import MODULE, Critical, Instance, Problem


_ = Translation('univention-management-console-module-diagnostic').translate

XML = "/usr/share/univention-management-console/saml/idp/*.xml"
X509CERT = ".//{http://www.w3.org/2000/09/xmldsig#}X509Certificate"

title = _('SAML certificate verification failed!')
run_descr = ['Checks SAML certificates']


def run(_umc_instance: Instance, rerun: bool = False) -> None:
    keycloak_fqdn = '%s%s' % (ucr.get('keycloak/server/sso/fqdn'), ucr.get('keycloak/server/sso/path'))
    sso_fqdn = ucr.get('ucs/server/sso/fqdn')
    umc_saml_idp = ucr.get('umc/saml/idp-server')
    # keycloak
    if keycloak_fqdn and 'realms/ucs/protocol/saml/descriptor' in umc_saml_idp:
        run_keycloak(_umc_instance, keycloak_fqdn, rerun)
    # simplesaml -> can be removed in 5.2
    elif sso_fqdn:
        run_simplesamlphp(_umc_instance, sso_fqdn, rerun)


def run_keycloak(_umc_instance: Instance, sso_fqdn: str, rerun: bool = False) -> None:
    problems: List[str] = []
    buttons: List[Dict[str, str]] = []
    links: List[Dict[str, str]] = []
    umc_modules: List[Dict[str, str]] = []

    idp = False
    for problem in test_identity_provider_certificate_keycloak(sso_fqdn):
        idp = True
        kwargs = problem.kwargs
        problems.append(kwargs["description"])
        buttons += kwargs.get("buttons", [])
        links += kwargs.get("links", [])
        umc_modules += kwargs.get("umc_modules", [])

    if idp and not rerun:
        problems.append(_(
            "Re-execute the join-script <tt>92univention-management-console-web-server</tt> via {join} "
            "or execute <tt>univention-run-join-scripts --force --run-scripts 92univention-management-console-web-server</tt> on the command line as user <i>root</i>.",
        ))
        buttons.append({
            "action": "fix_idp",
            "label": _("Re-run join script"),
        })
        umc_modules.append({
            "module": "join",
            # /univention/command/join/run
            # {"options":{"scripts":["92univention-management-console-web-server"],"force":true}}
        })

    if problems:
        raise Critical(
            description="\n".join(problems),
            buttons=buttons,
            links=links,
            umc_modules=umc_modules,
        )


def test_identity_provider_certificate_keycloak(sso_fqdn: str) -> Iterator[Problem]:
    """
    Check that all IDP certificates from :file:`/usr/share/univention-management-console/saml/idp/*.xml`
    are included in :url:`https:/$(ucr get ucs/server/sso/fqdn)/simplesamlphp/saml2/idp/certificate`.

    Fix: ``univention-run-join-scripts --force --run-scripts 92univention-management-console-web-server``
    """
    MODULE.process("Checks sso certificate by comparing 'ucr get keycloak/server/sso/fqdn' with the Location field in %s" % (XML,))

    backend = default_backend()
    certificate = None

    url = "https://%s/realms/ucs/protocol/saml/descriptor" % (sso_fqdn,)
    links = {
        "name": 'idp',
        "href": url,
        "label": url,
    }

    try:
        res = requests.get(url)
        data = res.content.decode("utf-8")
    except requests.exceptions.ConnectionError as exc:
        yield Critical(
            description=_("Failed to load certificate {{idp}}: {exc}").format(exc=exc),
            links=[links],
        )

    try:
        metadata_dom = fromstring(data)
        der_cert = metadata_dom.find(X509CERT).text
        certificate = x509.load_der_x509_certificate(b64decode(der_cert), backend)
        MODULE.process("Looking for certificate %s" % (certificate.subject,))
    except (ValueError, AttributeError, TypeError) as exc:
        yield Critical(
            description=_("Failed to load certificate {{idp}}: {exc}").format(exc=exc),
            links=[links],
        )

    # compare this with /usr/share/univention-management-console/saml/idp/*.xml
    if certificate:
        for idp in glob.glob(XML):
            try:
                tree = parse(idp)
            except OSError as exc:
                yield Critical(
                    description=_("Failed to load certificate {cert!r}: {exc}").format(cert=idp, exc=exc),
                )
                continue

            root = tree.getroot()
            nodes = root.findall(X509CERT)
            if not nodes:
                yield Critical(
                    description=_("Failed to find any certificate in {cert!r}").format(cert=idp),
                )
                continue

            for node in nodes:  # FIXME: currently only KeyDescriptor/@use="signing" relevant
                text = node.text
                der = b64decode(text)
                try:
                    cert = x509.load_der_x509_certificate(der, backend)
                    MODULE.process("Found certificate %s in %s" % (cert.subject, idp))
                except ValueError as exc:
                    yield Critical(
                        description=_("Failed to load certificate {cert!r}: {exc}").format(cert=idp, exc=exc),
                    )
                    continue

                if cert == certificate:
                    break
            else:
                yield Critical(
                    description=_("The SAML identity provider certificate {cert!r} is missing in {{idp}}.").format(cert=idp),
                    links=[links],
                )


def run_simplesamlphp(_umc_instance: Instance, sso_fqdn: str, rerun: bool = False) -> None:
    problems: List[str] = []
    buttons: List[Dict[str, str]] = []
    links: List[Dict[str, str]] = []
    umc_modules: List[Dict[str, str]] = []

    idp = False
    for problem in test_identity_provider_certificate(sso_fqdn):
        idp = True
        kwargs = problem.kwargs
        problems.append(kwargs["description"])
        buttons += kwargs.get("buttons", [])
        links += kwargs.get("links", [])
        umc_modules += kwargs.get("umc_modules", [])

    if idp and not rerun:
        problems.append(_(
            "Re-execute the join-script <tt>92univention-management-console-web-server</tt> via {join} "
            "or execute <tt>univention-run-join-scripts --force --run-scripts 92univention-management-console-web-server</tt> on the command line as user <i>root</i>.",
        ))
        buttons.append({
            "action": "fix_idp",
            "label": _("Re-run join script"),
        })
        umc_modules.append({
            "module": "join",
            # /univention/command/join/run
            # {"options":{"scripts":["92univention-management-console-web-server"],"force":true}}
        })

    sp = False
    for problem in test_service_provider_certificate():
        sp = True
        kwargs = problem.kwargs
        problems.append(kwargs["description"])
        buttons += kwargs.get("buttons", [])
        links += kwargs.get("links", [])
        umc_modules += kwargs.get("umc_modules", [])

    if sp:
        problems.append(_(
            "If you renewed your certificates please see {sdb-one} and {sdb-all} for more instructions. "
            "In that case the new certificate must be re-uploaded into LDAP.",
        ))
        links += [
            {
                "name": "sdb-one",
                "href": "https://help.univention.com/t/renewing-the-ssl-certificates/37",
                        "label": _("Univention Support Database - Renewing the TLS/SSL certificates"),
            },
            {
                "name": "sdb-all",
                "href": "https://help.univention.com/t/renewing-the-complete-ssl-certificate-chain/36",
                        "label": _("Univention Support Database - Renewing the complete TLS/SSL certificate chain"),
            },
        ]
        if not rerun:
            buttons.append({
                "action": "fix_sp",
                "label": _("Re-upload certificate"),
            })

    if problems:
        raise Critical(
            description="\n".join(problems),
            buttons=buttons,
            links=links,
            umc_modules=umc_modules,
        )


def test_identity_provider_certificate(sso_fqdn: str) -> Iterator[Problem]:
    """
    Check that all IDP certificates from :file:`/usr/share/univention-management-console/saml/idp/*.xml`
    are included in :url:`https:/$(ucr get ucs/server/sso/fqdn)/simplesamlphp/saml2/idp/certificate`.

    Fix: ``univention-run-join-scripts --force --run-scripts 92univention-management-console-web-server``
    """
    MODULE.process("Checks ucs-sso by comparing 'ucr get ucs/server/sso/fqdn' with the Location field in %s" % (XML,))

    backend = default_backend()

    # download from all ip addresses of ucs-sso the IDP certificate (/etc/simplesamlphp/*-idp-certificate.crt)
    _name, _aliaslist, addresslist = socket.gethostbyname_ex(sso_fqdn)
    for i, host in enumerate(addresslist):
        url = "https://%s/simplesamlphp/saml2/idp/certificate" % (host,)
        link = "addr%d" % (i,)
        links = {
            "name": link,
            "href": url,
            "label": url,
        }
        try:
            res = requests.get(url, headers={'host': sso_fqdn}, verify=False)  # required for SNI since Python 2.7.9 / 3.4  # noqa: S501
            data = res.content
        except requests.exceptions.ConnectionError as exc:
            yield Critical(
                description=_("Failed to load certificate {{{link}}}: {exc}").format(link=link, exc=exc),
                links=[links],
            )
            continue

        try:
            certificate = x509.load_pem_x509_certificate(data, backend)
            MODULE.process("Looking for certificate %s" % (certificate.subject,))
        except ValueError as exc:
            yield Critical(
                description=_("Failed to load certificate {{{link}}}: {exc}").format(link=link, exc=exc),
                links=[links],
            )
            continue

        # compare this with /usr/share/univention-management-console/saml/idp/*.xml
        for idp in glob.glob(XML):
            try:
                tree = parse(idp)
            except OSError as exc:
                yield Critical(
                    description=_("Failed to load certificate {cert!r}: {exc}").format(cert=idp, exc=exc),
                )
                continue

            root = tree.getroot()
            nodes = root.findall(X509CERT)
            if not nodes:
                yield Critical(
                    description=_("Failed to find any certificate in {cert!r}").format(cert=idp),
                )
                continue

            for node in nodes:  # FIXME: currently only KeyDescriptor/@use="signing" relevant
                text = node.text
                der = b64decode(text)
                try:
                    cert = x509.load_der_x509_certificate(der, backend)
                    MODULE.process("Found certificate %s in %s" % (cert.subject, idp))
                except ValueError as exc:
                    yield Critical(
                        description=_("Failed to load certificate {cert!r}: {exc}").format(cert=idp, exc=exc),
                    )
                    continue

                if cert == certificate:
                    break
            else:
                yield Critical(
                    description=_("The SAML identity provider certificate {cert!r} is missing in {{{link}}}.").format(cert=idp, link=link),
                    links=[links],
                )


def fix_idp(umc: Instance) -> None:
    MODULE.process("Re-running join-script 92univention-management-console-web-server")
    call(["univention-run-join-scripts", "--force", "--run-scripts", "92univention-management-console-web-server"])
    return run(umc, rerun=True)


def test_service_provider_certificate() -> Iterator[Problem]:
    """
    Check that local certificate :file:`/etc/univention/ssl/$FQHN/cert.pem` matches the certificate in LDAP
    `(&(serviceProviderMetadata=*)(univentionObjectType=saml/serviceprovider)(SAMLServiceProviderIdentifier=https://$FQHN/univention/saml/metadata))`

    Fix: ``/usr/share/univention-management-console/saml/update_metadata``
    """
    backend = default_backend()

    path = '/etc/univention/ssl/%(hostname)s.%(domainname)s/cert.pem' % ucr
    MODULE.process("Checking certificates of %s" % (path,))
    try:
        with open(path, "rb") as fd:
            data = fd.read()
    except OSError as exc:
        yield Critical(
            description=_("Failed to load certificate {cert!r}: {exc}").format(cert=path, exc=exc),
        )
        return

    try:
        certificate = x509.load_pem_x509_certificate(data, backend)
        MODULE.process("Looking for certificate %s" % (certificate.subject,))
    except ValueError as exc:
        yield Critical(
            description=_("Failed to load certificate {cert!r}: {exc}").format(cert=path, exc=exc),
        )
        return

    lo = univention.uldap.getMachineConnection()
    url = "https://%(hostname)s.%(domainname)s/univention/saml/metadata" % ucr
    search = filter_format("(&(serviceProviderMetadata=*)(univentionObjectType=saml/serviceprovider)(SAMLServiceProviderIdentifier=%s))", [url])
    certs = lo.search(search, attr=['serviceProviderMetadata'])
    for dn, attrs in certs:
        link, umcm = dns_link(dn)
        xml = attrs['serviceProviderMetadata'][0].decode('UTF-8')
        root = fromstring(xml)
        nodes = root.findall(X509CERT)
        if not nodes:
            yield Critical(
                description=_("Failed to find any certificate in {{{link}}}").format(link=link),
                umc_modules=[umcm],
            )
            continue

        for node in nodes:
            text = node.text
            der = b64decode(text)
            try:
                cert = x509.load_der_x509_certificate(der, backend)
                MODULE.process("Found certificate %s in %s" % (cert.subject, dn))
            except ValueError as exc:
                yield Critical(
                    description=_("Failed to load certificate {{{link}}}: {exc}").format(link=link, exc=exc),
                    umc_modules=[umcm],
                )
                continue

            if cert == certificate:
                break
        else:
            yield Critical(
                description=_("The SAML identity provider certificate {{{link}}} does not match the local certificate {loc!r}.").format(link=link, loc=path),
                umc_modules=[umcm],
            )


def dns_link(dn: str) -> Tuple[str, Dict[str, Any]]:
    """Create UMC UDM link for DN."""
    link = "udm:saml/serviceprovider"
    umcm: Dict[str, Any] = {
        "module": "udm",
        "flavor": "saml/serviceprovider",
        "props": {
            "openObject": {
                "objectDN": dn,
                "objectType": "saml/serviceprovider",
            },
        },
    }
    return (link, umcm)


def fix_sp(umc: Instance) -> None:
    MODULE.process("Re-running update_metadata")
    call(["/usr/share/univention-management-console/saml/update_metadata"])
    return run(umc, rerun=True)


actions: Dict[str, Callable[[Instance], None]] = {
    "fix_idp": fix_idp,
    "fix_sp": fix_sp,
}


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    run(0)
    main()
