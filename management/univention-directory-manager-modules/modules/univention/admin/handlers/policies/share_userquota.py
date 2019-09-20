# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin policy for the share userquota
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

from univention.admin.layout import Tab, Group
import univention.admin.syntax
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

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
object_name = _('User quota policy')
object_name_plural = _('User quota policies')
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
		include_in_default_search=True,
		required=True,
		may_change=False,
		identifies=True,
	),
	'softLimitSpace': univention.admin.property(
		short_description=_('Soft limit'),
		long_description=_('Soft limit. If exceeded users can be warned. Values may be entered with one of the following units as postfix: B (default), kB, MB, GB'),
		syntax=univention.admin.syntax.filesize,
	),
	'hardLimitSpace': univention.admin.property(
		short_description=_('Hard limit'),
		long_description=_('Hard limit. Can not be exceeded. Values may be entered with one of the following units as postfix: B (default), kB, MB, GB'),
		syntax=univention.admin.syntax.filesize,
	),
	'softLimitInodes': univention.admin.property(
		short_description=_('Soft limit (Files)'),
		long_description=_('Soft limit. If exceeded users can be warned.'),
		syntax=univention.admin.syntax.integer,
	),
	'hardLimitInodes': univention.admin.property(
		short_description=_('Hard limit (Files)'),
		long_description=_('Hard limit. Can not be exceeded.'),
		syntax=univention.admin.syntax.integer,
	),
	'reapplyeverylogin': univention.admin.property(
		short_description=_('Reapply settings on every login'),
		long_description=_('Reapply the mountpoint specific user quota policies on each user login. If not set, the initially configured quota settings will not be overwritten.'),
		syntax=univention.admin.syntax.TrueFalseUp,
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


lookup = object.lookup
identify = object.identify
