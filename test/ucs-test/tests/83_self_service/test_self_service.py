# -*- coding: utf-8 -*-

import univention.testing.utils as utils
import univention.testing.udm as udm_test
import univention.testing.strings as uts
from univention.testing.umc import Client

from threading import Thread
from smtpd import SMTPServer
import subprocess
import contextlib
import asyncore
import fcntl
import time


class SelfServiceUser(object):

	def __init__(self, username, password):
		self._client = Client()
		self.username = username
		self.password = password

	def request(self, uri, **kwargs):
		options = {'username': self.username, 'password': self.password}
		options.update(kwargs)
		return self._client.umc_command(uri, options)
		# TODO: kill all self-service UMC module processes because 1 process per request sums up and blocks resources for 15 minutes

	def get_contact(self):
		return dict((data['id'], data['value']) for data in self.request('passwordreset/get_contact').result)

	def set_contact(self, email='', mobile=''):
		return self.request('passwordreset/set_contact', email=email, mobile=mobile).result

	def get_reset_methods(self):
		return [x['id'] for x in self.request('passwordreset/get_reset_methods').result]

	def send_token(self, method):
		return self.request('passwordreset/send_token', method=method).result

	def set_password(self, token, password):
		return self.request('passwordreset/set_password', token=token, password=password).result


@contextlib.contextmanager
def self_service_user(email=None, **kwargs):
	with udm_test.UCSTestUDM() as udm:
		if 'mailPrimaryAddress' in kwargs:
			udm.create_object('mail/domain', ignore_exists=True, wait_for_replication=True, check_for_drs_replication=False, name=kwargs['mailPrimaryAddress'].split('@', 1)[1])
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
	time.sleep(3)
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
