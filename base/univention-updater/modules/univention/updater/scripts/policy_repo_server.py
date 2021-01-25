#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Updater
#  read the repository server
#
# Copyright 2004-2021 Univention GmbH
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
import sys
from typing import Dict, List, Tuple

from univention.config_registry import ConfigRegistry, handler_set
from univention.lib.policy_result import PolicyResultFailed, policy_result


def query_policy(ldap_hostdn: str) -> Tuple[str, str]:
    """
    Retrieve updateServer and version from policy.
    """
    try:
        results, _policies = policy_result(ldap_hostdn)
    except PolicyResultFailed as ex:
        sys.exit("failed to execute univention_policy_result: %s" % ex)

    server = one(results, "univentionRepositoryServer")  # univentionPolicyRepositorySync
    update = one(results, "univentionUpdateVersion")  # univentionPolicyUpdate

    return (server, update)


def one(results: Dict[str, List[str]], key: str) -> str:
    try:
        return results[key][0]
    except LookupError:
        return ""


def main() -> None:
    """
    Set repository server.
    """
    ucr = ConfigRegistry()
    ucr.load()

    hostdn = ucr.get('ldap/hostdn')
    if not hostdn:
        # can't query policy without host-dn
        exit(0)

    online_server = ucr.get('repository/online/server')
    mirror_server = ucr.get('repository/mirror/server')
    fqdn = '%(hostname)s.%(domainname)s' % ucr
    self_update = '%(version/version)s-%(version/patchlevel)s' % ucr

    ucr_variables = []  # type: List[str]

    new_server, policy_update = query_policy(hostdn)
    update = policy_update or self_update  # FIXME: not used - should be pass to `univention-repository-update --updateto=`

    if ucr.is_true('local/repository'):
        # on a repository server
        if not new_server:
            ucr_variables.append('repository/online/server?%s' % fqdn)
        elif new_server != mirror_server and new_server != fqdn:
            ucr_variables.append('repository/mirror/server=%s' % new_server)
    else:
        # without a local repository
        if new_server and new_server != online_server:
            ucr_variables.append('repository/online/server=%s' % new_server)

    if ucr_variables:
        handler_set(ucr_variables)


if __name__ == '__main__':
    main()
