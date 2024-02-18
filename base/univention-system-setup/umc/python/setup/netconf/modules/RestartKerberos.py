#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from univention.management.console.modules.setup.netconf.common import RestartService
from univention.management.console.modules.setup.netconf.conditions import NotNetworkOnly


class PhaseRestartKerberos(RestartService, NotNetworkOnly):
    service = "heimdal-kdc"
    priority = 28
