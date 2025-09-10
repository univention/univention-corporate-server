#!/usr/bin/python3
#
# Univention Management Console
#  module: manages system services
#
# SPDX-FileCopyrightText: 2011-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Any

import univention.config_registry
from univention.management.console import Translation
from univention.management.console.base import Base, UMC_Error
from univention.management.console.config import ucr
from univention.management.console.log import MODULE
from univention.management.console.modules.decorators import sanitize, simple_response, threaded
from univention.management.console.modules.sanitizers import PatternSanitizer, StringSanitizer
from univention.service_info import ServiceError, ServiceInfo


_ = Translation('univention-management-console-module-services').translate


class Instance(Base):

    @sanitize(pattern=PatternSanitizer(default='.*'))
    @simple_response
    def query(self, pattern: str) -> list[dict]:
        ucr.load()
        srvs = ServiceInfo()

        lang = _.__self__.locale.language
        if lang in (None, 'C'):
            lang = 'en'

        result = []
        for name, srv in srvs.services.items():
            key = srv.get('start_type', f'{name}/autostart')
            entry = {
                'service': name,
                'description': srv.get(f'description[{lang}]', srv.get('description')),
                'autostart': ucr.get(key, 'yes'),
                'isRunning': srv.running,
            }
            if entry['autostart'] not in ('yes', 'no', 'manually'):
                entry['autostart'] = 'yes'
            for value in entry.values():
                if pattern.match(str(value)):
                    result.append(entry)
                    break
        return result

    @sanitize(StringSanitizer(required=True))
    @threaded
    def start(self, request) -> None:
        return self._change_services(request.options, 'start')

    @sanitize(StringSanitizer(required=True))
    @threaded
    def stop(self, request) -> None:
        return self._change_services(request.options, 'stop')

    @sanitize(StringSanitizer(required=True))
    @threaded
    def restart(self, request) -> None:
        return self._change_services(request.options, 'restart')

    def _change_services(self, services: list[str], action: str) -> dict:
        error_messages = []
        srvs = ServiceInfo()
        for srv in services:
            service = srvs.get_service(srv)
            try:
                getattr(service, action)()
            except ServiceError as exc:
                MODULE.warning(f'Error during {action} of {srv}: {exc}')
                error_messages.append('%s\n%s' % ({
                    'start': _('Starting the service %s failed:'),
                    'stop': _('Stopping the service %s failed:'),
                    'restart': _('Restarting the service %s failed:'),
                }[action] % srv, exc))

        if error_messages:
            raise UMC_Error('\n\n'.join(error_messages))
        return {'success': True}

    @sanitize(StringSanitizer(required=True))
    def start_auto(self, request) -> None:
        self._change_start_type(request.options, 'yes')
        self.finished(request.id, {'success': True}, _('Successfully changed start type'))

    @sanitize(StringSanitizer(required=True))
    def start_manual(self, request) -> None:
        self._change_start_type(request.options, 'manually')
        self.finished(request.id, {'success': True}, _('Successfully changed start type'))

    @sanitize(StringSanitizer(required=True))
    def start_never(self, request) -> None:
        self._change_start_type(request.options, 'no')
        self.finished(request.id, {'success': True}, _('Successfully changed start type'))

    def _change_start_type(self, service_names: str, start_type: Any) -> None:
        service_info = ServiceInfo()
        services = [(service_name, service_info.services[service_name]) for service_name in service_names if service_name in service_info.services]
        values = ['%s=%s' % (service.get('start_type', f'{service_name}/autostart'), start_type) for service_name, service in services]
        univention.config_registry.handler_set(values)
        failed = [x for x in service_names if not service_info.services.get(x)]
        if failed:
            raise UMC_Error('%s %s' % (_('Could not change start type of the following services:'), ', '.join(failed)))
