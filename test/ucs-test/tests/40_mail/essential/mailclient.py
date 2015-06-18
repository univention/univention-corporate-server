"""
.. module:: mailclient
.. moduleauthor:: Ammar Najjar <najjar@univention.de>
"""
from itertools import izip
import email
import imaplib
import time
import univention.testing.strings as uts
import univention.testing.ucr as ucr_test

class WrongAcls(Exception):
	pass

class MailClient(imaplib.IMAP4, imaplib.IMAP4_SSL):

	"""MailClient is a wrapper for imaplib.IMAP4"""
	def __new__(self, host, port=143, ssl=False):
		"""Custom class creation

		:host: string, host name
		:port: int, port number
		:returns: instance of imaplib.IMAP4
		"""
		if ssl:
			return imaplib.IMAP4_SSL(host, port)
		else:
			return imaplib.IMAP4(host, port)


	def log_in(self, usermail, password):
		"""wrap the super login method with try except

		:usermail: string, user mail
		:password: string, user password
		"""
		try:
			self.login(usermail, password)
		except Exception as ex:
			print "Login Failed with exeption:%r" % ex
			raise

	def getMailBoxes(self):
		"""Get Mail boxes for the user logged in

		:returns: list of strings, list of existing mailboxes
		"""
		mBoxes = self.list()[1]
		return [x.split()[-1] for x in mBoxes if 'Noselect' not in x.split()[0]]

	def get_acl(self, mailbox):
		"""get the exact acls from getacl

		:mailbox: string, user mailbox name
		:returns: string, acl strign or permission denied
		"""
		code , acls = self.getacl(mailbox)
		acl = acls[0].split()
		i = iter(acl[1:])
		d = dict(izip(i, i));
		return {acl[0]:d}

	def check_acls(self, expected_acls):
		"""Check if the the correct acls are set

		:expected_acls: string
		The expected acls are also mapped to the new set of
		acls are shown in the permissions_map

		Raises an Exception if the set acls are not correct
		"""
		permissions_map = {
			"a" : "a",
			"l" : "l",
			"r" : "r",
			"s" : "s",
			"w" : "w",
			"i" : "i",
			"p" : "p",
			"k" : "kc",
			"x" : "xc",
			"t" : "td",
			"e" : "ed",
			"c" : "kxc",
			"d" : "ted",
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

	def check_read(self, expected_result):
		"""Checks the read access of a certain mailbox

		:expected_result: dict{mailbox : bool}
		"""
		for mailbox in expected_result:
			self.select(mailbox)
			print self.status(mailbox, '(MESSAGES RECENT UIDNEXT UIDVALIDITY UNSEEN)')
			typ, data = self.search(None, 'ALL')
			print 'Response code:', typ
			for num in data[0].split():
				typ, data = self.fetch(num, '(RFC822)')
				print 'Message %s\n%s\n' % (num, data[0][1])
			self.close()

	def check_post(self, expected_result):
		"""Checks the post access of a certain mailbox

		:expected_result: dict{mailbox : bool}
		"""
		for mailbox in expected_result:
			self.select(mailbox)
			print self.status(mailbox, '(MESSAGES RECENT UIDNEXT UIDVALIDITY UNSEEN)')
			typ, data = self.search(None, 'ALL')
			print 'Response code:', typ
			self.close()

	def check_append(self, expected_result):
		"""Checks the append access of a certain mailbox

		:expected_result: dict{mailbox : bool}
		"""
		for mailbox in expected_result:
			self.select(mailbox)
			print self.get_acl(mailbox)
			typ, data =  self.append(
				mailbox, '',
				imaplib.Time2Internaldate(time.time()),
				str(email.message_from_string('TEST %s' % mailbox))
			)
			print 'Append = ', typ
			self.close()

	def check_write(self, expected_result):
		"""Checks the write access of a certain mailbox

		:expected_result: dict{mailbox : bool}
		"""
		pass

	def check_all(self, expected_result):
		"""Checks all access of a certain mailbox

		:expected_result: dict{mailbox : bool}
		"""
		pass

def create_shared_mailfolder(udm, mailHomeServer, mail=None, user_permission=None, group_permission=None):
	with ucr_test.UCSTestConfigRegistry() as ucr:
		domain = ucr.get('domainname')
		basedn = ucr.get('ldap/base')
		dovecat = ucr.is_true('mail/dovecot')
	name = uts.random_name()
	if mail:
		shared_mail = '%s@%s' % (name, domain)
	else:
		shared_mail = ''
	udm.create_object(
		'mail/folder',
		position = 'cn=folder,cn=mail,%s' % basedn,
		set = {
			'name'                 : name,
			'mailHomeServer'       : mailHomeServer,
			'mailDomain'           : domain,
			'mailPrimaryAddress'   : shared_mail
		},
		append = {
			'sharedFolderUserACL'  : user_permission or [],
			'sharedFolderGroupACL' : group_permission or [],
		}
	)
	if dovecat:
		if mail:
			ret_value = 'shared/%s' % shared_mail
			# ret_value = '"/"'
		else:
			ret_value = '%s@%s/INBOX' % (name, domain)
	else:
		ret_value = 'shared/%s' % name
	return ret_value

# vim: set ft=python ts=4 sw=4 noet ai :
