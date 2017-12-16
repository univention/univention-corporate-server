# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin policy for the share userquota
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


class shareUserQuotaFixedAttributes(univention.admin.syntax.select):
	name = 'shareUserQuotaFixedAttributes'
	choices = [
		('univentionQuotaSoftLimitSpace', _('Soft limit')),
		('univentionQuotaHardLimitSpace', _('Hard limit')),
		('univentionQuotaSoftLimitInodes', _('Soft limit (Files)')),
		('univentionQuotaHardLimitInodes', _('Hard limit (Files)')),
		('univentionQuotaReapplyEveryLogin', _('Reapply settings on every login'))
	]


module = 'policies/share_userquota'
operations = ['add', 'edit', 'remove', 'search']

policy_oc = 'univentionPolicyShareUserQuota'
policy_apply_to = ["shares/share"]
policy_position_dn_prefix = "cn=userquota,cn=shares"

childs = 0
short_description = _('Policy: User quota')
policy_short_description = _('User quota')
long_description = _('Default quota for each user on a share')
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionPolicy', 'univentionPolicyShareUserQuota'],
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
	'softLimitSpace': univention.admin.property(
		short_description=_('Soft limit'),
		long_description=_('Soft limit. If exceeded users can be warned. Values may be entered with one of the following units as postfix: B (default), kB, MB, GB'),
		syntax=univention.admin.syntax.filesize,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'hardLimitSpace': univention.admin.property(
		short_description=_('Hard limit'),
		long_description=_('Hard limit. Can not be exceeded. Values may be entered with one of the following units as postfix: B (default), kB, MB, GB'),
		syntax=univention.admin.syntax.filesize,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'softLimitInodes': univention.admin.property(
		short_description=_('Soft limit (Files)'),
		long_description=_('Soft limit. If exceeded users can be warned.'),
		syntax=univention.admin.syntax.integer,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'hardLimitInodes': univention.admin.property(
		short_description=_('Hard limit (Files)'),
		long_description=_('Hard limit. Can not be exceeded.'),
		syntax=univention.admin.syntax.integer,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'reapplyeverylogin': univention.admin.property(
		short_description=_('Reapply settings on every login'),
		long_description=_('Reapply the mountpoint specific user quota policies on each user login. If not set, the initially configured quota settings will not be overwritten.'),
		syntax=univention.admin.syntax.TrueFalseUp,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False,
		default="FALSE"
	),

}
property_descriptions.update(dict([
	requiredObjectClassesProperty(),
	prohibitedObjectClassesProperty(),
	fixedAttributesProperty(syntax=shareUserQuotaFixedAttributes),
	emptyAttributesProperty(syntax=shareUserQuotaFixedAttributes),
	ldapFilterProperty(),
]))

layout = [
	Tab(_('General'), _('Quota'), layout=[
		Group(_('General user quota settings'), layout=[
			'name',
			['softLimitSpace', 'hardLimitSpace'],
			['softLimitInodes', 'hardLimitInodes'],
			['reapplyeverylogin']
		]),
	]),
	policy_object_tab()
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('hardLimitSpace', 'univentionQuotaHardLimitSpace', None, univention.admin.mapping.ListToString)
mapping.register('softLimitSpace', 'univentionQuotaSoftLimitSpace', None, univention.admin.mapping.ListToString)
mapping.register('hardLimitInodes', 'univentionQuotaHardLimitInodes', None, univention.admin.mapping.ListToString)
mapping.register('softLimitInodes', 'univentionQuotaSoftLimitInodes', None, univention.admin.mapping.ListToString)
mapping.register('reapplyeverylogin', 'univentionQuotaReapplyEveryLogin', None, univention.admin.mapping.ListToString)
register_policy_mapping(mapping)


class object(univention.admin.handlers.simplePolicy):
	module = module


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0):

	filter = univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionPolicyShareUserQuota')
	])

	if filter_s:
		filter_p = univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	return object.lookup(co, lo, filter, base, superordinate, scope, unique, required, timeout, sizelimit)


def identify(dn, attr, canonical=0):
	return 'univentionPolicyShareUserQuota' in attr.get('objectClass', [])
