# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for default paths
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
import univention.admin.handlers
import univention.admin.password
import univention.admin.localization

translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate


def plusBase(object, arg):
	return [arg + ',' + object.position.getDomain()]


module = 'settings/default'
superordinate = 'settings/cn'
childs = 0
operations = ['search', 'edit']
short_description = _('Preferences: Default')
long_description = ''
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionDefault'],
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		include_in_default_search=True,
		options=[],
		required=True,
		may_change=False,
		identifies=True,
		default=('univention', [])
	),
	'defaultGroup': univention.admin.property(
		short_description=_('Default Primary Group'),
		long_description='',
		syntax=univention.admin.syntax.GroupDN,
		multivalue=False,
		include_in_default_search=True,
		options=[],
		required=True,
		may_change=True,
		identifies=False,
	),
	'defaultComputerGroup': univention.admin.property(
		short_description=_('Default Computer Group'),
		long_description='',
		syntax=univention.admin.syntax.GroupDN,
		multivalue=False,
		include_in_default_search=True,
		options=[],
		required=True,
		may_change=True,
		identifies=False,
	),
	'defaultDomainControllerGroup': univention.admin.property(
		short_description=_('Default DC Slave Computer Group'),
		long_description='',
		syntax=univention.admin.syntax.GroupDN,
		multivalue=False,
		include_in_default_search=True,
		options=[],
		required=True,
		may_change=True,
		identifies=False,
	),
	'defaultDomainControllerMBGroup': univention.admin.property(
		short_description=_('Default DC Master & Backup Server Group'),
		long_description='',
		syntax=univention.admin.syntax.GroupDN,
		multivalue=False,
		include_in_default_search=True,
		options=[],
		required=True,
		may_change=True,
		identifies=False,
	),
	'defaultMemberServerGroup': univention.admin.property(
		short_description=_('Default Member Server Group'),
		long_description='',
		syntax=univention.admin.syntax.GroupDN,
		multivalue=False,
		include_in_default_search=True,
		options=[],
		required=True,
		may_change=True,
		identifies=False,
	),
	'defaultClientGroup': univention.admin.property(
		short_description=_('Default Client Computer Group'),
		long_description='',
		syntax=univention.admin.syntax.GroupDN,
		multivalue=False,
		include_in_default_search=True,
		options=[],
		required=True,
		may_change=True,
		identifies=False,
	),
	'defaultKdeProfiles': univention.admin.property(
		short_description=_('Default KDE Profiles'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False,
	),
}

layout = [
	Tab(_('General'), _('Basic values'), layout=[
		Group(_('Default settings description'), layout=[
			"name"
		]),
	]),
	Tab(_('Primary Groups'), _('Primary Groups'), layout=[
		Group(_('Primary Groups'), layout=[
			"defaultGroup",
			"defaultComputerGroup",
			"defaultDomainControllerMBGroup",
			"defaultDomainControllerGroup",
			"defaultMemberServerGroup",
			"defaultClientGroup"
		]),
	]),
	Tab(_('KDE Profiles'), _('KDE Profiles'), layout=[
		Group(_('KDE Profiles'), layout=[
			"defaultKdeProfiles",
		]),
	]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('defaultGroup', 'univentionDefaultGroup', None, univention.admin.mapping.ListToString)
mapping.register('defaultComputerGroup', 'univentionDefaultComputerGroup', None, univention.admin.mapping.ListToString)
mapping.register('defaultDomainControllerMBGroup', 'univentionDefaultDomainControllerMasterGroup', None, univention.admin.mapping.ListToString)
mapping.register('defaultDomainControllerGroup', 'univentionDefaultDomainControllerGroup', None, univention.admin.mapping.ListToString)
mapping.register('defaultMemberServerGroup', 'univentionDefaultMemberserverGroup', None, univention.admin.mapping.ListToString)
mapping.register('defaultClientGroup', 'univentionDefaultClientGroup', None, univention.admin.mapping.ListToString)
mapping.register('defaultKdeProfiles', 'univentionDefaultKdeProfiles')


class object(univention.admin.handlers.simpleLdap):
	module = module

	def _ldap_dn(self):
		return 'cn=default containers,cn=univention,%s' % (self.position.getDomain())


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0):

	filter = univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionDefault')
	])

	if filter_s:
		filter_p = univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res = []
	for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit):
		res.append(object(co, lo, None, dn, attributes=attrs))
	return res


def identify(dn, attr, canonical=0):

	return 'univentionDefault' in attr.get('objectClass', [])
