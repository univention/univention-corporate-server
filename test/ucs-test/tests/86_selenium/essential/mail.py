# -*- coding: utf-8 -*-
#
# UCS test
#
# Copyright 2013-2019 Univention GmbH
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

import glob
import smtplib
import imaplib
import email
import os
from os.path import basename
import re
import socket
import subprocess
import sys
import time
import uuid
import univention.testing.strings as uts
import univention.config_registry
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
import email.encoders as Encoders
import poplib

from univention.config_registry import handler_set
import univention.testing.utils as utils
import univention.testing.ucr as ucr_test
from univention.testing.decorators import WaitForNonzeroResultOrTimeout

COMMASPACE = ', '


class Mail(object):

	def __init__(self, timeout=10):
		self.timeout = timeout

	def get_reply(self, s):
		reply = ''
		try:
			buff_size = 1024
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
		s.settimeout(self.timeout)
		s.connect((hostname, 143))
		print self.get_reply(s)
		retval = self.send_and_receive(s, 'a001', 'login %s %s\r\n' % (username, password))
		self.send_and_receive(s, 'a002', 'logout\r\n')
		s.close()
		return (retval == 'OK')

	def get_imap_quota(self, username, password):
		hostname = socket.gethostname()
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.settimeout(self.timeout)
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

	def copy(self, message_set, old_mailbox, new_mailbox):
		rv, data = self.connection.select(old_mailbox)
		assert rv == "OK"
		rv, data = self.connection.copy(message_set, new_mailbox)
		assert rv == "OK"

	def create_subfolder(self, parent, child):
		# find separator symbol
		rv, data = self.connection.list()
		assert rv == "OK"
		separator = None
		regex = re.compile(r'^\(.*\) "(?P<separator>.*)" (?P<folder>.*)$')
		for s in data:
			sep, folder_name = regex.match(s).groups()
			if folder_name == parent:
				separator = sep
				break
		assert separator is not None, 'Could not find parent folder.'
		# create subfolder
		subfolder_name = '{}{}{}'.format(parent, separator, child)
		rv, data = self.connection.create(subfolder_name)
		assert rv == "OK"
		return subfolder_name

	def delete_folder(self, folder_name):
		rv, data = self.connection.delete(folder_name)
		assert rv == "OK"


class PopMail(Mail):

	def login_OK(self, username, password):
		hostname = socket.gethostname()
		con = poplib.POP3_SSL(hostname)
		con.set_debuglevel(2)
		con.user(username)
		try:
			con.pass_(password)
		except poplib.error_proto:
			return False
		finally:
			con.quit()
		return True


ucr = univention.config_registry.ConfigRegistry()
ucr.load()


def random_email():
	return '%s@%s' % (uts.random_name(), ucr.get('domainname'))


def make_token():
	return str(time.time())


def get_dir_files(dir_path, recursive=True, exclude=None):
	result = []
	if not exclude:
		exclude = []
	for f in glob.glob('%s/*' % dir_path):
		if os.path.isfile(f):
			result.append(f)
		if os.path.isdir(f) and recursive and f not in exclude:
			result.extend(get_dir_files(f))
	return result


def get_maildir_filenames(maildir):
	"""
	Returns all filenames for mails in specified dovecot maildir:

	Example: get_maildir_filenames('/var/spool/dovecot/private/example.com/user1/Maildir')
	['/var/spool/dovecot/private/example.com/user1/Maildir/cur/1435755414.M432893P22169.slave22b,S=1744,W=1783',
	'/var/spool/dovecot/private/example.com/user1/Maildir/new/1435734534.M432834534215.slave22b,S=2342,W=6545']
	"""
	blacklist = ["maildirfolder", "maildirsize"]
	result = []
	for dirpath, dirnames, filenames in os.walk(maildir.rstrip("/")):
		if basename(dirpath) == "Maildir":
			continue
		result.extend([os.path.join(dirpath, x) for x in filenames if not x.startswith("dovecot") and x not in blacklist])
	return result


def get_file_contain(token, _dir):
	for _file in get_dir_files(_dir, recursive=True):
		with open(_file) as fi:
			if token in fi.read():
				return os.path.basename(_file)


def virus_detected_and_quarantined(token, mail_address):
	"""
	Check if the virusmail with given token has been detected (==> virus_archive != None) and
	the user specified by mail_address and systemmail have been informed.
	"""
	virus_dir = '/var/lib/amavis/virusmails'
	virus_archive = get_file_contain(token, virus_dir)
	root_informed = user_informed = False
	if virus_archive:
		root_informed = bool(file_search_mail(tokenlist=[virus_archive], user='systemmail', timeout=0))
		user_informed = bool(file_search_mail(tokenlist=[virus_archive], mail_address=mail_address, timeout=0))
	return user_informed and root_informed


def deactivate_spam_detection():
	handler_set(['mail/antivir/spam=no'])


def activate_spam_detection():
	handler_set(['mail/antivir/spam=yes'])


def activate_spam_header_tag(tag):
	handler_set(['mail/antispam/headertag=%s' % tag])


def restart_postfix():
	cmd = ['/etc/init.d/postfix', 'restart']
	try:
		subprocess.Popen(cmd, stderr=open('/dev/null', 'w')).communicate()
	except EnvironmentError as ex:
		print >> sys.stderr, ex


def reload_postfix():
	cmd = ['/etc/init.d/postfix', 'force-reload']
	try:
		subprocess.Popen(cmd, stderr=open('/dev/null', 'w')).communicate()
	except EnvironmentError as ex:
		print >> sys.stderr, ex


def reload_amavis_postfix():
	for cmd in (
		['newaliases'],
		['/etc/init.d/amavis', 'force-reload'],
		['/etc/init.d/postfix', 'force-reload'],
	):
		try:
			subprocess.Popen(cmd, stderr=open('/dev/null', 'w')).communicate()
		except EnvironmentError as ex:
			print >> sys.stderr, ex


def get_spam_folder_name():
	"""
	Returns the name of the current spam folder
	"""
	if ucr.is_true('mail/dovecot'):
		folder = ucr.get('mail/dovecot/folder/spam', 'Spam')
		if folder and folder.lower() == 'none':
			folder = None
	else:
		folder = None
	return folder


@WaitForNonzeroResultOrTimeout
def spam_delivered(token, mail_address):
	delivered = False
	spam = False
	with ucr_test.UCSTestConfigRegistry() as ucr:
		spam_folder = ucr.get('mail/dovecot/folder/spam') or 'Spam'
	mail_dir = get_dovecot_maildir(mail_address, folder=spam_folder)
	if not os.path.isdir(mail_dir):
		print 'Warning: maildir %r does not exist!' % (mail_dir,)
	for _file in get_dir_files(mail_dir, recursive=True, exclude=["tmp"]):
		with open(_file) as fi:
			content = fi.read()
		delivered = delivered or (token in content)
		if delivered:
			if 'X-Spam-Flag: YES' in content:
				spam = spam or True
			break
	return delivered and spam


@WaitForNonzeroResultOrTimeout
def mail_delivered(token, user=None, mail_address=None, check_root=True):
	"""
	Check if a mail with the specified token or message ID has been delivered to a mail spool.
	A "token" is a string, that should occur in the mail body. The message ID is looked up in the
	mail header. The mail spool may be specified via multiple ways:
	"check_root": (boolean) checks /var/mail/systemmail for the requested token/messageid
	"user": (string) checks /var/mail/%s for the requested token/messageid
	"mail_address": (string) checks directly within the mail spool directory
		of the specified mail address for the requested token/messageid
	"""
	delivered = False
	if check_root:
		_file = '/var/mail/systemmail'
		if os.path.isfile(_file):
			with open(_file) as fi:
				delivered = delivered or (token in fi.read())
	if user:
		_file = os.path.join('/var/mail', user)
		if os.path.isfile(_file):
			with open(_file) as fi:
				delivered = delivered or (token in fi.read())
	if mail_address and '@' in mail_address:
		mail_dir = get_dovecot_maildir(mail_address)
		for _file in get_dir_files(mail_dir, recursive=True, exclude=["tmp"]):
			with open(_file) as fi:
				delivered = delivered or (token in fi.read())
				if delivered:
					break
	return delivered


def file_search_mail(tokenlist=None, user=None, mail_address=None, folder=None, timeout=0):
	"""
	Check if a mail with the specified token or message ID has been delivered to a mail spool.
	A "token" is a string, that should occur in the mail body. The message ID is looked up in the
	mail header. The mail spool may be specified via multiple ways:
	tokenlist: list of strings: list of strings that all have to be found within a mail
	user: string: if username is specified, a check of /var/mail/%s is performed
	mail_address: string: checks directly within the mail spool directory
	folder: string: if mail_address is specified and folder is not specified, file_search_mail
					searches only in the INBOX, if folder is specified too, the given folder
					is checked.
	timeout: integer: if the number of found mails is 0, the search is retried every second
					up to <timeout> attempts.
	:return: number of found mails
	"""
	result = 0
	if timeout < 1:
		timeout = 1
	while result == 0 and timeout > 0:
		timeout -= 1
		if user:
			_file = os.path.join('/var/mail', user)
			if os.path.isfile(_file):
				with open(_file) as fd:
					content = fd.read()
					for token in tokenlist:
						if token not in content:
							break
					else:
						result += 1

		if mail_address:
			mail_dir = get_dovecot_maildir(mail_address, folder=folder)
			files = get_maildir_filenames(mail_dir)

			if not os.path.isdir(mail_dir):
				print 'Warning: maildir %r does not exist!' % (mail_dir,)

			for _file in files:
				with open(_file) as fd:
					content = fd.read()
					for token in tokenlist:
						if token not in content:
							break
					else:
						result += 1
		if not result and timeout:
			time.sleep(1)
			print 'file_search_mail(tokenlist=%r, user=%r mail_address=%r, folder=%r): no mail found - %d attempt(s) left' % (tokenlist, user, mail_address, folder, timeout)
	return result


def imap_search_mail(token=None, messageid=None, server=None, imap_user=None, imap_password=None, imap_folder=None, use_ssl=True):
	"""
	Check if a mail with the specified token or message ID has been delivered to a specific mail folder.
	A "token" is a string, that should occur in the mail body. The message ID is looked up in the
	mail header.
	The search is performed via IMAP protocol, so at least server, username and folder have to be specified.

	:param token: string: this string is searched in the body of each mail in folder; please note that this is a slow and simple search and MIME parts are not decoded etc.
	:param messageid: string: this message id is searched in the mail header of each mail (faster than token search)
	:param server: string: fqdn or IP address of IMAP server
	:param imap_user: string: IMAP user
	:param imap_password: string: password for IMAP user; if not specified, 'univention' is used
	:param imap_folder: string: IMAP folder that is selected during search (no recursive search!)
	:param use_ssl: boolean: use SSL encryption for IMAP connection
	:return: integer: returns the number of matching mails (if neither token nor messageid is specified, the number of mails in folder is returned)
	"""

	assert token or messageid, "imap_search_mail: token or messageid have not been specified"
	server = server or '%s.%s' % (ucr.get('hostname'), ucr.get('domainname'))
	assert imap_user, "imap_search_mail: imap_user has not been specified"
	imap_password = imap_password or "univention"
	imap_folder = imap_folder or ""
	assert isinstance(imap_folder, str), "imap_search_mail: imap_folder is no string"

	if use_ssl:
		conn = imaplib.IMAP4_SSL(host=server)
	else:
		conn = imaplib.IMAP4(host=server)
	assert conn.login(imap_user, imap_password)[0] == 'OK', 'imap_search_mail: login failed'
	assert conn.select(imap_folder)[0] == 'OK', 'imap_search_mail: select folder %r failed' % (imap_folder,)

	foundcnt = 0
	if messageid:
		status, result = conn.search(None, '(HEADER Message-ID "%s")' % (messageid,))
		assert status == 'OK'
		result = result[0]
		if result:
			result = result.split()
			print 'Found %d messages matching msg id %r' % (len(result), messageid)
			foundcnt += len(result)

	if token:
		status, result = conn.search(None, 'ALL')
		assert status == 'OK'
		if result:
			msgids = result.split()
			print 'Folder contains %d messages' % (len(msgids),)
			for msgid in msgids:
				typ, msg_data = conn.fetch(msgid, '(BODY.PEEK[TEXT])')
				for response_part in msg_data:
					if isinstance(response_part, tuple):
						if token in response_part[1]:
							print 'Found token %r in msg %r' % (token, msgid)
							foundcnt += 1

	if not token and not messageid:
		status, result = conn.search(None, 'ALL')
		assert status == 'OK'
		if result:
			msgids = result.split()
			foundcnt = len(msgids)
			print 'Found %d messages in folder' % (foundcnt,)

	return foundcnt


class UCSTest_Mail_Exception(Exception):
	""" Generic ucstest mail error """


class UCSTest_Mail_InvalidFolderName(UCSTest_Mail_Exception):
	""" The given folder name is invalid """


class UCSTest_Mail_InvalidMailAddress(UCSTest_Mail_Exception):
	""" The given mail address is invalid """


class UCSTest_Mail_InvalidRecipientList(UCSTest_Mail_Exception):
	""" The given recipient list is invalid """


class UCSTest_Mail_MissingMailbox(UCSTest_Mail_Exception):
	""" At least one mailbox for the given mail addresses could not be found in given time range.
		The exception contains two arguments:
		- the list of checked mailboxes
		- the list of missing mailboxes (a subset of the first list)
	"""


def get_dovecot_maildir(mail_address, folder=None):
	"""
	Returns directory name for specified mail address.

	>>> get_dovecot_maildir('testuser@example.com')
	'/var/spool/dovecot/private/example.com/testuser/Maildir'

	>>> get_dovecot_maildir('someuser@foobar.com')
	'/var/spool/dovecot/private/foobar.com/someuser/Maildir'

	>>> get_dovecot_maildir('someuser@foobar.com', folder='Spam/SubSpam')
	'/var/spool/dovecot/private/foobar.com/someuser/Maildir/.Spam.SubSpam'

	>>> get_dovecot_maildir('only-localpart')
	Traceback (most recent call last):
	...
	UCSTest_Mail_InvalidMailAddress

	>>> get_dovecot_maildir('')
	Traceback (most recent call last):
	...
	UCSTest_Mail_InvalidMailAddress
	"""

	if not mail_address:
		raise UCSTest_Mail_InvalidMailAddress()
	if '@' not in mail_address:
		raise UCSTest_Mail_InvalidMailAddress()

	localpart, domain = mail_address.rsplit('@', 1)
	result = '/var/spool/dovecot/private/%s/%s/Maildir' % (domain.lower(), localpart.lower())
	if folder:
		result = '%s/.%s' % (result, folder.lstrip('/').replace('/', '.'))
	return result


def get_dovecot_shared_folder_maildir(foldername):
	"""
	Returns directory name for specified shared folder name.

	>>> get_dovecot_shared_folder_maildir('shared/myfolder@example.com')
	'/var/spool/dovecot/private/example.com/myfolder/Maildir'

	>>> get_dovecot_shared_folder_maildir('myfolder@example.com/INBOX')
	'/var/spool/dovecot/public/example.com/myfolder/.INBOX'
	"""
	if not foldername:
		raise UCSTest_Mail_InvalidFolderName()
	if '@' not in foldername or '/' not in foldername:
		raise UCSTest_Mail_InvalidFolderName()
	if foldername.count('/') > 1:
		raise UCSTest_Mail_InvalidFolderName()

	# shared folder with mail primary address
	if foldername.startswith('shared/'):
		return get_dovecot_maildir(foldername[7:])

	# shared folder without mail primary address
	localpart, domain = foldername.rsplit('@', 1)
	domain, folderpath = domain.split('/', 1)
	return '/var/spool/dovecot/public/%s/%s/.%s' % (domain, localpart.lower(), folderpath)


def create_shared_mailfolder(udm, mailHomeServer, mailAddress=None, user_permission=None, group_permission=None):
	with ucr_test.UCSTestConfigRegistry() as ucr:
		domain = ucr.get('domainname').lower()  # lower() can be removed, when #39721 is fixed
		basedn = ucr.get('ldap/base')
	name = uts.random_name()
	folder_mailaddress = ''
	if isinstance(mailAddress, str):
		folder_mailaddress = mailAddress
	elif mailAddress:
		folder_mailaddress = '%s@%s' % (name, domain)

	folder_dn = udm.create_object(
		'mail/folder',
		position='cn=folder,cn=mail,%s' % basedn,
		set={
			'name': name,
			'mailHomeServer': mailHomeServer,
			'mailDomain': domain,
			'mailPrimaryAddress': folder_mailaddress
		},
		append={
			'sharedFolderUserACL': user_permission or [],
			'sharedFolderGroupACL': group_permission or [],
		}
	)
	if mailAddress:
		folder_name = 'shared/%s' % folder_mailaddress
	else:
		folder_name = '%s@%s/INBOX' % (name, domain)
	return folder_dn, folder_name, folder_mailaddress


def create_random_msgid():
	""" returns a random and unique message ID """
	return '%s.%s' % (uuid.uuid1(), random_email())


def send_mail(recipients=None, sender=None, subject=None, msg=None, idstring='no id string',
	gtube=False, virus=False, attachments=[], server=None, port=0, tls=False, username=None, password=None,
	debuglevel=1, messageid=None, ssl=False):
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
	debuglevel: [optional] SMTP client debug level (default: 1)
	messageid:  [optional] message id (defaults to a random value)
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
	if recipients and isinstance(recipients, str):
		m_recipients = [recipients]
	elif recipients and isinstance(recipients, list):
		m_recipients = recipients
	else:
		raise UCSTest_Mail_InvalidRecipientList()
	if subject:
		m_subject = subject
	if server:
		m_server = server
	if port:
		m_port = int(port)
	else:
		if tls:
			m_port = 587
		else:
			m_port = 25
	if msg:
		m_msg = msg

	print '*** Sending mail: recipients=%r sender=%r subject=%r idstring=%r gtube=%r server=%r port=%r tls=%r username=%r password=%r HELO/EHLO=%r' % (
		m_recipients, m_sender, m_subject, idstring, gtube, m_server, m_port, tls, username, password, m_ehlo)

	if len(m_msg.split()) < 2:
		print('*** Warning: A body with only one word will be rated with BODY_SINGLE_WORD=2.499 and probably lead to the message being identified as spam.')

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
	mimemsg['Message-Id'] = messageid or create_random_msgid()

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
	if ssl:
		server = smtplib.SMTP_SSL(host=m_server, port=m_port, local_hostname=m_ehlo)
	else:
		server = smtplib.SMTP(host=m_server, port=m_port, local_hostname=m_ehlo)
	server.set_debuglevel(debuglevel)
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
		delivered = spam_delivered(token, mail_address=recipient_email)
	else:
		delivered = mail_delivered(token, mail_address=recipient_email)
	spam_str = 'Spam ' if spam else ''
	if should_be_delivered != delivered:
		if delivered:
			utils.fail('%sMail sent with token = %r to %s un-expectedly delivered' % (spam_str, token, recipient_email))
		else:
			utils.fail('%sMail sent with token = %r to %s un-expectedly not delivered' % (spam_str, token, recipient_email))


def check_sending_mail(
	username=None,
	password=None,
	recipient_email=None,
	tls=True,
	allowed=True,
	local=True
):
	token = 'The token is {}.'.format(time.time())
	try:
		ret_code = send_mail(
			recipients=recipient_email,
			msg=token,
			port=587,
			server='4.3.2.1',
			tls=tls,
			username=username,
			password=password
		)
		if bool(ret_code) == allowed:
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
