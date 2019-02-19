"""
.. module:: mailclient
.. moduleauthor:: Ammar Najjar <najjar@univention.de>
"""
from itertools import izip
from pexpect import spawn, EOF
import email
import imaplib
import sys
import time
import univention.testing.strings as uts
import univention.config_registry


class WrongAcls(Exception):
	pass


class LookupFail(Exception):
	pass


class ReadFail(Exception):
	pass


class AppendFail(Exception):
	pass


class WriteFail(Exception):
	pass


class BaseMailClient(object):
	"""BaseMailClient is a Base (interface) for imaplib.IMAP4_SSL and imaplib.IMAP4
	Does not work alone, can be used only as a super class of other child class.
	"""

	def login_plain(self, user, password, authuser=None):
		def plain_callback(response):
			if authuser is None:
				return "%s\x00%s\x00%s" % (user, user, password)
			else:
				return "%s\x00%s\x00%s" % (user, authuser, password)
		return self.authenticate('PLAIN', plain_callback)

	def log_in(self, usermail, password):
		"""wrap the super login method with try except

		:usermail: string, user mail
		:password: string, user password
		"""
		print('Logging in with username={!r} and password={!r}'.format(usermail, password))
		try:
			self.login(usermail, password)
			self.owner = usermail
		except Exception as ex:
			print "Login Failed with exception:%r" % ex
			raise

	def login_ok(self, usermail, password, expected_to_succeed=True):
		"""Check if login is OK

		:usermail: string, user mail
		:password: string, user password
		:expected_to_succeed: boolean, True if expected to be OK
		:return: 0 if the result = expected, else 1
		"""
		try:
			self.login(usermail, password)
			self.logout()
		except Exception as ex:
			if expected_to_succeed:
				print "Login Failed with exception:%r" % ex
				return 1
		return 0

	def get_quota_root(self, mailbox):
		"""docstring for get_quota_root"""
		response, quota_list = self.getquotaroot(mailbox)
		quota = quota_list[1][0].split(')')[0].split()[-1]
		return response, quota

	def getMailBoxes(self):
		"""Get Mail boxes for the user logged in

		:returns: list of strings, list of existing mailboxes
		"""
		result = []
		mBoxes = self.list()[1]
		if mBoxes[0]:
			result = [x.split('" ')[-1] for x in mBoxes if 'Noselect' not in x.split()[0]]
			for i, item in enumerate(result):
				if '"' in item:
					item = item.replace('"', '')
					result[i] = item
		return result

	def get_acl(self, mailbox):
		"""get the exact acls from getacl

		:mailbox: string, user mailbox name
		:returns: string, acl strign or permission denied
		"""
		code, acls = self.getacl(mailbox)
		if code != 'OK':
			raise ReadFail('Unable to read ACL for %r: %r %r' % (mailbox, code, acls))
		acl = acls[0].split()
		if '"' in acl[0]:
			x = acl[0].split('"', 1)[1]
			y = acl[1].split('"', 1)[0]
			acl[0] = "%s %s" % (x, y)
			del(acl[1])
		i = iter(acl[1:])
		d = dict(izip(i, i))
		return {acl[0]: d}

	def check_acls(self, expected_acls):
		"""Check if the the correct acls are set

		:expected_acls: string
		The expected acls are also mapped to the new set of
		acls are shown in the permissions_map

		Raises an Exception if the set acls are not correct
		"""
		permissions_map = {
			"a": "a",
			"l": "l",
			"r": "r",
			"s": "s",
			"w": "w",
			"i": "i",
			"p": "p",
			"k": "kc",
			"x": "xc",
			"t": "td",
			"e": "ed",
			"c": "kxc",
			"d": "ted",
		}
		for mailbox in expected_acls:
			current = self.get_acl(mailbox)
			print 'Current = ', current
			for who in expected_acls.get(mailbox):
				permissions = expected_acls.get(mailbox).get(who)
				set1 = set(''.join([permissions_map[x] for x in permissions]))
				set2 = set(current.get(mailbox).get(who))

				if not (who in current.get(mailbox).keys() or set1 == set2):
					raise WrongAcls('\nExpected = %s\nCurrent = %s\n' % (
						expected_acls.get(mailbox).get(who), current.get(mailbox).get(who)))

	def check_lookup(self, mailbox_owner, expected_result):
		"""Checks the lookup access of a certain mailbox

		:expected_result: dict{mailbox : bool}
		"""
		print('check_lookup() mailbox_owner={!r} expected_result={!r}'.format(mailbox_owner, expected_result))
		for mailbox, retcode in expected_result.items():
			if mailbox_owner != self.owner:
				mailbox = self.mail_folder(mailbox_owner, mailbox)
			data = self.getMailBoxes()
			print 'Lookup :', mailbox, data
			if (mailbox in data) != retcode:
				raise LookupFail('Un-expected result for listing the mailbox %s' % mailbox)

	def check_read(self, mailbox_owner, expected_result):
		"""Checks the read access of a certain mailbox

		:expected_result: dict{mailbox : bool}
		"""
		for mailbox, retcode in expected_result.items():
			if mailbox_owner != self.owner:
				mailbox = self.mail_folder(mailbox_owner, mailbox)
			self.select(mailbox)
			typ, data = self.status(mailbox, '(MESSAGES RECENT UIDNEXT UIDVALIDITY UNSEEN)')
			print 'Read Retcode:', typ, data
			if (typ == 'OK') != retcode:
				raise ReadFail('Unexpected read result for the inbox %s' % mailbox)
			if 'OK' in typ:
				# typ, data = self.search(None, 'ALL')
				# for num in data[0].split():
				# 	typ, data = self.fetch(num, '(RFC822)')
				# 	print 'Message %s\n%s\n' % (num, data[0][1])
				self.close()

	def check_append(self, mailbox_owner, expected_result):
		"""Checks the append access of a certain mailbox

		:expected_result: dict{mailbox : bool}
		"""
		for mailbox, retcode in expected_result.items():
			if mailbox_owner != self.owner:
				mailbox = self.mail_folder(mailbox_owner, mailbox)
			self.select(mailbox)
			typ, data = self.append(
				mailbox, '',
				imaplib.Time2Internaldate(time.time()),
				str(email.message_from_string('TEST %s' % mailbox))
			)
			print 'Append Retcode:', typ, data
			if (typ == 'OK') != retcode:
				raise AppendFail('Unexpected append result to inbox %s' % mailbox)
			if 'OK' in typ:
				self.close()

	def check_write(self, mailbox_owner, expected_result):
		"""Checks the write access of a certain mailbox

		:expected_result: dict{mailbox : bool}
		"""
		for mailbox, retcode in expected_result.items():
			# actual Permissions are given to shared/owner/INBOX
			# This is different than listing
			if mailbox_owner != self.owner and mailbox == 'INBOX':
				mailbox = 'shared/%s/INBOX' % (mailbox_owner,)
			subname = uts.random_name()
			typ, data = self.create('%s/%s' % (mailbox, subname))
			print 'Create Retcode:', typ, data
			if (typ == 'OK') != retcode:
				raise WriteFail('Unexpected create sub result mailbox in %s' % mailbox)
			if 'OK' in typ:
				typ, data = self.delete('%s/%s' % (mailbox, subname))
				print 'Delete Retcode:', typ, data
				if (typ == 'OK') != retcode:
					raise WriteFail('Unexpected delete sub result mailbox in %s' % mailbox)

	def mail_folder(self, mailbox_owner, mailbox):
		if mailbox == 'INBOX':
			return 'shared/%s' % (mailbox_owner,)
		if '/' not in mailbox:
			return 'shared/%s/%s' % (mailbox_owner, mailbox)
		return mailbox

	def check_permissions(self, owner_user, mailbox, permission):
		"""Check Permissions all together"""
		permissions = {
			'lookup': 'l',
			'read': 'lrs',
			'post': 'lrsp',
			'append': 'lrspi',
			'write': 'lrspiwcd',
			'all': 'lrspiwcda',
		}

		def lookup_OK(permission):
			return set(permissions.get('lookup')).issubset(permission)

		def read_OK(permission):
			return set(permissions.get('read')).issubset(permission)

		def post_OK(permission):
			return set(permissions.get('post')).issubset(permission)

		def append_OK(permission):
			return set(permissions.get('append')).issubset(permission)

		def write_OK(permission):
			return set(permissions.get('write')).issubset(permission)

		def all_OK(permission):
			return set(permissions.get('all')).issubset(permission)

		self.check_lookup(owner_user, {mailbox: lookup_OK(permission)})
		self.check_read(owner_user, {mailbox: read_OK(permission)})
		self.check_append(owner_user, {mailbox: append_OK(permission)})
		self.check_write(owner_user, {mailbox: write_OK(permission)})


class MailClient_SSL(imaplib.IMAP4_SSL, BaseMailClient):

	"""MailClient_SSL is a wrapper for imaplib.IMAP4_SSL"""

	def __init__(self, host, port=993):
		imaplib.IMAP4_SSL.__init__(self, host, port)


class MailClient(imaplib.IMAP4, BaseMailClient):

	"""MailClient is a wrapper for imaplib.IMAP4"""

	def __init__(self, host, port=143):
		imaplib.IMAP4.__init__(self, host, port)


# vim: set ft=python ts=4 sw=4 noet ai :
