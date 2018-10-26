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
* Encrypt, decrypt and sign using RSA.
* Create, store and load RSA keys.
"""

import os
import stat
import hashlib
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa, utils
from cryptography.exceptions import InvalidSignature

try:
	from typing import Optional
except ImportError:
	pass


class SimpleRSACryptography(object):
	"""
	Create signature of texts. Create, store and load keys.
	"""
	key_size = 2048

	def __init__(self):  # type: () -> None
		self.private_key = None  # type: rsa.RSAPrivateKey

	def create_keys(self):  # type: () -> None
		"""
		Create private and public keys and store them in
			:py:attr:`self.private_key` and :py:attr:`self.public_key`.

		:return: None
		"""
		self.private_key = rsa.generate_private_key(
			public_exponent=65537,
			key_size=self.key_size,
			backend=default_backend()
		)

	def store_keys(self, key_file, uid, gid, mode=None):  # type: (str, int, int, Optional[int]) -> None
		"""
		Save :py:attr:`self.private_key` in `key_file`. The public key does
		not need to be saved, it can be generated from the secret key.

		Warning: will overwrite an existing file.

		:param str key_file: file to store secret key in
		:param int uid: owner of file
		:param int gid: group of file
		:param int mode: file permissions, 600 if not set
		:return: None
		:raises IOError: if `key_file` cannot be written to
		"""
		assert self.private_key is not None
		assert isinstance(uid, int)
		assert isinstance(gid, int)
		assert isinstance(mode, int) or mode is None

		mode = mode or stat.S_IRUSR | stat.S_IWUSR
		with open(key_file, 'wb') as fp:
			os.fchown(fp.fileno(), uid, gid)
			os.fchmod(fp.fileno(), mode)
			fp.write(self.private_key_as_str)

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
		assert self.private_key is not None
		return self.private_key.private_bytes(
			encoding=serialization.Encoding.PEM,
			format=serialization.PrivateFormat.PKCS8,
			encryption_algorithm=serialization.NoEncryption()
		)

	@property
	def public_key(self):  # type: () -> rsa.RSAPublicKey
		assert self.private_key is not None
		return self.private_key.public_key()

	@property
	def public_key_as_str(self):  # type: () -> str
		return self.public_key.public_bytes(
			encoding=serialization.Encoding.PEM,
			format=serialization.PublicFormat.SubjectPublicKeyInfo
		)

	def encrypt(self, clear_text):  # type: (str) -> str
		"""
		Encrypt `text` with :py:attr:`self.public_key`.

		:param clear_text: the text to encrypt
		:return: the encrypted text (cyphertext)
		:rtype: str
		"""
		return self.public_key.encrypt(
			clear_text,
			padding.OAEP(
				mgf=padding.MGF1(algorithm=hashes.SHA256()),
				algorithm=hashes.SHA256(),
				label=None
			)
		)

	def decrypt(self, cyphertext):  # type: (str) -> str
		"""
		Decrypt `text` with :py:attr:`self.private_key`.

		:param cyphertext: the text to decrypt
		:return: the decrypted text (clear text)
		:rtype: str
		:raises ValueError: if cyphertext
		"""
		assert self.private_key is not None
		return self.private_key.decrypt(
			cyphertext,
			padding.OAEP(
				mgf=padding.MGF1(algorithm=hashes.SHA256()),
				algorithm=hashes.SHA256(),
				label=None
			)
		)

	def sign(self, text):  # type: (str) -> None
		"""
		Create a signature for `text`.

		:param str text: the text to sign
		:return: signed hash of `text`
		:rtype: str
		"""
		assert self.private_key is not None
		hashed_msg = hashlib.sha256(bytes(text)).digest()
		return self.private_key.sign(
			hashed_msg,
			padding.PSS(
				mgf=padding.MGF1(hashes.SHA256()),
				salt_length=padding.PSS.MAX_LENGTH
			),
			utils.Prehashed(hashes.SHA256())
		)

	def verify(self, signature, text):  # type: (str, str) -> bool
		"""
		Verify that `signature` is valid for `text`.

		:param str signature: the signature for `text`
		:param str text: the message that was signed
		:return: True if the signature is correct for the message
		"""
		hashed_msg = hashlib.sha256(bytes(text)).digest()
		try:
			self.public_key.verify(
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
