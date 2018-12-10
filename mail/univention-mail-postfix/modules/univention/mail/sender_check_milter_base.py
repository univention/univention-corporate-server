#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention mail Postfix
#  check allowed email senders
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
Base class for sender_check applications.
"""

import bz2
import json

from univention.mail.simple_crypt import SimpleAsymmetric, SimpleSymmetric, create_nonce
from univention.mail.milter_base import UCSMilterBase

try:
	from typing import Dict, Optional
except ImportError:
	pass


RSA_KEY_FILE = '/usr/lib/univention-mail-postfix/sender_check.key'
HEADER_SIG = 'X-univention-sender-check-sig'
HEADER_NONCE = 'X-univention-sender-check-nonce'


class SenderCheckMilterBase(UCSMilterBase):
	headers_to_collect = ('date', 'subject', 'message-id', HEADER_SIG.lower(), HEADER_NONCE.lower())
	public_keys = {}  # type: Dict[str, str]

	def __init__(self, opts=0, protos=0):  # type: (Optional[int], Optional[int]) -> None
		super(SenderCheckMilterBase, self).__init__(opts, protos)
		if not self.public_keys:
			self.public_keys.update(self.get_public_keys())
		if self._current_data.get('public_keys') != set(self.public_keys.keys()):
			self._current_data['public_keys'] = set(self.public_keys.keys())
			self.log('Public keys: {}'.format(', '.join(self.public_keys.keys() or ['None'])))
		fqdn = '{}.{}'.format(self.ucr['hostname'], self.ucr['domainname'])
		if fqdn not in self.public_keys:
			raise RuntimeError('Public key of this host ({!r}) not found. Run join script.'.format(fqdn))
		self._nonce = 0
		self.crypto = SimpleAsymmetric()
		self.crypto.load_keys(RSA_KEY_FILE)

	def clear_variables(self):  # type: () -> None
		super(SenderCheckMilterBase, self).clear_variables()
		self._nonce = 0

	@classmethod
	def sig_handler_reload(cls, num, frame):
		"""
		Reload UCR, :py:attr`cls.mail_domains` and :py:attr`cls.public_keys`.
		"""
		super(SenderCheckMilterBase, cls).sig_handler_reload(num, frame)
		cls.public_keys = cls.get_public_keys()
		cls.log('Public keys: {}'.format(', '.join(cls.public_keys.keys() or ['None'])))

	@classmethod
	def get_public_keys(cls):  # type: () -> Dict[str, str]
		lo = cls.get_lo()
		ldap_attr = ['univentionData', 'univentionDataMeta']
		ldap_filter = '(&(objectClass=univentionData)(univentionDataType=mail/signing/RSA_public_key))'
		ldap_base = 'cn=data,cn=univention,{}'.format(cls.get_ucr()['ldap/base'])
		ldap_result = lo.search(filter=ldap_filter, attr=ldap_attr, base=ldap_base)
		res = {}
		for dn, attrs in ldap_result:
			if not attrs.get('univentionData') or not attrs.get('univentionDataMeta'):
				cls.log('settings/data object without data or metadata: dn={!r} attrs={!r}'.format(dn, attrs), 'ERROR')
				continue
			for metadata in attrs['univentionDataMeta']:
				if metadata.startswith('host:'):
					try:
						bz2data = attrs['univentionData'][0]
						pem_str = bz2.decompress(bz2data)
					except (IndexError, ValueError):
						cls.log('Invalid data in {!r}.'.format(dn), 'ERROR')
						continue
					pub_key = SimpleAsymmetric.pem2public_key(pem_str)
					res[metadata[5:]] = pub_key  # strip leading 'host:'
		return res

	@property
	def nonce(self):  # type: () -> int
		"""Generate a (instance-cached) cryptographically secure random number."""
		if not self._nonce:
			self._nonce = create_nonce()
		return self._nonce

	def create_signature_text(self, from_address=None, to=None, date=None, message_id=None):
		# type: (Optional[str], Optional[str], Optional[str], Optional[str]) -> str
		"""
		The signature text for the `X-univention-sender-check-sig` header is
		created from:

		* `From`
		* `To`
		* `Date`
		* `Message-Id`
		* nonce

		The `Subject` is normalized to handle modifications by spam filters.

		A nonce (random int) is added that will also be stored encrypted in a
		separate header (`X-univention-sender-check-nonce`).

		:param str from_address: an email address, envelope-FROM will be used
			if unset
		:param str to: an email address, header-To will be used if unset
		:param str date: a date, header-Date will be used if unset
		:param str message_id: the mails message-id, header-message-id will be
			used if unset
		:return: signature text
		:rtype: str
		"""
		return '|'.join((
			(from_address or self.envelope_from).lower(),
			(to or self.header_data.get('to', '')).lower(),
			date or self.header_data.get('date', ''),
			message_id or self.header_data.get('message-id'),
			str(self.nonce),
		))

	def add_header_nonce(self, nonce):  # type: (str) -> None
		symmetric_key, cyphertext = SimpleSymmetric.encrypt(nonce)
		data = {'cyphertext': cyphertext}
		for host, pub_key in self.public_keys.items():
			data[host] = self.crypto.encrypt(symmetric_key, pub_key).encode('base64').strip()
		msg = json.dumps(data).encode('base64').strip()
		self.addHeader(HEADER_NONCE, msg)

	def decrypt_header_nonce(self, header_text):  # type: (str) -> str
		try:
			header = header_text.decode('base64')
		except ValueError:
			self.log('Invalid data in {}.'.format(HEADER_NONCE), self.queue_id, 'ERROR')
			return ''
		data = json.loads(header)
		try:
			cyphertext = data['cyphertext']
			enc_symmetric_key = data['{}.{}'.format(self.ucr['hostname'], self.ucr['domainname'])].decode('base64')
		except KeyError:
			self.log('Nonce was not encrypted for this host, only for: {!r}.'.format(data.keys()), self.queue_id, 'ERROR')
			return ''
		except ValueError:
			self.log('Invalid data in {}.'.format(HEADER_NONCE), self.queue_id, 'ERROR')
			return ''
		symmetric_key = self.crypto.decrypt(enc_symmetric_key)
		nonce = SimpleSymmetric.decrypt(cyphertext, symmetric_key)
		return nonce

	def remove_header_nonce(self):  # type: () -> None
		self.chgHeader(HEADER_NONCE, val='')

	def add_header_signature(self, text):  # type: (str) -> None
		signature = self.crypto.sign(text)
		sig = signature.encode('base64').strip()
		res = '{}.{};{}'.format(self.ucr['hostname'], self.ucr['domainname'], sig)
		self.addHeader(HEADER_SIG, res)

	def remove_header_signature(self):  # type: () -> None
		self.chgHeader(HEADER_SIG, val='')

	def verify_signature(self, signature, text):  # type: (str, str) -> bool
		host, _sep, signature = signature.partition(';')
		try:
			rsa_pub_key = self.public_keys[host]
		except KeyError:
			self.log('No public key registered for host {!r}.'.format(host), self.queue_id, 'ERROR')
			return False
		try:
			sig = signature.decode('base64')
		except ValueError:
			self.log('Invalid data in {}.'.format(HEADER_SIG), self.queue_id, 'ERROR')
			return False
		return self.crypto.verify(sig, text, rsa_pub_key)
