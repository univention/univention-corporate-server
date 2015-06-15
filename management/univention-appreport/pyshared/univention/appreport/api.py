# -*- coding: utf-8 -*-

import urllib2
import ldap
from json import dumps as json_encode

import univention.admin.uldap
import univention.admin.modules
import univention.config_registry
from univention.admin.uexceptions import base as udm_error
from univention.lib.package_manager import PackageManager

univention.admin.modules.update()
ldap_connection, ldap_position = univention.admin.uldap.getMachineConnection()
ucr = univention.config_registry.ConfigRegistry()
ucr.load()

UUID_SYSTEM = ucr.get('uuid/system')
UUID_LICENSE = ucr.get('uuid/license')

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


class ServerInterface(object):

	apps = ()

	def url(self, app):
		raise NotImplementedError('url')

	def body(self, app):
		return app.body()

	def encode_body(self, body):
		return json_encode(body)

	def headers(self, app):
		return {
			'X-System-Uuid': UUID_SYSTEM,
			'X-License-Uuid': UUID_LICENSE,
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


class UniventionServer(ServerInterface):

	apps = ('*',)

	def url(self, app):
		return 'http://localhost:8090/application-report/%s' % urllib2.quote(app.id)  # FIXME: remove
		return 'https://license.univention.de/application-report/%s' % urllib2.quote(app.id)


class CloudServiceProvider(ServerInterface):
	pass


class Application(object):

	id = None
	user_filter = '(!(disabled=all))'

	def __init__(self, app):
		self.app = app
		self.id = app.id

	def user_count(self):
		users_user = univention.admin.modules.get('users/user')
		try:
			return len(users_user.lookup(None, ldap_connection, self.user_filter))
		except AttributeError: # users_user is None
			raise
		except (ldap.LDAPError, udm_error):
			raise

	def body(self):
		return {
			'user_count': self.user_count()
		}
