#!/usr/bin/python3
# SPDX-FileCopyrightText: 2022-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| hook for assigning monitoring alerts to computer objects"""

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
