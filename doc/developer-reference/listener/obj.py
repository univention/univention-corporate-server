from __future__ import absolute_import, print_function

import os
from pwd import getpwnam
from typing import Dict, List, Optional, Tuple

import ldap
import univention.debug as ud
from listener import SetUID

name = "refcheck"
description = "Check referential integrity of uniqueMember relations"
filter = "(uniqueMember=*)"
attribute = ["uniqueMember"]
modrdn = "1"


class LocalLdap(object):
	PORT = 7636

	def __init__(self) -> None:
		self.data: Dict[str, str] = {}
		self.con: Optional[ldap.ldapobject.LDAPObject] = None

	def setdata(self, key: str, value: str):
		self.data[key] = value

	def prerun(self) -> None:
		try:
			self.con = ldap.initialize('ldaps://%s:%d' % (self.data["ldapserver"], self.PORT))
			self.con.simple_bind_s(self.data["binddn"], self.data["bindpw"])
		except ldap.LDAPError as ex:
			ud.debug(ud.LISTENER, ud.ERROR, str(ex))

	def postrun(self) -> None:
		if not self.con:
			return
		try:
			self.con.unbind()
			self.con = None
		except ldap.LDAPError as ex:
			ud.debug(ud.LISTENER, ud.ERROR, str(ex))


class LocalFile(object):
	USER = "listener"
	LOG = "/var/log/univention/refcheck.log"

	def initialize(self) -> None:
		try:
			ent = getpwnam(self.USER)
			with SetUID():
				with open(self.LOG, "w"):
					pass
				os.chown(self.LOG, ent.pw_uid, -1)
		except OSError as ex:
			ud.debug(ud.LISTENER, ud.ERROR, str(ex))

	def log(self, msg) -> None:
		with open(self.LOG, 'a') as log:
			print(msg, file=log)

	def clean(self) -> None:
		try:
			with SetUID():
				os.remove(self.LOG)
		except OSError as ex:
			ud.debug(ud.LISTENER, ud.ERROR, str(ex))


class ReferentialIntegrityCheck(LocalLdap, LocalFile):
	MESSAGES = {
		(False, False): "Still invalid: ",
		(False, True): "Now valid: ",
		(True, False): "Now invalid: ",
		(True, True): "Still valid: ",
	}

	def __init__(self) -> None:
		super(ReferentialIntegrityCheck, self).__init__()
		self._delay: Optional[Tuple[str, Dict[str, List[bytes]]]] = None

	def handler(
		self,
		dn: str,
		new: Dict[str, List[bytes]],
		old: Dict[str, List[bytes]],
		command: str = '',
	) -> None:
		if self._delay:
			old_dn, old = self._delay
			self._delay = None
			if "a" == command and old['entryUUID'] == new['entryUUID']:
				self.handler_move(old_dn, old, dn, new)
				return
			self.handler_remove(old_dn, old)

		if "n" == command and "cn=Subschema" == dn:
			self.handler_schema(old, new)
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

	def handler_add(self, dn: str, new: Dict[str, List[bytes]]) -> None:
		if not self._validate(new):
			self.log("New invalid object: " + dn)

	def handler_modify(
		self,
		dn: str,
		old: Dict[str, List[bytes]],
		new: Dict[str, List[bytes]],
	) -> None:
		valid = (self._validate(old), self._validate(new))
		msg = self.MESSAGES[valid]
		self.log(msg + dn)

	def handler_remove(self, dn: str, old: Dict[str, List[bytes]]) -> None:
		if not self._validate(old):
			self.log("Removed invalid: " + dn)

	def handler_move(
		self,
		old_dn: str,
		old: Dict[str, List[bytes]],
		new_dn: str,
		new: Dict[str, List[bytes]],
	) -> None:
		valid = (self._validate(old), self._validate(new))
		msg = self.MESSAGES[valid]
		self.log("%s %s -> %s" % (msg, old_dn, new_dn))

	def handler_schema(
		self,
		old: Dict[str, List[bytes]],
		new: Dict[str, List[bytes]],
	) -> None:
		self.log("Schema change")

	def _validate(self, data: Dict[str, List[bytes]]) -> bool:
		assert self.con
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
