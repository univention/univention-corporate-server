# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  allocator access
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

import univention.debug
import univention.admin.locking
import univention.admin.localization
import univention.admin.uexceptions

translation=univention.admin.localization.translation('univention/admin')
_=translation.translate

_type2attr = {	'uidNumber':			'uidNumber',
				'gidNumber':			'gidNumber',
				'uid':					'uid',
				'gid':					'gid',
				'sid':					'sambaSID',
				'domainSid':			'sambaSID',
				'mailPrimaryAddress':	'mailPrimaryAddress',
				'aRecord':				'aRecord',
				'mac':					'macAddress',
				'groupName':			'cn' }
_type2scope = {	'uidNumber':			'base',
				'gidNumber':			'base',
				'uid':					'domain',
				'gid':					'domain',
				'sid':					'base',
				'domainSid':			'base',
				'mailPrimaryAddress':	'domain',
				'aRecord':				'domain',
				'mac':					'domain',
				'groupName':			'domain' }
	

def requestUserSid(lo, position, uid_s):
	uid=int(uid_s)
	algorithmical_rid_base=1000
	rid=str(uid*2+algorithmical_rid_base)
	
	searchResult=lo.search(filter='objectClass=sambaDomain', attr=['sambaSID'])
	domainsid=searchResult[0][1]['sambaSID'][0]
	sid=domainsid+'-'+rid

	univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'ALLOCATE: request user sid. SID = %s-%s' % (domainsid,rid))
	
	return request(lo, position, 'sid', sid)


def requestGroupSid(lo, position, gid_s):
	gid=int(gid_s)
	algorithmical_rid_base=1000
	rid=str(gid*2+algorithmical_rid_base+1)

	searchResult=lo.search(filter='objectClass=sambaDomain', attr=['sambaSID'])
	domainsid=searchResult[0][1]['sambaSID'][0]
	sid=domainsid+'-'+rid
	
	return request(lo, position, 'sid', sid)


def acquireRange(lo, position, type, attr, ranges, scope='base'):

	univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'ALLOCATE: Start allocation for type = %s' % (type))
	startID = lo.getAttr('cn=%s,cn=temporary,cn=univention,%s' % (type,position.getBase()),'univentionLastUsedValue')

	univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'ALLOCATE: Start ID = %s' % (startID))

	if not startID:
		startID = ranges[0]['first']
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'ALLOCATE: Set Start ID to first %s' % (startID))
	else:
		startID = startID[0]

	for range in ranges:
		if int(startID) < range['first']:
			startID = range['first']
		last = range['last']
		while int(startID) < last+1:
			startID = int(startID)+1
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'ALLOCATE: Set Start ID %s' % (startID))
			try:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'ALLOCATE: Lock ID %s' % (startID))
				univention.admin.locking.lock(lo, position, type, str(startID), scope=scope)
			except univention.admin.uexceptions.noLock:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'ALLOCATE: Cant Lock ID %s' % (startID))
				continue
			except univention.admin.uexceptions.objectExists:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'ALLOCATE: Cant Lock existing ID %s' % (startID))
				continue
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'ALLOCATE: searchfor %s=%s' % (attr,startID))

			if lo.searchDn(base=position.getBase(), filter='(%s=%s)'%(attr,str(startID))):
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'ALLOCATE: Already used ID %s' % (startID))
				univention.admin.locking.unlock(lo, position, type, str(startID), scope=scope)
				continue

			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'ALLOCATE: Return ID %s' % (startID))
			return str(startID)

	raise univention.admin.uexceptions.noLock, _(': type was %s')%type


def acquireUnique(lo, position, type, value, attr, scope='base'):
	univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'LOCK acquireUnique scope = %s' % scope)
	if scope=='domain':
		searchBase=position.getDomain()
	else:
		searchBase=position.getBase()

	if type=="aRecord": # uniqueness is only relevant among hosts (one or more dns entrys having the same aRecord as a host are allowed)
		univention.admin.locking.lock(lo, position, type, value, scope=scope)
		if not lo.searchDn(base=searchBase, filter='(&(objectClass=univentionHost)(%s=%s))' % (attr, value)):
			return value
	elif type == "groupName": # search filter is more complex then in general case
		univention.admin.locking.lock(lo, position, type, value, scope=scope)
		if not lo.searchDn(base=searchBase, filter='(&(%s=%s)(|(objectClass=univentionGroup)(objectClass=sambaGroupMapping)(objectClass=posixGroup)))' % (attr, value)):
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'ALLOCATE return %s'% value)
			return value
	else:
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'LOCK univention.admin.locking.lock scope = %s' % scope)
		univention.admin.locking.lock(lo, position, type, value, scope=scope)
		if not lo.searchDn(base=searchBase, filter='%s=%s' % (attr, value)):
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'ALLOCATE return %s'% value)
			return value
	
	raise univention.admin.uexceptions.noLock, _(': type was %s')%type


def request(lo, position, type, value=None):
	if type in ( 'uidNumber', 'gidNumber' ):
		return acquireRange(lo, position, type, _type2attr[type], [{'first':1000,'last':55000},{'first':65536,'last':1000000}], scope = _type2scope[type])
	return acquireUnique(lo, position, type, value, _type2attr[type], scope = _type2scope[type])


def confirm(lo, position, type, value):
	if type in ( 'uidNumber', 'gidNumber' ):
		startID = lo.modify('cn=%s,cn=temporary,cn=univention,%s' % (type,position.getBase()),[('univentionLastUsedValue','1', value)])
	univention.admin.locking.unlock(lo, position, type, value, _type2scope[type])


def release(lo, position, type, value):
	univention.admin.locking.unlock(lo, position, type, value, _type2scope[type])

