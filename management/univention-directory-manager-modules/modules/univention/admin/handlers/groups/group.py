# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for groups
#
# Copyright (C) 2004-2009 Univention GmbH
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

import sys, string, copy, re
import univention.admin
import univention.admin.filter
import univention.admin.handlers
import univention.admin.allocators
import univention.admin.localization

translation=univention.admin.localization.translation('univention.admin.handlers.groups')
_=translation.translate

module='groups/group'
operations=['add','edit','remove','search','move']
usewizard=1
wizardmenustring=_("Groups")
wizarddescription=_("Add, edit and delete groups")
wizardoperations={"add":[_("Add"), _("Add group object")],"find":[_("Search"), _("Search group object(s)")]}

childs=0
short_description=_('Group: Group')
long_description=''
options={
	'posix': univention.admin.option(
			short_description=_('Posix group'),
			default=1
		),
	'samba': univention.admin.option(
			short_description=_('Samba group'),
			default=1
		)
}

module_search_filter=univention.admin.filter.conjunction('&', [
	univention.admin.filter.expression('objectClass', 'univentionGroup'),
	])

property_descriptions={
	'name': univention.admin.property(
			short_description=_('Name'),
			long_description='',
			syntax=univention.admin.syntax.gid,
			multivalue=0,
			options=['posix', 'samba'],
			required=1,
			may_change=1,
			identifies=1
		),
	'gidNumber': univention.admin.property(
			short_description=_('Group ID'),
			long_description='',
			syntax=univention.admin.syntax.integer,
			multivalue=0,
			required=0,
			may_change=0,
			identifies=0,
			options=['posix','samba']
		),
	'sambaRID': univention.admin.property(
			short_description=_('Relative ID'),
			long_description='',
			syntax=univention.admin.syntax.integer,
			multivalue=0,
			required=0,
			may_change=0,
			identifies=0,
			options=['samba']
		),
	'sambaGroupType': univention.admin.property(
			short_description=_('Samba group type'),
			long_description='',
			syntax=univention.admin.syntax.sambaGroupType,
			multivalue=0,
			required=0,
			may_change=1,
			identifies=0,
			default=('2',[]),
			options=['samba']
		),
	'description': univention.admin.property(
			short_description=_('Description'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['posix', 'samba'],
			required=0,
			may_change=1,
			identifies=0
		),
	'users': univention.admin.property(
			short_description=_('Users'),
			long_description='',
			syntax=univention.admin.syntax.userDn,
			multivalue=1,
			options=['posix'],
			required=0,
			may_change=1,
			dontsearch=1,
			identifies=0
		),
	'hosts': univention.admin.property(
			short_description=_('Hosts'),
			long_description='',
			syntax=univention.admin.syntax.hostDn,
			multivalue=1,
			options=['posix'],
			license=['UGS', 'UCS'],
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
			options=['posix'],
			required=0,
			may_change=1,
			dontsearch=0,
			identifies=0
		),
	'memberOf': univention.admin.property(
			short_description=_('Member of'),
			long_description='',
			syntax=univention.admin.syntax.groupDn,
			multivalue=1,
			options=['posix'],
			required=0,
			may_change=1,
			dontsearch=1,
			identifies=0
		),
	'nestedGroup': univention.admin.property(
			short_description=_('Nested group'),
			long_description='',
			syntax=univention.admin.syntax.groupDn,
			multivalue=1,
			options=['posix'],
			required=0,
			may_change=1,
			dontsearch=1,
			identifies=0
		)
}

# overwrite properties by UCR variables
ucr_properties = ['dontsearch']
univention.admin.ucr_overwrite_properties (module, ucr_properties, property_descriptions)

layout=[
	univention.admin.tab(_('General'),_('Basic settings'),[
		[univention.admin.field("name"), univention.admin.field("description")],
		[univention.admin.field("gidNumber"),univention.admin.field("sambaRID")],
		[univention.admin.field("sambaGroupType"), univention.admin.field("mailAddress")]
	] ),
	univention.admin.tab(_('Members'),_('Members of this Group'),[
		[univention.admin.field("users")]
	] ),
	univention.admin.tab(_('Host members'),_('Host members of this group'),[
		[univention.admin.field("hosts")]
	], advanced = True ),
	univention.admin.tab(_('Nested groups'),_('Membership of other groups'),[
		[univention.admin.field("nestedGroup")]
	], advanced = True ),
	univention.admin.tab(_('Member of'),_('Membership in other groups'),[
			[univention.admin.field("memberOf")]
	], advanced = True )
]


mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('sambaGroupType', 'sambaGroupType', None, univention.admin.mapping.ListToString)
mapping.register('mailAddress', 'mailPrimaryAddress', None, univention.admin.mapping.ListToString)

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

		self.alloc=[]

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate)


	def open(self):
		global options
		univention.admin.handlers.simpleLdap.open(self)

		self.options=[]
		if self.oldattr.has_key('objectClass'):
			ocs=self.oldattr['objectClass']
			if 'posixGroup' in ocs:
				self.options.append( 'posix' )
			if 'sambaGroupMapping' in ocs:
				self.options.append( 'samba' )
		else:
			self._define_options( options )

		self.info['gidNumber'] = self.oldattr.get('gidNumber', [''])[0]

		if 'samba' in self.options:
			sid = self.oldattr.get('sambaSID', [''])[0]
			pos = sid.rfind('-')
			self.info['sambaRID'] = sid[pos+1:]

		if self.dn:
			self['memberOf']=self.lo.searchDn(filter='(&(objectClass=posixGroup)(uniqueMember=%s))' % univention.admin.filter.escapeForLdapFilter(self.dn))

			self['users']=self['hosts']=self['nestedGroup']=[]
			if self.oldattr.has_key('uniqueMember'):
				groupMembers=self.oldattr['uniqueMember']

				for i in groupMembers:
					saved=0
					try:
						result = self.lo.searchDn(base=i, filter = 'objectClass=univentionGroup', unique=0)
						if result:
							self['nestedGroup'].append(i)
							saved=1
					except univention.admin.uexceptions.noObject:
						pass

					try:
						result = self.lo.searchDn(base=i, filter = 'objectClass=univentionHost', unique=0)
						if result:
							self['hosts'].append(i)
							saved=1
					except univention.admin.uexceptions.noObject:
						pass

					if not saved:
						self['users'].append(i)

			self.save()


	def exists(self):
		return self._exists

	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('name'), mapping.mapValue('name', self.info['name']), self.position.getDn())

	def _ldap_addlist(self):

		try:
			if self['gidNumber']:
				self.gidNum = univention.admin.allocators.acquireUnique(self.lo, self.position, 'gidNumber', self['gidNumber'], 'gidNumber', scope='base')
			else:
				self.gidNum = univention.admin.allocators.request(self.lo, self.position, 'gidNumber')
			self.alloc.append(('gidNumber', self.gidNum))

			if self[ 'mailAddress' ]:
				try:
					self.alloc.append( ( 'mailPrimaryAddress', self[ 'mailAddress' ] ) )
					univention.admin.allocators.request( self.lo, self.position, 'mailPrimaryAddress', value = self[ 'mailAddress' ] )
				except:
					self.cancel()
					raise univention.admin.uexceptions.mailAddressUsed


			if 'samba' in self.options and self.gidNum:
				if self['sambaRID']:
					searchResult = self.lo.search(filter='objectClass=sambaDomain', attr=['sambaSID'])
					domainsid=searchResult[0][1]['sambaSID'][0]
					sid = domainsid+'-'+self['sambaRID']
					self.groupSid = univention.admin.allocators.request(self.lo, self.position, 'sid', sid)
				else:
					num = self.gidNum
					while not hasattr(self,'groupSid') or not self.groupSid or self.groupSid == 'None':
						try:
							self.groupSid = univention.admin.allocators.requestGroupSid(self.lo, self.position, num)
						except univention.admin.uexceptions.noLock, e:
							num = str(int(num)+1)
				self.alloc.append(('sid', self.groupSid))
			else:
				self.groupSid=None

			error=0
			name=None

			try:
				self.alloc.append(('groupName', self['name']))
				name=univention.admin.allocators.request(self.lo, self.position, 'groupName', value=self['name'])
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'groups/group: arequested groupname without exception')
			except univention.admin.uexceptions.permissionDenied, e:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'groups/group: arequested groupname with permissionDenied exception')
				raise e
			except univention.admin.uexceptions.licenseNotFound, e:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'groups/group: arequested groupname with licenseNotFound exception')
				raise e
			except univention.admin.uexceptions.licenseInvalid, e:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'groups/group: arequested groupname with licenseInvalid exception')
				raise e
			except univention.admin.uexceptions.licenseExpired, e:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'groups/group: arequested groupname with licenseExpired exception')
				raise e
			except univention.admin.uexceptions.licenseWrongBaseDn, e:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'groups/group: arequested groupname with licenseWrongbaseDn exception')
				raise e
			except univention.admin.uexceptions.licenseDisableModify, e:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'groups/group: arequested groupname with licenseDisableModify exception')
				raise e
			except univention.admin.uexceptions.base, e:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'groups/group: arequested groupname with base (%s) exception'%e)
				error=1

			if not name or error:
				name=self['name']
				del(self.info['name'])
				self.oldinfo={}
				self.dn=None
				self._exists=0
				self.cancel()
				raise univention.admin.uexceptions.groupNameAlreadyUsed, '%s' % (name)
				return []

			ocs=['top']
			al=[]
			if 'posix' in self.options:
				ocs.append('posixGroup')
				ocs.append('univentionGroup')
			if 'samba' in self.options:
				ocs.append('sambaGroupMapping')
				if not 'posix' in self.options:
					ocs.append('organizationalRole')
				al.append(('sambaSID', [self.groupSid]))

			al.append(('gidNumber', [self.gidNum]))

			al.insert(0, ('objectClass', ocs))
			return al
		except:
			self.cancel()
			raise

	def _ldap_modlist( self ):

		ml=univention.admin.handlers.simpleLdap._ldap_modlist( self )
		if self.hasChanged( 'mailAddress' ) and self[ 'mailAddress' ]:
			for i, j in self.alloc:
				if i == 'mailPrimaryAddress': break
			else:
				try:
					self.alloc.append( ( 'mailPrimaryAddress', self[ 'mailAddress' ] ) )
					univention.admin.allocators.request( self.lo, self.position, 'mailPrimaryAddress', value = self[ 'mailAddress' ] )
				except:
					self.cancel()
					raise univention.admin.uexceptions.mailAddressUsed

		old = self.oldinfo.get( 'users', [] ) + self.oldinfo.get('hosts', []) + self.oldinfo.get('nestedGroup', []) 
		new = self.info.get('users', []) + self.info.get('hosts', []) + self.info.get('nestedGroup', [])
		if old != new:
			ml.append( ( 'uniqueMember', old, new ) )
			uids = self.lo.getAttr( self.dn, 'memberUid' )
			new_uids = []
			for member in new:
				if member.startswith('uid='): # UID is stored in DN --> use UID directly
					new_uids.append( member[ member.find('=') + 1 : member.find(',') ] ) # string between first '=' and first ','
				else: # UID is not stored in DN --> fetch UID by DN
					uid_list = self.lo.getAttr(member, 'uid')
					# a group have no uid attribute, see Bug #12644
					if len(uid_list) > 0:
						new_uids.append(uid_list[0])
						if len(uid_list) > 1:
							univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'groups/group: A groupmember has multiple UIDs (%s %s)' % (member, str(uid_list)))
			ml.append( ( 'memberUid', uids, new_uids ) )
		return ml

	def _ldap_post_create(self):
		name=univention.admin.allocators.release(self.lo, self.position, 'groupName', value=self['name'])
		if 'posix' in self.options:
			univention.admin.allocators.confirm(self.lo, self.position, 'gidNumber', self.gidNum)
		if 'samba' in self.options:
			univention.admin.allocators.confirm(self.lo, self.position, 'sid', self.groupSid)
		if self[ 'mailAddress' ]:
			univention.admin.allocators.confirm( self.lo, self.position, 'mailPrimaryAddress', self[ 'mailAddress' ] )
		self.__update_membership()

	def _ldap_post_modify( self ):
		if self.hasChanged( 'mailAddress' ) and self[ 'mailAddress' ]:
			univention.admin.allocators.confirm( self.lo, self.position, 'mailPrimaryAddress', self[ 'mailAddress' ] )
		self.__update_membership()

	def _ldap_pre_remove(self):
		if not hasattr(self,"options"):
			self.open()
		self.open()
		if 'posix' in self.options:
			self.gidNum=self.oldattr['gidNumber'][0]
		if 'samba' in self.options:
			self.groupSid=self.oldattr['sambaSID'][0]
		if hasattr(self,'gidNum'):
			searchResult=self.lo.searchDn(base=self.position.getDomain(), filter='(&(objectClass=person)(gidNumber=%s))'%self.gidNum, scope='domain')
			if searchResult:
				raise univention.admin.uexceptions.primaryGroupUsed
		if hasattr(self,'groupSid'):
			searchResult=self.lo.searchDn(base=self.position.getDomain(), filter='(&(objectClass=person)(sambaPrimaryGroupSID=%s))'%self.groupSid, scope='domain')
			if searchResult:
				raise univention.admin.uexceptions.primaryGroupUsed

	def _ldap_post_remove(self):

		if 'posix' in self.options:
			univention.admin.allocators.release(self.lo, self.position, 'gidNumber', self.gidNum)
		if 'samba' in self.options:
			univention.admin.allocators.release(self.lo, self.position, 'sid', self.groupSid)

		for group in self.info.get('memberOf', []):
			if type(group) == type([]):
				group=group[0]
			members=self.lo.getAttr(group, 'uniqueMember')
			if not self.__case_insensitive_in_list(self.dn, members):
				continue
			newmembers=copy.deepcopy(members)
			newmembers=self.__case_insensitive_remove_from_list(self.dn, newmembers)
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'groups/group: remove from supergroup %s'%group)
			self.__set_membership_attributes( group, members, newmembers )

	def _ldap_post_move(self, olddn):

		settings_module=univention.admin.modules.get('settings/default')
		settings_object=univention.admin.objects.get(settings_module, None, self.lo, position='', dn='cn=default,cn=univention,%s'%self.lo.base)
		settings_object.open()
		for attr in ['defaultGroup','defaultMemberServerGroup','defaultClientGroup',
					 'defaultDomainControllerMBGroup','defaultDomainControllerGroup','defaultComputerGroup']:
			if settings_object[attr].lower() == olddn.lower():
				settings_object[attr] = self.dn
		settings_object.modify()

		for group in self.info.get('memberOf', []):
			if type(group) == type([]):
				group=group[0]
			members=self.lo.getAttr(group, 'uniqueMember')
			if not self.__case_insensitive_in_list(olddn, members):
				continue
			newmembers=copy.deepcopy(members)
			newmembers=self.__case_insensitive_remove_from_list(olddn, newmembers)
			newmembers.append(self.dn)
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'groups/group: updating supergroup %s'%group)
			self.__set_membership_attributes( group, members, newmembers )

	def cancel(self):
		for i,j in self.alloc:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'cancel: release (%s): %s' % (i,j) )
			univention.admin.allocators.release(self.lo, self.position, i, j)

	def __update_membership(self):

		if self.exists():
			old_groups = self.oldinfo.get('memberOf', [])
			old_name = self.oldinfo.get('name')
			new_name = self.info.get('name')
		else:
			old_groups = []
			old_name = ""
			new_name = ""

		# rewrite membership attributes in "supergroup" if we have a new name (rename)
		if not old_name == new_name:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'groups/group: rewrite memberuid after rename')
			newdn = self.dn
			newdn = newdn.replace(old_name, new_name, 1)
			for group in self.info.get('memberOf', []):
				if type(group) == type([]):
					group=group[0]
				members=self.lo.getAttr(group, 'uniqueMember')
				newmembers=copy.deepcopy(members)
				newmembers=self.__case_insensitive_remove_from_list(self.dn, newmembers)
				newmembers.append(newdn)
				self.__set_membership_attributes( group, members, newmembers )

		add_to_group=[]
		remove_from_group=[]

		for group in old_groups:
			if group and not self.__case_insensitive_in_list(group, self.info.get('memberOf', [])):
				remove_from_group.append(group)

		for group in self.info.get('memberOf', []):
			if group and not self.__case_insensitive_in_list(group, old_groups):
				add_to_group.append(group)

		for group in add_to_group:
			if type(group) == type([]):
				group=group[0]
			members=self.lo.getAttr(group, 'uniqueMember')
			if self.__case_insensitive_in_list(self.dn, members):
				continue
			newmembers=copy.deepcopy(members)
			newmembers.append(self.dn)
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'groups/group: add to supergroup %s'%group)
			self.__set_membership_attributes( group, members, newmembers )

		for group in remove_from_group:
			if type(group) == type([]):
				group=group[0]
			members=self.lo.getAttr(group, 'uniqueMember')
			if not self.__case_insensitive_in_list(self.dn, members):
				continue
			newmembers=copy.deepcopy(members)
			newmembers=self.__case_insensitive_remove_from_list(self.dn, newmembers)
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'groups/group: remove from supergroup %s'%group)
			self.__set_membership_attributes( group, members, newmembers )

	def __set_membership_attributes( self, group, members, newmembers ):
		newuids = map( lambda x: x[ x.find( '=' ) + 1 : x.find( ',' ) ], newmembers )
		self.lo.modify( group, [ ( 'uniqueMember', members, newmembers ) ] )
		#don't set the memberUid attribute for nested groups, see Bug #11868
		# uids = self.lo.getAttr( group, 'memberUid' )
		# self.lo.modify( group, [ ( 'memberUid', uids, newuids ) ] )

	def __case_insensitive_in_list(self, dn, list):
		for element in list:
			if dn.decode('utf8').lower() == element.decode('utf8').lower():
				return True
		return False

	def __case_insensitive_remove_from_list(self, dn, list):
		for element in list:
			if dn.decode('utf8').lower() == element.decode('utf8').lower():
				remove_element = element
		list.remove(remove_element)
		return list

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('cn', '*'),
		univention.admin.filter.conjunction('|',
		  [univention.admin.filter.conjunction('&',
				[univention.admin.filter.expression('objectClass', 'univentionGroup'),]),
		   univention.admin.filter.conjunction('&',
				[univention.admin.filter.expression('objectClass', 'sambaGroupMapping'),])
		   ])
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

	return 'univentionGroup' in attr.get('objectClass', [])
