#!/usr/bin/python3
# SPDX-FileCopyrightText: 2025-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import ipaddress
import socket
import urllib.parse
from collections.abc import Iterator
from typing import Any

import univention.admin.modules as udm_modules
import univention.admin.uldap
from univention.admin.handlers import simpleLdap
from univention.config_registry import ucr_live as ucr
from univention.lib.i18n import Translation
from univention.management.console.log import MODULE
from univention.management.console.modules.diagnostic import Instance, Warning  # noqa: A004


_ = Translation("univention-management-console-module-diagnostic").translate

title = _("Check portals/entry objects for unresolvable host names")
description = [_("All checked portals/entry objects are ok.")]
run_descr = [_("Checks portals/entry objects for unresolvable host names")]


class PortalChecker:
    def __init__(self) -> None:
        self.checked_hosts: dict[str, bool] = {}
        univention.admin.modules.update()
        (self.ldap_connection, self.position) = univention.admin.uldap.getMachineConnection()

    def lookup(self, module_name: str, filter_expression: str = "") -> Iterator[simpleLdap]:
        module = udm_modules.get(module_name)
        for instance in module.lookup(None, self.ldap_connection, filter_expression):
            instance.open()
            yield instance

    def find_all_portal_entry_problems(self) -> Any:
        ignore_list = ucr.get("diagnostic/check/24_portal_entries/ignore", "").split(",")
        for obj in self.lookup("portals/entry"):
            if obj["name"] in ignore_list:
                continue
            links = obj["link"]
            if isinstance(links, str):
                links = [links]
            for lang, link in links:
                parsed_link = urllib.parse.urlparse(link)
                host = parsed_link.hostname if parsed_link.netloc else ""
                try:
                    ipaddress.ip_address(host)
                except ValueError:
                    if not host.strip(" "):  # Not an IP but empty host ==> relative URL address but no hostname/fqdn
                        continue
                else:
                    continue  # it's an IP address

                if host not in self.checked_hosts:
                    self.checked_hosts[host] = self.is_valid_host(host)
                if not self.checked_hosts[host]:
                    MODULE.process(
                        "portals/entry object %s does not contain a resolvable host in %s URL: %s",
                        obj.dn,
                        lang,
                        link,
                    )
                    yield obj.dn, lang, link, self.umc_link(obj.dn)

    def is_valid_host(self, host: str) -> bool:
        """Checks if the given host/fqdn is resolvable via DNS."""
        try:
            socket.getaddrinfo(host, None)
        except socket.gaierror:
            return False
        return True

    def umc_link(self, dn: str) -> tuple[str, dict[str, Any]]:
        text = "udm:navigation"
        link = {
            "module": "udm",
            "flavor": "navigation",
            "props": {
                "openObject": {
                    "objectDN": dn,
                    "objectType": "portals/entry",
                },
            },
        }
        return text, link


def run(_umc_instance: Instance) -> None:
    errortext = [
        " ".join(
            [
                _("Found possibly invalid portal entries in the following objects."),
                _("Please make sure that the host part of all URLs is resolvable via DNS."),
            ],
        ),
    ]
    modules = []
    text_tmpl = _(
        'The object {dn} contains an unresolvable host in the "{lang}" URL: "{url}" (see {{{link}}}):',
    )

    checker = PortalChecker()
    for dn, lang, url, umc_link in checker.find_all_portal_entry_problems():
        (text, link) = umc_link
        errortext.append("")
        errortext.append(text_tmpl.format(dn=dn, lang=lang, url=url, link=text))
        modules.append(link)

    if modules:
        raise Warning(description="\n".join(errortext), umc_modules=modules)


if __name__ == "__main__":
    run(None)
