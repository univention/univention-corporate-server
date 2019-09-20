# -*- coding: utf-8 -*-
"""
|UDM| allocators to allocate and lock resources for |LDAP| object creation.
"""
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

import ldap
from ldap.filter import filter_format

import univention.debug as ud
import univention.admin.locking
import univention.admin.uexceptions
from univention.admin import localization
from univention.admin import configRegistry

translation = localization.translation('univention/admin')
_ = translation.translate

_type2attr = {
	'uidNumber': 'uidNumber',
	'gidNumber': 'gidNumber',
	'uid': 'uid',
	'gid': 'gid',
	'sid': 'sambaSID',
	'domainSid': 'sambaSID',
	'mailPrimaryAddress': 'mailPrimaryAddress',
	'aRecord': 'aRecord',
	'mac': 'macAddress',
	'groupName': 'cn'
}
_type2scope = {
	'uidNumber': 'base',
	'gidNumber': 'base',
	'uid': 'domain',
	'gid': 'domain',
	'sid': 'base',
	'domainSid': 'base',
	'mailPrimaryAddress': 'domain',
	'aRecord': 'domain',
	'mac': 'domain',
	'groupName': 'domain'
}


def requestUserSid(lo, position, uid_s):
	uid = int(uid_s)
	algorithmical_rid_base = 1000
	rid = str(uid * 2 + algorithmical_rid_base)

	searchResult = lo.search(filter='objectClass=sambaDomain', attr=['sambaSID'])
	domainsid = searchResult[0][1]['sambaSID'][0]
	sid = domainsid + '-' + rid

	ud.debug(ud.ADMIN, ud.INFO, 'ALLOCATE: request user sid. SID = %s-%s' % (domainsid, rid))

	return request(lo, position, 'sid', sid)


def requestGroupSid(lo, position, gid_s, generateDomainLocalSid=False):
	gid = int(gid_s)
	algorithmical_rid_base = 1000
	rid = str(gid * 2 + algorithmical_rid_base + 1)

	if generateDomainLocalSid:
		sid = 'S-1-5-32-' + rid
	else:
		searchResult = lo.search(filter='objectClass=sambaDomain', attr=['sambaSID'])
		domainsid = searchResult[0][1]['sambaSID'][0]
		sid = domainsid + '-' + rid

	return request(lo, position, 'sid', sid)


def acquireRange(lo, position, atype, attr, ranges, scope='base'):

	ud.debug(ud.ADMIN, ud.INFO, 'ALLOCATE: Start allocation for type = %r' % atype)
	startID = lo.getAttr('cn=%s,cn=temporary,cn=univention,%s' % (ldap.dn.escape_dn_chars(atype), position.getBase()), 'univentionLastUsedValue')

	ud.debug(ud.ADMIN, ud.INFO, 'ALLOCATE: Start ID = %r' % startID)

	if not startID:
		startID = ranges[0]['first']
		ud.debug(ud.ADMIN, ud.INFO, 'ALLOCATE: Set Start ID to first %r' % startID)
	else:
		startID = int(startID[0])

	for _range in ranges:
		if startID < _range['first']:
			startID = _range['first']
		last = _range['last'] + 1
		other = None

		while startID < last:
			startID += 1
			ud.debug(ud.ADMIN, ud.INFO, 'ALLOCATE: Set Start ID %r' % startID)
			try:
				if other:
					# exception occurred while locking other, so atype was successfully locked and must be released
					univention.admin.locking.unlock(lo, position, atype, str(startID - 1), scope=scope)
					other = None
				ud.debug(ud.ADMIN, ud.INFO, 'ALLOCATE: Lock ID %r for %r' % (startID, atype))
				univention.admin.locking.lock(lo, position, atype, str(startID), scope=scope)
				if atype in ('uidNumber', 'gidNumber'):
					# reserve the same ID for both
					other = 'uidNumber' if atype == 'gidNumber' else 'gidNumber'
					ud.debug(ud.ADMIN, ud.INFO, 'ALLOCATE: Lock ID %r for %r' % (startID, other))
					univention.admin.locking.lock(lo, position, other, str(startID), scope=scope)
			except univention.admin.uexceptions.noLock:
				ud.debug(ud.ADMIN, ud.INFO, 'ALLOCATE: Cannot Lock ID %r' % startID)
				continue
			except univention.admin.uexceptions.objectExists:
				ud.debug(ud.ADMIN, ud.INFO, 'ALLOCATE: Cannot Lock existing ID %r' % startID)
				continue

			if atype in ('uidNumber', 'gidNumber'):
				_filter = filter_format('(|(uidNumber=%s)(gidNumber=%s))', (str(startID), str(startID)))
			else:
				_filter = '(%s=%d)' % (attr, startID)
			ud.debug(ud.ADMIN, ud.INFO, 'ALLOCATE: searchfor %r' % _filter)
			if lo.searchDn(base=position.getBase(), filter=_filter):
				ud.debug(ud.ADMIN, ud.INFO, 'ALLOCATE: Already used ID %r' % startID)
				univention.admin.locking.unlock(lo, position, atype, str(startID), scope=scope)
				if other:
					univention.admin.locking.unlock(lo, position, other, str(startID), scope=scope)
					other = None
				continue

			ud.debug(ud.ADMIN, ud.INFO, 'ALLOCATE: Return ID %r' % startID)
			if other:
				univention.admin.locking.unlock(lo, position, other, str(startID), scope=scope)
			return str(startID)

	raise univention.admin.uexceptions.noLock(_('The attribute %r could not get locked.') % (atype,))


def acquireUnique(lo, position, type, value, attr, scope='base'):
	ud.debug(ud.ADMIN, ud.INFO, 'LOCK acquireUnique scope = %s' % scope)
	if scope == 'domain':
		searchBase = position.getDomain()
	else:
		searchBase = position.getBase()

	if type == "aRecord":  # uniqueness is only relevant among hosts (one or more dns entries having the same aRecord as a host are allowed)
		univention.admin.locking.lock(lo, position, type, value, scope=scope)
		if not lo.searchDn(base=searchBase, filter=filter_format('(&(objectClass=univentionHost)(%s=%s))', (attr, value))):
			return value
	elif type in ['groupName', 'uid'] and configRegistry.is_true('directory/manager/user_group/uniqueness', True):
		univention.admin.locking.lock(lo, position, type, value, scope=scope)
		if not lo.searchDn(base=searchBase, filter=filter_format('(|(&(cn=%s)(|(objectClass=univentionGroup)(objectClass=sambaGroupMapping)(objectClass=posixGroup)))(uid=%s))', (value, value))):
			ud.debug(ud.ADMIN, ud.INFO, 'ALLOCATE return %s' % value)
			return value
	elif type == "groupName":  # search filter is more complex then in general case
		univention.admin.locking.lock(lo, position, type, value, scope=scope)
		if not lo.searchDn(base=searchBase, filter=filter_format('(&(%s=%s)(|(objectClass=univentionGroup)(objectClass=sambaGroupMapping)(objectClass=posixGroup)))', (attr, value))):
			ud.debug(ud.ADMIN, ud.INFO, 'ALLOCATE return %s' % value)
			return value
	else:
		ud.debug(ud.ADMIN, ud.INFO, 'LOCK univention.admin.locking.lock scope = %s' % scope)
		univention.admin.locking.lock(lo, position, type, value, scope=scope)
		if not lo.searchDn(base=searchBase, filter=filter_format('%s=%s', (attr, value))):
			ud.debug(ud.ADMIN, ud.INFO, 'ALLOCATE return %s' % value)
			return value

	raise univention.admin.uexceptions.noLock(_('The attribute %r could not get locked.') % (type,))


def request(lo, position, type, value=None):
	if type in ('uidNumber', 'gidNumber'):
		return acquireRange(lo, position, type, _type2attr[type], [{'first': 1000, 'last': 55000}, {'first': 65536, 'last': 1000000}], scope=_type2scope[type])
	return acquireUnique(lo, position, type, value, _type2attr[type], scope=_type2scope[type])


def confirm(lo, position, type, value, updateLastUsedValue=True):
	if type in ('uidNumber', 'gidNumber') and updateLastUsedValue:
		lo.modify('cn=%s,cn=temporary,cn=univention,%s' % (ldap.dn.escape_dn_chars(type), position.getBase()), [('univentionLastUsedValue', '1', value)])
	univention.admin.locking.unlock(lo, position, type, value, _type2scope[type])


def release(lo, position, type, value):
	univention.admin.locking.unlock(lo, position, type, value, _type2scope[type])
