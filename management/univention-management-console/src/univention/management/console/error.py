#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  Exception classes for UMC modules
#
# Copyright 2017-2019 Univention GmbH
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

from __future__ import absolute_import

from univention.lib.i18n import Translation
from univention.management.console.config import ucr

_ = Translation('univention.management.console').translate


class UMC_Error(Exception):
	status = 400
	msg = None
	with_traceback = False

	def __init__(self, message=None, status=None, result=None, headers=None, traceback=None):
		message = message or self.msg
		super(UMC_Error, self).__init__(message)
		self.msg = message
		self.result = result
		self.headers = headers
		self.traceback = traceback
		if isinstance(status, int):
			self.status = status


class BadRequest(UMC_Error):
	msg = _('Bad request')
	status = 400


class Unauthorized(UMC_Error):
	msg = _('Unauthorized')
	status = 401


class Forbidden(UMC_Error):
	msg = _('Forbidden')
	status = 403


class NotFound(UMC_Error):
	msg = _('Not found')
	status = 404


class MethodNotAllowed(UMC_Error):
	msg = _('Method not allowed')
	status = 405


class NotAcceptable(UMC_Error):
	status = 406


class UnprocessableEntity(UMC_Error):
	status = 422


class ServerError(UMC_Error):
	msg = _('Internal error')
	status = 500


class BadGateway(UMC_Error):
	status = 502


class ServiceUnavailable(UMC_Error):
	status = 503


class PasswordRequired(Unauthorized):

	def __init__(self):
		message = _('This action requires you to supply your password.')
		super(PasswordRequired, self).__init__(message, self.status, {'password_required': True})


class LDAP_ServerDown(UMC_Error):

	def __init__(self):
		ucr.load()
		self._is_master = ucr.get('server/role') == 'domaincontroller_master'
		self._updates_available = ucr.is_true('update/available')
		self._fqdn = '%s.%s' % (ucr.get('hostname'), ucr.get('domainname'))
		message = '\n'.join(self._error_msg())
		super(LDAP_ServerDown, self).__init__(message, status=503)

	def _error_msg(self):
		yield _('Cannot connect to the LDAP service.')
		yield _('The following steps can help to solve this problem:')
		if self._is_master:
			yield ' * ' + _('Check if enough hard disk space and free RAM is available on this server or free some resources')
		else:
			yield ' * ' + _('Make sure the domain controller master is running and reachable from %s') % (self._fqdn,)
			yield ' * ' + _('Check if enough hard disk space and free RAM is available on this server and on the domain controller master or free some resources')
		yield ' * ' + _('Restart the LDAP service on the domain controller master either via "service slapd restart" on command line or with the UMC module "System services"')
		if self._updates_available:
			yield ' * ' + _('Install the latest software updates')
		# TODO: reuse but not in LDAP_ServerDown
		# yield _('If the problem persists additional hints about the cause can be found in the following log file(s):')
		# yield ' * /var/log/univention/management-console-server.log'
		# yield ' * /var/log/univention/management-console-module-*.log'


class LDAP_ConnectionFailed(LDAP_ServerDown):

	def __init__(self, exc):
		self.exc = exc
		super(LDAP_ConnectionFailed, self).__init__()

	def _error_msg(self):
		yield _('Cannot connect to the LDAP service.')
		yield _('Error message: %s') % (self.exc.args[0].get('info', ''),)
		yield ''
		yield _('The following steps can help to solve this problem:')
		if not self._is_master:
			yield ' * ' + _('Make sure the domain controller master is running and reachable from %s') % (self._fqdn,)
		yield ' * ' + _('Check the SSL certificates, proxy and firewall settings')
		yield ' * ' + _('In case the SSL certificates are expired or a recent renewal of the root SSL CA has been done, please consider http://sdb.univention.de/1183')
		yield ' * ' + _('Restart the LDAP service on the domain controller master either via "service slapd restart" on command line or with the UMC module "System services"')
		if self._updates_available:
			yield ' * ' + _('Install the latest software updates')
