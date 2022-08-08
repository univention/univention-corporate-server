# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
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
|UDM| module for groups
"""

import copy
import time
import ldap
from ldap.filter import filter_format

import univention.admin
from univention.admin.layout import Tab, Group
import univention.admin.uldap
import univention.admin.filter
import univention.admin.handlers
import univention.admin.allocators
import univention.admin.localization
import univention.debug as ud
from univention.admin import configRegistry
from univention.admin.uldap import DN

translation = univention.admin.localization.translation('univention.admin.handlers.groups')
_ = translation.translate

module = 'groups/group'
operations = ['add', 'edit', 'remove', 'search', 'move', 'copy']
childs = False
short_description = _('Group')
object_name = _('Group')
object_name_plural = _('Groups')
long_description = ''
options = {
	'default': univention.admin.option(
		short_description=short_description,
		default=True,
		objectClasses=['top', 'univentionGroup'],
	),
	'posix': univention.admin.option(
		short_description=_('Posix group'),
		default=1,
		objectClasses=('posixGroup',),
	),
	'samba': univention.admin.option(
		short_description=_('Samba group'),
		default=1,
		objectClasses=('sambaGroupMapping',),
	)
}

property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description='',
		syntax=univention.admin.syntax.gid,
		include_in_default_search=True,
		required=True,
		identifies=True,
		readonly_when_synced=True,
	),
	'gidNumber': univention.admin.property(
		short_description=_('Group ID'),
		long_description='',
		syntax=univention.admin.syntax.integer,
		may_change=False,
		options=['posix', 'samba']
	),
	'sambaRID': univention.admin.property(
		short_description=_('Relative ID'),
		long_description='',
		syntax=univention.admin.syntax.integer,
		readonly_when_synced=True,
		options=['samba']
	),
	'sambaGroupType': univention.admin.property(
		short_description=_('Windows group type'),
		long_description='',
		syntax=univention.admin.syntax.sambaGroupType,
		default=('2', []),
		options=['samba'],
		copyable=True,
	),
	'sambaPrivileges': univention.admin.property(
		short_description=_('Samba privilege'),
		long_description=_('Manage samba privileges'),
		syntax=univention.admin.syntax.SambaPrivileges,
		multivalue=True,
		options=['samba'],
		copyable=True,
	),
	'adGroupType': univention.admin.property(
		short_description=_('AD group type'),
		long_description=_('Active Directory group type'),
		syntax=univention.admin.syntax.adGroupType,
		options=['samba'],
		default=('-2147483646', []),
		dontsearch=True,
		readonly_when_synced=True,
		copyable=True,
	),
	'description': univention.admin.property(
		short_description=_('Description'),
		long_description='',
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
		options=['posix', 'samba'],
		readonly_when_synced=True,
		copyable=True,
	),
	'users': univention.admin.property(
		short_description=_('Users'),
		long_description='',
		syntax=univention.admin.syntax.UserDN,
		multivalue=True,
		options=['posix'],
		dontsearch=True,
		readonly_when_synced=True,
		copyable=True,
	),
	'hosts': univention.admin.property(
		short_description=_('Hosts'),
		long_description='',
		syntax=univention.admin.syntax.HostDN,
		multivalue=True,
		options=['posix'],
		license=['UGS', 'UCS'],
		dontsearch=True,
		readonly_when_synced=True,
		copyable=True,
	),
	'mailAddress': univention.admin.property(
		short_description=_('Mail address'),
		long_description='',
		syntax=univention.admin.syntax.emailAddressValidDomain,
		include_in_default_search=True,
		options=['posix'],
		readonly_when_synced=True,
	),
	'memberOf': univention.admin.property(
		short_description=_('Member of'),
		long_description='',
		syntax=univention.admin.syntax.GroupDN,
		multivalue=True,
		options=['posix'],
		dontsearch=True,
		readonly_when_synced=True,
		copyable=True,
	),
	'nestedGroup': univention.admin.property(
		short_description=_('Groups'),
		long_description='',
		syntax=univention.admin.syntax.GroupDN,
		multivalue=True,
		options=['posix'],
		dontsearch=True,
		readonly_when_synced=True,
		copyable=True,
	),
	'allowedEmailUsers': univention.admin.property(
		short_description=_('Users that are allowed to send e-mails to the group'),
		long_description='',
		syntax=univention.admin.syntax.UserDN,
		multivalue=True,
		options=['posix'],
		dontsearch=True,
		copyable=True,
	),
	'allowedEmailGroups': univention.admin.property(
		short_description=_('Groups that are allowed to send e-mails to the group'),
		long_description='',
		syntax=univention.admin.syntax.GroupDN,
		multivalue=True,
		options=['posix'],
		dontsearch=True,
		copyable=True,
	)
}

layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('Group account'), layout=[
			['name', 'description'],
		]),
		Group(_('Members of this group'), layout=[
			'users',
			'nestedGroup'
		]),
	]),
	Tab(_('Mail'), _('Mail settings of this group'), advanced=True, layout=[
		'mailAddress',
		'allowedEmailUsers',
		'allowedEmailGroups',
	]),
	Tab(_('Host members'), _('Host members of this group'), advanced=True, layout=[
		'hosts'
	]),
	Tab(_('Member of'), _('Membership in other groups'), advanced=True, layout=[
		'memberOf'
	]),
	Tab(_('Group ID'), _('ID of this group'), advanced=True, layout=[
		'gidNumber',
	]),
	Tab(_('Windows'), _('Windows account settings'), advanced=True, layout=[
		'sambaRID',
		'sambaGroupType',
		'adGroupType',
		'sambaPrivileges'
	]),
	Tab('Apps'),  # not translated!
]


def unmapSambaRid(oldattr):
	sid = oldattr.get('sambaSID', [b''])[0].decode('ASCII')
	sid, has_rid, rid = sid.rpartition(u'-')
	if has_rid and rid.isdigit():
		return rid


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('gidNumber', 'gidNumber', None, univention.admin.mapping.ListToString, encoding='ASCII')
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('sambaGroupType', 'sambaGroupType', None, univention.admin.mapping.ListToString)
mapping.register('mailAddress', 'mailPrimaryAddress', None, univention.admin.mapping.ListToString, encoding='ASCII')
mapping.register('adGroupType', 'univentionGroupType', None, univention.admin.mapping.ListToString)
mapping.register('sambaPrivileges', 'univentionSambaPrivilegeList', encoding='ASCII')
mapping.register('allowedEmailUsers', 'univentionAllowedEmailUsers')
mapping.register('allowedEmailGroups', 'univentionAllowedEmailGroups')
mapping.registerUnmapping('sambaRID', unmapSambaRid)


class AgingCache(object):

	def __new__(type, *args, **kwargs):
		# Falls es noch keine Instanz dieser Klasse gibt, wird eine erstellt und in _the_instance abgelegt.
		# Diese wird dann jedes mal zurückgegeben.
		if '_the_instance' not in type.__dict__:
			type._the_instance = object.__new__(type, *args, **kwargs)
		return type._the_instance

	def __init__(self):
		if '_ready' not in dir(self):
			self._ready = True
			self.timeout = 300
			self.data = {}
			self.timer = {}

	def is_valid(self, item):
		if item in self.timer:
			if self.timer.get(item, -1) > time.time():
				return True
			del self.timer[item]
			del self.data[item]
		return False

	def get(self, item):
		return self.data.get(item, {})

	def set(self, item, data):
		if not isinstance(data, dict):
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
	module = module

	def open(self):
		univention.admin.handlers.simpleLdap.open(self)

		try:
			caching_timeout = int(configRegistry.get('directory/manager/web/modules/groups/group/caching/uniqueMember/timeout', '300'))
			self.cache_uniqueMember.set_timeout(caching_timeout)
		except Exception:
			pass

		if self.exists():
			self['memberOf'] = self.lo.searchDn(filter=filter_format('(&(objectClass=posixGroup)(uniqueMember=%s))', [self.dn]))

			time_start = time.time()

			self['users'] = []
			self['hosts'] = []
			self['nestedGroup'] = []
			for i in [x.decode('utf-8') for x in self.oldattr.get('uniqueMember', [])]:
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
					cache_uniqueMember.set(i, {'type': 'user'})
				else:
					result = self.lo.getAttr(i, 'objectClass')
					if result:
						if b'univentionGroup' in result:
							self['nestedGroup'].append(i)
							cache_uniqueMember.set(i, {'type': 'group'})
						elif b'univentionHost' in result:
							self['hosts'].append(i)
							cache_uniqueMember.set(i, {'type': 'host'})
						elif set(result) & {b'person', b'inetOrgPerson', b'organizationalPerson'}:
							self['users'].append(i)
						elif b'univentionUserTemplate' in result:
							continue
						else:
							raise RuntimeError('%s not detected: %r' % (i, result))

			time_end = time.time()
			ud.debug(ud.ADMIN, ud.INFO, 'groups/group: open(): member check duration: %1.2fs' % (time_end - time_start))

			self.save()

	def fast_member_add(self, memberdnlist, uidlist):
		ml = []
		uids = set()
		members = set()
		searchResult = self.lo.get(self.dn, attr=['uniqueMember', 'memberUid'])
		if searchResult:
			uids = {x.decode('UTF-8').lower() for x in searchResult.get('memberUid', [])}
			members = {x.decode('UTF-8').lower() for x in searchResult.get('uniqueMember', [])}

		add_uidlist = [uid for uid in uidlist if uid.lower() not in uids]
		if add_uidlist:
			ml.append(('memberUid', b'', [x.encode('UTF-8') for x in add_uidlist]))

		add_memberdnlist = [dn for dn in memberdnlist if dn.lower() not in members]

		if add_memberdnlist:
			ml.append(('uniqueMember', b'', [x.encode('UTF-8') for x in add_memberdnlist]))

		if ml:
			try:
				return self.lo.modify(self.dn, ml)
			except ldap.NO_SUCH_OBJECT:
				raise univention.admin.uexceptions.noObject(self.dn)
			except ldap.INSUFFICIENT_ACCESS:
				raise univention.admin.uexceptions.permissionDenied()
			except ldap.LDAPError as msg:
				raise univention.admin.uexceptions.ldapError(msg.args[0]['desc'])

		# return True if object has been modified
		return bool(ml)

	def fast_member_remove(self, memberdnlist, uidlist, ignore_license=False, _retry_on_attribute_error=True):
		ml = []
		uids = set()
		members = set()
		searchResult = self.lo.get(self.dn, attr=['uniqueMember', 'memberUid'])
		if searchResult:
			uids = {x.decode('UTF-8').lower() for x in searchResult.get('memberUid', [])}
			members = {x.decode('UTF-8').lower() for x in searchResult.get('uniqueMember', [])}

		remove_uidlist = [uid for uid in uidlist if uid.lower() in uids]
		if remove_uidlist:
			ml.append(('memberUid', [x.encode('UTF-8') for x in remove_uidlist], b''))

		remove_memberdnlist = [dn for dn in memberdnlist if dn.lower() in members]
		if remove_memberdnlist:
			ml.append(('uniqueMember', [x.encode('UTF-8') for x in remove_memberdnlist], b''))

		if ml:
			try:
				try:
					return self.lo.modify(self.dn, ml, exceptions=True, ignore_license=ignore_license)
				except ldap.NO_SUCH_ATTRIBUTE:
					# maybe this is the refint overlay:
					# uniqueMember has already been removed. lets try again, probably with just memberUid...
					if not _retry_on_attribute_error:
						raise
					return self.fast_member_remove(memberdnlist, uidlist, ignore_license=ignore_license, _retry_on_attribute_error=False)
			except ldap.NO_SUCH_OBJECT:
				raise univention.admin.uexceptions.noObject(self.dn)
			except ldap.INSUFFICIENT_ACCESS:
				raise univention.admin.uexceptions.permissionDenied()
			except ldap.LDAPError as msg:
				raise univention.admin.uexceptions.ldapError(msg.args[0]['desc'])

		# return True if object has been modified
		return bool(ml)

	def _check_uid_gid_uniqueness(self):
		if not configRegistry.is_true("directory/manager/uid_gid/uniqueness", True):
			return
		if "posix" in self.options or "samba" in self.options:
			fg = univention.admin.filter.expression('uidNumber', self['gidNumber'], escape=True)
			user_objects = univention.admin.handlers.users.user.lookup(self.co, self.lo, filter_s=fg)
			if user_objects:
				raise univention.admin.uexceptions.gidNumberAlreadyUsedAsUidNumber(repr(self["gidNumber"]))

	def _ldap_pre_ready(self):
		super(object, self)._ldap_pre_ready()

		# get lock for name
		if not self.exists() or self.hasChanged('name') and self['name'].lower() != self.oldinfo['name'].lower():
			try:
				self.request_lock('groupName', self['name'])
			except univention.admin.uexceptions.noLock:
				raise univention.admin.uexceptions.groupNameAlreadyUsed(self['name'])

		# get lock for mailPrimaryAddress
		if self['mailAddress'] and (not self.exists() or self.hasChanged('mailAddress') and self['mailAddress'].lower() != self.oldinfo.get('mailAddress', '').lower()):
			try:
				self.request_lock('mailPrimaryAddress', self['mailAddress'])
			except univention.admin.uexceptions.noLock:
				raise univention.admin.uexceptions.mailAddressUsed(self['mailAddress'])

	def _ldap_pre_create(self):
		super(object, self)._ldap_pre_create()

		if self['gidNumber']:
			univention.admin.allocators.acquireUnique(self.lo, self.position, 'gidNumber', self['gidNumber'], 'gidNumber', scope='base')
			self.alloc.append(('gidNumber', self['gidNumber'], False))
		else:
			self['gidNumber'] = self.request_lock('gidNumber')

		self.check_for_group_recursion()
		self._check_uid_gid_uniqueness()

	def _ldap_pre_modify(self):
		super(object, self)._ldap_pre_modify()
		self.check_for_group_recursion()
		self.check_ad_group_type_change()

		if self.hasChanged('gidNumber'):
			# this should never happen, as gidNumber is marked as unchangeable
			self._check_uid_gid_uniqueness()

	def _ldap_addlist(self):
		al = super(object, self)._ldap_addlist()

		if 'posix' not in self.options:
			al.append(('objectClass', b'organizationalRole'))  # any STRUCTURAL class with 'cn'

		return al

	def _ldap_modlist(self):
		ml = univention.admin.handlers.simpleLdap._ldap_modlist(self)

		self._samba_sid = None
		if 'samba' in self.options:
			# samba privileges
			if self.hasChanged('sambaPrivileges'):
				o = self.oldattr.get('objectClass', [])
				# add univentionSambaPrivileges objectclass
				if self['sambaPrivileges'] and b'univentionSambaPrivileges' not in o:
					ml.insert(0, ('objectClass', b'', b'univentionSambaPrivileges'))

			# samba SID
			if self['gidNumber'] and not self.exists() or self.hasChanged('sambaRID'):
				sid = self.__generate_group_sid(self['gidNumber'])
				ml.append(('sambaSID', self.oldattr.get('sambaSID', [b'']), [sid.encode('ASCII')]))
				self._samba_sid = sid

		old = DN.set(self.oldinfo.get('users', []) + self.oldinfo.get('hosts', []) + self.oldinfo.get('nestedGroup', []))
		new = DN.set(self.info.get('users', []) + self.info.get('hosts', []) + self.info.get('nestedGroup', []))
		if old != new:
			# create lists for uniqueMember entries to be added or removed
			uniqueMemberAdd = list(DN.values(new - old))
			uniqueMemberRemove = list(DN.values(old - new))
			old = list(DN.values(old))
			new = list(DN.values(new))

			def getUidList(uniqueMembers):
				result = []
				for uniqueMember in uniqueMembers:
					dn = ldap.dn.str2dn(uniqueMember)[0]
					try:
						result.append([x[1] for x in dn if x[0].lower() == 'uid'][0])
					except IndexError:
						# UID is not stored in DN --> fetch UID by DN
						uid_list = self.lo.getAttr(uniqueMember, 'uid')
						# a group have no uid attribute, see Bug #12644
						if uid_list:
							result.append(uid_list[0].decode('UTF-8'))
							if len(uid_list) > 1:
								ud.debug(ud.ADMIN, ud.WARN, 'groups/group: A groupmember has multiple UIDs (%s %r)' % (uniqueMember, uid_list))
				return result

			# calling keepCase is not necessary as the LDAP server already handles the case when removing elements
			# TODO: removable?
			def keepCase(members, oldMembers):
				mapping = {x.lower(): x for x in oldMembers}
				return [mapping.get(member.lower(), member) for member in members]

			# create lists for memberUid entries to be added or removed
			memberUidAdd = getUidList(uniqueMemberAdd)
			memberUidRemove = getUidList(uniqueMemberRemove)

			if uniqueMemberRemove:
				uniqueMemberRemove = keepCase(uniqueMemberRemove, old)
				uniqueMemberRemove = [x.encode('UTF-8') for x in uniqueMemberRemove]
				ml.append(('uniqueMember', uniqueMemberRemove, ''))

			if uniqueMemberAdd:
				uniqueMemberAdd = [x.encode('UTF-8') for x in uniqueMemberAdd]
				ml.append(('uniqueMember', '', uniqueMemberAdd))

			oldMemberUids = [x.decode('UTF-8') for x in self.oldattr.get('memberUid', ())]
			if memberUidRemove:
				memberUidRemove = keepCase(memberUidRemove, oldMemberUids)
				memberUidRemove = [x.encode('UTF-8') for x in memberUidRemove]
				ml.append(('memberUid', memberUidRemove, ''))

			if memberUidAdd:
				memberUidAdd = [x.encode('UTF-8') for x in memberUidAdd]
				ml.append(('memberUid', '', memberUidAdd))

		return ml

	def _ldap_post_create(self):
		super(object, self)._ldap_post_create()
		self.__update_membership()

	def _ldap_post_modify(self):
		super(object, self)._ldap_post_modify()
		self.__update_membership()
		old_sid = self.oldattr.get('sambaSID', [b''])[0].decode('ASCII')
		if self._samba_sid and self._samba_sid != old_sid:
			for dn, attr in self.lo.search(ldap.filter.filter_format('(sambaPrimaryGroupSID=%s)', [old_sid]), attr=['sambaPrimaryGroupSID']):
				self.lo.modify(dn, [('sambaPrimaryGroupSID', attr.get('sambaPrimaryGroupSID', []), [self._samba_sid.encode('ASCII')])])

	def _ldap_pre_remove(self):
		super(object, self)._ldap_pre_remove()
		self.open()
		# is this group in mentioned in settings/default?
		try:
			dn, attrs = self.lo.search(filter='objectClass=univentionDefault', base=self.position.getDomain(), scope='domain', unique=True, required=True)[0]
		except ldap.NO_SUCH_OBJECT:
			pass
		else:
			for attr, value in attrs.items():
				if attr.lower().endswith('group') and self.dn.encode('UTF-8') in value:
					raise univention.admin.uexceptions.primaryGroupUsed(_('It is used as %s.') % attr)

		gidNum = None
		groupSid = None
		if 'posix' in self.old_options:
			gidNum = self.oldattr['gidNumber'][0].decode('ASCII')
			if self.lo.searchDn(base=self.position.getDomain(), filter=filter_format('(&(objectClass=person)(gidNumber=%s))', [gidNum]), scope='domain'):
				raise univention.admin.uexceptions.primaryGroupUsed(gidNum)
		if 'samba' in self.old_options:
			groupSid = self.oldattr['sambaSID'][0].decode('ASCII')
			if self.lo.searchDn(base=self.position.getDomain(), filter=filter_format('(&(objectClass=person)(sambaPrimaryGroupSID=%s))', [groupSid]), scope='domain'):
				raise univention.admin.uexceptions.primaryGroupUsed(groupSid)
		if gidNum:
			self.alloc.append(('gidNumber', gidNum))
		if groupSid:
			self.alloc.append(('sid', groupSid))
		self.alloc.append(('groupName', self.oldattr['cn'][0].decode('UTF-8')))
		if self.oldattr.get('mailPrimaryAddress'):
			self.alloc.append(('mailPrimaryAddress', self.oldattr['mailPrimaryAddress'][0].decode('UTF-8')))

	def _ldap_post_remove(self):
		super(object, self)._ldap_post_remove()
		for group in self.info.get('memberOf', []):
			if isinstance(group, list):
				group = group[0]
			members = [x.decode('UTF-8') for x in self.lo.getAttr(group, 'uniqueMember')]
			if not self.__case_insensitive_in_list(self.dn, members):
				continue
			newmembers = copy.deepcopy(members)
			newmembers = self.__case_insensitive_remove_from_list(self.dn, newmembers)
			ud.debug(ud.ADMIN, ud.INFO, 'groups/group: remove from supergroup %s' % group)
			self.__set_membership_attributes(group, members, newmembers)

	def _ldap_post_move(self, olddn):
		super(object, self)._ldap_post_move(olddn)
		settings_module = univention.admin.modules.get('settings/default')
		settings_object = univention.admin.objects.get(settings_module, None, self.lo, position='', dn='cn=default,cn=univention,%s' % self.lo.base)
		settings_object.open()
		for attr in ['defaultGroup', 'defaultMemberServerGroup', 'defaultClientGroup', 'defaultDomainControllerMBGroup', 'defaultDomainControllerGroup', 'defaultComputerGroup']:
			if settings_object[attr].lower() == olddn.lower():
				settings_object[attr] = self.dn
		settings_object.modify()

		for group in self.info.get('memberOf', []):
			if isinstance(group, list):
				group = group[0]
			members = [x.decode('UTF-8') for x in self.lo.getAttr(group, 'uniqueMember')]
			if not self.__case_insensitive_in_list(olddn, members):
				continue
			newmembers = copy.deepcopy(members)
			newmembers = self.__case_insensitive_remove_from_list(olddn, newmembers)
			newmembers.append(self.dn)
			ud.debug(ud.ADMIN, ud.INFO, 'groups/group: updating supergroup %s' % group)
			self.__set_membership_attributes(group, members, newmembers)

	def __update_membership(self):

		if self.exists():
			old_groups = self.oldinfo.get('memberOf', [])
			old_name = self.oldinfo.get('name', '')
			new_name = self.info.get('name', '')
		else:
			old_groups = []
			old_name = ""
			new_name = ""

		# rewrite membership attributes in "supergroup" if we have a new name (rename)
		if old_name and old_name != new_name:
			ud.debug(ud.ADMIN, ud.INFO, 'groups/group: rewrite memberuid after rename')
			for group in self.info.get('memberOf', []):
				if isinstance(group, list):
					group = group[0]
				members = [x.decode('UTF-8') for x in self.lo.getAttr(group, 'uniqueMember')]
				newmembers = copy.deepcopy(members)
				newmembers = self.__case_insensitive_remove_from_list(self.old_dn, newmembers)
				newmembers.append(self.dn)
				self.__set_membership_attributes(group, members, newmembers)

		add_to_group = []
		remove_from_group = []

		for group in old_groups:
			if group and not self.__case_insensitive_in_list(group, self.info.get('memberOf', [])):
				remove_from_group.append(group)

		for group in self.info.get('memberOf', []):
			if group and not self.__case_insensitive_in_list(group, old_groups):
				add_to_group.append(group)

		for group in add_to_group:
			if isinstance(group, list):
				group = group[0]
			members = [x.decode('UTF-8') for x in self.lo.getAttr(group, 'uniqueMember')]
			if self.__case_insensitive_in_list(self.dn, members):
				continue
			newmembers = copy.deepcopy(members)
			newmembers.append(self.dn)
			ud.debug(ud.ADMIN, ud.INFO, 'groups/group: add to supergroup %s' % group)
			self.__set_membership_attributes(group, members, newmembers)

		for group in remove_from_group:
			if isinstance(group, list):
				group = group[0]
			members = [x.decode('UTF-8') for x in self.lo.getAttr(group, 'uniqueMember')]
			newmembers = copy.deepcopy(members)
			if self.__case_insensitive_in_list(self.dn, members):
				newmembers = self.__case_insensitive_remove_from_list(self.dn, newmembers)
			if self.__case_insensitive_in_list(self.old_dn, newmembers):
				newmembers = self.__case_insensitive_remove_from_list(self.old_dn, newmembers)
			if members != newmembers:
				ud.debug(ud.ADMIN, ud.INFO, 'groups/group: remove from supergroup %s' % group)
				self.__set_membership_attributes(group, members, newmembers)

	def __set_membership_attributes(self, group, members, newmembers):
		members_bytes = [x.encode('UTF-8') for x in members]
		newmembers_bytes = [x.encode('UTF-8') for x in newmembers]
		self.lo.modify(group, [('uniqueMember', members_bytes, newmembers_bytes)])
		# don't set the memberUid attribute for nested groups, see Bug #11868
		# uids = self.lo.getAttr( group, 'memberUid' )
		# newuids = map(lambda x: x[x.find('=') + 1: x.find(',')], newmembers)
		# self.lo.modify( group, [ ( 'memberUid', uids, newuids ) ] )

	@staticmethod
	def __case_insensitive_in_list(dn, members):
		return dn.lower() in (x.lower() for x in members)

	@staticmethod
	def __case_insensitive_remove_from_list(dn, members):
		dn_lower = dn.lower()
		return [x for x in members if x.lower() != dn_lower]

	def check_for_group_recursion(self):
		# perform check only if membership of groups has changed
		if not self.hasChanged('memberOf') and not self.hasChanged('nestedGroup'):
			return

		# perform check only if enabled via UCR
		if configRegistry.get('directory/manager/web/modules/groups/group/checks/circular_dependency', 'yes').lower() in ('no', 'false', '0'):
			return

		grpdn2childgrpdns = {}
		grp_module = univention.admin.modules.get('groups/group')

		cn = self.info.get('name', 'UNKNOWN')

		# test self dependency
		# ==> nestedGroup or memberOf contains self.dn
		for field in ('nestedGroup', 'memberOf'):
			if self.dn.lower() in (x.lower() for x in self.info.get(field, [])):
				raise univention.admin.uexceptions.circularGroupDependency('%s ==> %s' % (cn, cn))

		# test short dependencies: A -> B -> A
		# ==> intersection of nestedGroup and memberOf is not empty
		set_nestedGroup = {x.lower() for x in self.info.get('nestedGroup', [])}
		set_memberOf = {x.lower() for x in self.info.get('memberOf', [])}
		set_intersection = set_nestedGroup & set_memberOf
		if set_intersection:
			childdn = list(set_intersection)[0]
			# get cn for first detected object
			childobj = univention.admin.objects.get(grp_module, self.co, self.lo, position='', dn=childdn)
			childcn = childobj.info.get('name', 'UNKNOWN')
			raise univention.admin.uexceptions.circularGroupDependency('%s ==> %s ==> %s' % (childcn, cn, childcn))

		# test long dependencies: A -> B -> C -> A
		if self.info.get('memberOf'):   # TODO: FIXME:  perform extended check only if self.hasChanged('memberOf') is True
			# if user added some groups to memberOf, the group objects specified in memberOf do not contain self as
			# uniqueMember (aka nestedGroup) when this test is performed. So this test has to perform the recursion check
			# with each member of memberOf as parent
			for upgrp in self.info.get('memberOf', []):
				for subgrp in self.info.get('nestedGroup', []):
					self._check_group_childs_for_recursion(grp_module, grpdn2childgrpdns, subgrp.lower(), [upgrp.lower(), self.dn.lower()])
		else:
			for subgrp in self.info.get('nestedGroup', []):
				self._check_group_childs_for_recursion(grp_module, grpdn2childgrpdns, subgrp.lower(), [self.dn.lower()])

	def _check_group_childs_for_recursion(self, grp_module, grpdn2childgrpdns, dn, parents=[]):
		if dn not in grpdn2childgrpdns:
			grpobj = univention.admin.objects.get(grp_module, self.co, self.lo, position='', dn=dn)
			grpobj.open()
			childs = grpobj.info.get('nestedGroup', [])
			grpdn2childgrpdns[dn] = childs
		else:
			childs = grpdn2childgrpdns[dn]

		new_parents = parents + [dn]
		for childgrp in childs:
			if childgrp.lower() in new_parents:
				dnCircle = new_parents[new_parents.index(childgrp.lower()):] + [childgrp.lower()]
				cnCircle = []
				# get missing cn's if required
				grpdn2cn = {self.dn.lower(): self.info.get('name', 'UNKNOWN')}
				for x in dnCircle:
					if not x.lower() in grpdn2cn:
						xobj = univention.admin.objects.get(grp_module, self.co, self.lo, position='', dn=x)
						grpdn2cn[x.lower()] = xobj.info.get('name', 'UNKNOWN')
					cnCircle.append(grpdn2cn[x.lower()])
				raise univention.admin.uexceptions.circularGroupDependency(' ==> '.join(cnCircle))

			self._check_group_childs_for_recursion(grp_module, grpdn2childgrpdns, childgrp.lower(), new_parents)

	def __is_groupType_universal(self, adGroupType):
		try:
			return int(adGroupType) & 0x8
		except ValueError:
			return False

	def __is_groupType_global(self, adGroupType):
		try:
			return int(adGroupType) & 0x2
		except ValueError:
			return False

	def __is_groupType_domain_local(self, adGroupType):
		try:
			return int(adGroupType) & 0x4
		except ValueError:
			return False

	def __is_groupType_local(self, adGroupType):
		try:
			return int(adGroupType) & 0x1
		except ValueError:
			return False

	def _is_global_member(self):
		searchResult = self.lo.search(base=self.position.getDomain(), filter=filter_format('(uniqueMember=%s)', [self.dn]), attr=['univentionGroupType'])
		for (dn, attr) in searchResult:
			groupType = attr.get('univentionGroupType', [None])[0]
			if self.__is_groupType_global(groupType):
				return True
		return False

	def _has_domain_local_member(self):
		for member_dn in [x.decode('UTF-8') for x in self.oldattr.get('uniqueMember', [])]:
			searchResult = self.lo.getAttr(member_dn, 'univentionGroupType')
			if searchResult:
				if self.__is_groupType_domain_local(searchResult[0]):
					return True
		return False

	def _has_universal_member(self):
		for member_dn in [x.decode('UTF-8') for x in self.oldattr.get('uniqueMember', [])]:
			searchResult = self.lo.getAttr(member_dn, 'univentionGroupType')
			if searchResult:
				if self.__is_groupType_universal(searchResult[0]):
					return True
		return False

	def check_ad_group_type_change(self):
		if not self.hasChanged('adGroupType'):
			return

		old_groupType = self.oldinfo.get('adGroupType', 0)
		new_groupType = self.info.get('adGroupType', 0)

		ud.debug(ud.ADMIN, ud.INFO, 'groups/group: old_groupType: %s' % old_groupType)
		ud.debug(ud.ADMIN, ud.INFO, 'groups/group: new_groupType: %s' % new_groupType)

		if not old_groupType or not new_groupType:
			return

		if self.__is_groupType_local(old_groupType):
			raise univention.admin.uexceptions.adGroupTypeChangeLocalToAny

		if self.__is_groupType_local(new_groupType):
			raise univention.admin.uexceptions.adGroupTypeChangeToLocal

		# See for details:
		#  http://technet.microsoft.com/en-us/library/cc755692%28v=ws.10%29.aspx

		if self.__is_groupType_global(old_groupType) and self.__is_groupType_domain_local(new_groupType):
			raise univention.admin.uexceptions.adGroupTypeChangeGlobalToDomainLocal
		elif self.__is_groupType_domain_local(old_groupType) and self.__is_groupType_global(new_groupType):
			raise univention.admin.uexceptions.adGroupTypeChangeDomainLocalToGlobal
		elif self.__is_groupType_global(old_groupType) and self.__is_groupType_universal(new_groupType):
			# Global to universal:
			#  This conversion is allowed only if the group that you want to change is not a member of
			#  another global scope group.
			if self._is_global_member():
				raise univention.admin.uexceptions.adGroupTypeChangeGlobalToUniversal
		elif self.__is_groupType_domain_local(old_groupType) and self.__is_groupType_universal(new_groupType):
			# Domain local to universal:
			#  This conversion is allowed only if the group that you want to change does not have
			#  another domain local group as a member.
			if self._has_domain_local_member():
				raise univention.admin.uexceptions.adGroupTypeChangeDomainLocalToUniversal
		elif self.__is_groupType_universal(old_groupType) and self.__is_groupType_global(new_groupType):
			# Universal to global:
			#  This conversion is allowed only if the group that you want to change does not have
			#  another universal group as a member.
			if self._has_universal_member():
				raise univention.admin.uexceptions.adGroupTypeChangeUniversalToGlobal

	def __allocate_rid(self, rid):
		searchResult = self.lo.search(filter='objectClass=sambaDomain', attr=['sambaSID'])
		new_groupType = self.info.get('adGroupType', 0)
		if self.__is_groupType_local(new_groupType):
			sid = u'S-1-5-32-' + self['sambaRID']
		else:
			domainsid = searchResult[0][1]['sambaSID'][0].decode('ASCII')
			sid = domainsid + u'-' + rid
		try:
			return self.request_lock('sid', sid)
		except univention.admin.uexceptions.noLock:
			raise univention.admin.uexceptions.sidAlreadyUsed(rid)

	def __generate_group_sid(self, gidNum):
		new_groupType = self.info.get('adGroupType', 0)

		ud.debug(ud.ADMIN, ud.INFO, 'groups/group: new_groupType: %s' % new_groupType)
		if self['sambaRID']:
			return self.__allocate_rid(self['sambaRID'])
		elif self.s4connector_present and not self.__is_groupType_local(new_groupType):
			# In this case Samba 4 must create the SID, the s4 connector will sync the
			# new sambaSID back from Samba 4.
			return u'S-1-4-%s' % (gidNum,)

		num = gidNum
		generateDomainLocalSid = self.__is_groupType_local(new_groupType)
		while True:
			try:
				groupSid = univention.admin.allocators.requestGroupSid(self.lo, self.position, num, generateDomainLocalSid=generateDomainLocalSid)
				self.alloc.append(('sid', groupSid))
				return groupSid
			except univention.admin.uexceptions.noLock:
				num = str(int(num) + 1)

	@classmethod
	def unmapped_lookup_filter(cls):
		return univention.admin.filter.conjunction('&', [
			univention.admin.filter.expression('cn', '*', escape=False),
			univention.admin.filter.conjunction('|', [
				univention.admin.filter.conjunction('&', [univention.admin.filter.expression('objectClass', 'univentionGroup'), ]),
				univention.admin.filter.conjunction('&', [univention.admin.filter.expression('objectClass', 'sambaGroupMapping'), ])
			])
		])


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
