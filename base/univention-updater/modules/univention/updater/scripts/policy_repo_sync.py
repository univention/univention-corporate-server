#!/usr/bin/python3
#
# Univention Updater
#  read the repository settings
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
import os
from sys import exit

from univention.config_registry import ConfigRegistry
from univention.lib.policy_result import PolicyResultFailed, policy_result


# Name of the cron.d file
CRON_D = '/etc/cron.d/univention-repository-sync'


def write_cron_job(cron: str) -> None:
    with open(CRON_D, 'w') as cron_file:
        cron_file.write('# cron job for syncing repository\n')
        cron_file.write("PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\n")
        if cron == '* * * * * ':
            return

        cron_file.write('%s root /usr/sbin/univention-repository-update net >>/var/log/univention/repository.log\n' % cron)


def one(results: dict[str, list[str]], key: str) -> str:
    try:
        return results[key][0]
    except LookupError:
        return ""


def main() -> None:
    if os.path.exists(CRON_D):
        os.unlink(CRON_D)

    configRegistry = ConfigRegistry()
    configRegistry.load()
    ldap_hostdn = configRegistry.get('ldap/hostdn')
    if not ldap_hostdn:
        return

    try:
        results, _policies = policy_result(ldap_hostdn)
    except PolicyResultFailed as ex:
        exit('failed to execute univention_policy_result: %s' % ex)

    cron = one(results, "univentionRepositoryCron")
    if cron:
        write_cron_job(cron)


if __name__ == '__main__':
    main()
