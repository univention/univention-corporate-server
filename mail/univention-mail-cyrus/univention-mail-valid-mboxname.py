#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Mail Cyrus
#  check for invalid chars in imap folder names
#
# Copyright (C) 2011-2015 Univention GmbH
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

# this is allowed in cyrus 2.4
GOODCHARS = " +,-.0123456789:=@ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz~"

# this is the delimiter and was never allowd
GOODCHARS += "/&"

import imaplib
import sys
import os
import types
import re

list_response_pattern = re.compile(r'\((?P<flags>.*?)\) "(?P<delimiter>.*)" (?P<name>.*)')
host = "localhost"
user = "cyrus"
password = ""

# get password
if os.path.isfile("/etc/cyrus.secret"):
	password = open('/etc/cyrus.secret').read()
	if password[-1] == '\n':
		password = password[0:-1]

if not password:
	sys.stderr.write("could not find /etc/cyrus.secret for imap login as user cyrus\n")
	sys.exit(1)

# imap login
try:
	imap = imaplib.IMAP4_SSL(host)
except Exception, e:
	sys.stderr.write("imap ssl connect to %s failed\n" % host)
	sys.exit(1)
try:
	imap.login(user, password)
except Exception, e:
	sys.stderr.write("imap login to %s failed\n" % host)
	sys.exit(1)

# get list of mbox's from server
ret, result = imap.list(pattern="*")

# get a list of bad mbox names
badMboxNames = []
for res in result:
	if res:
		if isinstance(res, types.TupleType) and len(res) > 0:
			# ('(\\HasNoChildren) "/" {29}', 'user/admin/test@univention.qa')
			res = '(\\HasNoChildren) "/" "%s"' % res[-1].strip()
		elif isinstance(res, types.StringType):
			# (\HasNoChildren) "/" "user/admin/test folder@univention.qa"
			pass
		else:
			# hmm, not sure what this means, do nothing
			res = ""

	if res:
		m = list_response_pattern.match(res)
		name = ""
		if m and len(m.groups()) > 2:
			flags, delimiter, name = m.groups()
			name = name.strip('"')
	
		if name:
			good = True
			formattedName = ""
			for char in name:
				if not char in GOODCHARS:
					formattedName += "(->)%s(<-)" % char
					good = False
				else:
					formattedName += char
			if not good:
				badMboxNames.append("mbox name: %s (%s)" % (name, formattedName))

if badMboxNames:
	print "The cyrus imap server supports these characters in imap folder names:"
	print GOODCHARS
	print
	print "The following imap folder names with invalid characters were found:"
	for mbox in badMboxNames:
		print "\t" + mbox

	# return 99 to indicate invalid mailbox folder names
	sys.exit(99)

sys.exit(0)
