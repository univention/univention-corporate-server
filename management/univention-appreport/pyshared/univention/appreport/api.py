# -*- coding: utf-8 -*-
#
# Univention Application Reporting
#
# Copyright (C) 2015 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of the software contained in this package
# as well as the source package itself are made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this package provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use the software under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

import urllib2
import ldap
from json import dumps as json_encode

import univention.debug as ud
import univention.admin.uldap
import univention.admin.modules
import univention.config_registry
from univention.admin.uexceptions import base as udm_error
from univention.lib.package_manager import PackageManager

univention.admin.modules.update()
ldap_connection, ldap_position = univention.admin.uldap.getMachineConnection()
ucr = univention.config_registry.ConfigRegistry()
ucr.load()

UUID_SYSTEM = ucr.get('uuid/system', '')
UUID_LICENSE = ucr.get('uuid/license', '')
LDAP_BASE = ucr.get('ldap/base', '')

from univention.management.console.modules.appcenter import app_center
APPS = dict((app.id.lower(), app) for app in app_center.Application.all_installed(PackageManager(), only_local=True, localize=False))


class Request(object):

	def __init__(self, url, body, headers):
		self.url = url
		self.body = body
		self.headers = headers
		self.request = urllib2.Request(url, body, headers)

	def __repr__(self):
		return '<Request(%s, %r)>' % (self.url, self.headers)


class ServiceInterface(object):

	apps = ()

	def url(self, app):
		raise NotImplementedError('url')

	def body(self, app):
		body = {
			'uuid/system': UUID_SYSTEM,
			'uuid/license': UUID_LICENSE,
			'ldap/base': LDAP_BASE,
		}
		body.update(app.body())
		return body

	def encode_body(self, body):
		return json_encode(body)

	def headers(self, app):
		return {
			'Content-Type': 'application/json'
		}

	def application(self, app):
		return Application(app)

	def __init__(self):
		if '*' in self.apps:
			self._apps = [app for app in APPS.values()]
		else:
			self._apps = [APPS.get(app.lower()) for app in self.apps]

		self._apps = [self.application(app) for app in self._apps]

	def requests(self):
		for app in self._apps:
			yield self.build_request(app)

	def build_request(self, app):
		return Request(self.url(app), self.encode_body(self.body(app)), self.headers(app))


class UniventionServer(ServiceInterface):

	def __init__(self):
		if ucr.is_true('appreport/*/report', False):
			self.apps = ('*',)
		else:
			self.apps = [app for app in APPS if ucr.is_true('appreport/%s/report' % (app,), False)]

		super(UniventionServer, self).__init__()

	def url(self, app):
		return 'https://license.univention.de/appreport/%s' % urllib2.quote(app.id)


class Application(object):

	def __init__(self, app):
		self.app = app
		self.id = app.id
		self.object_type = ucr.get('appreport/%s/object_type' % (self.id,), 'users/user')
		self.object_filter = ucr.get('appreport/%s/object_filter' % (self.id,), '')
		self.ldap_filter = ucr.get('appreport/%s/ldap_filter' % (self.id,), '(&((!(disabled=all)%(object_filter)s))')
		if '%' in self.ldap_filter:
			self.ldap_filter = self.ldap_filter % self.__dict__

	def object_count(self):
		object_ = univention.admin.modules.get(self.object_type)
		try:
			return len(object_.lookup(None, ldap_connection, self.ldap_filter))
		except AttributeError as exc:  # object_ is None
			ud.debug(ud.MAIN, ud.ERROR, 'Unknown object type? %r=%r: %s' % (self.object_type, object_, exc))
			raise
		except (ldap.LDAPError, udm_error) as exc:
			ud.debug(ud.MAIN, ud.ERROR, 'LDAP lookup failure: %s' % (exc,))
			raise

	def body(self):
		return {
			'count': self.object_count()
		}
