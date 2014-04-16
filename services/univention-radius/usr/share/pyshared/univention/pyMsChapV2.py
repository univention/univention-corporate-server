#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention RADIUS 802.1X
#  helper functions for RFC 2759
#
# Copyright (C) 2012-2014 Univention GmbH
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
	def expandDesKey(key):
		key = list(key)
		number = 0
		while key:
			number *= 256
			number += ord(key.pop(0))
		key = []
		while number:
			key.append(chr(number % 128*2))
			number /= 128
		return ''.join(reversed(key))
	return pyDes.des(expandDesKey(key), pyDes.ECB).encrypt(data)

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
	Response+= DesEncrypt(Challenge, ZPasswordHash[7:14])
	Response+= DesEncrypt(Challenge, ZPasswordHash[14:21])
	return Response

def GenerateAuthenticatorResponse(Password, NtResponse, PeerChallenge, AuthenticatorChallenge, UserName):
	Magic1 = '\x4D\x61\x67\x69\x63\x20\x73\x65\x72\x76\x65\x72\x20\x74\x6F\x20\x63\x6C\x69\x65\x6E\x74\x20\x73\x69\x67\x6E\x69\x6E\x67\x20\x63\x6F\x6E\x73\x74\x61\x6E\x74'
	Magic2 = '\x50\x61\x64\x20\x74\x6F\x20\x6D\x61\x6B\x65\x20\x69\x74\x20\x64\x6F\x20\x6D\x6F\x72\x65\x20\x74\x68\x61\x6E\x20\x6F\x6E\x65\x20\x69\x74\x65\x72\x61\x74\x69\x6F\x6E'
	PasswordHash = NtPasswordHash(Password)
	PasswordHashHash = HashNtPasswordHash(PasswordHash)
	Challenge = ChallengeHash(PeerChallenge, AuthenticatorChallenge, UserName)
	Digest = hashlib.sha1(PasswordHashHash + NtResponse + Magic1).digest()
	Digest = hashlib.sha1(Digest           + Challenge  + Magic2).digest()
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

if __name__ == "__main__":
	executeTestVectors()
