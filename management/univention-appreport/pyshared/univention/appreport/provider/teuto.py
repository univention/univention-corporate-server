# -*- coding: utf-8 -*-

from univention.appreport.api import CloudServiceProvider, Application
from urllib2 import quote


class OwnCloud(Application):
	user_filter = '(&((owncloudEnabled=1)%s)' % (Application.user_filter,)


class Teuto(CloudServiceProvider):

	apps = ('owncloud5', 'owncloud6', 'owncloud7', 'owncloud8')

	def application(self, app):
		if app.id.startswith('owncloud'):
			return OwnCloud(app)
		return super(Teuto, self).application(app)

	def uri(self, app):
		return 'http://localhost/app-report/%s' % (quote(app.id),)
