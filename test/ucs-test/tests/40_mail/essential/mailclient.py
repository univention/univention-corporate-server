
import imaplib

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
		if len(acl) == 3:
			return acl[2]
		else:
			return acls[0]
