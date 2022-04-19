#!/usr/bin/python3
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
|UDM| module for nagios time priod objects
"""

import re
from ldap.filter import filter_format

from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.handlers
import univention.admin.syntax
import univention.admin.localization
import univention.admin.uexceptions

translation = univention.admin.localization.translation('univention.admin.handlers.nagios')
_ = translation.translate

module = 'nagios/timeperiod'
default_containers = ['cn=nagios']

childs = False
short_description = _('Nagios time period')
object_name = _('Nagios time period')
object_name_plural = _('Nagios time periods')
long_description = ''
operations = ['search', 'edit', 'add', 'remove']


class syntax_timeperiod(univention.admin.syntax.simple):
	name = 'timeperiod'
	_re = re.compile(r'^([0-9][0-9]\:[0-9][0-9]-[0-9][0-9]\:[0-9][0-9](,[0-9][0-9]\:[0-9][0-9]-[0-9][0-9]\:[0-9][0-9])*)?$')

	@classmethod
	def parse(self, text):
		if text and self._re.match(text) is not None:
			for period in text.split(','):
				(start, end) = period.split('-')
				(shour, smin) = start.split(':')
				(ehour, emin) = end.split(':')
				if ((int(shour) >= 24) and (int(smin) != 0)) or (int(smin) > 59):
					raise univention.admin.uexceptions.valueError(_("No valid timeperiod list!"))
				if ((int(ehour) >= 24) and (int(emin) != 0)) or (int(emin) > 59):
					raise univention.admin.uexceptions.valueError(_("No valid timeperiod list!"))
				shour += smin
				ehour += emin
				if (int(shour) > int(ehour)):
					raise univention.admin.uexceptions.valueError(_("No valid timeperiod list!"))
			return text
		raise univention.admin.uexceptions.valueError(_("No valid timeperiod list!"))


options = {
	'default': univention.admin.option(
		short_description=short_description,
		default=True,
		objectClasses=['top', 'univentionNagiosTimeperiodClass'],
	),
}

property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description=_('Name'),
		syntax=univention.admin.syntax.string_numbers_letters_dots,
		include_in_default_search=True,
		required=True,
		may_change=False,
		identifies=True
	),
	'description': univention.admin.property(
		short_description=_('Description'),
		long_description=_('Description of time period (eg. non-workhours)'),
		syntax=univention.admin.syntax.string_numbers_letters_dots_spaces,
		include_in_default_search=True,
		required=True,
	),
	'periodMonday': univention.admin.property(
		short_description=_('Monday'),
		long_description=_('enter list of periods (e.g. 00:00-07:15,14:30-18:32,23:00-24:00)'),
		syntax=syntax_timeperiod,
	),
	'periodTuesday': univention.admin.property(
		short_description=_('Tuesday'),
		long_description=_('enter list of periods (e.g. 00:00-07:15,14:30-18:32,23:00-24:00)'),
		syntax=syntax_timeperiod,
	),
	'periodWednesday': univention.admin.property(
		short_description=_('Wednesday'),
		long_description=_('enter list of periods (e.g. 00:00-07:15,14:30-18:32,23:00-24:00)'),
		syntax=syntax_timeperiod,
	),
	'periodThursday': univention.admin.property(
		short_description=_('Thursday'),
		long_description=_('enter list of periods (e.g. 00:00-07:15,14:30-18:32,23:00-24:00)'),
		syntax=syntax_timeperiod,
	),
	'periodFriday': univention.admin.property(
		short_description=_('Friday'),
		long_description=_('enter list of periods (e.g. 00:00-07:15,14:30-18:32,23:00-24:00)'),
		syntax=syntax_timeperiod,
	),
	'periodSaturday': univention.admin.property(
		short_description=_('Saturday'),
		long_description=_('enter list of periods (e.g. 00:00-07:15,14:30-18:32,23:00-24:00)'),
		syntax=syntax_timeperiod,
	),
	'periodSunday': univention.admin.property(
		short_description=_('Sunday'),
		long_description=_('enter list of periods (e.g. 00:00-07:15,14:30-18:32,23:00-24:00)'),
		syntax=syntax_timeperiod,
	)
}


layout = [
	Tab(_('General'), _('Time Period Settings'), layout=[
		Group(_('General Nagios time period settings'), layout=[
			["name", "description"],
			["periodMonday", "periodTuesday"],
			["periodWednesday", "periodThursday"],
			["periodFriday", "periodSaturday"],
			"periodSunday"
		]),
	]),
]


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module

	def _post_unmap(self, info, values):
		value = values.get('univentionNagiosTimeperiod', [b''])[0].decode('ASCII')
		if value:
			periods = value.split('#', 6)
			info['periodMonday'] = periods[0]
			info['periodTuesday'] = periods[1]
			info['periodWednesday'] = periods[2]
			info['periodThursday'] = periods[3]
			info['periodFriday'] = periods[4]
			info['periodSaturday'] = periods[5]
			info['periodSunday'] = periods[6]
		return info

	def _ldap_pre_remove(self):
		super(object, self)._ldap_pre_remove()
		# refuse deletion if there is still a reference
		period_filter = filter_format('(&(objectClass=univentionNagiosServiceClass)(|(univentionNagiosCheckPeriod=%s)(univentionNagiosNotificationPeriod=%s)))', [self['name'], self['name']])
		if self.lo.searchDn(base=self.position.getDomain(), filter=period_filter, scope='sub'):
			raise univention.admin.uexceptions.nagiosTimeperiodUsed()

	def _ldap_modlist(self):
		ml = univention.admin.handlers.simpleLdap._ldap_modlist(self)

		# timeperiod list for one weekday is hash separated - only usage of [0-9:-] is allowed
		# those lists are concatenated with hashes as delimiter
		periodslist = [self['periodMonday'], self['periodTuesday'], self['periodWednesday'], self['periodThursday'], self['periodFriday'], self['periodSaturday'], self['periodSunday']]
		for i in range(len(periodslist)):
			if periodslist[i] is None:
				periodslist[i] = ''
		newperiods = '#'.join(periodslist)

		ml.append(('univentionNagiosTimeperiod', self.oldattr.get('univentionNagiosTimeperiod', []), [newperiods.encode('ASCII')]))

		return ml


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
