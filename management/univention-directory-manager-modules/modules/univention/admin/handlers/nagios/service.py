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

translation=univention.admin.localization.translation('univention.admin.handlers.nagios')
_=translation.translate

module = 'nagios/service'

childs = 0
short_description = _('Nagios Service')
long_description = ''
operations = [ 'search', 'edit', 'add', 'remove' ]

ldap_search_period = univention.admin.syntax.LDAP_Search(
	filter = '(objectClass=univentionNagiosTimeperiodClass)',
	attribute = [ 'nagios/timeperiod: name' ],
	value='nagios/timeperiod: name' )


property_descriptions={
	'name': univention.admin.property(
			short_description= _('Name'),
			long_description= _('Name of Service'),
			syntax=univention.admin.syntax.string_numbers_letters_dots,
			multivalue=0,
			options=[],
			required=1,
			may_change=0,
			identifies=1
		),
	'description': univention.admin.property(
			short_description= _('Description'),
			long_description= _('Service-Description'),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'checkCommand': univention.admin.property(
			short_description= _('Plugin Command'),
			long_description= _('Command name of Nagios plugin'),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0
		),
	'checkArgs': univention.admin.property(
			short_description = _('Plugin Command Arguments'),
			long_description = _('Arguments of used Nagios plugin'),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'useNRPE': univention.admin.property(
			short_description = _('Use NRPE'),
			long_description = _('Use NRPE to check remote services'),
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'checkPeriod': univention.admin.property(
			short_description = _('Check Period'),
			long_description = _('Check services within check period'),
			syntax=ldap_search_period,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0
		),
	'maxCheckAttempts': univention.admin.property(
			short_description = _('Maximum number of check attempts'),
			long_description = _('Maximum number of check attempts with non-OK-result until contact will be notified'),
			syntax=univention.admin.syntax.integer,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			default='10',
			identifies=0
		),
	'normalCheckInterval': univention.admin.property(
			short_description = _('Check Interval'),
			long_description = _('Interval between checks'),
			syntax=univention.admin.syntax.integer,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			default='10',
			identifies=0
		),
	'retryCheckInterval': univention.admin.property(
			short_description = _('Retry Check Interval'),
			long_description = _('Interval between re-checks if service is in non-OK-state'),
			syntax=univention.admin.syntax.integer,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			default='1',
			identifies=0
		),
	'notificationInterval': univention.admin.property(
			short_description = _('Notification Interval'),
			long_description = _('Interval between notifications'),
			syntax=univention.admin.syntax.integer,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			default='180',
			identifies=0
		),
	'notificationPeriod': univention.admin.property(
			short_description = _('Notification Period'),
			long_description = _('Send notifications during this period'),
			syntax=ldap_search_period,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0
		),
	'notificationOptionWarning': univention.admin.property(
			short_description = _('Notify if service state changes to WARNING'),
			long_description = '',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			default='1',
			may_change=1,
			identifies=0
		),
	'notificationOptionCritical': univention.admin.property(
			short_description = _('Notify if service state changes to CRITICAL'),
			long_description = '',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			default='1',
			may_change=1,
			identifies=0
		),
	'notificationOptionUnreachable': univention.admin.property(
			short_description = _('Notify if service state changes to UNREACHABLE'),
			long_description = '',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			default='1',
			may_change=1,
			identifies=0
		),
	'notificationOptionRecovered': univention.admin.property(
			short_description = _('Notify if service state changes to RECOVERED'),
			long_description = '',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			default='1',
			may_change=1,
			identifies=0
		),
	'assignedHosts': univention.admin.property(
			short_description = _('Assigned Hosts'),
			long_description = _('Check services on these hosts'),
			syntax=univention.admin.syntax.nagiosHostsEnabledDn,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		)
}


layout=[
	univention.admin.tab( _('General'), _('Basic Values'),
			[ [ univention.admin.field( "name" ), univention.admin.field( "description" ) ],
			  [ univention.admin.field( "checkCommand" ), univention.admin.field( "checkArgs" ) ],
			  [ univention.admin.field( "useNRPE" ) ]
			  ] ),
	univention.admin.tab( _('Interval'), _('Check Settings'),
			[ [ univention.admin.field( "normalCheckInterval" ), univention.admin.field( "retryCheckInterval" ) ],
			  [ univention.admin.field( "maxCheckAttempts" ), univention.admin.field( "checkPeriod" ) ]
			  ] ),
	univention.admin.tab( _('Notification'), _('Notification Settings'),
			[ [ univention.admin.field( "notificationInterval" ), univention.admin.field( "notificationPeriod" ) ],
			  [ univention.admin.field( "notificationOptionWarning" ), univention.admin.field( "notificationOptionCritical" ) ],
			  [ univention.admin.field( "notificationOptionUnreachable" ), univention.admin.field( "notificationOptionRecovered" ) ]
			  ] ),
	univention.admin.tab( _('Hosts'), _('Assigned Hosts'),
			[ [ univention.admin.field( "assignedHosts" ) ]
			  ] )
	]


mapping=univention.admin.mapping.mapping()

mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('checkCommand', 'univentionNagiosCheckCommand', None, univention.admin.mapping.ListToString)
mapping.register('checkArgs', 'univentionNagiosCheckArgs', None, univention.admin.mapping.ListToString)
mapping.register('useNRPE', 'univentionNagiosUseNRPE', None, univention.admin.mapping.ListToString)

mapping.register('normalCheckInterval', 'univentionNagiosNormalCheckInterval', None, univention.admin.mapping.ListToString)
mapping.register('retryCheckInterval', 'univentionNagiosRetryCheckInterval', None, univention.admin.mapping.ListToString)
mapping.register('maxCheckAttempts', 'univentionNagiosMaxCheckAttempts', None, univention.admin.mapping.ListToString)
mapping.register('checkPeriod', 'univentionNagiosCheckPeriod', None, univention.admin.mapping.ListToString)

mapping.register('notificationInterval', 'univentionNagiosNotificationInterval', None, univention.admin.mapping.ListToString)
mapping.register('notificationPeriod', 'univentionNagiosNotificationPeriod', None, univention.admin.mapping.ListToString)

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
			if self.oldattr.get('univentionNagiosNotificationOptions', []):
				options = self.oldattr.get('univentionNagiosNotificationOptions', [])[0].split(',')
				if 'w' in options:
					self[ 'notificationOptionWarning' ] = '1'
				else:
					self[ 'notificationOptionWarning' ] = '0'

				if 'c' in options:
					self[ 'notificationOptionCritical' ] = '1'
				else:
					self[ 'notificationOptionCritical' ] = '0'

				if 'u' in options:
					self[ 'notificationOptionUnreachable' ] = '1'
				else:
					self[ 'notificationOptionUnreachable' ] = '0'

				if 'r' in options:
					self[ 'notificationOptionRecovered' ] = '1'
				else:
					self[ 'notificationOptionRecovered' ] = '0'

		_re = re.compile('^([^.]+)\.(.+?)$')

		# convert host FQDN to host DN
		hostlist = []
		hosts = self.oldattr.get('univentionNagiosHostname', [])
		for host in hosts:
			# split into relDomainName and zoneName
			if host and _re.match(host) != None:
				(relDomainName, zoneName) = _re.match(host).groups()
				# find correct dNSZone entry
				res=self.lo.search('(&(objectClass=dNSZone)(zoneName=%s)(relativeDomainName=%s)(aRecord=*))' % (zoneName, relDomainName))
				if not res:
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'service.py: open: couldn''t find dNSZone of %s' % host)
				else:
					# found dNSZone
					filter='(&(objectClass=univentionHost)'
					for aRecord in res[0][1]['aRecord']:
						filter += '(aRecord=%s)' % aRecord
					filter += '(cn=%s))' % relDomainName

					# find dn of host that is related to given aRecords
					res=self.lo.search(filter)
					if res:
						hostlist.append( res[0][0] )

		self['assignedHosts'] = hostlist

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
		pass

	def _ldap_post_remove(self):
		pass

	def _update_policies(self):
		pass

	def _ldap_addlist(self):
		return [ ('objectClass', ['top', 'univentionNagiosServiceClass' ] ) ]

	def _ldap_modlist(self):
		ml=univention.admin.handlers.simpleLdap._ldap_modlist(self)

		options = []
		if self[ 'notificationOptionWarning' ]:
			options.append('w')
		if self[ 'notificationOptionCritical' ]:
			options.append('c')
		if self[ 'notificationOptionUnreachable' ]:
			options.append('u')
		if self[ 'notificationOptionRecovered' ]:
			options.append('r')

		newoptions = ','.join(options)
		ml.append( ('univentionNagiosNotificationOptions', self.oldattr.get('univentionNagiosNotificationOptions', []), newoptions) )

		# save assigned hosts
		if self.hasChanged('assignedHosts'):
			hostlist = []
			for hostdn in self.info['assignedHosts']:
				aRecords = self.lo.getAttr(hostdn, 'aRecord')
				if aRecords and aRecords[0]:
					res=self.lo.search('(&(objectClass=dNSZone)(aRecord=%s)(zoneName=*)(relativeDomainName=*))' % aRecords[0])
					if res:
						fqdn = res[0][1]['relativeDomainName'][0]+'.'+res[0][1]['zoneName'][0]
						hostlist.append(fqdn)

			ml.insert(0, ('univentionNagiosHostname', self.oldattr.get('univentionNagiosHostname', []), hostlist))

		return ml


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):
	filter=univention.admin.filter.conjunction('&', [
				univention.admin.filter.expression('objectClass', 'univentionNagiosServiceClass'),
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
	return 'univentionNagiosServiceClass' in attr.get('objectClass', [])
