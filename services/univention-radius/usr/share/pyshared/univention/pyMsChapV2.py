#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention RADIUS 802.1X
#  helper functions for RFC 2759
#
# Copyright (C) 2012-2019 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of the software contained in this package
# as well as the source package itself are made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this package provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use the software under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

import hashlib
import univention.pyDes as pyDes


def md4(data):
	md = hashlib.new('md4')
	md.update(data)
	return md.digest()


def DesEncrypt(data, key):

	def convertKey(key):
		"""
		Converts a 7-bytes key to an 8-bytes key based on an algorithm.
		"""
		assert len(key) == 7, "NTLM convertKey needs 7-byte key"
		bytes = [
			key[0],
			chr(((ord(key[0]) << 7) & 0xFF) | (ord(key[1]) >> 1)),
			chr(((ord(key[1]) << 6) & 0xFF) | (ord(key[2]) >> 2)),
			chr(((ord(key[2]) << 5) & 0xFF) | (ord(key[3]) >> 3)),
			chr(((ord(key[3]) << 4) & 0xFF) | (ord(key[4]) >> 4)),
			chr(((ord(key[4]) << 3) & 0xFF) | (ord(key[5]) >> 5)),
			chr(((ord(key[5]) << 2) & 0xFF) | (ord(key[6]) >> 6)),
			chr((ord(key[6]) << 1) & 0xFF),
		]
		return "".join([setOddParity(b) for b in bytes])

	def setOddParity(byte):
		"""
		Turns one-byte into odd parity. Odd parity means that a number in
		binary has odd number of 1's.
		"""
		assert len(byte) == 1
		parity = 0
		ordbyte = ord(byte)
		for dummy in range(8):
			if (ordbyte & 0x01) != 0:
				parity += 1
			ordbyte >>= 1
		ordbyte = ord(byte)
		if parity % 2 == 0:
			if (ordbyte & 0x01) != 0:
				ordbyte &= 0xFE
			else:
				ordbyte |= 0x01
		return chr(ordbyte)

	return pyDes.des(convertKey(key), pyDes.ECB).encrypt(data)

	# as alternative, this seems to work too, but
	# the package python-passlib has to be installed
	# import passlib.utils.des
	# return passlib.utils.des.des_encrypt_block(key, data)


def GenerateNtResponse(AuthenticatorChallenge, PeerChallenge, UserName, Password):
	Challenge = ChallengeHash(PeerChallenge, AuthenticatorChallenge, UserName)
	PasswordHash = NtPasswordHash(Password)
	Response = ChallengeResponse(Challenge, PasswordHash)
	return Response


def ChallengeHash(PeerChallenge, AuthenticatorChallenge, UserName):
	Challenge = hashlib.sha1(PeerChallenge + AuthenticatorChallenge + UserName).digest()
	return Challenge[:8]


def NtPasswordHash(Password):
	PasswordHash = md4(Password)
	return PasswordHash


def HashNtPasswordHash(PasswordHash):
	PasswordHashHash = md4(PasswordHash)
	return PasswordHashHash


def ChallengeResponse(Challenge, PasswordHash):
	ZPasswordHash = PasswordHash.ljust(21, '\0')
	Response = DesEncrypt(Challenge, ZPasswordHash[0:7])
	Response += DesEncrypt(Challenge, ZPasswordHash[7:14])
	Response += DesEncrypt(Challenge, ZPasswordHash[14:21])
	return Response


def GenerateAuthenticatorResponse(Password, NtResponse, PeerChallenge, AuthenticatorChallenge, UserName):
	Magic1 = '\x4D\x61\x67\x69\x63\x20\x73\x65\x72\x76\x65\x72\x20\x74\x6F\x20\x63\x6C\x69\x65\x6E\x74\x20\x73\x69\x67\x6E\x69\x6E\x67\x20\x63\x6F\x6E\x73\x74\x61\x6E\x74'
	Magic2 = '\x50\x61\x64\x20\x74\x6F\x20\x6D\x61\x6B\x65\x20\x69\x74\x20\x64\x6F\x20\x6D\x6F\x72\x65\x20\x74\x68\x61\x6E\x20\x6F\x6E\x65\x20\x69\x74\x65\x72\x61\x74\x69\x6F\x6E'
	PasswordHash = NtPasswordHash(Password)
	PasswordHashHash = HashNtPasswordHash(PasswordHash)
	Challenge = ChallengeHash(PeerChallenge, AuthenticatorChallenge, UserName)
	Digest = hashlib.sha1(PasswordHashHash + NtResponse + Magic1).digest()
	Digest = hashlib.sha1(Digest + Challenge + Magic2).digest()
	AuthenticatorResponse = 'S=' + Digest.encode('hex').upper()
	return AuthenticatorResponse


def CheckAuthenticatorResponse(Password, NtResponse, PeerChallenge, AuthenticatorChallenge, UserName, ReceivedResponse):
	ResponseOK = False
	MyResponse = GenerateAuthenticatorResponse(Password, NtResponse, PeerChallenge, AuthenticatorChallenge, UserName)
	if (MyResponse == ReceivedResponse):
		ResponseOK = True
	return ResponseOK


def executeTestVectors():
	UserName = '\x55\x73\x65\x72'
	assert u'User'.encode('ascii') == UserName
	Password = '\x63\x00\x6C\x00\x69\x00\x65\x00\x6E\x00\x74\x00\x50\x00\x61\x00\x73\x00\x73\x00'
	assert u'clientPass'.encode('utf-16le') == Password
	AuthenticatorChallenge = '\x5B\x5D\x7C\x7D\x7B\x3F\x2F\x3E\x3C\x2C\x60\x21\x32\x26\x26\x28'
	PeerChallenge = '\x21\x40\x23\x24\x25\x5E\x26\x2A\x28\x29\x5F\x2B\x3A\x33\x7C\x7E'
	Challenge = '\xD0\x2E\x43\x86\xBC\xE9\x12\x26'
	assert ChallengeHash(PeerChallenge, AuthenticatorChallenge, UserName) == Challenge
	PasswordHash = '\x44\xEB\xBA\x8D\x53\x12\xB8\xD6\x11\x47\x44\x11\xF5\x69\x89\xAE'
	assert NtPasswordHash(Password) == PasswordHash
	NtResponse = '\x82\x30\x9E\xCD\x8D\x70\x8B\x5E\xA0\x8F\xAA\x39\x81\xCD\x83\x54\x42\x33\x11\x4A\x3D\x85\xD6\xDF'
	assert NtResponse == GenerateNtResponse(AuthenticatorChallenge, PeerChallenge, UserName, Password)
	PasswordHashHash = '\x41\xC0\x0C\x58\x4B\xD2\xD9\x1C\x40\x17\xA2\xA1\x2F\xA5\x9F\x3F'
	assert HashNtPasswordHash(PasswordHash) == PasswordHashHash
	AuthenticatorResponse = 'S=407A5589115FD0D6209F510FE9C04566932CDA56'
	assert GenerateAuthenticatorResponse(Password, NtResponse, PeerChallenge, AuthenticatorChallenge, UserName) == AuthenticatorResponse

	test_ntlm = [
		# key, data, resp
		('CAA1239D44DA7EDF926BCE39F5C65D0F', '4c29654e436e7844', '1cffa87d8b48ce73a71e3e6c9a9dd80f112d48dfeea8792c'),
		('3b1b47e42e0463276e3ded6cef349f93', 'b019d38bad875c9d', 'e6285df3287c5d194f84df1a94817c7282d09754b6f9e02a'),
		('624aac413795cdc1ff17365faf1ffe89', '6da297169f7aa9c2', '2e17884ea16177e2b751d53b5cc756c3cd57cdfd6e3bf8b9'),
		('3b1b47e42e0463276e3ded6cef349f93', 'eacf7d5a2a6fa7d4', 'd2025bc5d6c201af7472550a677ca9904245a16ebb542a8e'),
		('ae33a32dca8c9821844f740d5b3f4d6c', '677f1c557a5ee96c', '1bb250184772028e54394762ded81de1f608e6f37e7de5b0'),
		('c4ea95cb148df11bf9d7c3611ad6d722', '514246973ea892c1', '497e9072282f5d33529e7359177d42ac9e106600630d3a6d'),
		('cd06ca7c7e10c99b1d33b7485a2ed808', '0123456789abcdef', '25a98c1c31e81847466b29b2df4680f39958fb8c213a9cc6'),
		('ff3750bcc2b22412c2265b23734e0dac', '0123456789abcdef', 'c337cd5cbd44fc9782a667af6d427c6de67c20c2d3e77c56'),
		('04b8e0ba74289cc540826bab1dee63ae', 'ffffff0011223344', 'c951c8b1ddf71b2f8ec0be33f21ad93b7cd5fb2cd6cf51c5'),
		('00563126f04f3875c417f789b00e72d2', '5355f4fc60c8888a', '9681672b365655d0592c3e4009547b9e11bc751b6e97943b'),
	]

	for key, data, resp in test_ntlm:
		assert resp == ChallengeResponse(data.decode('hex'), key.decode('hex')).encode('hex')

	# see https://forge.univention.org/bugzilla/show_bug.cgi?id=38785
	res = ChallengeResponse('5355f4fc60c8888a'.decode('hex'), '00563126f04f3875c417f789b00e72d2'.decode('hex'))
	assert res.encode('hex') == '9681672b365655d0592c3e4009547b9e11bc751b6e97943b'


if __name__ == "__main__":
	executeTestVectors()
