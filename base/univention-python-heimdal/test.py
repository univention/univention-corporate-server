#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# Copyright 2003-2019 Univention GmbH
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

import sys
import unittest
from tempfile import NamedTemporaryFile
from base64 import b64decode

import heimdal

PY2 = sys.version_info[:2] < (3, 0)

TYPES = {
	'des-cbc-crc': heimdal.ETYPE_DES_CBC_CRC,
	'des-cbc-md4': heimdal.ETYPE_DES_CBC_MD4,
	'des-cbc-md5': heimdal.ETYPE_DES_CBC_MD5,
	'des': heimdal.ETYPE_DES_CBC_MD5,
	'des-cbc-raw': heimdal.ETYPE_DES_CBC_RAW,
	'des3-cbc-raw': heimdal.ETYPE_DES3_CBC_RAW,
	'des3-cbc-sha1': heimdal.ETYPE_DES3_CBC_SHA1,
	'des3-cbc-sha1-kd': heimdal.ETYPE_DES3_CBC_SHA1,
	'des3-hmac-sha1': heimdal.ETYPE_DES3_CBC_SHA1,
	'aes128-cts-hmac-sha1-96': heimdal.ETYPE_AES128_CTS_HMAC_SHA1_96,
	'aes128-cts': heimdal.ETYPE_AES128_CTS_HMAC_SHA1_96,
	'aes128-sha1': heimdal.ETYPE_AES128_CTS_HMAC_SHA1_96,
	'aes256-cts-hmac-sha1-96': heimdal.ETYPE_AES256_CTS_HMAC_SHA1_96,
	'aes256-cts': heimdal.ETYPE_AES256_CTS_HMAC_SHA1_96,
	'aes256-sha1': heimdal.ETYPE_AES256_CTS_HMAC_SHA1_96,
	'aes128-cts-hmac-sha256-128': heimdal.ETYPE_AES128_CTS_HMAC_SHA256_128,
	'aes128-sha2': heimdal.ETYPE_AES128_CTS_HMAC_SHA256_128,
	'aes256-cts-hmac-sha384-192': heimdal.ETYPE_AES256_CTS_HMAC_SHA384_192,
	'aes256-sha2': heimdal.ETYPE_AES256_CTS_HMAC_SHA384_192,
	'arcfour-hmac': heimdal.ETYPE_ARCFOUR_HMAC_MD5,
	'rc4-hmac': heimdal.ETYPE_ARCFOUR_HMAC_MD5,
	'arcfour-hmac-md5': heimdal.ETYPE_ARCFOUR_HMAC_MD5,
	'arcfour-hmac-exp': heimdal.ETYPE_ARCFOUR_HMAC_MD5_56,
	'rc4-hmac-exp': heimdal.ETYPE_ARCFOUR_HMAC_MD5_56,
	'arcfour-hmac-md5-exp': heimdal.ETYPE_ARCFOUR_HMAC_MD5_56,
	'camellia128-cts-cmac': heimdal.ETYPE_CAMELLIA128_CTS_CMAC,
	'camellia128-cts': heimdal.ETYPE_CAMELLIA128_CTS_CMAC,
	'camellia256-cts-cmac': heimdal.ETYPE_CAMELLIA256_CTS_CMAC,
	'camellia256-cts': heimdal.ETYPE_CAMELLIA256_CTS_CMAC,
}
REALM = 'EXAMPLE.COM'
USERNAME = 'Administrator'
USER = '{}@{}'.format(USERNAME, REALM)
ENCSTR = "des-cbc-md5"
ENCINT = 3
KVNO = 0
PASSWORD = 'univention'


@unittest.skipUnless(hasattr(sys, 'gettotalrefcount'), 'requires Python debug build')
class TestRefcount(unittest.TestCase):
	def test_context(self):
		before = middle = after = 0
		before = sys.gettotalrefcount()
		context = heimdal.context()
		middle = sys.gettotalrefcount()
		del context
		after = sys.gettotalrefcount()

		self.assertGreater(middle, before)
		self.assertLess(after, middle)
		self.assertEqual(before, after)

	def test_principal(self):
		context = heimdal.context()

		before = middle = after = 0
		before = sys.gettotalrefcount()
		principal = heimdal.principal(context, USER)
		middle = sys.gettotalrefcount()
		del principal
		after = sys.gettotalrefcount()

		self.assertGreater(middle, before)
		self.assertLess(after, middle)
		self.assertEqual(before, after)

	@unittest.skip('Requires working kerberos services')
	def test_creds(self):
		context = heimdal.context()
		principal = heimdal.principal(context, USER)
		tkt_service = ""

		before = middle = after = 0
		before = sys.gettotalrefcount()
		creds = heimdal.creds(context, principal, PASSWORD, tkt_service)
		middle = sys.gettotalrefcount()
		del creds
		after = sys.gettotalrefcount()

		self.assertGreater(middle, before)
		self.assertLess(after, middle)
		self.assertEqual(before, after)

	def test_keytab(self):
		context = heimdal.context()

		before = middle = after = 0
		with NamedTemporaryFile() as tmpfile:
			before = sys.gettotalrefcount()
			keytab = heimdal.keytab(context, tmpfile.name)
			middle = sys.gettotalrefcount()
			del keytab
			after = sys.gettotalrefcount()

		self.assertGreater(middle, before)
		self.assertLess(after, middle)
		self.assertEqual(before, after)

	def test_salt(self):
		context = heimdal.context()
		principal = heimdal.principal(context, USER)

		before = middle = after = 0
		before = sys.gettotalrefcount()
		salt = heimdal.salt(context, principal)
		middle = sys.gettotalrefcount()
		del salt
		after = sys.gettotalrefcount()

		self.assertGreater(middle, before)
		self.assertLess(after, middle)
		self.assertEqual(before, after)

	def test_enctype(self):
		context = heimdal.context()

		before = middle = after = 0
		before = sys.gettotalrefcount()
		enctype = heimdal.enctype(context, ENCSTR)
		middle = sys.gettotalrefcount()
		del enctype
		after = sys.gettotalrefcount()

		self.assertGreater(middle, before)
		self.assertLess(after, middle)
		self.assertEqual(before, after)

	def test_keyblock(self):
		context = heimdal.context()

		before = middle = after = 0
		before = sys.gettotalrefcount()
		keyblock = heimdal.keyblock_raw(context, ENCINT, TestKeyblock.VALUE)
		middle = sys.gettotalrefcount()
		del keyblock
		after = sys.gettotalrefcount()

		self.assertGreater(middle, before)
		self.assertLess(after, middle)
		self.assertEqual(before, after)

	def test_exception(self):
		before = middle = after = 0

		def inner():
			try:
				raise heimdal.KRB5KDC_ERR_NONE()
			except heimdal.KRB5KDC_ERR_NONE as ex:
				middle = sys.gettotalrefcount()
				del ex

			if PY2:
				# Py2 keeps a reference for the last exception for re-raising
				# <https://cosmicpercolator.com/2016/01/13/exception-leaks-in-python-2-and-3/>
				sys.exc_clear()

			return middle

		before = sys.gettotalrefcount()
		middle = inner()
		after = sys.gettotalrefcount()

		self.assertGreater(middle, before)
		self.assertLess(after, middle)
		self.assertEqual(before, after)


class TestContext(unittest.TestCase):
	def setUp(self):
		self.context = heimdal.context()

	def test_get_permitted_enctypes(self):
		for typ in self.context.get_permitted_enctypes():
			self.assertEqual(typ.toint(), TYPES[str(typ)])

	def test_dir(self):
		self.assertLessEqual({'get_permitted_enctypes'}, set(dir(self.context)))


class TestPrincipal(unittest.TestCase):
	def setUp(self):
		context = heimdal.context()
		self.principal = heimdal.principal(context, USER)

	def test_type(self):
		with self.assertRaises(TypeError):
			heimdal.principal(None, USER)
		with self.assertRaises(TypeError):
			heimdal.principal("", USER)
		with self.assertRaises(TypeError):
			heimdal.principal(object(), USER)

	def test_principal(self):
		self.assertEqual(USER, str(self.principal))

	def test_realm(self):
		self.assertEqual(REALM, self.principal.realm())

	def test_dir(self):
		self.assertLessEqual({'realm'}, set(dir(self.principal)))


@unittest.skip('Requires working kerberos services')
class TestCreds(unittest.TestCase):
	def setUp(self):
		context = heimdal.context()
		principal = heimdal.principal(context, USER)
		tkt_service = ""
		self.creds = heimdal.creds(self.context, principal, PASSWORD, tkt_service)

	def test_parse(self):
		(enctype, kvno, name) = self.creds.parse()
		self.assertIn(enctype, TYPES)
		self.assertInstance(kvno, int)
		self.assertEqual(name, 'krbtgt/{0}@{0}'.format(REALM))

	@unittest.skip('WIP')
	def test_change_password(self):
		self.creds.change_password(PASSWORD)

	def test_dir(self):
		self.assertEqual({'parse', 'change_password'}, set(dir(self.creds)))


class TestKeytab(unittest.TestCase):
	def setUp(self):
		self.context = heimdal.context()

	def test_keytab_missing(self):
		with NamedTemporaryFile() as tmpfile:
			keytab = heimdal.keytab(self.context, tmpfile.name)
		with self.assertRaises(IOError):
			keytab.list()

	def test_keytab_empty(self):
		with NamedTemporaryFile() as tmpfile:
			keytab = heimdal.keytab(self.context, tmpfile.name)
			with self.assertRaises(heimdal.Krb5Error):
				keytab.list()

	def test_keytab_add(self):
		with NamedTemporaryFile() as tmpfile:
			keytab = heimdal.keytab(self.context, tmpfile.name)
			salt_flag = 0
			random_flag = 0
			keytab.add(USER, KVNO, ENCSTR, PASSWORD, salt_flag, random_flag)
			((kvno, enctype, principal, timestamp, keyblock),) = keytab.list()
			self.assertEqual(KVNO, kvno)
			self.assertEqual(ENCSTR, enctype)
			self.assertEqual(USER, principal)
			self.assertGreater(timestamp, 0)
			self.assertNotEqual(keyblock, "")

	def test_keytab_remove_missing(self):
		with NamedTemporaryFile() as tmpfile:
			keytab = heimdal.keytab(self.context, tmpfile.name)
			with self.assertRaises(heimdal.Krb5Error) as ex:
				keytab.remove(USER, KVNO, ENCSTR)

			self.assertEqual(-1765328203, ex.exception.code)  # #define KRB5_KT_NOTFOUND

	def test_keytab_remove_existing(self):
		with NamedTemporaryFile() as tmpfile:
			keytab = heimdal.keytab(self.context, tmpfile.name)
			salt_flag = 0
			random_flag = 0
			keytab.add(USER, KVNO, ENCSTR, PASSWORD, salt_flag, random_flag)
			keytab.remove(USER, KVNO, ENCSTR)

	def test_dir(self):
		with NamedTemporaryFile() as tmpfile:
			keytab = heimdal.keytab(self.context, tmpfile.name)
			self.assertLessEqual({'add', 'list', 'remove'}, set(dir(keytab)))


class TestSalt(unittest.TestCase):
	VALUE = '{}{}'.format(REALM, USERNAME)

	def setUp(self):
		self.context = heimdal.context()

	def test_salt(self):
		principal = heimdal.principal(self.context, USER)
		salt = heimdal.salt(self.context, principal)
		self.assertEqual(self.VALUE, salt.saltvalue())

	def test_salt_raw(self):
		salt = heimdal.salt_raw(self.context, self.VALUE)
		self.assertEqual(self.VALUE, salt.saltvalue())

	def test_dir(self):
		salt = heimdal.salt_raw(self.context, self.VALUE)
		self.assertLessEqual({'saltvalue'}, set(dir(salt)))


class TestEnctype(unittest.TestCase):
	def setUp(self):
		context = heimdal.context()
		self.enctype = heimdal.enctype(context, ENCSTR)

	def test_type(self):
		with self.assertRaises(TypeError):
			heimdal.enctype(None, ENCSTR)
		with self.assertRaises(TypeError):
			heimdal.enctype("", ENCSTR)
		with self.assertRaises(TypeError):
			heimdal.enctype(object(), ENCSTR)

	def test_enctype(self):
		self.assertEqual(ENCINT, self.enctype.toint())

	def test_dir(self):
		self.assertLessEqual({'toint'}, set(dir(self.enctype)))


class TestKeyblock(unittest.TestCase):
	VALUE = b64decode('g6ihvI/qdqE=')

	def setUp(self):
		self.context = heimdal.context()
		self.enctype = heimdal.enctype(self.context, ENCSTR)
		self.principal = heimdal.principal(self.context, USER)

	def test_keyblock_principal(self):
		keyblock = heimdal.keyblock(self.context, self.enctype, PASSWORD, self.principal)
		self.assertEqual(ENCSTR, str(keyblock.keytype()))
		self.assertEqual(self.VALUE, keyblock.keyvalue())

	def test_keyblock_salt(self):
		salt = heimdal.salt(self.context, self.principal)
		keyblock = heimdal.keyblock(self.context, self.enctype, PASSWORD, salt)
		self.assertEqual(ENCSTR, str(keyblock.keytype()))
		self.assertEqual(self.VALUE, keyblock.keyvalue())

	def test_keyblock_raw(self):
		keyblock = heimdal.keyblock_raw(self.context, ENCINT, self.VALUE)
		self.assertEqual(ENCSTR, str(keyblock.keytype()))
		self.assertEqual(self.VALUE, keyblock.keyvalue())

	def test_dir(self):
		keyblock = heimdal.keyblock_raw(self.context, ENCINT, self.VALUE)
		self.assertLessEqual({'keytype', 'keyvalue'}, set(dir(keyblock)))


class TestCcache(unittest.TestCase):
	def setUp(self):
		self.context = heimdal.context()
		self.principal = heimdal.principal(self.context, USER)
		self.ccache = heimdal.ccache(self.context)

	def test_list(self):
		with self.assertRaises(IOError):
			self.ccache.list()

	def test_init(self):
		self.ccache.initialize(self.principal)
		self.assertEqual(self.ccache.list(), [])
		self.ccache.destroy()
		self.ccache.destroy()

	def test_use_after_destroy(self):
		self.ccache.initialize(self.principal)
		self.ccache.destroy()
		with self.assertRaises(IOError):
			self.ccache.list()

	@unittest.skip('WIP')
	@unittest.skip('Requires working kerberos services')
	def test_store_cred(self):
		self.ccache.initialize(self.principal)
		tkt_service = ""
		creds = heimdal.creds(self.context, self.principal, PASSWORD, tkt_service)
		self.ccache.store_cred(creds)


class TestASN1(unittest.TestCase):
	VALUE = b64decode('DvtFDa7V3K0=')
	SALT = '{}{}'.format('PHAHN.DEV', USERNAME)
	ASN1 = b64decode('MDihEzARoAMCAQOhCgQIDvtFDa7V3K2iITAfoAMCAQOhGAQWUEhBSE4uREVWQWRtaW5pc3RyYXRvcg==')

	def test_asn1_decode_key(self):
		(keyblock, salt, kvno) = heimdal.asn1_decode_key(self.ASN1)
		self.assertEqual(ENCSTR, str(keyblock.keytype()))
		self.assertEqual(self.VALUE, keyblock.keyvalue())
		self.assertEqual(self.SALT, salt.saltvalue())
		self.assertEqual(KVNO, kvno)

	def test_asn1_decode_key_with_context(self):
		context = heimdal.context()
		(keyblock, salt, kvno) = heimdal.asn1_decode_key(self.ASN1, context)
		self.assertEqual(ENCSTR, str(keyblock.keytype()))
		self.assertEqual(self.VALUE, keyblock.keyvalue())
		self.assertEqual(self.SALT, salt.saltvalue())
		self.assertEqual(KVNO, kvno)

	def test_asn1_encode_key(self):
		context = heimdal.context()
		keyblock = heimdal.keyblock_raw(context, ENCINT, self.VALUE)
		salt = heimdal.salt_raw(context, self.SALT)
		asn1 = heimdal.asn1_encode_key(keyblock, salt, KVNO)
		self.assertEqual(self.ASN1, asn1)

	def test_asn1_encode_key_without_salt(self):
		context = heimdal.context()
		keyblock = heimdal.keyblock_raw(context, ENCINT, self.VALUE)
		asn1 = heimdal.asn1_encode_key(keyblock, None, KVNO)
		self.assertIsNotNone(asn1)

	def test_asn1_encode_key_invalid_salt(self):
		context = heimdal.context()
		keyblock = heimdal.keyblock_raw(context, ENCINT, self.VALUE)
		with self.assertRaises(TypeError):
			heimdal.asn1_encode_key(keyblock, 0, KVNO)


class TestException(unittest.TestCase):
	KRB5KDC_ERR_NONE = -1765328384

	def test_KRB5KDC_ERR_NONE(self):
		with self.assertRaises(heimdal.KRB5KDC_ERR_NONE) as cm:
			raise heimdal.KRB5KDC_ERR_NONE()
		self.assertEqual(cm.exception.code, self.KRB5KDC_ERR_NONE)

	def test_exception(self):
		with self.assertRaises(heimdal.Krb5Error) as cm:
			heimdal.asn1_decode_key("")
		self.assertIsNone(cm.exception.code)


if __name__ == '__main__':
	unittest.main()
