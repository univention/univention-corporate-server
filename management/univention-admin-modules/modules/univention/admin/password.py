# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  password encryption methods
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os, heimdal, codecs, types, string, sys

def crypt(password):
	"""return crypt hash"""

	valid = ['.', '/', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
		'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v',
		'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
		'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
		'U', 'V', 'W', 'X', 'Y', 'Z', '0', '1', '2', '3', '4', '5',
		'6', '7', '8', '9' ]
	salt = ''
	urandom = open("/dev/urandom", "r")
	for i in range(0,8):
		o = urandom.read(1)
		salt = salt + valid[(ord(o) % 64)]

	urandom.close()

	import crypt
	return crypt.crypt(password.encode('utf-8'), '$1$%s$' % salt)

def ntlm(password):
	"""return tuple with NT and LanMan hash"""

	p_to, p_from = os.popen2('/usr/sbin/univention-smbencrypt')

	p_to.write( password.encode( 'utf-8' ) + '\n' )
	p_to.close()

	r = p_from.read()[:-1]
	r = r.split(':')

	return (r[1],r[0])

def krb5_asn1(principal, password, context=None):
	list=[]
	if type(principal) == types.UnicodeType:
		principal = str( principal )
	if type(password) == types.UnicodeType:
		password = str( password )
	if not context:
		context = heimdal.context()
	for etype in context.get_default_in_tkt_etypes():
		keyblock = heimdal.keyblock(context, etype, password, heimdal.principal(context, principal))
		list.append(heimdal.asn1_encode_key(keyblock, None, 0))
	return list
