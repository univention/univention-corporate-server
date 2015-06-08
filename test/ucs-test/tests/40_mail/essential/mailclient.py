"""
.. module:: mailclient
.. moduleauthor:: Ammar Najjar <najjar@univention.de>
"""
from itertools import izip
import imaplib
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
		return [x.split()[2] for x in mBoxes]

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
			for who in expected_acls.get(mailbox):
				permissions = expected_acls.get(mailbox).get(who)
				set1 = set(''.join([permissions_map[x] for x in permissions]))
				set2 = set(current.get(mailbox).get(who))

				if not (who in current.get(mailbox).keys() or set1 == set2):
					raise WrongAcls('\nExpected = %s\nCurrent = %s\n' % (
						expected_acls.get(mailbox).get(who), current.get(mailbox).get(who)))


def create_shared_mailfolder(udm, mailHomeServer, user_permission=None, group_permission=None):
	with ucr_test.UCSTestConfigRegistry() as ucr:
		domain = ucr.get('domainname')
		basedn = ucr.get('ldap/base')
	name = uts.random_name()
	udm.create_object(
		'mail/folder',
		position = 'cn=folder,cn=mail,%s' % basedn,
		set = {
			'name'                 : name,
			'mailHomeServer'       : mailHomeServer,
			'mailDomain'           : domain,
		},
		append = {
			'sharedFolderUserACL'  : user_permission or [],
			'sharedFolderGroupACL' : group_permission or [],
		}
	)
	return 'shared/%s' % name

# vim: set ft=python ts=4 sw=4 noet ai :
