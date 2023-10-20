#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
# -*- coding: utf-8 -*-
## desc: |
##  Test if all expected modules are available for 'root' and 'administrator'
##  users, with different join-states.
## roles-not:
##  - basesystem
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

from pathlib import Path
from typing import List

from univention.lib.i18n import Translation
from univention.testing.browser.lib import UMCBrowserTest


_ = Translation("ucs-test-browser").translate


MASTER = "master"
BACKUP = "backup"
SLAVE = "slave"
MEMBER = "member"

ADMIN = "Administrator"
ROOT = "root"

expected_modules_for_role = {
    MASTER: {
        ADMIN: [
            _("Filesystem quotas"),
            _("Groups"),
            _("Users"),
            _("Computers"),
            _("Nagios"),
            _("Printers"),
            _("DHCP"),
            _("DNS"),
            _("Domain join"),
            _("LDAP directory"),
            _("Mail"),
            _("Networks"),
            _("Policies"),
            _("Shares"),
            _("SAML identity provider"),
            _("Certificate settings"),
            _("Hardware information"),
            _("Language settings"),
            _("Network settings"),
            _("Process overview"),
            _("System services"),
            _("Univention Configuration Registry"),
            _("System diagnostic"),
            _("App Center"),
            _("Package Management"),
            _("Repository Settings"),
            _("Software update"),
        ],
        ROOT: [
            _("Filesystem quotas"),
            _("Domain join"),
            _("Certificate settings"),
            _("Hardware information"),
            _("Language settings"),
            _("Network settings"),
            _("Process overview"),
            _("System services"),
            _("Univention Configuration Registry"),
            _("Software update"),
        ],
    },
    BACKUP: {
        ADMIN: [
            _("Filesystem quotas"),
            _("Groups"),
            _("Users"),
            _("Computers"),
            _("Nagios"),
            _("Printers"),
            _("DHCP"),
            _("DNS"),
            _("Domain join"),
            _("LDAP directory"),
            _("Mail"),
            _("Networks"),
            _("Policies"),
            _("Shares"),
            _("SAML identity provider"),
            _("Hardware information"),
            _("Language settings"),
            _("Network settings"),
            _("Process overview"),
            _("System services"),
            _("Univention Configuration Registry"),
            _("System diagnostic"),
            _("App Center"),
            _("Package Management"),
            _("Repository Settings"),
            _("Software update"),
        ],
        ROOT: [
            _("Filesystem quotas"),
            _("Domain join"),
            _("Hardware information"),
            _("Language settings"),
            _("Network settings"),
            _("Process overview"),
            _("System services"),
            _("Univention Configuration Registry"),
            _("Software update"),
        ],
    },
    SLAVE: {
        ADMIN: [
            _("Filesystem quotas"),
            _("Domain join"),
            _("Hardware information"),
            _("Language settings"),
            _("Network settings"),
            _("Process overview"),
            _("System services"),
            _("Univention Configuration Registry"),
            _("System diagnostic"),
            _("App Center"),
            _("Package Management"),
            _("Repository Settings"),
            _("Software update"),
        ],
        ROOT: [
            _("Filesystem quotas"),
            _("Domain join"),
            _("Hardware information"),
            _("Language settings"),
            _("Network settings"),
            _("Process overview"),
            _("System services"),
            _("Univention Configuration Registry"),
            _("Software update"),
        ],
    },
    MEMBER: {
        ADMIN: [
            _("Filesystem quotas"),
            _("Domain join"),
            _("Hardware information"),
            _("Language settings"),
            _("Network settings"),
            _("Process overview"),
            _("System services"),
            _("Univention Configuration Registry"),
            _("System diagnostic"),
            _("App Center"),
            _("Package Management"),
            _("Repository Settings"),
            _("Software update"),
        ],
        ROOT: [
            _("Filesystem quotas"),
            _("Domain join"),
            _("Hardware information"),
            _("Language settings"),
            _("Network settings"),
            _("Process overview"),
            _("System services"),
            _("Univention Configuration Registry"),
            _("Software update"),
        ],
    },
}


def test_module_availability(umc_browser_test: UMCBrowserTest, ucr):
    role = determine_ucs_role(ucr)
    users = determine_users_by_join_status()

    for user in users:
        umc_browser_test.login(user, skip_xhr_check=user != "Administrator")
        expected_modules = set(expected_modules_for_role[role][user])
        assert set(umc_browser_test.get_available_modules()) & expected_modules == expected_modules


def determine_ucs_role(ucr) -> str:
    server_role = ucr.get("server/role")
    if server_role == "domaincontroller_master":
        return MASTER
    elif server_role == "domaincontroller_backup":
        return BACKUP
    elif server_role == "domaincontroller_slave":
        return SLAVE
    elif server_role == "memberserver":
        return MEMBER
    else:
        raise Exception(f"Test is run on invalid server-role {server_role}")


def determine_users_by_join_status() -> List[str]:
    if Path("/var/univention-join/joined").is_file():
        return [ADMIN, ROOT]
    else:
        return [ROOT]
