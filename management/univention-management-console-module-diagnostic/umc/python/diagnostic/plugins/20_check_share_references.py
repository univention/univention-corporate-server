#!/usr/bin/python3
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from collections.abc import Iterator
from typing import Any

from ldap.filter import filter_format

import univention.admin.modules as udm_modules
import univention.admin.objects as udm_objects
import univention.admin.uldap
from univention.admin.handlers import simpleLdap
from univention.config_registry import ucr_live as ucr
from univention.lib.i18n import Translation
from univention.management.console.log import MODULE
from univention.management.console.modules.diagnostic import Instance, Warning  # noqa: A004


_ = Translation("univention-management-console-module-diagnostic").translate

title = _("Check shares/* objects for dangling host references")
description = [_("All checked shares/* objects are ok.")]
run_descr = [_("Checks shares/* objects for dangling host references")]


class ShareReferenceChecker:
    def __init__(self) -> None:
        self.checked_hosts: dict[str, bool] = {}
        univention.admin.modules.update()
        (self.ldap_connection, self.position) = univention.admin.uldap.getMachineConnection()

    def lookup(self, module_name: str, filter_expression: str = "") -> Iterator[simpleLdap]:
        module = udm_modules.get(module_name)
        for instance in module.lookup(None, self.ldap_connection, filter_expression):
            instance.open()
            yield instance

    def find_all_share_reference_problems(self) -> Any:
        for property_name, udm_module in (
            ("host", "shares/share"),
            ("spoolHost", "shares/printer"),
            ("spoolHost", "shares/printergroup"),
        ):
            for obj in self.lookup(udm_module):
                host_fqdn_list = obj[property_name]
                if isinstance(host_fqdn_list, str):
                    host_fqdn_list = [host_fqdn_list]
                for host_fqdn in host_fqdn_list:
                    if host_fqdn not in self.checked_hosts:
                        self.checked_hosts[host_fqdn] = self.is_valid_host(host_fqdn)
                    if not self.checked_hosts[host_fqdn]:
                        MODULE.process("%s object %s does not contain a valid %s: %s", udm_module, obj.dn, property_name, host_fqdn)
                        yield udm_module, obj.dn, host_fqdn, self.umc_link(udm_module, obj.dn)

    def is_valid_host(self, host_fqdn: str) -> bool:
        """Checks if the given host refers to an existing UCS host object."""
        host_name = host_fqdn.split(".", 1)[0]
        filter_str = filter_format(
            "(&(cn=%s)(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer)))",
            (host_name,),
        )
        for dn, attrs in self.ldap_connection.search(filter_str):
            for module in udm_modules.identify(dn, attrs):
                record = udm_objects.get(
                    module,
                    None,
                    self.ldap_connection,
                    self.position,
                    dn,
                    attr=attrs,
                    attributes=attrs,
                )
                record.open()
                if record.info.get("domain"):
                    fqdn = f"{record['name']}.{record['domain']}"
                else:
                    fqdn = f"{record['name']}.{ucr.get('domainname')}"
                if host_fqdn == fqdn:
                    return True
        return False

    def umc_link(self, udm_module: str, dn: str) -> tuple[str, dict[str, Any]]:
        text = "udm:dns/dns"
        link = {
            "module": "udm",
            "flavor": udm_module,
            "props": {
                "openObject": {
                    "objectDN": dn,
                    "objectType": udm_module,
                },
            },
        }
        return text, link


def run(_umc_instance: Instance) -> None:
    errortext = [
        " ".join(
            [
                _("Found invalid host entries in the following share/* objects."),
                _(
                    "Please make sure that only hosts are specified that exist as a suitable computer object in LDAP.",
                ),
            ],
        ),
    ]
    modules = []
    text_tmpl = _(
        'The {udm_module} object {dn} contains an invalid "host" resp. "spoolHost" entry: "{host}" (see {{{link}}}):',
    )

    ref_checker = ShareReferenceChecker()
    for udm_module, dn, host, umc_link in ref_checker.find_all_share_reference_problems():
        (text, link) = umc_link
        errortext.append("")
        errortext.append(text_tmpl.format(udm_module=udm_module, dn=dn, host=host, link=text))
        modules.append(link)

    if modules:
        raise Warning(description="\n".join(errortext), umc_modules=modules)


if __name__ == "__main__":
    run(None)
