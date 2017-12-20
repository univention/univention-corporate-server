# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the user objects
#
# Copyright 2017 Univention GmbH
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

from __future__ import absolute_import

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

translation = univention.admin.localization.translation('univention.admin.handlers.users')
_ = translation.translate

module = 'users/all'
childmodules = ['users/user', 'users/ldap', 'users/self']

childs = False
short_description = _('User')
long_description = ''
operations = ['search']
virtual = True
options = {}
property_descriptions = {
	'username': univention.admin.property(
		short_description=_('Name'),
		long_description='',
		syntax=univention.admin.syntax.hostName,
		multivalue=False,
		include_in_default_search=True,
		options=[],
		required=True,
		may_change=True,
		identifies=True
	),
}

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'uid', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0):
	res = []
	for child in childmodules:
		user = univention.admin.modules.get(child)
		res.extend(user.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit))
	return res


def identify(dn, attr, canonical=0):
	pass
