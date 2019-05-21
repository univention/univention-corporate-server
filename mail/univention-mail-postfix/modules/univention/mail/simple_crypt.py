# -*- coding: utf-8 -*-
#
# Copyright 2018 Univention GmbH
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

"""
Asymmetric:

	* Encrypt, decrypt and sign using RSA.
	* Create, store and load RSA private and public keys.

Symmetric:

	* Encrypt and decrypt sign using AES.
	* Create AES keys.
"""

import os
import stat
import codecs
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa, utils
from cryptography.exceptions import InvalidSignature

try:
	from typing import Optional, Tuple
except ImportError:
	pass


class SimpleAsymmetric(object):
	"""
	Asymmetric encryption: Encrypt, decrypt and sign using RSA. Create, store
	and load keys.
	"""
	def __init__(self, key_size=2048):  # type: (int) -> None
		assert isinstance(key_size, int)

		self.private_key = None  # type: rsa.RSAPrivateKey
		self.key_size = key_size

	def create_keys(self):  # type: () -> None
		"""
		Create private and public keys. They will be store in
		:py:attr:`self.private_key` and :py:attr:`self.public_key`.

		:return: None
		"""
		self.private_key = rsa.generate_private_key(
			public_exponent=65537,
			key_size=self.key_size,
			backend=default_backend()
		)

	def store_keys(self, key_file, uid=None, gid=None, mode=None, write_pub=True):
		# type: (str, Optional[int], Optional[int], Optional[int], Optional[bool]) -> None
		"""
		Save :py:attr:`self.private_key` in `key_file` in PEM format. The
		public key does	not need to be saved, as it can be generated from the
		secret key. But	it can be exported if desired.

		Warning: will overwrite existing files.

		:param str key_file: file to store secret key in
		:param int uid: owner of files or if not set current process's real user id
		:param int gid: group of files or if not set current process's read group id
		:param int mode: file permissions or if not set 0o600 (-rw-------)
		:param bool write_pub: whether to write the public key to `key_file[:-3]+'pub'`
		:return: None
		:raises IOError: if `key_file` cannot be written to
		"""
		assert self.private_key is not None, 'No private key: create or load keys first.'
		assert isinstance(uid, int) or uid is None
		assert isinstance(gid, int) or gid is None
		assert isinstance(mode, int) or mode is None

		def _save_write(path, text):
			with open(path, 'wb') as fp:
				os.fchown(fp.fileno(), uid, gid)
				os.fchmod(fp.fileno(), mode)
				fp.write(text)

		uid = uid or os.getuid()
		gid = gid or os.getgid()
		mode = mode or stat.S_IRUSR | stat.S_IWUSR
		_save_write(key_file, self.private_key_as_str)
		if write_pub:
			path = '{}pub'.format(key_file[:-3])
			_save_write(path, self.public_key_as_str)

	def load_keys(self, key_file):  # type: (str) -> None
		"""
		Load private key from `key_file` (public key will be generated from
		it) and store them in :py:attr:`self.private_key` and
		:py:attr:`self.public_key`.

		:param str key_file: file to load secret key from
		:return: None
		:raises IOError: if `key_file` cannot be read from
		"""
		with open(key_file, 'rb') as fp:
			self.private_key = serialization.load_pem_private_key(
				fp.read(),
				password=None,
				backend=default_backend()
			)

	@property
	def private_key_as_str(self):  # type: () -> str
		assert self.private_key is not None, 'No private key: create or load keys first.'
		return self.private_key.private_bytes(
			encoding=serialization.Encoding.PEM,
			format=serialization.PrivateFormat.PKCS8,
			encryption_algorithm=serialization.NoEncryption()
		)

	@property
	def public_key(self):  # type: () -> rsa.RSAPublicKey
		assert self.private_key is not None, 'No private key: create or load keys first.'
		return self.private_key.public_key()

	@property
	def public_key_as_str(self):  # type: () -> str
		return self.public_key.public_bytes(
			encoding=serialization.Encoding.PEM,
			format=serialization.PublicFormat.SubjectPublicKeyInfo
		)

	def encrypt(self, clear_text, public_key=None):  # type: (str, Optional[rsa.RSAPublicKey]) -> str
		"""
		Encrypt `text` with `public_key` or :py:attr:`self.public_key`.

		:param str clear_text: the text to encrypt
		:param str public_key: key used to encrypt `clear_text`, if unset
			:py:attr:`self.public_key` is used
		:return: the encrypted text (cyphertext)
		:rtype: str
		"""
		public_key = public_key or self.public_key
		return public_key.encrypt(
			clear_text,
			padding.OAEP(
				mgf=padding.MGF1(algorithm=hashes.SHA256()),
				algorithm=hashes.SHA256(),
				label=None
			)
		)

	def decrypt(self, cyphertext, private_key=None):  # type: (str, Optional[rsa.RSAPrivateKey]) -> str
		"""
		Decrypt `text` with :py:attr:`self.private_key`.

		:param str cyphertext: the text to decrypt
		:param str private_key: key used to decrypt `cyphertext`, if unset
			:py:attr:`self.private_key` is used
		:return: the decrypted text (clear text)
		:rtype: str
		:raises ValueError: if cyphertext cannot be decrypted
		"""
		private_key = private_key or self.private_key
		assert private_key is not None, 'No private key: create or load keys first.'

		return private_key.decrypt(
			cyphertext,
			padding.OAEP(
				mgf=padding.MGF1(algorithm=hashes.SHA256()),
				algorithm=hashes.SHA256(),
				label=None
			)
		)

	def sign(self, text, private_key=None):  # type: (str, Optional[rsa.RSAPrivateKey]) -> None
		"""
		Create a signature for `text`.

		:param str text: the text to sign
		:param str private_key: key used to sign `text`, if unset
			:py:attr:`self.private_key` is used
		:return: signed hash of `text`
		:rtype: str
		"""
		private_key = private_key or self.private_key
		assert private_key is not None, 'No private key: create or load keys first.'

		hashed_msg = hashlib.sha256(bytes(text)).digest()
		return private_key.sign(
			hashed_msg,
			padding.PSS(
				mgf=padding.MGF1(hashes.SHA256()),
				salt_length=padding.PSS.MAX_LENGTH
			),
			utils.Prehashed(hashes.SHA256())
		)

	def verify(self, signature, text, public_key=None):  # type: (str, str, Optional[rsa.RSAPublicKey]) -> bool
		"""
		Verify that `signature` is valid for `text`.

		:param str signature: the signature for `text`
		:param str text: the message that was signed
		:param str public_key: key used to verify the signature, if unset
			:py:attr:`self.public_key` is used
		:return: True if the signature is correct for the message
		"""
		public_key = public_key or self.public_key
		hashed_msg = hashlib.sha256(bytes(text)).digest()
		try:
			public_key.verify(
				signature,
				hashed_msg,
				padding.PSS(
					mgf=padding.MGF1(hashes.SHA256()),
					salt_length=padding.PSS.MAX_LENGTH
				),
				utils.Prehashed(hashes.SHA256())
			)
			return True
		except InvalidSignature:
			return False

	@staticmethod
	def pem2public_key(pem):  # type: (str) -> rsa.RSAPublicKey
		"""
		Create a RSA public key from a PEM string.

		:param str pem: PEM string
		:return: rsa.RSAPublicKey instance
		:rtype: rsa.RSAPublicKey
		"""
		return serialization.load_pem_public_key(pem, default_backend())


class SimpleSymmetric(object):
	"""
	Symmetric encryption using Fernet (AES [CBC], SHA256).
	"""

	@staticmethod
	def create_key():  # type: () -> str
		"""
		Create a symmetric key.

		:return: the key
		:rtype: str
		"""
		return Fernet.generate_key()

	@classmethod
	def encrypt(cls, text, key=None):  # type: (str, Optional[str]) -> Tuple[str, str]
		"""
		Encrypt a text using the supplied or a fresh key.

		:param str text: clear text to encrypt
		:param str key: use this key or if unset create a fresh one
		:return: tuple: key, cyphertext
		:rtype: tuple(str, str)
		"""
		key = key or cls.create_key()
		fernet = Fernet(key)
		return key, fernet.encrypt(bytes(text))

	@staticmethod
	def decrypt(text, key):  # type: (str, str) -> str
		"""
		Decrypt `text` using `key`.

		:param str text: cyphertext
		:param str key: key to use
		:return: clear text
		:rtype: str
		"""
		fernet = Fernet(key)
		return fernet.decrypt(bytes(text))


def create_nonce():  # type: () -> int
	"""
	Generate a cryptographically secure random number.

	:return: a random integer (from urandom)
	:rtype: int
	"""
	return int(codecs.encode(os.urandom(20), 'hex'), 16)
