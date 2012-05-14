# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for groups
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

import copy
import time
import ldap

import univention.admin
from univention.admin.layout import Tab, Group
import univention.admin.uldap
import univention.admin.filter
import univention.admin.handlers
import univention.admin.allocators
import univention.admin.localization
import univention.debug
from univention.admin import configRegistry

translation=univention.admin.localization.translation('univention.admin.handlers.groups')
_=translation.translate

module='groups/group'
operations=['add','edit','remove','search','move']
usewizard=1
wizardmenustring=_("Groups")
wizarddescription=_("Add, edit and delete groups")
wizardoperations={"add":[_("Add"), _("Add group object")],"find":[_("Search"), _("Search group object(s)")]}

childs=0
short_description=_('Group')
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

# global caching variable
if configRegistry.is_true('directory/manager/samba3/legacy', False):
	s4connector_present = False
elif configRegistry.is_false('directory/manager/samba3/legacy', False):
	s4connector_present = True
else:
	s4connector_present = None


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
			may_change=1,
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
	'sambaPrivileges': univention.admin.property(
			short_description = _( 'Samba privileges' ),
			long_description = _( 'Manage samba privileges' ),
			syntax = univention.admin.syntax.SambaPrivileges,
			multivalue = True,
			options = [ 'samba' ],
			required = False,
			dontsearch = False,
			may_change = True,
			identifies = False,
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
			syntax=univention.admin.syntax.UserDN,
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
			syntax=univention.admin.syntax.HostDN,
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
			syntax=univention.admin.syntax.GroupDN,
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
			syntax=univention.admin.syntax.GroupDN,
			multivalue=1,
			options=['posix'],
			required=0,
			may_change=1,
			dontsearch=1,
			identifies=0
		),
	'allowedEmailUsers': univention.admin.property(
			short_description=_( 'Users that are allowed to send e-mails to the group' ),
			long_description='',
			syntax=univention.admin.syntax.UserDN,
			multivalue=1,
			options=['posix'],
			required=0,
			may_change=1,
			dontsearch=1,
			identifies=0
		),
	'allowedEmailGroups': univention.admin.property(
			short_description=_('Groups that are allowed to send e-mails to the group'),
			long_description='',
			syntax=univention.admin.syntax.GroupDN,
			multivalue=1,
			options=['posix'],
			required=0,
			may_change=1,
			dontsearch=1,
			identifies=0
		)
}

layout = [
	Tab( _( 'General' ),_( 'Basic settings' ), layout = [
		Group( _( 'Group account' ), layout = [
			[ 'name', 'description' ],
		]),
		Group ( _('Members of this group'), layout = [
				'users',
				'nestedGroup'
		]),
		]),
	Tab( _( 'Mail' ), _( 'Mail settings of this group' ), advanced = True, layout = [
		'mailAddress', 
		'allowedEmailUsers',
		'allowedEmailGroups',
		] ),
	Tab( _( 'Host members' ), _( 'Host members of this group' ), advanced = True, layout = [
		'hosts'
		] ),
	Tab( _( 'Member of' ), _( 'Membership in other groups' ), advanced = True, layout = [
		'memberOf'
		] ),
	Tab( _( 'Group ID' ), _( 'ID of this group' ), advanced = True, layout = [
		'gidNumber',
		] ),
	Tab( _( 'Windows' ), _( 'Windows account settings' ), advanced = True, layout = [
		'sambaRID',
		'sambaGroupType',
		'sambaPrivileges'
		] )
]

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('sambaGroupType', 'sambaGroupType', None, univention.admin.mapping.ListToString)
mapping.register('mailAddress', 'mailPrimaryAddress', None, univention.admin.mapping.ListToString)
mapping.register('sambaPrivileges', 'univentionSambaPrivilegeList')

def _case_insensitive_in_list(dn, list):
	for element in list:
		if dn.decode('utf8').lower() == element.decode('utf8').lower():
			return True
	return False

def _case_insensitive_get_item_in_list(dn, list):
	for element in list:
		if dn.decode('utf8').lower() == element.decode('utf8').lower():
			return element
	return None

def _case_insensitive_remove_from_list(dn, list):
	remove_element = None
	for element in list:
		if dn.decode('utf8').lower() == element.decode('utf8').lower():
			remove_element = element
	if remove_element:
		list.remove(remove_element)
	return list

class AgingCache(object):
	def __new__(type, *args, **kwargs):
		# Falls es noch keine Instanz dieser Klasse gibt, wird eine erstellt und in _the_instance abgelegt.
		# Diese wird dann jedes mal zurückgegeben.
		if not '_the_instance' in type.__dict__:
			type._the_instance = object.__new__(type, *args, **kwargs)
		return type._the_instance

	def __init__(self):
		if not '_ready' in dir(self):
			self._ready = True
			self.timeout = 300
			self.data = {}
			self.timer = {}

	def is_valid(self, item):
		if item in self.timer:
			if self.timer.get(item,-1) > time.time():
				return True
			del self.timer[item]
			del self.data[item]
		return False

	def get(self, item):
		return self.data.get(item,{})

	def set(self, item, data):
		if not type(data) == dict:
			raise Exception('AgingCache.set() requires a dict as data value')
		self.data[item] = copy.deepcopy(data)
		self.timer[item] = time.time() + self.timeout

	def remove(self, item):
		if item in self.timer:
			del self.timer[item]
			del self.data[item]

	def set_timeout(self, timeout):
		self.timer = timeout

cache_uniqueMember = AgingCache()

class object(univention.admin.handlers.simpleLdap):
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes = [] ):
		global mapping
		global property_descriptions
		global s4connector_present

		self.mapping=mapping
		self.descriptions=property_descriptions

		self.alloc=[]

		# s4connector_present is a global caching variable than can be
		# None ==> ldap has not been checked for servers with service "S4 Connector"
		# True ==> at least one server with IP address (aRecord) is present
		# False ==> no server is present
		if s4connector_present == None:
			searchResult = lo.search('(&(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))(univentionService=S4 Connector))', attr = ['aRecord'])
			s4connector_present = True
			if not [ ddn for (ddn, attr) in searchResult if attr.has_key('aRecord') ]:
				s4connector_present = False

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate, attributes = attributes )

	def open(self):
		global options
		univention.admin.handlers.simpleLdap.open(self)

		try:
			caching_timeout = int(configRegistry.get('directory/manager/web/modules/groups/group/caching/uniqueMember/timeout','300'))
			self.cache_uniqueMember.set_timeout( caching_timeout )
		except:
			pass

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

			time_start = time.time()

			self['users']=self['hosts']=self['nestedGroup']=[]
			if self.oldattr.has_key('uniqueMember'):
				groupMembers=self.oldattr['uniqueMember']

				for i in groupMembers:
					if cache_uniqueMember.is_valid(i):
						membertype = cache_uniqueMember.get(i).get('type')
						if membertype == 'user':
							self['users'].append(i)
						elif membertype == 'group':
							self['nestedGroup'].append(i)
						elif membertype == 'host':
							self['hosts'].append(i)
					elif i.startswith('uid='):
						self['users'].append(i)
						cache_uniqueMember.set(i, { 'type': 'user' })
					else:
						result = self.lo.getAttr(i, 'objectClass' )
						if result:
							if 'univentionGroup' in result:
								self['nestedGroup'].append(i)
								cache_uniqueMember.set(i, { 'type': 'group' })
							elif 'univentionHost' in result:
								self['hosts'].append(i)
								cache_uniqueMember.set(i, { 'type': 'host' })
							else:
								self['users'].append(i)
						else:
							# removing following line breaks deletion of computers from groups
							self['users'].append(i)

			time_end = time.time()
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'groups/group: open(): member check duration: %1.2fs' % (time_end - time_start))


			self['allowedEmailUsers'] = []
			if self.oldattr.has_key('univentionAllowedEmailUsers'):
				self['allowedEmailUsers'] = self.oldattr['univentionAllowedEmailUsers']

			self['allowedEmailGroups'] = []
			if self.oldattr.has_key('univentionAllowedEmailGroups'):
				self['allowedEmailGroups'] = self.oldattr['univentionAllowedEmailGroups']

			self.save()

	def fast_member_add(self, memberdnlist, uidlist):
		ml = []
		uids = []
		members = []
		searchResult = self.lo.search(base=self.dn, attr=['uniqueMember','memberUid'])
		if searchResult:
			uids = searchResult[0][1].get('memberUid',[])
			members = searchResult[0][1].get('uniqueMember',[])

		add_uidlist = []
		for uid in uidlist:
			if uid and not _case_insensitive_in_list(uid, uids):
				add_uidlist.append( uid )
		if add_uidlist:
			ml.append( ( 'memberUid', '', add_uidlist ) )

		add_memberdnlist = []
		for memberdn in memberdnlist:
			if memberdn and not _case_insensitive_in_list(memberdn, members):
				add_memberdnlist.append(memberdn)
		if add_memberdnlist:
			ml.append( ( 'uniqueMember', '', add_memberdnlist ) )

		if ml:
			try:
				return self.lo.modify(self.dn, ml)
			except ldap.NO_SUCH_OBJECT, msg:
				raise univention.admin.uexceptions.noObject
			except ldap.INSUFFICIENT_ACCESS, msg:
				raise univention.admin.uexceptions.permissionDenied
			except ldap.LDAPError, msg:
				raise univention.admin.uexceptions.ldapError, msg[0]['desc']

		# return True if object has been modified
		return bool(ml)

	def fast_member_remove(self, memberdnlist, uidlist, ignore_license=0):
		ml = []
		uids = []
		members = []
		searchResult = self.lo.search(base=self.dn, attr=['uniqueMember','memberUid'])
		if searchResult:
			uids = searchResult[0][1].get('memberUid',[])
			members = searchResult[0][1].get('uniqueMember',[])

		remove_uidlist = []
		for uid in uidlist:
			if uid and _case_insensitive_in_list(uid, uids):
				remove_uidlist.append( _case_insensitive_get_item_in_list(uid, uids) )
		if remove_uidlist:
			ml.append( ( 'memberUid', remove_uidlist, '' ) )

		remove_memberdnlist = []
		for memberdn in memberdnlist:
			if memberdn and _case_insensitive_in_list(memberdn, members):
				remove_memberdnlist.append( _case_insensitive_get_item_in_list(memberdn, members) )
		if remove_memberdnlist:
			ml.append( ( 'uniqueMember', remove_memberdnlist, '' ) )

		if ml:
			try:
				return self.lo.modify(self.dn, ml, ignore_license=ignore_license)
			except ldap.NO_SUCH_OBJECT, msg:
				raise univention.admin.uexceptions.noObject
			except ldap.INSUFFICIENT_ACCESS, msg:
				raise univention.admin.uexceptions.permissionDenied
			except ldap.LDAPError, msg:
				raise univention.admin.uexceptions.ldapError, msg[0]['desc']

		# return True if object has been modified
		return bool(ml)

	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('name'), mapping.mapValue('name', self.info['name']), self.position.getDn())
		self.check_for_group_recursion()

	def _ldap_pre_modify(self):
		self.check_for_group_recursion()

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
				self.groupSid = self.__generate_group_sid(self.gidNum)

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

		if 'samba' in self.options:
			# samba privileges
			if self.hasChanged( 'sambaPrivileges' ):
				o = self.oldattr.get( 'objectClass', [] )
				# add univentionSambaPrivileges objectclass
				if self[ 'sambaPrivileges'] and not "univentionSambaPrivileges" in o:
					ml.insert( 0, ( 'objectClass', '', 'univentionSambaPrivileges' ) )

			if self.hasChanged('sambaRID') and not hasattr(self, 'groupSid'):
				self.groupSid = self.__generate_group_sid(self.oldattr['gidNumber'][0])
				ml.append(('sambaSID', self.oldattr.get('sambaSID', ['']), [self.groupSid]))
				self.update_sambaPrimaryGroupSid = True


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

		old = set( self.oldinfo.get( 'users', [] ) + self.oldinfo.get('hosts', []) + self.oldinfo.get('nestedGroup', []) )
		new = set( self.info.get('users', []) + self.info.get('hosts', []) + self.info.get('nestedGroup', []) )
		if old != new:
			# create lists for uniqueMember entries to be added or removed
			uniqueMemberAdd = list( new - old )    #  (new - old) ==> new set with elements in "new" but not in "old"
			uniqueMemberRemove = list( old - new ) #  (old - new) ==> new set with elements in "old" but not in "new"

			def getUidList(uniqueMembers):
				result = []
				for uniqueMember in uniqueMembers:
					if uniqueMember.startswith('uid='): # UID is stored in DN --> use UID directly
						result.append( univention.admin.uldap.explodeDn(uniqueMember, 1)[0] )
					else:
						# UID is not stored in DN --> fetch UID by DN
						uid_list = self.lo.getAttr(uniqueMember, 'uid')
						# a group have no uid attribute, see Bug #12644
						if len(uid_list) > 0:
							result.append( uid_list[0] )
							if len(uid_list) > 1:
								univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'groups/group: A groupmember has multiple UIDs (%s %s)' % (uniqueMember, str(uid_list)))
				return result

			def adaptCase( members, oldMembers ):
				newMembers = []
				oldMembers = tuple(  oldMembers )
				oldMembersLowerCase = map( lambda x: x.lower(), oldMembers )
				for member in map( lambda x: x.lower(), members ):
					found = -1
					for oldMember in oldMembersLowerCase:
						found += 1
						if member == oldMember:
							newMembers.append( oldMembers[ found ] )
							break

				return newMembers

			# create lists for memberUid entries to be added or removed
			memberUidAdd    = getUidList(uniqueMemberAdd)
			memberUidRemove = getUidList(uniqueMemberRemove)

			if uniqueMemberRemove:
				uniqueMemberRemove = adaptCase( uniqueMemberRemove, old )
				ml.append( ( 'uniqueMember', uniqueMemberRemove, '' ) )
			if uniqueMemberAdd:
				ml.append( ( 'uniqueMember', '', uniqueMemberAdd ) )
			if memberUidRemove:
				oldMemberUids = self.oldattr.get( 'memberUid', () ) 
				memberUidRemove = adaptCase( memberUidRemove, oldMemberUids )
				ml.append( ( 'memberUid', memberUidRemove, '' ) )
			if memberUidAdd:
				ml.append( ( 'memberUid', '', memberUidAdd ) )

		oldEmailUsers = self.oldinfo.get( 'allowedEmailUsers', [] )
		newEmailUsers = self.info.get( 'allowedEmailUsers', [] )
		if set(oldEmailUsers) != set(newEmailUsers): # compare sets since the order of values does not matter
			ml.append( ('univentionAllowedEmailUsers', oldEmailUsers, newEmailUsers) )

		oldEmailGroups = self.oldinfo.get( 'allowedEmailGroups', [] )
		newEmailGroups = self.info.get( 'allowedEmailGroups', [] )
		if set(oldEmailGroups) != set(newEmailGroups): # compare sets since the order of values does not matter
			ml.append( ('univentionAllowedEmailGroups', oldEmailGroups, newEmailGroups) )

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
		if hasattr(self, 'groupSid'):
			self._update_sambaPrimaryGroupSID(self.oldattr.get('sambaSID', [])[0], self.groupSid)

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

	def check_for_group_recursion(self):
		# perform check only if membership of groups has changed
		if not self.hasChanged('memberOf') and not self.hasChanged('nestedGroup'):
			return

		# perform check only if enabled via UCR
		if configRegistry.get('directory/manager/web/modules/groups/group/checks/circular_dependency','yes').lower() in ('no','false','0'):
			return

		grpdn2childgrpdns = {}
		grp_module=univention.admin.modules.get('groups/group')

		cn = self.info.get('name', 'UNKNOWN')

		# test self dependency
		# ==> nestedGroup or memberOf contains self.dn
		for field in ('nestedGroup', 'memberOf'):
			if self.dn.lower() in [ x.lower() for x in self.info.get(field,[]) ]:
				raise univention.admin.uexceptions.circularGroupDependency('%s ==> %s' % (cn, cn))

		# test short dependencies: A -> B -> A
		# ==> intersection of nestedGroup and memberOf is not empty
		set_nestedGroup = set( [ x.lower() for x in self.info.get('nestedGroup',[]) ] )
		set_memberOf = set( [ x.lower() for x in self.info.get('memberOf',[]) ] )
		set_intersection = set_nestedGroup & set_memberOf
		if set_intersection:
			childdn = list(set_intersection)[0]
			# get cn for first detected object
			childobj = univention.admin.objects.get(grp_module, self.co, self.lo, position='', dn=childdn)
			childcn = childobj.info.get('name','UNKNOWN')
			raise univention.admin.uexceptions.circularGroupDependency('%s ==> %s ==> %s' % (childcn, cn, childcn))

		# test long dependencies: A -> B -> C -> A
		if self.info.get('memberOf'):   # TODO: FIXME:  perform extended check only if self.hasChanged('memberOf') is True
			# if user added some groups to memberOf, the group objects specified in memberOf do not contain self als
			# uniqueMember (aka nestedGroup) when this test is performed. So this test has to perform the recursion check
			# with each member of memberOf as parent
			for upgrp in self.info.get('memberOf',[]):
				for subgrp in self.info.get('nestedGroup',[]):
					self._check_group_childs_for_recursion(grp_module, grpdn2childgrpdns, subgrp.lower(), [ upgrp.lower(), self.dn.lower() ])
		else:
			for subgrp in self.info.get('nestedGroup',[]):
				self._check_group_childs_for_recursion(grp_module, grpdn2childgrpdns, subgrp.lower(), [ self.dn.lower() ])


	def _check_group_childs_for_recursion(self, grp_module, grpdn2childgrpdns, dn, parents=[]):
		if not dn in grpdn2childgrpdns:
			grpobj = univention.admin.objects.get(grp_module, self.co, self.lo, position='', dn=dn)
			grpobj.open()
			childs = grpobj.info.get('nestedGroup',[])
			grpdn2childgrpdns[ dn ] = childs
		else:
			childs = grpdn2childgrpdns[ dn ]

		new_parents = parents + [ dn ]
		for childgrp in childs:
			if childgrp.lower() in new_parents:
				dnCircle = new_parents[ new_parents.index(childgrp.lower()): ] + [ childgrp.lower() ]
				cnCircle = []
				# get missing cn's if required
				grpdn2cn = { self.dn.lower(): self.info.get('name','UNKNOWN') }
				for x in dnCircle:
					if not x.lower() in grpdn2cn:
						xobj = univention.admin.objects.get(grp_module, self.co, self.lo, position='', dn=x)
						grpdn2cn[ x.lower() ] = xobj.info.get('name','UNKNOWN')
					cnCircle.append( grpdn2cn[x.lower()] )
				raise univention.admin.uexceptions.circularGroupDependency(' ==> '.join(cnCircle))

			self._check_group_childs_for_recursion(grp_module, grpdn2childgrpdns, childgrp.lower(), new_parents)

	def __generate_group_sid(self, gidNum):
		# TODO: cleanup function
		groupSid = None

		if self['sambaRID']:
			searchResult = self.lo.search(filter='objectClass=sambaDomain', attr=['sambaSID'])
			domainsid=searchResult[0][1]['sambaSID'][0]
			sid = domainsid+'-'+self['sambaRID']
			groupSid = univention.admin.allocators.request(self.lo, self.position, 'sid', sid)
			self.alloc.append(('sid', groupSid))
		else:
			num = self.gidNum
			if s4connector_present:
				# In this case Samba 4 must create the SID, the s4 connector will sync the
				# new sambaSID back from Samba 4.
				groupSid='S-1-4-%s' % num
			else:
				while not groupSid or groupSid == 'None':
					try:
						groupSid = univention.admin.allocators.requestGroupSid(self.lo, self.position, num)
					except univention.admin.uexceptions.noLock, e:
						num = str(int(num)+1)
				self.alloc.append(('sid', groupSid))
		return groupSid

	def _update_sambaPrimaryGroupSID(self, oldSid, newSid):
		if hasattr(self, 'update_sambaPrimaryGroupSid') and self.update_sambaPrimaryGroupSid:
			res = self.lo.search('sambaPrimaryGroupSID=%s' % oldSid, attr=['sambaPrimaryGroupSID'])
			for dn,attr in res:
				self.lo.modify(dn, [ ('sambaPrimaryGroupSID', attr.get('sambaPrimaryGroupSID', []), [newSid]) ] )
			self.update_sambaPrimaryGroupSid = False

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
	for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit):
		res.append( object( co, lo, None, dn, attributes = attrs ) )
	return res

def identify(dn, attr, canonical=0):

	return 'univentionGroup' in attr.get('objectClass', [])
