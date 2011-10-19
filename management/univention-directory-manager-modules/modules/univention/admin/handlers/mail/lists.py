# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for mailinglists
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
import univention.admin.filter
import univention.admin.handlers
import univention.admin.allocators
import univention.admin.localization

translation=univention.admin.localization.translation('univention.admin.handlers.mail')
_=translation.translate

module='mail/lists'
operations=['add','edit','remove','search','move']
usewizard=1

childs=0
short_description=_('Mail: Mailing lists')
long_description=''

module_search_filter=univention.admin.filter.expression('objectClass', 'univentionMailList'),

property_descriptions={
	'name': univention.admin.property(
			short_description=_('Name'),
			long_description='',
			syntax=univention.admin.syntax.gid,
			multivalue=0,
			required=1,
			may_change=1,
			identifies=1
		),
	'description': univention.admin.property(
			short_description=_('Description'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			required=0,
			may_change=1,
			identifies=0
		),
	'members': univention.admin.property(
			short_description=_('Members'),
			long_description='',
			syntax=univention.admin.syntax.emailAddress,
			multivalue=1,
			required=0,
			may_change=1,
			dontsearch=1,
			identifies=0
		),
	'mailAddress': univention.admin.property(
			short_description=_('Mail address'),
			long_description='',
			syntax=univention.admin.syntax.emailAddress,
			multivalue=0,
			required=0,
			may_change=1,
			dontsearch=0,
			identifies=0
		),
	'allowedEmailUsers': univention.admin.property(
			short_description=_('Allowed e-mail users'),
			long_description='',
			syntax=univention.admin.syntax.UserDN,
			multivalue=1,
			required=0,
			may_change=1,
			dontsearch=1,
			identifies=0
		),
	'allowedEmailGroups': univention.admin.property(
			short_description=_('Allowed e-mail groups'),
			long_description='',
			syntax=univention.admin.syntax.GroupDN,
			multivalue=1,
			required=0,
			may_change=1,
			dontsearch=1,
			identifies=0
		)
}

layout = [
	Tab( _( 'General' ), _( 'Basic settings' ), layout = [
		Group( _( 'General' ), layout = [
			[ "name", "description" ],
			"mailAddress",
			"members"
		] ),
	] ),
	Tab( _( 'Allowed users' ), _( 'Users that are allowed to send e-mails to the list' ), advanced = True, layout = [
		"allowedEmailUsers"
		] ),
	Tab( _( 'Allowed groups' ), _( 'Groups that are allowed to send e-mails to the list' ), advanced = True, layout = [
		"allowedEmailGroups"
		] )
	]

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('members', 'univentionMailMember')
mapping.register('mailAddress', 'mailPrimaryAddress', None, univention.admin.mapping.ListToString)

class object(univention.admin.handlers.simpleLdap):
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes = [] ):
		global mapping
		global property_descriptions

		self.mapping=mapping
		self.descriptions=property_descriptions

		self.alloc=[]

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate, attributes = attributes )


	def open(self):

		univention.admin.handlers.simpleLdap.open(self)

		self['allowedEmailUsers'] = []
		if self.oldattr.has_key('univentionAllowedEmailUsers'):
			self['allowedEmailUsers'] = self.oldattr['univentionAllowedEmailUsers']

		self['allowedEmailGroups'] = []
		if self.oldattr.has_key('univentionAllowedEmailGroups'):
			self['allowedEmailGroups'] = self.oldattr['univentionAllowedEmailGroups']

		self.save()

	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('name'), mapping.mapValue('name', self.info['name']), self.position.getDn())

	def _ldap_post_create(self):
		if self[ 'mailAddress' ]:
			univention.admin.allocators.confirm( self.lo, self.position, 'mailPrimaryAddress', self[ 'mailAddress' ] )

	def _ldap_post_modify( self ):
		if self[ 'mailAddress' ] and self.hasChanged( 'mailAddress' ):
			univention.admin.allocators.confirm( self.lo, self.position, 'mailPrimaryAddress', self[ 'mailAddress' ] )

	def _ldap_addlist(self):
		ocs=['top']
		al=[]
		ocs.append('univentionMailList')
		# mail address MUST be unique
		if self[ 'mailAddress' ]:
			try:
				self.alloc.append( ( 'mailPrimaryAddress', self[ 'mailAddress' ] ) )
				univention.admin.allocators.request( self.lo, self.position, 'mailPrimaryAddress', value = self[ 'mailAddress' ] )
			except:
				univention.admin.allocators.release( self.lo, self.position, 'mailPrimaryAddress', value = self[ 'mailAddress' ] )
				raise univention.admin.uexceptions.mailAddressUsed

		al.insert(0, ('objectClass', ocs))
		return al

	def _ldap_modlist( self ):
		if self.hasChanged( 'mailAddress' ) and self[ 'mailAddress' ]:
			for i, j in self.alloc:
				if i == 'mailPrimaryAddress': break
			else:
				try:
					univention.admin.allocators.request( self.lo, self.position, 'mailPrimaryAddress', value = self[ 'mailAddress' ] )
				except:
					univention.admin.allocators.release( self.lo, self.position, 'mailPrimaryAddress', value = self[ 'mailAddress' ] )
					raise univention.admin.uexceptions.mailAddressUsed

		ml = univention.admin.handlers.simpleLdap._ldap_modlist( self )

		oldEmailUsers = self.oldinfo.get( 'allowedEmailUsers', [] )
		newEmailUsers = self.info.get( 'allowedEmailUsers', [] )
		if oldEmailUsers != newEmailUsers:
			ml.append( ('univentionAllowedEmailUsers', oldEmailUsers, newEmailUsers) )

		oldEmailGroups = self.oldinfo.get( 'allowedEmailGroups', [] )
		newEmailGroups = self.info.get( 'allowedEmailGroups', [] )
		if oldEmailGroups != newEmailGroups:
			ml.append( ('univentionAllowedEmailGroups', oldEmailGroups, newEmailGroups) )

		return ml


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionMailList')
		])

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit):
		res.append( object( co, lo, None, dn, attributes = attrs ) )
	return res

def identify(dn, attr, canonical=0):

	return 'univentionMailList' in attr.get('objectClass', [])

