#
# Univention Monitoring
#  listener module: update configuration of prometheus alert manager
#
# SPDX-FileCopyrightText: 2022-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os
from urllib.parse import quote

import requests
import yaml

import univention.debug as ud
from univention.config_registry import ucr
from univention.listener.handler import ListenerModuleHandler

from listener import SetUID


name = 'monitoring-client'

DIRECTORY = '/var/lib/univention-appcenter/apps/prometheus/conf/'


def safe_path(filename):
    return quote(filename, safe='')


def escape_prometheus_regex(string):
    for char in r'.^$*+?()[]{}\|':
        string = string.replace(char, '\\' + char)
    return string


class MonitoringClient(ListenerModuleHandler):

    def initialize(self):
        if os.path.exists(DIRECTORY):
            return
        with self.as_root():
            os.makedirs(DIRECTORY)

    def create(self, dn, new):
        with self.as_root():
            self._write_config(new)

    def modify(self, dn, old, new, old_dn):
        with self.as_root():
            self._write_config(new)

    def remove(self, dn, old):
        with self.as_root():
            self._remove_config(old)

    def get_fqdn(self, dn):
        obj = self.lo.get(dn, ['cn', 'associatedDomain'])
        try:
            return '%s.%s' % (obj['cn'][0].decode('UTF-8'), obj['associatedDomain'][0].decode('UTF-8'))
        except KeyError:
            pass

    def replace_template(self, string, template_values):
        for key, value in template_values:
            string = string.replace(f'%{key}%', value)
        return string

    def _write_config(self, attrs):
        name = attrs['cn'][0].decode('UTF-8')
        template_values = [
            label.decode('UTF-8').split('=', 1)
            for label in attrs.get('univentionMonitoringAlertTemplateValue', [b''])
            if label
        ]
        expr = attrs['univentionMonitoringAlertQuery'][0].decode('UTF-8')
        if '%instance%' in expr:
            assigned_hosts = [self.get_fqdn(x.decode('UTF-8')) for x in attrs.get('univentionMonitoringAlertHosts', [])]
            assigned_hosts = [x for x in assigned_hosts if x]
            if not assigned_hosts:
                return self._remove_config(attrs)

            # FIXME: regex DoS possible?
            template_values.append(('instance', 'instance=~"(%s)"' % '|'.join(escape_prometheus_regex(host) for host in assigned_hosts)))

        expr = self.replace_template(expr, template_values)
        alert_group = attrs.get('univentionMonitoringAlertGroup', attrs['cn'])[0].decode('UTF-8')
        description = self.replace_template(attrs.get('description', [b''])[0].decode('UTF-8'), template_values)
        summary = self.replace_template(attrs.get('univentionMonitoringAlertSummary', [b''])[0].decode('UTF-8'), template_values)
        for_ = attrs.get('univentionMonitoringAlertFor', [b'10s'])[0].decode('UTF-8')
        labels = [
            label.decode('UTF-8').split('=', 1)
            for label in attrs.get('univentionMonitoringAlertLabel', [b''])
            if label
        ]
        alert_config = {
            'groups': [{
                'name': alert_group,
                'rules': [
                    {
                        'alert': name,
                        'expr': expr,
                        'for': for_,
                        'annotations': {'title': summary, 'description': description},
                        'labels': dict(labels),
                    },
                ],
            }],
        }

        filename = os.path.join(DIRECTORY, safe_path(f"alert_{name}.yml"))
        with open(filename, "w") as fd:
            fd.write(yaml.dump(alert_config, default_style=None, default_flow_style=False))

    def _remove_config(self, attrs):
        name = attrs['cn'][0].decode('UTF-8')
        filename = os.path.join(DIRECTORY, safe_path(f"alert_{name}.yml"))
        try:
            os.remove(filename)
        except FileNotFoundError:
            ud.debug(ud.LISTENER, ud.WARN, 'alert definition does not exists: %s' % (filename,))

    def post_run(self):
        # type: () -> None
        ud.debug(ud.LISTENER, ud.INFO, 'Reloading prometheus alert manager')
        url = 'http://localhost/metrics-prometheus/-/reload'
        with SetUID(0), open('/etc/machine.secret') as fd:
            response = requests.post(url, auth=('%(hostname)s$' % ucr, fd.read().strip()))
            try:
                response.raise_for_status()
            except requests.HTTPError as exc:
                ud.debug(ud.LISTENER, ud.ERROR, 'Error reloading prometheus alert rules: %s' % (exc,))

    class Configuration(ListenerModuleHandler.Configuration):
        name = name
        ldap_filter = '(objectClass=univentionMonitoringAlert)'
        description = 'Create configuration for Prometheus AlertManager'
