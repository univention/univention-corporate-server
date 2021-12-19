# -*- coding: utf-8 -*-
#
# Copyright 2004-2022 Univention GmbH
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

"""
|UDM| password encryption methods.
"""

from __future__ import absolute_import

import re
import bcrypt
import hashlib
from typing import List, Optional, Tuple  # noqa: F401

import heimdal
import passlib.hash

import univention.debug as ud
from univention.admin._ucr import configRegistry

RE_PASSWORD_SCHEME = re.compile(r'^{(\w+)}(!?)(.*)', re.I)


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
		urandom = open("/dev/urandom", "rb")
		for i in range(0, 16):  # up to 16 bytes of salt are evaluated by crypt(3), overhead is ignored
			o = ord(urandom.read(1))
			while not o < 256 // len(valid) * len(valid):  # make sure not to skew the distribution when using modulo
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

	from crypt import crypt as _crypt
	return _crypt(password, '$%s$%s$' % (method_id, salt, ))


def bcrypt_hash(password):
	# type: (str) -> str
	"""
	Return bcrypt hash.

	:param password: password string.
	:returns: the hashed password string.
	"""
	cost_factor = int(configRegistry.get('password/hashing/bcrypt/cost_factor', '12'))
	prefix = configRegistry.get('password/hashing/bcrypt/prefix', '2b').encode('utf8')
	salt = bcrypt.gensalt(rounds=cost_factor, prefix=prefix)
	return bcrypt.hashpw(password.encode('utf-8'), salt).decode('ASCII')


def ntlm(password):
	# type: (str) -> Tuple[str, str]
	"""
	Return tuple with NT and LanMan hash.

	:param password: password string.
	:returns: 2-tuple (NT, LanMan)
	"""
	nt = passlib.hash.nthash.hash(password).upper()

	if configRegistry.is_true('password/samba/lmhash', False):
		lm = passlib.hash.lmhash.hash(password).upper()
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
	>>> unlock_password('{BCRYPT}!')
	'{BCRYPT}'
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
	>>> lock_password('{BCRYPT}')
	'{BCRYPT}!'
	>>> lock_password('foo').startswith('{crypt}!$')
	True
	"""
	# cleartext password?
	if not RE_PASSWORD_SCHEME.match(password):
		if configRegistry.is_true('password/hashing/bcrypt'):
			return "{BCRYPT}!%s" % (bcrypt_hash(password))
		return "{crypt}!%s" % (crypt(password))

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


def get_password_history(password, pwhistory, pwhlen):
	# type: (str, str, int) -> str
	"""
	Append the given password as hash to the history of password hashes

	:param password: the new password.
	:param pwhistory: history of previous password hashes.
	:param pwhlen: length of the password history.
	:returns: modified password hash history.

	>>> get_password_history("a", "b", 0)
	'b'
	>>> len(get_password_history("a", "", 1).split(' '))
	1
	>>> len(get_password_history("a", "b", 1).split(' '))
	1
	>>> len(get_password_history("a", "b", 2).split(' '))
	2
	"""
	# create hash
	if password.startswith('{NT}'):
		# hash set by connector
		newpwhash = password
	elif configRegistry.is_true('password/hashing/bcrypt'):
		newpwhash = "{BCRYPT}%s" % (bcrypt_hash(password))
	else:
		newpwhash = crypt(password)

	# this preserves a temporary disabled history
	if pwhlen > 0:
		# split the history
		pwlist = pwhistory.strip().split(' ')
		# append new hash
		pwlist.append(newpwhash)
		# strip old hashes
		pwlist = pwlist[-pwhlen:]
		# build history
		pwhistory = ' '.join(pwlist)
	return pwhistory


def password_already_used(password, pwhistory):
	# type: (str, str) -> bool
	"""
	Check if the password is already used in the password hash history.

	:param password: new password hash.
	:param pwhistory: history of previous password hashes.
	:returns: `True` when already used, `False` otherwise,


	>>> password_already_used('a', '')
	False
	>>> password_already_used('a', 'b')
	False
	>>> password_already_used('a', 'b ' + crypt('a'))
	True
	"""
	for line in pwhistory.split(" "):
		linesplit = line.split("$")  # $method_id$salt$password_hash
		try:
			if linesplit[0] == '{BCRYPT}':
				password_hash = line[len('{BCRYPT}'):]
				if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('ASCII')):
					return True
			elif linesplit[0] == '{NT}':
				password_hash = line[len('{NT}$'):]
				if password_hash == ntlm(password)[0]:
					ud.debug(ud.ADMIN, ud.ERROR, '\nntlm(password) == [%s]' % (line))
					return True
			else:
				password_hash = crypt(password, linesplit[1], linesplit[2])
		except IndexError:  # old style password history entry, no method id/salt in there
			hash_algorithm = hashlib.new("sha1")
			hash_algorithm.update(password.encode("utf-8"))
			password_hash = hash_algorithm.hexdigest().upper()
		if password_hash == line:
			return True
	return False


class PasswortHistoryPolicy(object):
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
