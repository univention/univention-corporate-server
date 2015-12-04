# -*- coding: utf-8 -*-

import univention.testing.utils as utils
import univention.testing.udm as udm_test
import univention.testing.strings as uts

from httplib import HTTPConnection, HTTPException
import contextlib
import json


class HTTPError(Exception):

	def __init__(self, response, content):
		self.response = response
		self.content = content


class Connection(object):

	def __init__(self, host='localhost'):
		self._headers = {
			'Content-Type': 'application/json',
			'Accept': 'application/json; q=1.0; text/html; q=0.5; */*; q=0.1',
			'X-Requested-With': 'XMLHttpRequest',
			'Accept-Language': 'en-US',
		}
		self.base_host = host
		self.base_uri = 'http://%s/univention-self-service/%%s' % (self.base_host,)

	def request(self, uri, data):
		print 'requesting %r with %r' % (uri, data)
		connection = HTTPConnection(self.base_host)
		connection.request('POST', self.base_uri % (uri,), json.dumps(data), headers=self._headers)
		response = connection.getresponse()
		content = response.read()
		print 'response = %s' % (response.status,)
		assert response.getheader('Content-Type', '').startswith('application/json'), content
		content = json.loads(content)
		if response.status >= 300:
			raise HTTPError(response, content)
		return content
		# TODO: kill all self-service UMC module processes because 1 process per request sums up and blocks resources for 15 minutes


class SelfServiceUser(Connection):

	def __init__(self, username, password):
		super(SelfServiceUser, self).__init__()
		self.username = username
		self.password = password

	def request(self, uri, **kwargs):
		data = {'username': self.username, 'password': self.password}
		data.update(kwargs)
		return super(SelfServiceUser, self).request(uri, data)

	def get_contact(self):
		return dict((data['id'], data['value']) for data in self.request('passwordreset/get_contact').get('result'))

	def set_contact(self, email='', mobile=''):
		return self.request('passwordreset/set_contact', email=email, mobile=mobile).get('result')

	def get_reset_methods(self):
		return [x['id'] for x in self.request('passwordreset/get_reset_methods').get('result')]

	def send_token(self, method):
		return self.request('passwordreset/send_token', method=method).get('result')

	def set_password(self, token, password):
		return self.request('passwordreset/set_password', token=token, password=password).get('result')


@contextlib.contextmanager
def self_service_user():
	with udm_test.UCSTestUDM() as udm:
		password = uts.random_string()
		dn, username = udm.create_user(password=password)
		utils.verify_ldap_object(dn)
		yield SelfServiceUser(username, password)
