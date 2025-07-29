#!/usr/bin/python3
#
# Univention Updater
#  read the repository server
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import sys

from univention.config_registry import ConfigRegistry, handler_set
from univention.lib.policy_result import PolicyResultFailed, policy_result


def query_policy(ldap_hostdn: str) -> tuple[str, str]:
    """Retrieve updateServer and version from policy."""
    try:
        results, _policies = policy_result(ldap_hostdn)
    except PolicyResultFailed as ex:
        sys.exit("failed to execute univention_policy_result: %s" % ex)

    server = one(results, "univentionRepositoryServer")  # univentionPolicyRepositorySync
    update = one(results, "univentionUpdateVersion")  # univentionPolicyUpdate

    return (server, update)


def one(results: dict[str, list[str]], key: str) -> str:
    try:
        return results[key][0]
    except LookupError:
        return ""


def main() -> None:
    """Set repository server."""
    ucr = ConfigRegistry()
    ucr.load()

    hostdn = ucr.get('ldap/hostdn')
    if not hostdn:
        # can't query policy without host-dn
        sys.exit(0)

    online_server = ucr.get('repository/online/server')
    mirror_server = ucr.get('repository/mirror/server')
    fqdn = '%(hostname)s.%(domainname)s' % ucr
    self_update = '%(version/version)s-%(version/patchlevel)s' % ucr

    ucr_variables: list[str] = []

    new_server, policy_update = query_policy(hostdn)
    policy_update or self_update  # FIXME: not used - should be pass to `univention-repository-update --updateto=`  # noqa: B018

    if ucr.is_true('local/repository'):
        # on a repository server
        if not new_server:
            ucr_variables.append('repository/online/server?http://%s' % fqdn)
        elif new_server not in (mirror_server, fqdn):
            ucr_variables.append('repository/mirror/server=%s' % new_server)
    else:
        # without a local repository
        if new_server and new_server != online_server:
            ucr_variables.append('repository/online/server=http://%s' % new_server)

    if ucr_variables:
        handler_set(ucr_variables)


if __name__ == '__main__':
    main()
