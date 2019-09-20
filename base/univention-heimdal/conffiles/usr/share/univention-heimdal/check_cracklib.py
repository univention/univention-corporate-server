#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# @%@UCRWARNING=# @%@
# Copyright 2004-2019 Univention GmbH
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
import univention.password


def main():
	params = {}
	end = False
	while not end:
		line = sys.stdin.readline()
		line = line[:-1]
		if line == 'end':
			end = True
			continue

		try:
			key, val = line.split(': ', 1)
		except:
			print 'key value pair is not correct: %s' % line
			sys.exit(1)
		params[key] = val

	if 'new-password' not in params:
		print 'missing password'
		sys.exit(1)

	if 'principal' in params:
		pwdCheck = univention.password.Check(None, params['principal'])
		try:
			pwdCheck.check(params['new-password'])
			print 'APPROVED'
		except ValueError as e:
			print str(e)


try:
	main()
except:
	import traceback
	print traceback.format_exc().replace('\n', ' ')  # heimdal-kdc / kpasswd only displays the first line as error message.
	sys.exit(1)
