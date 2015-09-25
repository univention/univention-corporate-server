#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Send a token to a user using a text message service.
#
# Copyright 2015 Univention GmbH
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

#############################################################################
#                                                                           #
# This is meant as an example. Please feel free to copy this file and adapt #
# it to your needs. After testing it, change the UCR variable               #
# self-service/email/cmd to point to your file.                             #
#                                                                           #
# To test your script, run:                                                 #
#                                                                           #
# echo '{"username": "test", "addresses": ["test@example.org"], "server": "localhost", "token": "abcdefgh"}' | /usr/lib/univention-self-service/my_send_sms.py #
#                                                                           #
#############################################################################

#############################################################################
#                                                                           #
# A JSON string must be read from the standard input (stdin). Decoded it    #
# yields the username, the text message gateway that is configured in the   #
# UCR variable 'self-service/sms/server'.                                   #
#                                                                           #
# If the return code is other that 0, it is assumed that it was not         #
# possible to send the token to the user. The token is then deleted from    #
# the database.                                                             #
#                                                                           #
#############################################################################

import sys
import json

try:
	infos = json.loads(sys.stdin.read().rstrip())
except ValueError:
	print "JSON is expected as input."
	sys.exit(1)

print "send_sms.py: received data: %r" % infos
sys.exit(0)
