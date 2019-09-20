# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the policies
#
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

from univention.admin.layout import Tab
import univention.admin.filter
import univention.admin.localization

import univention.admin.handlers
import univention.admin.handlers.policies

translation = univention.admin.localization.translation('univention.admin.handlers.policies')
_ = translation.translate


module = 'policies/policy'

childs = 0
short_description = _('Policy')
object_name = _('Policy')
object_name_plural = _('Policies')
long_description = ''
help_link = _('https://docs.software-univention.de/manual-4.4.html#central:policies')
help_text = _('<p>Policies are objects that can be connected with other objects in the directory tree. Connected policies allow to define object properties in a unified manner. Policies that are connected with containers or organizational units are inherited by all objects located below.</p><p>More information can be found in the <a href="https://docs.software-univention.de/manual-4.4.html#central:policies" target="_blank">online documentation for UCS</a>.</p>')
operations = ['search']
childmodules = []
for pol in univention.admin.handlers.policies.policies:
	if hasattr(pol, 'module'):
		childmodules.append(pol.module)
virtual = 1
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description='',
		syntax=univention.admin.syntax.policyName,
		include_in_default_search=True,
		required=True,
		identifies=True
	)
}
layout = [Tab(_('General'), _('Basic settings'), layout=["name"])]

mapping = univention.admin.mapping.mapping()


class object(univention.admin.handlers.simpleLdap):
	module = module


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0):
	res = []
	for pol in univention.admin.handlers.policies.policies:
		r = pol.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)
		res.extend(r)

	return res


def identify(dn, attr, canonical=0):
	pass
