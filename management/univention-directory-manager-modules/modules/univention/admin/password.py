# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  password encryption methods
#
# Copyright 2004-2017 Univention GmbH
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

import heimdal
import types
import smbpasswd
import univention.config_registry

configRegistry = univention.config_registry.ConfigRegistry()
configRegistry.load()


def crypt(password, method_id=None, salt=None):
	"""return crypt hash"""
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
	"""return tuple with NT and LanMan hash"""

	nt = smbpasswd.nthash(password)

	if configRegistry.is_true('password/samba/lmhash', False):
		lm = smbpasswd.lmhash(password)
	else:
		lm = ''

	return (nt, lm)


def krb5_asn1(principal, password, krb5_context=None):
	list = []
	if isinstance(principal, types.UnicodeType):
		principal = str(principal)
	if isinstance(password, types.UnicodeType):
		password = str(password)
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
	return password and (password.startswith('{crypt}!') or password.startswith('{LANMAN}!'))


def unlock_password(password):
	if is_locked(password):
		if password.startswith("{crypt}!"):
			return password.replace("{crypt}!", "{crypt}")
		elif password.startswith('{LANMAN}!'):
			return password.replace("{LANMAN}!", "{LANMAN}")
	return password


def lock_password(password):
	# cleartext password?
	if not password.startswith('{crypt}') and not password.startswith('{LANMAN}'):
		return "{crypt}!%s" % (univention.admin.password.crypt('password'))

	if not is_locked(password):
		if password.startswith("{crypt}"):
			return password.replace("{crypt}", "{crypt}!")
		elif password.startswith("{LANMAN}"):
			return password.replace("{LANMAN}", "{LANMAN}!")
	return password
