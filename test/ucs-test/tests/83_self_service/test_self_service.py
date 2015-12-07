# -*- coding: utf-8 -*-

import univention.testing.utils as utils
import univention.testing.udm as udm_test
import univention.testing.strings as uts

from httplib import HTTPConnection, HTTPException
from threading import Thread
from smtpd import SMTPServer
import subprocess
import contextlib
import asyncore
import json
import fcntl


class HTTPError(Exception):

	def __init__(self, response, content):
		self.response = response
		self.content = content
		super(HTTPError, self).__init__(response, content)
		print self

	def __str__(self):
		return unicode(self).encode('utf-8')

	def __unicode__(self):
		return u'Status: %s, content=%r' % (self.response.status, self.content)


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
def self_service_user(email=None, **kwargs):
	with udm_test.UCSTestUDM() as udm:
		password = uts.random_string()
		if email:
			kwargs['PasswordRecoveryEmail'] = email
		dn, username = udm.create_user(password=password, **kwargs)
		utils.verify_ldap_object(dn)
		yield SelfServiceUser(username, password)


@contextlib.contextmanager
def capture_mails(timeout=5):

	class Mail(SMTPServer):

		def __init__(self, *args, **kwargs):
			SMTPServer.__init__(self, *args, **kwargs)
			self.set_reuse_addr()
			fcntl.fcntl(self.socket.fileno(), fcntl.F_SETFD, fcntl.fcntl(self.socket.fileno(), fcntl.F_GETFD) | fcntl.FD_CLOEXEC)
			self.data = []

		def process_message(self, peer, mailfrom, rcpttos, data):
			print 'receiving email with length=', len(data)
			self.data.append(data)

	class MailServer(object):

		def __init__(self):
			print 'Starting mail server'
			self.smtp = Mail(('', 25), '')
			self.thread = Thread(target=asyncore.loop, kwargs={'timeout': timeout})
			self.thread.start()

		def stop(self):
			print 'Stopping mail server'
			self.smtp.close()
			self.thread.join()

	subprocess.call(['invoke-rc.d', 'postfix', 'stop'], close_fds=True)
	try:
		server = MailServer()
		try:
			yield server.smtp
		finally:
			try:
				server.smtp.close()
			except:
				print 'Warn: Could not close SMTP socket'
			server.stop()
	finally:
		print '(re)starting postfix'
		subprocess.call(['invoke-rc.d', 'postfix', 'start'], close_fds=True)
