#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Common Python Library
#
# Copyright 2010-2015 Univention GmbH
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


import univention.admin.uldap
import univention.admin.objects
import univention.admin.modules
import univention.admin.handlers.users.user

univention.admin.modules.update()

def lock(userdn, lock_timestamp):
	"""
	Lock user account, used by ppolicy OpenLDAP overlay

	>>> import univention.lib.account
	>>> univention.lib.account.lock('uid=user1,dc=example,dc=com', '20141006192950Z')
	>>>

	"""

	if not lock_timestamp:	## timed unlocking via ppolicy not implemented yet, so block it.
		return

	co = None
	try:
		lo, pos = univention.admin.uldap.getAdminConnection()
	except:
		lo, pos = univention.admin.uldap.getMachineConnection()

	module = univention.admin.modules.get('users/user')

	univention.admin.modules.init(lo, pos, module)

	object = module.object(co, lo, pos, userdn)

	object.open()
	object['locked'] = "all"
	dn = object.modify()

