# -*- coding: utf-8 -*-
#
# UCS test
#
# Copyright 2013-2015 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

from univention.config_registry import handler_set
import glob
import smtplib
import imaplib
import email
import os
import re
import socket
import subprocess
import sys
import time
import univention.testing.strings as uts
import univention.config_registry
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
import email.encoders as Encoders
import univention.testing.utils as utils
import univention.testing.ucr as ucr_test
# from univention.testing.decorators import SetMailDeliveryTimeout
from decorators import SetMailDeliveryTimeout

COMMASPACE = ', '


def disable_mail_quota():
	handler_set(['mail/cyrus/imap/quota=no'])
	subprocess.call(['/etc/init.d/cyrus-imapd', 'restart'])


def enable_mail_quota():
	handler_set(['mail/cyrus/imap/quota=yes'])
	subprocess.call(['/etc/init.d/cyrus-imapd', 'restart'])


class Mail(object):

	def get_reply(self, s):
		try:
			buff_size = 1024
			reply = ''
			while(True):
				part = s.recv(buff_size)
				reply += part
				if len(part) < buff_size:
					break
			return reply
		except:
			return reply

	def send_message(self, s, message):
		print message,
		s.send(message)


class ImapMail(Mail):

	def get_mails(self, filter='ALL', mailbox='INBOX'):
		msgs = []
		rv, data = self.connection.select(mailbox)
		assert rv == "OK"
		rv, msg_ids = self.connection.search(None, filter)
		assert rv == "OK"
		for num in msg_ids[0].split():
			rv, msg = self.connection.fetch(num, '(RFC822)')
			assert rv == "OK"
			msgs.append(email.message_from_string(msg[0][1]))
		return msgs

	def get_connection(self, host, user, password):
		self.connection = imaplib.IMAP4_SSL(host)
		rv, data = self.connection.login(user, password)
		assert rv == "OK"

	def get_return_code(self, id, response):
		regex = '%s (.*?) .*$' % id
		m = re.search(regex, response)
		try:
			return m.group(1)
		except:
			return '-ERR'

	def send_and_receive(self, s, id, message):
		self.send_message(s, '%s %s' % (id, message))
		response = self.get_reply(s)
		while True:
			response2 = self.get_reply(s)
			if response2:
				response += response2
			else:
				break
		print response
		r = self.get_return_code(id, response)
		return r

	def send_and_receive_quota(self, s, id, message):
		self.send_message(s, '%s %s' % (id, message))
		response = self.get_reply(s)
		while True:
			response2 = self.get_reply(s)
			if response2:
				response += response2
			else:
				break
		print response
		r = self.get_return_code(id, response)
		return (r, response)

	def login_OK(self, username, password):
		hostname = socket.gethostname()
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.settimeout(10)
		s.connect((hostname, 143))
		print self.get_reply(s)
		retval = self.send_and_receive(s, 'a001', 'login %s %s\r\n' % (username, password))
		self.send_and_receive(s, 'a002', 'logout\r\n')
		s.close()
		return (retval == 'OK')

	def get_imap_quota(self, username, password):
		hostname = socket.gethostname()
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.settimeout(10)
		s.connect((hostname, 143))
		retval = self.send_and_receive_quota(s, 'a001', 'login %s %s\r\n' % (username, password))
		retval = self.send_and_receive_quota(s, 'a002', 'GETQUOTAROOT INBOX\r\n')  # user/%s\r\n' % username)
		regex = '\(STORAGE 0 (.*)\)'
		m = re.search(regex, retval[1])
		try:
			quota = int(m.group(1))
		except:
				quota = -1
		self.send_and_receive_quota(s, 'a003', 'logout\r\n')
		s.close()
		return quota, retval[0]


class PopMail(Mail):

	def get_return_code(self, response):
		regex = '(.*?) .*$'
		m = re.search(regex, response)
		try:
			return m.group(1)
		except:
			return '-ERR'

	def send_and_receive(self, s, message):
		self.send_message(s, message)
		response = self.get_reply(s)
		print response,
		r = self.get_return_code(response)
		return r

	def login_OK(self, username, password):
		hostname = socket.gethostname()
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.settimeout(10)
		s.connect((hostname, 110))
		print self.get_reply(s),
		self.send_and_receive(s, 'USER %s' % username)
		retval = self.send_and_receive(s, 'PASS %s' % password)
		self.send_and_receive(s, 'QUIT')
		s.close()
		return (retval == '+OK')


ucr = univention.config_registry.ConfigRegistry()
ucr.load()


def random_email():
	return '%s@%s' % (uts.random_name, ucr.get('domainname'))


def make_token():
	return str(time.time())


def get_dir_files(dir_path, recursive=True):
	result = []
	for f in glob.glob('%s/*' % dir_path):
		if os.path.isfile(f):
			result.append(f)
		if os.path.isdir(f) and recursive:
			result.extend(get_dir_files(f))
	return result


def get_file_contain(token, _dir):
	for _file in get_dir_files(_dir, recursive=True):
		with open(_file) as fi:
			if token in fi.read():
				return os.path.basename(_file)


def virus_delivered(token, mail_address):
	virus_dir = '/var/lib/amavis/virusmails'
	mail_dir = [get_cyrus_maildir(mail_address), '/var/mail']
	virusarchive = get_file_contain(token, virus_dir)
	found = 0
	for _dir in mail_dir:
		if virusarchive:
			for _file in get_dir_files(_dir):
				with open(_file) as fi:
					if virusarchive in fi.read():
						found += 1
	return found == 2


def deactivate_spam_detection():
	handler_set(['mail/antispam=no', 'mail/antivir/spam=no'])


def activate_spam_header_tag(tag):
	handler_set(['mail/antispam/headertag=%s' % tag])


def reload_postfix():
	cmd = ['/etc/init.d/postfix', 'force-reload']
	try:
		subprocess.Popen(cmd).communicate()
	except EnvironmentError as ex:
		print >> sys.stderr, ex


def reload_amavis_postfix():
	for cmd in (
		['newaliases'],
		['/etc/init.d/amavis', 'force-reload'],
		['/etc/init.d/postfix', 'force-reload'],
	):
		try:
			subprocess.Popen(cmd).communicate()
		except EnvironmentError as ex:
			print >> sys.stderr, ex


@SetMailDeliveryTimeout()
def spam_delivered(token, mail_address):
	delivered = False
	spam = False
	with ucr_test.UCSTestConfigRegistry() as ucr:
		dovecot_spam = ucr.get('mail/dovecot/folder/spam')
		cyrus_spam = ucr.get('mail/cyrus/folder/spam')
	# cyrus
	spam_folder = cyrus_spam or 'Spam'
	mail_dir = os.path.join(get_cyrus_maildir(mail_address), spam_folder)
	for _file in get_dir_files(mail_dir, recursive=True):
		with open(_file) as fi:
			content = fi.read()
		delivered = delivered or (token in content)
		if delivered:
			if 'X-Spam-Flag: YES' in content:
				spam = spam or True
			break
	# dovecot
	spam_folder = dovecot_spam or 'Spam'
	mail_dir = os.path.join(get_dovcot_maildir(mail_address), spam_folder)
	for _file in get_dir_files(mail_dir, recursive=True):
		with open(_file) as fi:
			content = fi.read()
		delivered = delivered or (token in content)
		if delivered:
			if 'X-Spam-Flag: YES' in content:
				spam = spam or True
			break
	return delivered and spam


@SetMailDeliveryTimeout()
def mail_delivered(token, user=None, mail_address=None, check_root=True):
	delivered = False
	if check_root:
		_file = ('/var/mail/systemmail')
		if os.path.isfile(_file):
			with open(_file) as fi:
				delivered = delivered or (token in fi.read())
	if user:
		_file = os.path.join('/var/mail', user)
		if os.path.isfile(_file):
			with open(_file) as fi:
				delivered = delivered or (token in fi.read())
	if mail_address:
		mail_dir = get_cyrus_maildir(mail_address)
		for _file in get_dir_files(mail_dir, recursive=True):
			with open(_file) as fi:
				delivered = delivered or (token in fi.read())
				if delivered:
					break
		mail_dir = get_dovcot_maildir(mail_address)
		for _file in get_dir_files(mail_dir, recursive=True):
			with open(_file) as fi:
				delivered = delivered or (token in fi.read())
				if delivered:
					break
	return delivered


class UCSTest_Mail_Exception(Exception):
	""" Generic ucstest mail error """
	pass


class UCSTest_Mail_InvalidMailAddress(UCSTest_Mail_Exception):
	""" The given mail address is invalid """
	pass


class UCSTest_Mail_InvalidRecipientList(UCSTest_Mail_Exception):
	""" The given recipient list is invalid """
	pass


class UCSTest_Mail_MissingMailbox(UCSTest_Mail_Exception):
	""" At least one mailbox for the given mail addresses could not be found in given time range.
		The exception contains two arguments:
		- the list of checked mailboxes
		- the list of missing mailboxes (a subset of the first list)
	"""
	pass


def get_dovcot_maildir(mail_address):
	"""
	Returns directory name for specified mail address.

	>>> get_dovcot_maildir('testuser@example.com')
	'/var/spool/dovecot/private/example.com/testuser/Maildir'

	>>> get_dovcot_maildir('someuser@foobar.com')
	'/var/spool/dovecot/private/foobar.com/someuser/Maildir'

	>>> get_dovcot_maildir('only-localpart')
	Traceback (most recent call last):
	...
	UCSTest_Mail_InvalidMailAddress

	>>> get_dovcot_maildir('')
	Traceback (most recent call last):
	...
	UCSTest_Mail_InvalidMailAddress
	"""

	if not mail_address:
		raise UCSTest_Mail_InvalidMailAddress()
	if '@' not in mail_address:
		raise UCSTest_Mail_InvalidMailAddress()

	# FIXME cyrus uses a special UTF-7 encoding for umlauts for example - this encoding is currently missing
	mail_address, domain = mail_address.rsplit('@', 1)
	if '.' in mail_address:
		mail_address = mail_address.replace('.', '^')
	return '/var/spool/dovecot/private/%s/%s/Maildir' % (domain, mail_address.lower())

def get_cyrus_maildir(mail_address):
	"""
	Returns directory name for specified mail address.

	>>> get_cyrus_maildir('testuser@example.com')
	'/var/spool/cyrus/mail/domain/e/example.com/t/user/testuser'

	>>> get_cyrus_maildir('someuser@foobar.com')
	'/var/spool/cyrus/mail/domain/f/foobar.com/s/user/someuser'

	>>> get_cyrus_maildir('only-localpart')
	Traceback (most recent call last):
	...
	UCSTest_Mail_InvalidMailAddress

	>>> get_cyrus_maildir('')
	Traceback (most recent call last):
	...
	UCSTest_Mail_InvalidMailAddress
	"""

	if not mail_address:
		raise UCSTest_Mail_InvalidMailAddress()
	if '@' not in mail_address:
		raise UCSTest_Mail_InvalidMailAddress()

	# FIXME cyrus uses a special UTF-7 encoding for umlauts for example - this encoding is currently missing
	mail_address, domain = mail_address.rsplit('@', 1)
	if '.' in mail_address:
		mail_address = mail_address.replace('.', '^')
	# mail_address = re.sub("[0-9]", 'q', s)
	return '/var/spool/cyrus/mail/domain/%s/%s/%s/user/%s' % (domain[0].lower(), domain.lower(), re.sub("[0-9]", "q", mail_address[0].lower()), mail_address.lower())


def wait_for_mailboxes(mailboxes, timeout=90):
	"""
	Wait for cyrus listener module to create IMAP folders for specified mail addresses.
	Raises an exception if creation takes longer than <timeout> seconds.

	>>> wait_for_mailboxes(['foo1@example.com', 'bar@example.com'], timeout=2)
	Traceback (most recent call last):
	...
	UCSTest_Mail_MissingMailbox: (['foo1@example.com', 'bar@example.com'], ['foo1@example.com', 'bar@example.com'])
	"""
	print 'Waiting for up to %ds for new mailboxes (%r)' % (timeout, mailboxes)

	for i in xrange(timeout):
		missing_mailboxes = []
		for addr in mailboxes:
			if not os.path.isdir(get_cyrus_maildir(addr)):
				missing_mailboxes.append(addr)
		if not missing_mailboxes:
			break

		sys.stdout.write('.')
		sys.stdout.flush()
		time.sleep(1)
	else:
		print
		print 'not all mailboxes have been found within %d seconds (missing=%r)' % (timeout, missing_mailboxes)
		raise UCSTest_Mail_MissingMailbox(mailboxes, missing_mailboxes)
	print


def send_mail(recipients=None, sender=None, subject=None, msg=None, idstring='no id string',
	       gtube=False, virus=False, attachments=[], server=None, port=25, tls=False, username=None, password=None):
	"""
	Send a mail to mailserver.
	Arguments:
	recipients: single recipient as string or a list of recipients
	            (e.g. 'foo@example.com' or ['foo@example.com', 'bar@example.com'])
	sender:	    [optional] mail address of sender (default: tarpit@example.com)
	subject:    [optional] mail subject (default: 'Testmessage %s' % time.ctime() )
	msg:	    [optional] mail message; if msg is defined, idstring will be ignored!
	idstring:   [optional] idstring that will be integrated into default mail
	gtube:	    [optional] if True, gtube teststring will be added to mail (default: False)
	virus:	    [optional] if True, an attachment with virus signature will be added to mail
	attachments:[optional] list of filenames to be attached to mail
	server:	    [optional] name or IP address of mailserver (default: localhost)
	port:       [optional] port, the mailserver will listen on (default: 25)
	tls:	    [optional] use TLS if true
	username:   [optional] authenticate against mailserver if username and password are set
	password:	[optional] authenticate against mailserver if username and password are set
	"""

	# default values
	m_sender = 'tarpit@example.com'
	m_subject = 'Testmessage %s' % time.ctime()
	m_ehlo = 'ucstest.%d.example.com' % os.getpid()
	m_server = 'localhost'
	m_port = 25
	m_msg = '''Hello,

This is a test mail. Please do not answer.
(%s)
.
Regards,
.
...ucs-test
''' % idstring

	# use user values if defined
	if sender:
		m_sender = sender
	if recipients and type(recipients) == str:
		m_recipients = [recipients]
	elif recipients and type(recipients) == list:
		m_recipients = recipients
	else:
		raise UCSTest_Mail_InvalidRecipientList()
	if subject:
		m_subject = subject
	if server:
		m_server = server
	if port:
		m_port = int(port)
	if msg:
		m_msg = msg

	print '*** Sending mail: recipients=%r sender=%r subject=%r idstring=%r gtube=%r server=%r port=%r tls=%r username=%r password=%r HELO/EHLO=%r' % (
		m_recipients, m_sender, m_subject, idstring, gtube, m_server, m_port, tls, username, password, m_ehlo)

	# build message
	# m_body = ''
	# m_body += 'From: %s\n' % m_sender
	# m_body += 'To: %s\n' % ', '.join(m_recipients)
	# m_body += 'Subject: %s\n' % m_subject
	# m_body += '.\n'
	# m_body += m_msg
	# m_body += '.\n'
	if gtube:
		m_msg += '\nXJS*C4JDBQADN1.NSBN3*2IDNEN*GTUBE-STANDARD-ANTI-UBE-TEST-EMAIL*C.34X\n'

	mimemsg = MIMEMultipart()
	mimemsg['From'] = m_sender
	mimemsg['To'] = COMMASPACE.join(m_recipients)
	mimemsg['Date'] = time.strftime("%a, %d %b %Y %H:%M:%S +0000")
	mimemsg['Subject'] = m_subject
	mimemsg['UCS-TEST'] = idstring

	mimemsg.attach(MIMEText(m_msg))

	if virus:
		mimemsg.attach(MIMEText('X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*'))

	for fn in attachments:
		part = MIMEBase('application', "octet-stream")
		part.set_payload(open(fn, 'rb').read())
		Encoders.encode_base64(part)
		part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(fn))
		mimemsg.attach(part)

	# The actual mail send part
	server = smtplib.SMTP(host=m_server, port=m_port, local_hostname=m_ehlo)
	server.set_debuglevel(1)
	if tls:
		server.starttls()
	if username and password:
		server.login(username, password)
	ret_code = server.sendmail(m_sender, m_recipients, mimemsg.as_string())
	server.quit()
	return ret_code


def check_delivery(token, recipient_email, should_be_delivered, spam=False):
	print "%s is waiting for an email; should be delivered = %r" % (recipient_email, should_be_delivered)
	if spam:
		delivered  = spam_delivered(token, mail_address=recipient_email)
	else:
		delivered  = mail_delivered(token, mail_address=recipient_email)
	spam_str = 'Spam ' if spam else ''
	if should_be_delivered != delivered:
		if delivered:
			utils.fail('%sMail sent with token = %r to %s un-expectedly delivered' % (spam_str, token, recipient_email))
		else:
			utils.fail('%sMail sent with token = %r to %s un-expectedly not delivered' % (spam_str, token, recipient_email))


def check_sending_mail(
	username        = None,
	password        = None,
	recipient_email = None,
	tls             = True,
	allowed         = True,
	local           = True
	):
	token = str(time.time())
	try:
		ret_code = send_mail(
			recipients = recipient_email,
			msg        = token,
			port       = 587,
			server     = '4.3.2.1',
			tls        = tls,
			username   = username,
			password   = password
		)
		if (bool(ret_code) == allowed):
			utils.fail('Sending allowed = %r, but return code = %r\n {} means there are no refused recipient' % (allowed, ret_code))
		if local:
			check_delivery(token, recipient_email, allowed)
	except smtplib.SMTPException as ex:
		if allowed and (tls or 'access denied' in str(ex)):
			utils.fail('Mail sent failed with exception: %s' % ex)


if __name__ == '__main__':
	import doctest
	doctest.testmod()
# vim: ft=python:ts=4:sw=4:noet:
