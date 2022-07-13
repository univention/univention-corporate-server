#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright 2022 Univention GmbH
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

"""
|UDM| hook for assigning monitoring alerts to computer objects
"""

from ldap.filter import filter_format

import univention.admin.modules
import univention.admin.objects
from univention.admin.hook import simpleHook


class MonitoringComputer(simpleHook):

	# FIXME: hide extended attribute if univentionService!=UCS Monitoring

	def hook_open(self, obj):
		if obj.exists():
			obj.info['monitoringAlerts'] = obj.lo.searchDn(filter_format('(&(objectClass=univentionMonitoringAlert)(univentionMonitoringAlertHosts=%s))', [obj.dn]))

	def hook_ldap_addlist(self, obj, al=[]):
		return [x for x in al if x[0] != 'univentionDoesNotExists']

	def hook_ldap_modlist(self, obj, ml=[]):
		return [x for x in ml if x[0] != 'univentionDoesNotExists']

	def hook_ldap_pre_modify(self, obj):
		self.change_referenced_alerts(obj)

	def hook_ldap_post_create(self, obj):
		self.change_referenced_alerts(obj)

	def change_referenced_alerts(self, obj):
		for dn in obj.info.get('monitoringAlerts', []):
			if dn in obj.oldinfo['monitoringAlerts']:
				continue
			alert = univention.admin.objects.get(univention.admin.modules.get('monitoring/alert'), None, obj.lo, '', dn)
			alert.open()
			alert['assignedHosts'] = alert['assignedHosts'] + [obj.dn]
			alert.modify()

		for dn in obj.oldinfo.get('monitoringAlerts', []):
			if dn in obj.info['monitoringAlerts']:
				continue
			alert = univention.admin.objects.get(univention.admin.modules.get('monitoring/alert'), None, obj.lo, '', dn)
			alert.open()
			alert['assignedHosts'] = [x for x in alert['assignedHosts'] if not obj.lo.compare_dn(x, obj.dn)]
			alert.modify()
