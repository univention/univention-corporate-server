# -*- coding: utf-8 -*-
#
# Univention RADIUS 802.1X
#  NTLM-Authentication program
#
# Copyright (C) 2012-2014 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of the software contained in this package
# as well as the source package itself are made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this package provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use the software under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

import operator
import time
import univention.admin.filter
import univention.config_registry

userToGroup = {} # { "user": ["group1", "group2", ], }
groupInfo = {} # { "group1": (23, True, ), }
whitelisting = None
def loadInfo():
	global whitelisting
	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()
	whitelisting = configRegistry.is_true('radius/mac/whitelisting')
	for key in configRegistry:
		if key.startswith('proxy/filter/usergroup/'):
			group = key[len('proxy/filter/usergroup/'):]
			users = configRegistry[key].split(',')
			for user in users:
				if user not in userToGroup:
					userToGroup[user] = []
				userToGroup[user].append(group)
		elif key.startswith('proxy/filter/groupdefault/'):
			group = key[len('proxy/filter/groupdefault/'):]
			rule = configRegistry[key]
			priority = 0
			try:
				priority = int(configRegistry.get('proxy/filter/setting/%s/priority' % (rule, ), ''))
			except ValueError:
				pass
			wlanEnabled = configRegistry.is_true('proxy/filter/setting/%s/wlan' % (rule, ))
			if wlanEnabled is not None:
				groupInfo[group] = (priority, wlanEnabled, )

def checkProxyFilterPolicy(username):
	groups = userToGroup.get(username)
	if groups is None:
		return False
	groups = [groupInfo[group] for group in groups if group in groupInfo]
	if not groups:
		return False
	(maxPriority, _, ) = max(groups)
	if not True in [wlanEnabled for (priority, wlanEnabled, ) in groups if priority == maxPriority]:
		return False
	return True

def traceProxyFilterPolicy(username):
	message = ''
	groups = userToGroup.get(username)
	if groups is None:
		return False, 'User %r not found\n\n' % (username, )
	groupInfos = [groupInfo[group] for group in groups if group in groupInfo]
	if groupInfos:
		(maxPriority, _, ) = max(groupInfos)
	else:
		maxPriority = None
	for group in groups:
		if group in groupInfo:
			(priority, wlanEnabled, ) = groupInfo[group]
			if priority == maxPriority:
				if wlanEnabled:
					message += '-> Group %r: ALLOW (priority %r)\n' % (group, priority, )
				else:
					message += '-> Group %r: DENY (priority %r)\n' % (group, priority, )
			else:
				if wlanEnabled:
					message += '-> Group %r: allow (ignored) (priority %r)\n' % (group, priority, )
				else:
					message += '-> Group %r: deny (ignored) (priority %r)\n' % (group, priority, )
		else:
			message += '-> Group %r: not specified\n' % (group, )
	if not True in [wlanEnabled for (priority, wlanEnabled, ) in groupInfos if priority == maxPriority]:
		return False, message + '\n'
	else:
		return True, message + '\n'

def curried(function):
	return lambda args: function(*args)

def concat(list_of_lists):
	'''concatenate all lists in a list of lists into one list'''
	return reduce(operator.add, list_of_lists, [])

@curried
def checkAccessAttribute(dn, attributes):
	access = attributes.get('univentionNetworkAccess')
	if access == ['1']:
		return dn, True
	if access == ['0']:
		return dn, False
	return dn, False

def reducePolicies(policies):
	'''evaluate list of same-level policy values ("or" == allow trumps deny)'''
	return reduce(operator.or_, policies)

def filterPolicyGroups(groupPolicies):
	policies = [policy for (groupDn, policy) in groupPolicies]
	groupsWithout = [groupDn for (groupDn, policy) in groupPolicies]
	return policies, groupsWithout

def findUser(ldapConnection, uid):
	return ldapConnection.search(filter=str(univention.admin.filter.expression('uid', uid)), attr=['univentionNetworkAccess'])

def findStation(ldapConnection, station):
	station = ':'.join([byte.encode('hex') for byte in station])
	return ldapConnection.search(filter=str(univention.admin.filter.expression('macAddress', station)), attr=['univentionNetworkAccess'])

def findDnGroups(ldapConnection, dn):
	return ldapConnection.search(filter=str(univention.admin.filter.expression('uniqueMember', dn)), attr=['univentionNetworkAccess'])

def evaluateLdapPolicies(ldapConnection, searchResult):
	def _findDnGroups(dn):
		return findDnGroups(ldapConnection, dn)
	policies, groupsWithoutPolicy = filterPolicyGroups(map(checkAccessAttribute, searchResult))
	if policies:
		policy = reducePolicies(policies)
	else:
		policy = False
	if groupsWithoutPolicy:
		return policy or evaluateLdapPolicies(ldapConnection, concat(map(_findDnGroups, groupsWithoutPolicy)))
	else:
		return policy

def traceLdapPolicies(ldapConnection, searchResult, level=''):
	def _findDnGroups(dn):
		return findDnGroups(ldapConnection, dn)
	@curried
	def formatPolicyGroup(group, policy):
		if policy == True:
			return level + 'ALLOW %r' % (group, )
		if policy == False:
			return level + 'DENY %r' % (group, )
		return ''
	policyGroups = map(checkAccessAttribute, searchResult)
	message = '\n'.join(filter(None, map(formatPolicyGroup, policyGroups)))
	if message:
		message += '\n'
	policies, groupsWithoutPolicy = filterPolicyGroups(policyGroups)
	if groupsWithoutPolicy:
		# build message tree-like
		for group in groupsWithoutPolicy:
			message += level + '%r\n' % (group, )
			_, messages = traceLdapPolicies(ldapConnection, _findDnGroups(group), level=level + '-> ')
			message += messages
		# but evaluate result collapsed
		result, _ = traceLdapPolicies(ldapConnection, concat(map(_findDnGroups, groupsWithoutPolicy)))
		if result is not None:
			policies.append(result)
	if not policies:
		return False, message
	if reducePolicies(policies):
		return True, message
	else:
		return False, message

def checkNetworkAccess(ldapConnection, username):
	result = findUser(ldapConnection, username)
	if not result:
		return False
	return evaluateLdapPolicies(ldapConnection, result)

def checkStationWhitelist(ldapConnection, stationId):
	if not whitelisting:
		return True
	result = findStation(ldapConnection, stationId)
	if not result:
		return False
	return evaluateLdapPolicies(ldapConnection, result)

def traceNetworkAccess(ldapConnection, username):
	if userToGroup or groupInfo: # proxy UCRV set, UCS@school mode
		resultProxy, message = traceProxyFilterPolicy(username)
	else:
		resultProxy, message = False, ''
	result = findUser(ldapConnection, username)
	if result:
		resultLdap, messageLdap = traceLdapPolicies(ldapConnection, result)
	else:
		resultLdap, messageLdap = False, 'User %r does not exist\n' % (username, )
	message += messageLdap + '\n'
	if bool(resultProxy or resultLdap):
		message += 'Thus access for user is ALLOWED.\n'
	else:
		message += 'Thus access for user is DENIED.\n'
	return bool(resultProxy or resultLdap), message

def traceStationWhitelist(ldapConnection, stationId):
	result = findStation(ldapConnection, stationId)
	if result:
		result, message = traceLdapPolicies(ldapConnection, result)
	else:
		result, message = False, 'Station %r does not exist\n' % (':'.join([byte.encode('hex') for byte in stationId]), )
	if not whitelisting:
		message += 'MAC filtering is disabled by radius/mac/whitelisting.\n'
		result = True
	if result is None:
		message += '\nThus access for station is DENIED by default.\n'
	elif result:
		message += '\nThus access for station is ALLOWED.\n'
	else:
		message += '\nThus access for station is DENIED.\n'
	return bool(result), message

SAMBA_ACCOUNT_FLAG_DISABLED = 'D'
SAMBA_ACCOUNT_FLAG_LOCKED = 'L'
DISALLOWED_SAMBA_ACCOUNT_FLAGS = frozenset((SAMBA_ACCOUNT_FLAG_DISABLED, SAMBA_ACCOUNT_FLAG_LOCKED, ))

def parseUsername(username):
	'''convert username from host/-format to $-format if required'''
	if not username.startswith('host/'):
		return username
	username = username.split('/', 1)[1] # remove host/
	username = username.split('.', 1)[0] # remove right of '.'
	return username + '$'

def getNTPasswordHash(ldapConnection, username, stationId):
	'stationId may be None if it was not supplied to the program'
	username = parseUsername(username)
	if userToGroup or groupInfo: # proxy UCRV set, UCS@school mode
		if not (checkProxyFilterPolicy(username) or checkNetworkAccess(ldapConnection, username)):
			return None
	else: # UCS mode
		if not checkNetworkAccess(ldapConnection, username):
			return None
	if not checkStationWhitelist(ldapConnection, stationId):
		return None
	# user is authorized to use the W-LAN, retrieve NT-password-hash from LDAP and return it
	result = ldapConnection.search(filter=str(univention.admin.filter.expression('uid', username)), attr=['sambaNTPassword', 'sambaAcctFlags'])
	if not result:
		return None
	sambaAccountFlags = frozenset(result[0][1]['sambaAcctFlags'][0])
	if sambaAccountFlags & DISALLOWED_SAMBA_ACCOUNT_FLAGS:
		return None
	return result[0][1]['sambaNTPassword'][0].decode('hex')

loadInfo()
