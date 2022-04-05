#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  Error document
#
# Copyright 2020-2022 Univention GmbH
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

import json
import cgitb
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
	elif url.startswith('/univention/'):
		service_name = 'Univention Management Console Server'
		service = 'univention-management-console-server'
		if status == 503:
			reason = 'UMC Service Unavailable'

	message = "The %s could not be reached. Please restart %s or try again later." % (service_name, service)
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
