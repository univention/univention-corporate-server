# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from univention.management.console.modules.setup.netconf.common import RestartService


class PhaseRestartNscd(RestartService):
    service = "nscd"
    priority = 18
