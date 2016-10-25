__package__ = ""  # workaround for PEP 366
name = "refcheck"
description = "Check referential integrity of uniqueMember relations"
filter = "(uniqueMember=*)"
attribute = ["uniqueMember"]
modrdn = "1"

import os
import ldap
import listener
import univention.debug as ud
from pwd import getpwnam


class LocalLdap(object):
	PORT = 7389

	def __init__(self):
		self.data = {}
		self.con = None

	def setdata(self, key, value):
		self.data[key] = value

	def prerun(self):
		try:
			self.con = ldap.open(self.data["ldapserver"], port=self.PORT)
			self.con.simple_bind_s(self.data["binddn"], self.data["bindpw"])
		except ldap.LDAPError as ex:
			ud.debug(ud.LISTENER, ud.ERROR, str(ex))

	def postrun(self):
		try:
			self.con.unbind()
			self.con = None
		except ldap.LDAPError as ex:
			ud.debug(ud.LISTENER, ud.ERROR, str(ex))


class LocalFile(object):
	USER = "listener"
	LOG = "/var/log/univention/refcheck.log"

	def initialize(self):
		try:
			ent = getpwnam(self.USER)
			with AsRoot():
				open(self.LOG, "wb")
				os.chown(self.LOG, ent.pw_uid, -1)
		except OSError as ex:
			ud.debug(ud.LISTENER, ud.ERROR, str(ex))

	def log(self, msg):
		with open(self.LOG, 'ab') as log:
			print >> log, msg

	def clean(self):
		try:
			with AsRoot():
				os.remove(self.LOG)
		except OSError as ex:
			ud.debug(ud.LISTENER, ud.ERROR, str(ex))


class AsRoot(object):

	"""
	Temporarily change effective UID to 'root'.
	"""

	def __enter__(self):
		listener.setuid(0)

	def __exit__(self, exc_type, exc_value, traceback):
		listener.unsetuid()


class ReferentialIntegrityCheck(LocalLdap, LocalFile):
	MESSAGES = {
		(False, False): "Still invalid: ",
		(False, True): "Now valid: ",
		(True, False): "Now invalid: ",
		(True, True): "Still valid: ",
	}

	def __init__(self):
		super(ReferentialIntegrityCheck, self).__init__()
		self._delay = None

	def handler(self, dn, new, old, command=''):
		if self._delay:
			old_dn, old = self._delay
			self._delay = None
			if "a" == command and old['entryUUID'] == new['entryUUID']:
				self.handler_move(old_dn, old, dn, new)
				return
			self.handler_remove(old_dn, old)

		if "n" == command and "cn=Subschema" == dn:
			self.handler_schema()
		elif new and not old:
			self.handler_add(dn, new)
		elif new and old:
			self.handler_modify(dn, old, new)
		elif not new and old:
			if "r" == command:
				self._delay = (dn, old)
			else:
				self.handler_remove(dn, old)
		else:
			pass  # ignore, reserved for future use

	def handler_add(self, dn, new):
		if not self._validate(new):
			self.log("New invalid object: " + dn)

	def handler_modify(self, dn, old, new):
		valid = (self._validate(old), self._validate(new))
		msg = self.MESSAGES[valid]
		self.log(msg + dn)

	def handler_remove(self, dn, old):
		if not self._validate(old):
			self.log("Removed invalid: " + dn)

	def handler_move(self, old_dn, old, new_dn, new):
		valid = (self._validate(old), self._validate(new))
		msg = self.MESSAGES[valid]
		self.log("%s %s -> %s" % (msg, old_dn, new_dn))

	def handler_schema(self):
		self.log("Schema change")

	def _validate(self, data):
		try:
			for dn in data["uniqueMember"]:
				self.con.search_ext_s(dn, ldap.SCOPE_BASE, attrlist=[], attrsonly=1)
			return True
		except ldap.NO_SUCH_OBJECT:
			return False
		except ldap.LDAPError as ex:
			ud.debug(ud.LISTENER, ud.ERROR, str(ex))
			return False


_instance = ReferentialIntegrityCheck()
initialize = _instance.initialize
handler = _instance.handler
clean = _instance.clean
prerun = _instance.prerun
postrun = _instance.postrun
setdata = _instance.setdata
