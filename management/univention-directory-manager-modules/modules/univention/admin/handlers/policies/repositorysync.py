# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin policy for the repository sync
#
# Copyright 2004-2011 Univention GmbH
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
import univention.admin.cron

import univention.debug

translation=univention.admin.localization.translation('univention.admin.handlers.policies')
_=translation.translate

class repositorySyncFixedAttributes(univention.admin.syntax.select):
	name='repositorySyncFixedAttributes'
	choices=[
		('univentionRepositoryCron',_('Repository synchronisation')),
		]

module='policies/repositorysync'
operations=['add','edit','remove','search']

policy_oc='univentionPolicyRepositorySync'
policy_apply_to=["computers/domaincontroller_master", "computers/domaincontroller_backup", "computers/domaincontroller_slave", "computers/memberserver"]
policy_position_dn_prefix="cn=repository,cn=update"

childs=0
short_description=_('Policy: Repository synchronisation')
policy_short_description=_('Repository synchronisation')
long_description=''
options={
}
property_descriptions={
	'name': univention.admin.property(
			short_description=_('Name'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=1,
			may_change=0,
			identifies=1,
		),
	'month': univention.admin.property(
			short_description=_('Month'),
			long_description='',
			syntax=univention.admin.syntax.Month,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'day': univention.admin.property(
			short_description=_('Day'),
			long_description='',
			syntax=univention.admin.syntax.Day,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'weekday': univention.admin.property(
			short_description=_('Day of week'),
			long_description='',
			syntax=univention.admin.syntax.Weekday,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'hour': univention.admin.property(
			short_description=_('Hour'),
			long_description='',
			syntax=univention.admin.syntax.Hour,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'minute': univention.admin.property(
			short_description=_('Minute'),
			long_description='',
			syntax=univention.admin.syntax.Minute,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'requiredObjectClasses': univention.admin.property(
			short_description=_('Required object classes'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'prohibitedObjectClasses': univention.admin.property(
			short_description=_('Excluded object classes'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'fixedAttributes': univention.admin.property(
			short_description=_('Fixed attributes'),
			long_description='',
			syntax=repositorySyncFixedAttributes,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'emptyAttributes': univention.admin.property(
			short_description=_('Empty attributes'),
			long_description='',
			syntax=repositorySyncFixedAttributes,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
}

layout = [
	Tab(_('General'),_('Repository syncronisation settings'), layout = [
		Group( _( 'General' ), layout = [
			'name',
			[ 'month', 'weekday' ],
			[ 'day', 'hour' ],
			'minute'
		] ),
	] ),
	Tab(_('Object'),_('Object'), advanced = True, layout = [
		[ 'requiredObjectClasses' , 'prohibitedObjectClasses' ],
		[ 'fixedAttributes', 'emptyAttributes' ]
	] ),
]

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('requiredObjectClasses', 'requiredObjectClasses')
mapping.register('prohibitedObjectClasses', 'prohibitedObjectClasses')
mapping.register('fixedAttributes', 'fixedAttributes')
mapping.register('emptyAttributes', 'emptyAttributes')

class object(univention.admin.handlers.simplePolicy):
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes = [] ):
		global mapping
		global property_descriptions

		self.mapping=mapping
		self.descriptions=property_descriptions

		univention.admin.handlers.simplePolicy.__init__(self, co, lo, position, dn, superordinate, attributes )

		self.cron_parsed=0
		oldcron=self.oldattr.get('univentionRepositoryCron', [''])[0]
		if oldcron:
			self.parse_cron(oldcron)
			self.cron_parsed=1
		self.save()
		self.changes=0

	def parse_cron(self,cronstring):
		# don't use self[key] inside here - it will be recursive call(ed by) __getitem__
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'repositorysync cron: %s' % cronstring)
		cron=univention.admin.cron.cron_split(cronstring)
		keys=['minute', 'hour', 'day', 'month', 'weekday']
		for key in keys:
			if cron.has_key(key):
				self[key]=[]
				for i in range(0, len(cron[key])):
					if str(cron[key][i]) != '*':
						univention.admin.handlers.simplePolicy.__getitem__(self,key).append(str(cron[key][i]))
						
 	def __getitem__(self, key):
		value=univention.admin.handlers.simplePolicy.__getitem__(self,key) # need this first to initialize policy-results
 		# set cron if we are in resultmode
		if self.resultmode and hasattr(self,'policy_attrs') and self.policy_attrs.has_key('univentionRepositoryCron') \
			and (not self.cron_parsed):
 			self.parse_cron(self.policy_attrs['univentionRepositoryCron']['value'][0])
			if not self.cron_parsed:
				self.save()
				self.changes=0
			self.cron_parsed=1

			value=univention.admin.handlers.simplePolicy.__getitem__(self,key) # need to reload
		return value


	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('name'), mapping.mapValue('name', self.info['name']), self.position.getDn())

	def _ldap_addlist(self):
		return [ ('objectClass', ['top', 'univentionPolicy', 'univentionPolicyRepositorySync']) ]

	def _ldap_modlist(self):
		ml=univention.admin.handlers.simplePolicy._ldap_modlist(self)
		if self.hasChanged(['minute', 'hour', 'day', 'month', 'weekday']):

			list={}
			if self.has_key('minute'):
				list['minute']=self['minute']
			if self.has_key('hour'):
				list['hour']=self['hour']
			if self.has_key('day'):
				list['day']=self['day']
			if self.has_key('month'):
				list['month']=self['month']
			if self.has_key('weekday'):
				list['weekday']=self['weekday']
			cron=univention.admin.cron.cron_create(list)
			ml.append(('univentionRepositoryCron', self.oldattr.get('univentionRepositoryCron', []), [cron]))
		return ml
	
def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionPolicyRepositorySync')
		])

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	try:
		for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit):
			res.append( object( co, lo, None, dn, attributes = attrs ) )
	except:
		pass
	return res

def identify(dn, attr, canonical=0):
	return 'univentionPolicyRepositorySync' in attr.get('objectClass', [])
