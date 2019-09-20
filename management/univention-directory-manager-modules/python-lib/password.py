#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Common Python Library
#
# Copyright 2010-2019 Univention GmbH
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

from ldap.filter import filter_format

import univention.admin.uldap
import univention.admin.objects
import univention.admin.modules
import univention.admin.handlers.users.user

univention.admin.modules.update()


def change(username, password):
	"""
	Change the password of the given user

	>>> import univention.lib.password
	>>> univention.lib.password.change('Administrator', 'secret12345')
	>>> univention.lib.password.change('Administrator@DOMAIN.DE', 'secret12345')
	>>>

	"""
	co = None
	try:
		lo, pos = univention.admin.uldap.getAdminConnection()
	except:
		lo, pos = univention.admin.uldap.getMachineConnection()

	module = univention.admin.modules.get('users/user')

	univention.admin.modules.init(lo, pos, module)

	if username.find('@') > 0:  # krb5Principal
		filter = filter_format('krb5PrincipalName=%s', [username])
	else:
		filter = filter_format('uid=%s', [username])
	objects = module.lookup(co, lo, filter, superordinate=None, unique=True, required=True, timeout=-1, sizelimit=0)

	# search was unique and required
	object = objects[0]

	object.open()
	object['password'] = unicode(password)
	object.modify()
