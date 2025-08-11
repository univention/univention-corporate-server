#!/usr/bin/python3
#
# Univention Updater
#  read the maintenance settings
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os
from shlex import quote
from sys import exit

from univention.config_registry import ConfigRegistry
from univention.lib.policy_result import PolicyResultFailed, policy_result


# Name of the cron.d file
CRON_D = '/etc/cron.d/univention-maintenance'


def write_cron_job(configRegistry: ConfigRegistry, cron: str, updateto: str, reboot: str, try_release_update: bool) -> None:
    with open(CRON_D, 'w') as file:
        file.write('# cron job for update\n')
        file.write('PATH=/sbin:/usr/sbin:/usr/bin:/bin\n')
        if cron == '* * * * * ':
            return
        cmd = ['/usr/sbin/jitter 600 true']
        if try_release_update:
            cmd.append(
                '/usr/share/univention-updater/univention-updater %s %s --silent --noninteractive' % (
                    'local' if configRegistry.is_true('local/repository') else 'net',
                    '--updateto=%s' % (quote(updateto),) if updateto else '',
                ))
        cmd.append('/usr/share/univention-updater/univention-actualise --dist-upgrade --silent')
        if reboot:
            cmd.append(
                'if [ -f /run/univention-updater-reboot ];then '
                'at -f /var/lib/univention-updater/reboot.at -- %s 2>/dev/null;'
                'rm -f /run/univention-updater-reboot;'
                'fi' % (
                    quote(reboot),))
        print('%s\troot\t%s' % (cron, ';'.join(cmd)), file=file)


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

    cron_active = one(results, "univentionCronActive") == "1"
    cron = one(results, "univentionCron")
    updateto = one(results, "univentionUpdateVersion")
    reboot = one(results, "univentionInstallationReboot")
    try_release_update = one(results, "univentionUpdateActivate") == "TRUE"

    if cron_active and cron:
        write_cron_job(configRegistry, cron, updateto, reboot, try_release_update)


if __name__ == "__main__":
    main()
