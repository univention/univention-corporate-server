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

import unittest
from tempfile import NamedTemporaryFile
from base64 import b64decode

import heimdal

TYPES = {
	'des-cbc-crc': 1,
	'des-cbc-md4': 2,
	'des-cbc-md5': 3,
	'des': 3,
	'des-cbc-raw': 4,
	'des3-cbc-raw': 6,
	'des3-cbc-sha1': 16,
	'des3-cbc-sha1-kd': 16,
	'des3-hmac-sha1': 16,
	'aes128-cts-hmac-sha1-96': 17,
	'aes128-cts': 17,
	'aes128-sha1': 17,
	'aes256-cts-hmac-sha1-96': 18,
	'aes256-cts': 18,
	'aes256-sha1': 18,
	'aes128-cts-hmac-sha256-128': 19,
	'aes128-sha2': 19,
	'aes256-cts-hmac-sha384-192': 20,
	'aes256-sha2': 20,
	'arcfour-hmac': 23,
	'rc4-hmac': 23,
	'arcfour-hmac-md5': 23,
	'arcfour-hmac-exp': 24,
	'rc4-hmac-exp': 24,
	'arcfour-hmac-md5-exp': 24,
	'camellia128-cts-cmac': 25,
	'camellia128-cts': 25,
	'camellia256-cts-cmac': 26,
	'camellia256-cts': 26,
}
REALM = 'EXAMPLE.COM'
USERNAME = 'Administrator'
USER = '{}@{}'.format(USERNAME, REALM)
ENCSTR = "des-cbc-md5"
ENCINT = 3
KVNO = 0
PASSWORD = 'univention'


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

	@unittest.skip('Memory corruption')
	def test_keytab_remove_existing(self):
		with NamedTemporaryFile() as tmpfile:
			keytab = heimdal.keytab(self.context, tmpfile.name)
			salt_flag = 0
			random_flag = 0
			keytab.add(USER, KVNO, ENCSTR, PASSWORD, salt_flag, random_flag)
			keytab.remove(USER, KVNO, ENCSTR)

	@unittest.skip('SIGSEGV')
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

	def test_asn1_encode_key(self):
		context = heimdal.context()
		keyblock = heimdal.keyblock_raw(context, ENCINT, self.VALUE)
		salt = heimdal.salt_raw(context, self.SALT)
		asn1 = heimdal.asn1_encode_key(keyblock, salt, KVNO)
		self.assertEqual(self.ASN1, asn1)


if __name__ == '__main__':
	unittest.main()
