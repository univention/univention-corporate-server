#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Univention Nagios
#  univention admin nagios module
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import re, sys, string
import univention.admin.filter
import univention.admin.handlers
import univention.admin.syntax
import univention.admin.localization
import univention.admin.uexceptions

translation=univention.admin.localization.translation('univention.admin.handlers.nagios')
_=translation.translate

module = 'nagios/timeperiod'

childs = 0
short_description = _('Nagios Time Period')
long_description = ''
operations = [ 'search', 'edit', 'add', 'remove' ]


class syntax_timeperiod(univention.admin.syntax.simple):
	name='timeperiod'
	_re = re.compile('^([0-9][0-9]\:[0-9][0-9]-[0-9][0-9]\:[0-9][0-9](,[0-9][0-9]\:[0-9][0-9]-[0-9][0-9]\:[0-9][0-9])*)?$')

	def parse(self, text):
		if text and self._re.match(text) != None:
			for period in text.split(','):
				(start,end) = period.split('-')
				(shour,smin) = start.split(':')
				(ehour,emin) = end.split(':')
				if ((int(shour)>=24) and (int(smin) != 0)) or (int(smin) > 59):
					raise univention.admin.uexceptions.valueError, _("No valid timeperiod list!")
				if ((int(ehour)>=24) and (int(emin) != 0)) or (int(emin) > 59):
					raise univention.admin.uexceptions.valueError, _("No valid timeperiod list!")
				shour+=smin
				ehour+=emin
				if (int(shour) > int(ehour)):
					raise univention.admin.uexceptions.valueError, _("No valid timeperiod list!")
			return text
		raise univention.admin.uexceptions.valueError, _("No valid timeperiod list!")


property_descriptions={
	'name': univention.admin.property(
			short_description= _('Name'),
			long_description= _('Name'),
			syntax=univention.admin.syntax.string_numbers_letters_dots,
			multivalue=0,
			options=[],
			required=1,
			may_change=0,
			identifies=1
		),
	'description': univention.admin.property(
			short_description= _('Description'),
			long_description= _('Description of time period (eg. non-workhours)'),
			syntax=univention.admin.syntax.string_numbers_letters_dots_spaces,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0
		),
	'periodMonday': univention.admin.property(
			short_description= _('Monday'),
			long_description= _('enter list of periods (e.g. 00:00-07:15,14:30-18:32,23:00-24:00)'),
			syntax=syntax_timeperiod,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'periodTuesday': univention.admin.property(
			short_description= _('Tuesday'),
			long_description= _('enter list of periods (e.g. 00:00-07:15,14:30-18:32,23:00-24:00)'),
			syntax=syntax_timeperiod,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'periodWednesday': univention.admin.property(
			short_description= _('Wednesday'),
			long_description= _('enter list of periods (e.g. 00:00-07:15,14:30-18:32,23:00-24:00)'),
			syntax=syntax_timeperiod,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'periodThursday': univention.admin.property(
			short_description= _('Thursday'),
			long_description= _('enter list of periods (e.g. 00:00-07:15,14:30-18:32,23:00-24:00)'),
			syntax=syntax_timeperiod,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'periodFriday': univention.admin.property(
			short_description= _('Friday'),
			long_description= _('enter list of periods (e.g. 00:00-07:15,14:30-18:32,23:00-24:00)'),
			syntax=syntax_timeperiod,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'periodSaturday': univention.admin.property(
			short_description= _('Saturday'),
			long_description= _('enter list of periods (e.g. 00:00-07:15,14:30-18:32,23:00-24:00)'),
			syntax=syntax_timeperiod,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'periodSunday': univention.admin.property(
			short_description= _('Sunday'),
			long_description= _('enter list of periods (e.g. 00:00-07:15,14:30-18:32,23:00-24:00)'),
			syntax=syntax_timeperiod,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		)
}


layout=[
	univention.admin.tab( _('General'), _('Time Period Settings'),
	      [
			[ univention.admin.field( "name" ), univention.admin.field( "description" ) ],
			[ univention.admin.field( "periodMonday" ), univention.admin.field( "periodTuesday" ) ],
			[ univention.admin.field( "periodWednesday" ), univention.admin.field( "periodThursday" ) ],
			[ univention.admin.field( "periodFriday" ), univention.admin.field( "periodSaturday" ) ],
			[ univention.admin.field( "periodSunday" ) ]
		  ] )
	]



mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, arg=None):
		global mapping
		global property_descriptions

		self.co=co
		self.lo=lo
		self.dn=dn
		self.position=position
		self._exists=0
		self.mapping=mapping
		self.descriptions=property_descriptions

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate)

	def exists(self):
		return self._exists

	def open(self):
		univention.admin.handlers.simpleLdap.open(self)
		if self.dn:
			if self.oldattr.get('univentionNagiosTimeperiod', []):
				periods = self.oldattr.get('univentionNagiosTimeperiod', [])[0].split('#')
				self[ 'periodMonday' ] = periods[0]
				self[ 'periodTuesday' ] = periods[1]
				self[ 'periodWednesday' ] = periods[2]
				self[ 'periodThursday' ] = periods[3]
				self[ 'periodFriday' ] = periods[4]
				self[ 'periodSaturday' ] = periods[5]
				self[ 'periodSunday' ] = periods[6]
		self.save()

	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('name'), mapping.mapValue('name', self.info['name']), self.position.getDn())

	def _ldap_post_create(self):
		pass

	def _ldap_pre_modify(self):
		pass

	def _ldap_post_modify(self):
		pass

	def _ldap_pre_remove(self):
		# refuse deletion if there is still a reference
		searchResult=self.lo.searchDn(base=self.position.getDomain(), filter='(&(objectClass=univentionNagiosServiceClass)(|(univentionNagiosCheckPeriod=%s)(univentionNagiosNotificationPeriod=%s)))' % (self['name'], self['name']), scope='sub')
		if searchResult:
			raise univention.admin.uexceptions.nagiosTimeperiodUsed

	def _ldap_post_remove(self):
		pass

	def _update_policies(self):
		pass

	def _ldap_addlist(self):
		return [ ('objectClass', ['top', 'univentionNagiosTimeperiodClass' ] ) ]

	def _ldap_modlist(self):
		ml=univention.admin.handlers.simpleLdap._ldap_modlist(self)

		# timeperiod list for one weekday is hash separated - only usage of [0-9:-] is allowed
		# those lists are concatenated with hashes as delimiter
		periodslist = [ self['periodMonday'], self['periodTuesday'], self['periodWednesday'], self['periodThursday'],
						self['periodFriday'], self['periodSaturday'], self['periodSunday'] ]
		for i in range(len(periodslist)):
			if periodslist[i] == None:
				periodslist[i] = ''
		newperiods = '#'.join(periodslist)

		ml.append( ('univentionNagiosTimeperiod', self.oldattr.get('univentionNagiosTimeperiod', []), newperiods) )

		return ml

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):
	filter=univention.admin.filter.conjunction('&', [
				univention.admin.filter.expression('objectClass', 'univentionNagiosTimeperiodClass'),
				])

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	for dn in lo.searchDn(unicode(filter), base, scope, unique, required, timeout, sizelimit):
		res.append(object(co, lo, None, dn))
	return res


def identify(dn, attr, canonical=0):
	return 'univentionNagiosTimeperiodClass' in attr.get('objectClass', [])
