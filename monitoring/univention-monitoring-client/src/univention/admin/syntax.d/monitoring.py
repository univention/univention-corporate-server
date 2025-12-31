#!/usr/bin/python3
# SPDX-FileCopyrightText: 2022-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| syntax classes for monitoring alerts"""

import univention.admin.syntax


class monitoringEnabledHosts(univention.admin.syntax.UDM_Objects):
    udm_modules = ('computers/computer', )
    udm_filter = '(univentionService=UCS Monitoring)'


class monitoringAlerts(univention.admin.syntax.UDM_Objects):
    udm_modules = ('monitoring/alert', )
