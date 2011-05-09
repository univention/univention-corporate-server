# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  LDAP locking methods
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

import ldap, time
import univention.debug
import univention.admin.uexceptions

def lockDn(lo, position, type, value, scope):
	dn = [ [('cn', value,        ldap.AVA_STRING)],
	       [('cn', type,         ldap.AVA_STRING)],
	       [('cn', 'temporary',  ldap.AVA_STRING)],
	       [('cn', 'univention', ldap.AVA_STRING)],
	       ]
	if scope == 'domain':
		dn += ldap.dn.str2dn(position.getDomain())
	else:
		dn += ldap.dn.str2dn(position.getBase())
	return ldap.dn.dn2str(dn)

def lock(lo, position, type, value, scope='domain', timeout=300):

	_d=univention.debug.function('admin.locking.lock type=%s value=%s scope=%s timeout=%d' % (type, value, scope, timeout))
	dn=lockDn(lo, position, type, value, scope)

	now=int(time.time())
	if timeout > 0:
		locktime=now+timeout
	else:
		locktime=0
	al=[
		('objectClass', ['top', 'lock']),
		('cn', [value]),
		('lockTime', [str(locktime)]),
	]
	if not lo.get(dn, ['lockTime']):
		try:
			lo.add(dn, al, exceptions=0)
			return locktime
		except ldap.ALREADY_EXISTS:
			pass
		except univention.admin.uexceptions.permissionDenied, e:
			raise e
		else:
			raise univention.admin.uexceptions.noLock, _(': type was %s')%type

	oldlocktime=lo.getAttr(dn, 'lockTime')
	if oldlocktime and oldlocktime[0]:
		oldlocktime=int(oldlocktime[0])
	else:
		oldlocktime=0

	# lock is old, try again
	if oldlocktime > 0 and oldlocktime < now:
		ml=[
			('lockTime', str(oldlocktime), str(locktime))
		]
		try:
			lo.modify(dn, ml, exceptions=1)
			return locktime
		except 'f':
			pass
	
	# locking failed
	raise univention.admin.uexceptions.noLock

def relock(lo, position, type, value, scope='domain', timeout=300):

	_d=univention.debug.function('admin.locking.relock type=%s value=%s scope=%s timeout=%d' % (type, value, scope, timeout))
	dn=lockDn(lo, position, type, value, scope)

	now=int(time.time())
	if timeout > 0:
		locktime=now+timeout
	else:
		locktime=0
	ml=[
		('lockTime', 1, str(locktime))
	]
	try:
		lo.modify(dn, ml, exceptions=1)
		return locktime
	except 'f':
		pass
	
	# locking failed
	raise univention.admin.uexceptions.noLock

def unlock(lo, position, type, value, scope='domain'):
	
	_d=univention.debug.function('admin.locking.unlock type=%s value=%s scope=%s' % (type, value, scope))
	dn=lockDn(lo, position, type, value, scope)
	try:
		lo.delete(dn, exceptions=1)
	except ldap.NO_SUCH_OBJECT:
		pass
	
def getLock(lo, position, type, value, scope='domain'):
	dn=lockDn(lo, position, type, value, scope)
	try:
		return int(lo.getAttr(dn, 'lockTime', exceptions=1)[0])
	except ldap.NO_SUCH_OBJECT:
		return 0


