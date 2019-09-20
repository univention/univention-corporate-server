# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin policy for the client maintenance
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
policy_apply_to = ["computers/domaincontroller_master", "computers/domaincontroller_backup", "computers/domaincontroller_slave", "computers/memberserver", "computers/managedclient", "computers/mobileclient"]
policy_position_dn_prefix = "cn=installation,cn=update"

childs = 0
short_description = _('Policy: Maintenance')
object_name = _('Maintenance policy')
object_name_plural = _('Maintenance policies')
policy_short_description = _('Maintenance')
long_description = ''
options = {
	'default': univention.admin.option(
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
		oldcron = self.oldattr.get('univentionCron', [''])[0]
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
				for i in range(0, len(cron[key])):
					if str(cron[key][i]) != '*':
						univention.admin.handlers.simplePolicy.__getitem__(self, key).append(str(cron[key][i]))

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

			list = {}
			if self.has_property('minute'):
				list['minute'] = self['minute']
			if self.has_property('hour'):
				list['hour'] = self['hour']
			if self.has_property('day'):
				list['day'] = self['day']
			if self.has_property('month'):
				list['month'] = self['month']
			if self.has_property('weekday'):
				list['weekday'] = self['weekday']
			cron = univention.admin.cron.cron_create(list)
			ml.append(('univentionCron', self.oldattr.get('univentionCron', []), [cron]))
		return ml


lookup = object.lookup
identify = object.identify
