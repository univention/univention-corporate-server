#!/usr/bin/python3
# SPDX-FileCopyrightText: 2017-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import glob
from base64 import b64decode
from collections.abc import Callable, Iterator
from subprocess import call
from typing import Any

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
    umc_saml_idp = ucr.get('umc/saml/idp-server', '')
    if not umc_saml_idp:
        # SSO not configured
        return

    keycloak_uri = ucr.get('ucs/server/sso/uri', 'https://ucs-sso-ng.%s' % ucr['domainname'])
    # keycloak
    if keycloak_uri and 'realms/ucs/protocol/saml/descriptor' in umc_saml_idp:
        run_keycloak(_umc_instance, keycloak_uri, rerun)


def run_keycloak(_umc_instance: Instance, sso_uri: str, rerun: bool = False) -> None:
    problems: list[str] = []
    buttons: list[dict[str, str]] = []
    links: list[dict[str, str]] = []
    umc_modules: list[dict[str, str]] = []

    idp = False
    for problem in test_identity_provider_certificate_keycloak(sso_uri):
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


def test_identity_provider_certificate_keycloak(sso_uri: str) -> Iterator[Problem]:
    """
    Check that all IDP certificates from :file:`/usr/share/univention-management-console/saml/idp/*.xml`
    are included in Keycloak.

    Fix: ``univention-run-join-scripts --force --run-scripts 92univention-management-console-web-server``
    """
    MODULE.process("Checks sso certificate by comparing 'ucr get ucs/server/sso/uri' FQDN with the Location field in %s", XML)

    backend = default_backend()
    certificate = None
    data = None

    url = "%s/realms/ucs/protocol/saml/descriptor" % (sso_uri,)
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

    if data:
        try:
            metadata_dom = fromstring(data)
            der_cert = metadata_dom.find(X509CERT).text
            certificate = x509.load_der_x509_certificate(b64decode(der_cert), backend)
            MODULE.process("Looking for certificate %s", certificate.subject)
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
                    MODULE.process("Found certificate %s in %s", cert.subject, idp)
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
    MODULE.process("Checking certificates of %s", path)
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
        MODULE.process("Looking for certificate %s", certificate.subject)
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
                MODULE.process("Found certificate %s in %s", cert.subject, dn)
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


def dns_link(dn: str) -> tuple[str, dict[str, Any]]:
    """Create UMC UDM link for DN."""
    link = "udm:saml/serviceprovider"
    umcm: dict[str, Any] = {
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


actions: dict[str, Callable[[Instance], None]] = {
    "fix_idp": fix_idp,
    "fix_sp": fix_sp,
}


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    run(0)
    main()
