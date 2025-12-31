#!/usr/bin/python3
#
# Univention Management Console
#  Error document
#
# SPDX-FileCopyrightText: 2020-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import cgitb
import json
import re


cgitb.enable()


def application(environ, start_response):
    status, _, reason = environ.get('REDIRECT_STATUS', '200 OK').partition(' ')
    status = int(status)
    reason = reason or {502: 'Proxy Error', 503: 'Service Unavailable'}.get(status, reason)
    url = environ.get('REDIRECT_URL', '')
    service = 'it'
    service_name = 'Service'
    if url.startswith('/univention/udm'):
        service_name = 'Univention Directory Manager REST API'
        service = 'univention-directory-manager-rest'
        if status == 503:
            reason = 'UDM REST Unavailable'
    elif url.startswith('/univention/portal'):
        service = 'univention-portal-server'
        service_name = 'Portal Server'
        if status == 503:
            reason = 'Portal Service Unavailable'
    elif re.match('^/univention/(auth|saml|oidc|get|set|command|upload|logout|logout-sse)($|/.*$)', url):
        service_name = 'Univention Management Console Server'
        service = 'univention-management-console-server'
        if status == 503:
            reason = 'UMC Service Unavailable'
    elif url.startswith('/univention/'):
        pass

    message = "The %s could not be reached. Please try again later, try accesssing via https and FQDN or restart %s." % (service_name, service)
    if status == 502:
        message += ' %s' % (environ.get('REDIRECT_ERROR_NOTES', ''),)
        message = message.rstrip()
    data = {
        "status": status,
        "message": message,
        # DEBUG: "environ": dict((key, val) for key, val in environ.items() if not key.startswith('wsgi.') and not key.startswith('mod_wsgi.')),
    }
    response_header = [('Content-type', 'application/json')]  # TODO: give HTML when json is not accepable
    start_response('%d %s' % (status, reason), response_header)
    return [json.dumps(data).encode('UTF-8')]
