# -*- coding: utf-8 -*-
#
# Copyright 2004-2022 Univention GmbH
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

"""
|UDM| module for the client maintenance policies
"""

from univention.admin.layout import Tab, Group
import univention.admin.syntax
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
import univention.admin.cron

import univention.debug as ud

from univention.admin.policy import (
	register_policy_mapping, policy_object_tab,
	requiredObjectClassesProperty, prohibitedObjectClassesProperty,
	fixedAttributesProperty, emptyAttributesProperty, ldapFilterProperty
)


translation = univention.admin.localization.translation('univention.admin.handlers.policies')
_ = translation.translate


class maintenanceFixedAttributes(univention.admin.syntax.select):
	name = 'maintenanceFixedAttributes'
	choices = [
		('univentionCron', _('Maintenance')),
	]


module = 'policies/maintenance'
operations = ['add', 'edit', 'remove', 'search']

policy_oc = 'univentionPolicyInstallationTime'
policy_apply_to = ["computers/domaincontroller_master", "computers/domaincontroller_backup", "computers/domaincontroller_slave", "computers/memberserver"]
policy_position_dn_prefix = "cn=installation,cn=update"

childs = False
short_description = _('Policy: Maintenance')
object_name = _('Maintenance policy')
object_name_plural = _('Maintenance policies')
policy_short_description = _('Maintenance')
long_description = ''
options = {
	'default': univention.admin.option(
		short_description=short_description,
		default=True,
		objectClasses=['top', 'univentionPolicy', 'univentionPolicyInstallationTime'],
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
	'startup': univention.admin.property(
		short_description=_('Perform maintenance after system startup'),
		long_description='',
		syntax=univention.admin.syntax.boolean,
	),
	'shutdown': univention.admin.property(
		short_description=_('Perform maintenance before system shutdown'),
		long_description='',
		syntax=univention.admin.syntax.boolean,
	),
	'reboot': univention.admin.property(
		short_description=_('Reboot after maintenance'),
		long_description='',
		syntax=univention.admin.syntax.timeSpec,
	),
	'cron': univention.admin.property(
		short_description=_('Use Cron settings'),
		long_description='',
		syntax=univention.admin.syntax.boolean,
	),
	'month': univention.admin.property(
		short_description=_('Month'),
		long_description='',
		syntax=univention.admin.syntax.Month,
		multivalue=True,
	),
	'day': univention.admin.property(
		short_description=_('Day'),
		long_description='',
		syntax=univention.admin.syntax.Day,
		multivalue=True,
	),
	'weekday': univention.admin.property(
		short_description=_('Day of week'),
		long_description='',
		syntax=univention.admin.syntax.Weekday,
		multivalue=True,
	),
	'hour': univention.admin.property(
		short_description=_('Hour'),
		long_description='',
		syntax=univention.admin.syntax.Hour,
		multivalue=True,
	),
	'minute': univention.admin.property(
		short_description=_('Minute'),
		long_description='',
		syntax=univention.admin.syntax.Minute,
		multivalue=True,
	),

}
property_descriptions.update(dict([
	requiredObjectClassesProperty(),
	prohibitedObjectClassesProperty(),
	fixedAttributesProperty(syntax=maintenanceFixedAttributes),
	emptyAttributesProperty(syntax=maintenanceFixedAttributes),
	ldapFilterProperty(),
]))

layout = [
	Tab(_('General'), _('Maintenance settings'), layout=[
		Group(_('General maintenance settings'), layout=[
			'name',
			'startup',
			'shutdown',
			'cron',
			'reboot',
			['month', 'weekday'],
			['day', 'hour'],
			'minute'
		]),
	]),
	policy_object_tab()
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('startup', 'univentionInstallationStartup', None, univention.admin.mapping.ListToString)
mapping.register('shutdown', 'univentionInstallationShutdown', None, univention.admin.mapping.ListToString)
mapping.register('reboot', 'univentionInstallationReboot', None, univention.admin.mapping.ListToString)
mapping.register('cron', 'univentionCronActive', None, univention.admin.mapping.ListToString)
register_policy_mapping(mapping)


class object(univention.admin.handlers.simplePolicy):
	module = module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes=[]):
		univention.admin.handlers.simplePolicy.__init__(self, co, lo, position, dn, superordinate, attributes)

		self.cron_parsed = 0
		oldcron = self.oldattr.get('univentionCron', [b''])[0].decode('ASCII')
		if oldcron:
			self.parse_cron(oldcron)
			self.cron_parsed = 1
		self.save()

	def parse_cron(self, cronstring):
		# don't use self[key] inside here - it will be recursive call(ed by) __getitem__
		ud.debug(ud.ADMIN, ud.INFO, 'maintenance cron: %s' % cronstring)
		cron = univention.admin.cron.cron_split(cronstring)
		keys = ['minute', 'hour', 'day', 'month', 'weekday']
		for key in keys:
			if key in cron:
				self[key] = []
				for value in cron[key]:
					if value != u'*':
						univention.admin.handlers.simplePolicy.__getitem__(self, key).append(value)

	def __getitem__(self, key):
		value = univention.admin.handlers.simplePolicy.__getitem__(self, key)  # need this first to initialize policy-results
		# set cron if we are in resultmode
		if self.resultmode and hasattr(self, 'policy_attrs') and 'univentionCron' in self.policy_attrs \
			and (not self.cron_parsed):
			self.parse_cron(self.policy_attrs['univentionCron']['value'][0])
			if not self.cron_parsed:
				self.save()
				self.changes = 0
			self.cron_parsed = 1

			value = univention.admin.handlers.simplePolicy.__getitem__(self, key)  # need to reload
		return value

	def _ldap_modlist(self):
		ml = univention.admin.handlers.simplePolicy._ldap_modlist(self)
		if self.hasChanged(['minute', 'hour', 'day', 'month', 'weekday']):

			cron = {}
			if self.has_property('minute'):
				cron['minute'] = self['minute']
			if self.has_property('hour'):
				cron['hour'] = self['hour']
			if self.has_property('day'):
				cron['day'] = self['day']
			if self.has_property('month'):
				cron['month'] = self['month']
			if self.has_property('weekday'):
				cron['weekday'] = self['weekday']
			cron = univention.admin.cron.cron_create(cron)
			ml.append(('univentionCron', self.oldattr.get('univentionCron', []), [cron.encode('ASCII')]))
		return ml


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
