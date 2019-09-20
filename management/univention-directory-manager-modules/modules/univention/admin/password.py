# -*- coding: utf-8 -*-
"""
|UDM| password encryption methods.
"""
# Copyright 2004-2019 Univention GmbH
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

from __future__ import absolute_import

import re
import hashlib
import heimdal
import smbpasswd
import string
import univention.config_registry
import univention.debug as ud
try:
	from typing import List, Optional, Tuple  # noqa F401
except ImportError:
	pass

configRegistry = univention.config_registry.ConfigRegistry()
configRegistry.load()

RE_PASSWORD_SCHEME = re.compile('^{(\w+)}(!?)(.*)', re.I)


def crypt(password, method_id=None, salt=None):
	# type: (str, Optional[str], Optional[str]) -> str
	"""
	Return crypt hash.

	:param password: password string.
	:param method_id: optional hash type, MD5, SHA256/SHA-256, SHA512/SHA-512.
	:param salt: salt for randomize the hashing.
	:returns: the hashed password string.
	"""
	hashing_method = configRegistry.get('password/hashing/method', 'sha-512').upper()

	if salt is None:
		salt = ''
		valid = [
			'.', '/', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
			'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v',
			'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
			'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
			'U', 'V', 'W', 'X', 'Y', 'Z', '0', '1', '2', '3', '4', '5',
			'6', '7', '8', '9']
		urandom = open("/dev/urandom", "r")
		for i in xrange(0, 16):  # up to 16 bytes of salt are evaluated by crypt(3), overhead is ignored
			o = ord(urandom.read(1))
			while not o < 256 / len(valid) * len(valid):  # make sure not to skew the distribution when using modulo
				o = ord(urandom.read(1))
			salt = salt + valid[(o % len(valid))]
		urandom.close()

	if method_id is None:
		method_id = {
			'MD5': '1',
			'SHA256': '5',
			'SHA-256': '5',
			'SHA512': '6',
			'SHA-512': '6',
		}.get(hashing_method, '6')

	import crypt
	return crypt.crypt(password.encode('utf-8'), '$%s$%s$' % (method_id, salt, ))


def ntlm(password):
	# type: (str) -> Tuple[str, str]
	"""
	Return tuple with NT and LanMan hash.

	:param password: password string.
	:returns: 2-tuple (NT, LanMan)
	"""
	nt = smbpasswd.nthash(password)

	if configRegistry.is_true('password/samba/lmhash', False):
		lm = smbpasswd.lmhash(password)
	else:
		lm = ''

	return (nt, lm)


def krb5_asn1(principal, password, krb5_context=None):
	# type: (str, str, Optional[heimdal.context]) -> List[bytes]
	"""
	Generate Kerberos password hashes.

	:param principal: Kerberos principal name.
	:param password: password string.
	:param krb5_context: optional Kerberos context.
	:returns: list of ASN1 encoded Kerberos hashes.
	"""
	list = []
	if isinstance(principal, unicode):
		principal = principal.encode('utf-8')
	if isinstance(password, unicode):
		password = password.encode('utf-8')
	if not krb5_context:
		krb5_context = heimdal.context()
	for krb5_etype in krb5_context.get_permitted_enctypes():
		if str(krb5_etype) == 'des3-cbc-md5' and configRegistry.is_false('password/krb5/enctype/des3-cbc-md5', True):
			continue
		krb5_principal = heimdal.principal(krb5_context, principal)
		krb5_keyblock = heimdal.keyblock(krb5_context, krb5_etype, password, krb5_principal)
		krb5_salt = heimdal.salt(krb5_context, krb5_principal)
		list.append(heimdal.asn1_encode_key(krb5_keyblock, krb5_salt, 0))
	return list


def is_locked(password):
	# type: (str) -> bool
	"""
	Check is the password (hash) is locked

	:param password: password hash.
	:returns: `True` when locked, `False` otherwise.

	>>> is_locked('foo')
	False
	>>> is_locked('{crypt}$1$foo')
	False
	>>> is_locked('{crypt}!$1$foo')
	True
	>>> is_locked('{KINIT}')
	False
	>>> is_locked('{LANMAN}!')
	True
	"""
	match = RE_PASSWORD_SCHEME.match(password or '')
	return match is not None and '!' == match.group(2)


def unlock_password(password):
	# type: (str) -> str
	"""
	Remove prefix from password used for locking.

	:param password: password hash.
	:returns: the unlocked password hash.

	>>> unlock_password('{crypt}!$1$foo')
	'{crypt}$1$foo'
	>>> unlock_password('{LANMAN}!')
	'{LANMAN}'
	>>> unlock_password('{SASL}!')
	'{SASL}'
	>>> unlock_password('{KINIT}!')
	'{KINIT}'
	"""
	if is_locked(password):
		match = RE_PASSWORD_SCHEME.match(password).groups()
		password = '{%s}%s' % (match[0], match[2])
	return password


def lock_password(password):
	# type: (str) -> str
	"""
	Add prefix to password used for locking.

	:param password: password hash.
	:returns: the locked password hash.

	>>> lock_password('{crypt}$1$foo')
	'{crypt}!$1$foo'
	>>> lock_password('{LANMAN}')
	'{LANMAN}!'
	>>> lock_password('{SASL}')
	'{SASL}!'
	>>> lock_password('{KINIT}')
	'{KINIT}!'
	>>> lock_password('foo').startswith('{crypt}!$')
	True
	"""
	# cleartext password?
	if not RE_PASSWORD_SCHEME.match(password):
		return "{crypt}!%s" % (univention.admin.password.crypt(password))

	if not is_locked(password):
		match = RE_PASSWORD_SCHEME.match(password).groups()
		password = '{%s}!%s' % (match[0], match[2])
	return password


def password_is_auth_saslpassthrough(password):
	# type: (str) -> bool
	"""
	Check if the password hash indicates the use of |SASL|.

	:param apssword: password hash.
	:returns: `True` is |SASL| shall be used, `False` otherwise.
	"""
	return password.startswith('{SASL}') and configRegistry.get('directory/manager/web/modules/users/user/auth/saslpassthrough', 'no').lower() == 'keep'


def get_password_history(newpwhash, pwhistory, pwhlen):
	# type: (str, str, int) -> str
	"""
	Append the given password hash to the history of password hashed

	:param newpwhash: new password hash.
	:param pwhistory: history of previous password hashes.
	:param pwhlen: length of the password history.
	:returns: modified password hash history.
	"""
	# split the history
	if len(string.strip(pwhistory)):
		pwlist = string.split(pwhistory, ' ')
	else:
		pwlist = []

	# this preserves a temporary disabled history
	if pwhlen > 0:
		if len(pwlist) < pwhlen:
			pwlist.append(newpwhash)
		else:
			# calc entries to cut out
			cut = 1 + len(pwlist) - pwhlen
			pwlist[0:cut] = []
			if pwhlen > 1:
				# and append to shortened history
				pwlist.append(newpwhash)
			else:
				# or replace the history completely
				if len(pwlist) > 0:
					pwlist[0] = newpwhash
					# just to be sure...
					pwlist[1:] = []
				else:
					pwlist.append(newpwhash)
	# and build the new history
	res = string.join(pwlist)
	return res


def password_already_used(password, pwhistory):
	# type: (str, str) -> bool
	"""
	Check if the password is already used in the password hash history.

	:param password: new password hash.
	:param pwhistory: history of previous password hashes.
	:returns: `True` when already used, `False` otherwise,
	"""
	for line in pwhistory.split(" "):
		linesplit = line.split("$")  # $method_id$salt$password_hash
		try:
			password_hash = univention.admin.password.crypt(password, linesplit[1], linesplit[2])
			ud.debug(ud.ADMIN, ud.ERROR, '\n== [%s]\n== [%s]' % (password_hash, line))
		except IndexError:  # old style password history entry, no method id/salt in there
			hash_algorithm = hashlib.new("sha1")
			hash_algorithm.update(password.encode("utf-8"))
			password_hash = hash_algorithm.hexdigest().upper()
		if password_hash == line:
			return True
	return False


class PasswortHistoryPolicy(type('', (), {}).mro()[-1]):
	"""
	Policy for handling history of password hashes.
	"""

	def __init__(self, pwhistoryPolicy):
		super(PasswortHistoryPolicy, self).__init__()
		self.pwhistoryPolicy = pwhistoryPolicy
		self.pwhistoryLength = None
		self.pwhistoryPasswordLength = 0
		self.pwhistoryPasswordCheck = False
		self.expiryInterval = 0
		if pwhistoryPolicy:
			try:
				self.pwhistoryLength = max(0, int(pwhistoryPolicy['length'] or 0))
			except ValueError:
				ud.debug(ud.ADMIN, ud.WARN, 'Corrupt Password history policy (history length): %r' % (pwhistoryPolicy.dn,))
			try:
				self.pwhistoryPasswordLength = max(0, int(pwhistoryPolicy['pwLength'] or 0))
			except ValueError:
				ud.debug(ud.ADMIN, ud.WARN, 'Corrupt Password history policy (password length): %r' % (pwhistoryPolicy.dn,))
			self.pwhistoryPasswordCheck = (pwhistoryPolicy['pwQualityCheck'] or '').lower() in ['true', '1']
			try:
				self.expiryInterval = max(0, int(pwhistoryPolicy['expiryInterval'] or 0))
			except ValueError:
				ud.debug(ud.ADMIN, ud.WARN, 'Corrupt Password history policy (expiry interval): %r' % (pwhistoryPolicy.dn,))


if __name__ == '__main__':
	import doctest
	doctest.testmod()
