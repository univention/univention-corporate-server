#!/usr/bin/python2.7
#
# Copyright 2011-2019 Univention GmbH
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

'''
Univention Samba 4
This tool overwrites the sambaSID attribute with the attribute univentionSamba4SID
'''

import sys
import optparse
import univention.admin
import univention.admin.uldap
import univention.config_registry

configRegistry = univention.config_registry.ConfigRegistry()
configRegistry.load()

parser = optparse.OptionParser(usage='Usage: %prog (-n|-a)\nReplaces the attribute sambaSID with the attribute univentionSamba4SID for user and groups.')
parser.add_option(
	'-n', '--no-action',
	dest='action', action='store_false',
	help='do not modify the directory, show what would have been done'
)
parser.add_option(
	'-a', '--action',
	dest='action', action='store_true',
	help='do modify the directory'
)
(options, args, ) = parser.parse_args()

if options.action is None:
	print 'Neither --no-action nor --action given!'
	parser.print_help()
	sys.exit(3)
if args:
	print >> sys.stderr, 'Unknown arguments %r!' % (args, )
	parser.print_help()
	sys.exit(3)

try:
	lo, position = univention.admin.uldap.getAdminConnection()
except IOError:
	lo, position = univention.admin.uldap.getMachineConnection()

res = lo.search(filter='univentionSamba4SID=*', attr=['dn', 'sambaSID', 'univentionSamba4SID'])

modify = False
for user in res:
	sambaSID = user[1].get('sambaSID', [])[0]
	univentionSamba4SID = user[1].get('univentionSamba4SID', [])[0]
	if sambaSID == univentionSamba4SID:
		continue

	modify = True
	if not options.action:
		print 'Would set sambaSID to %s for %s' % (univentionSamba4SID, user[0])
		continue
	print 'Set sambaSID to %s for %s' % (univentionSamba4SID, user[0])
	lo.modify(user[0], [('sambaSID', sambaSID, univentionSamba4SID)])

if not modify:
	print 'No object was found.'
