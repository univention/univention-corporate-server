# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin policy for the desktop settings
#
# Copyright 2004-2017 Univention GmbH
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

from univention.admin.layout import Tab, Group
import univention.admin.syntax
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

import univention.debug

from univention.admin.policy import (
	register_policy_mapping, policy_object_tab,
	requiredObjectClassesProperty, prohibitedObjectClassesProperty,
	fixedAttributesProperty, emptyAttributesProperty, ldapFilterProperty
)


translation = univention.admin.localization.translation('univention.admin.handlers.policies')
_ = translation.translate


class desktopFixedAttributes(univention.admin.syntax.select):
	name = 'desktopFixedAttributes'
	choices = [
		(('univentionDesktopLanguage'), _('Desktop language')),
		(('univentionDesktopProfile'), _('Desktop profile'))
	]


module = 'policies/desktop'
operations = ['add', 'edit', 'remove', 'search']

policy_oc = 'univentionPolicyDesktop'
policy_apply_to = ["users/user"]
policy_position_dn_prefix = "cn=desktop"
childs = 0
short_description = _('Policy: Desktop')
policy_short_description = _('Desktop settings')
long_description = ''
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionPolicy', 'univentionPolicyDesktop'],
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description='',
		syntax=univention.admin.syntax.policyName,
		multivalue=False,
		include_in_default_search=True,
		options=[],
		required=True,
		may_change=False,
		identifies=True,
	),
	'language': univention.admin.property(
		short_description=_('Desktop language'),
		long_description='',
		syntax=univention.admin.syntax.language,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'profile': univention.admin.property(
		short_description=_('Desktop profile'),
		long_description='',
		syntax=univention.admin.syntax.KDE_Profile,
		multivalue=True,
		include_in_default_search=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'logonScripts': univention.admin.property(
		short_description=_('Logon scripts'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'logoutScripts': univention.admin.property(
		short_description=_('Logout scripts'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),

}
property_descriptions.update(dict([
	requiredObjectClassesProperty(),
	prohibitedObjectClassesProperty(),
	fixedAttributesProperty(syntax=desktopFixedAttributes),
	emptyAttributesProperty(syntax=desktopFixedAttributes),
	ldapFilterProperty(),
]))

layout = [
	Tab(_('General'), _('Desktop settings'), layout=[
		Group(_('General desktop settings'), layout=[
			'name',
			'language',
			'profile',
			['logonScripts', "logoutScripts"],
		]),
	]),
	policy_object_tab(),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('language', 'univentionDesktopLanguage', None, univention.admin.mapping.ListToString)
mapping.register('profile', 'univentionDesktopProfile')
mapping.register('logonScripts', 'univentionDesktopLogonScripts')
mapping.register('logoutScripts', 'univentionDesktopLogoutScripts')
register_policy_mapping(mapping)


class object(univention.admin.handlers.simplePolicy):
	module = module


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0):

	filter = univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionPolicyDesktop')
	])

	if filter_s:
		filter_p = univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	return object.lookup(co, lo, filter, base, superordinate, scope, unique, required, timeout, sizelimit)


def identify(dn, attr, canonical=0):
	return 'univentionPolicyDesktop' in attr.get('objectClass', [])
