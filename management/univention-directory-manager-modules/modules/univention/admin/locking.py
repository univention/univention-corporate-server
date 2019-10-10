# -*- coding: utf-8 -*-
"""
|LDAP| locking methods for |UDM|.
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
import time

import univention.debug as ud
import univention.admin.uexceptions
from univention.admin import localization

translation = localization.translation('univention/admin')
_ = translation.translate


def lockDn(lo, position, type, value, scope):
	"""
	Build |DN| of lock object.

	:param lo: |LDAP| connection.
	:param position: |UDM| position specifying the |LDAP| base container.
	:param type: A string describing the type of object, e.g. `user`.
	:param value: A unique value for the object, e.g. `uid`.
	:param scope: The scope for the lock, e.g. `domain`.
	:returns: A |LDAP| |DN|.
	"""
	dn = [
		[('cn', value, ldap.AVA_STRING)],
		[('cn', type, ldap.AVA_STRING)],
		[('cn', 'temporary', ldap.AVA_STRING)],
		[('cn', 'univention', ldap.AVA_STRING)],
	]
	if scope == 'domain':
		dn += ldap.dn.str2dn(position.getDomain())
	else:
		dn += ldap.dn.str2dn(position.getBase())
	return ldap.dn.dn2str(dn)


def lock(lo, position, type, value, scope='domain', timeout=300):
	"""
	Lock an |UDM| object.

	:param lo: |LDAP| connection.
	:param position: |UDM| position specifying the |LDAP| base container.
	:param type: A string describing the type of object, e.g. `user`.
	:param value: A unique value for the object, e.g. `uid`.
	:param scope: The scope for the lock, e.g. `domain`.
	:param timeout: Number of seconds for the lock being valid.
	:raises univention.admin.uexceptions.permissionDenied: if the lock time cannot be modified.
	:raises univention.admin.uexceptions.noLock: if the lock cannot be acquired.
	:returns: Number of seconds since the UNIX epoch until which the lock is acquired.
	"""
	_d = ud.function('admin.locking.lock type=%s value=%s scope=%s timeout=%d' % (type, value, scope, timeout))  # noqa: F841
	dn = lockDn(lo, position, type, value, scope)

	now = int(time.time())
	if timeout > 0:
		locktime = now + timeout
	else:
		locktime = 0
	al = [
		('objectClass', ['top', 'lock']),
		('cn', [value]),
		('lockTime', [str(locktime)]),
	]
	if not lo.get(dn, ['lockTime']):
		try:
			lo.add(dn, al)
			return locktime
		except ldap.ALREADY_EXISTS:
			pass
		except univention.admin.uexceptions.permissionDenied:
			raise univention.admin.uexceptions.permissionDenied(_('Can not modify lock time of %r.') % (dn,))

	oldlocktime = lo.getAttr(dn, 'lockTime')
	if oldlocktime and oldlocktime[0]:
		oldlocktime = int(oldlocktime[0])
	else:
		oldlocktime = 0

	# lock is old, try again
	if oldlocktime > 0 and oldlocktime < now:
		ml = [
			('lockTime', str(oldlocktime), str(locktime))
		]
		try:
			lo.modify(dn, ml, exceptions=True)
			return locktime
		except ldap.INSUFFICIENT_ACCESS:
			raise univention.admin.uexceptions.permissionDenied(_('Can not modify lock time of %r.') % (dn,))

	raise univention.admin.uexceptions.noLock(_('The attribute %r could not get locked.') % (type,))


def relock(lo, position, type, value, scope='domain', timeout=300):
	"""
	Extend a lock of an |UDM| object.

	:param lo: |LDAP| connection.
	:param position: |UDM| position specifying the |LDAP| base container.
	:param type: A string describing the type of object, e.g. `user`.
	:param value: A unique value for the object, e.g. `uid`.
	:param scope: The scope for the lock, e.g. `domain`.
	:param timeout: Number of seconds for the lock being valid.
	:raises univention.admin.uexceptions.permissionDenied: if the lock time cannot be modified.
	:raises univention.admin.uexceptions.noLock: if the lock was not acquired.
	:returns: Number of seconds since the UNIX epoch until which the lock is acquired.
	"""
	_d = ud.function('admin.locking.relock type=%s value=%s scope=%s timeout=%d' % (type, value, scope, timeout))  # noqa: F841
	dn = lockDn(lo, position, type, value, scope)

	now = int(time.time())
	if timeout > 0:
		locktime = now + timeout
	else:
		locktime = 0
	ml = [
		('lockTime', 1, str(locktime))
	]
	try:
		lo.modify(dn, ml, exceptions=True)
		return locktime
	except ldap.INSUFFICIENT_ACCESS:
		raise univention.admin.uexceptions.permissionDenied(_('Can not modify lock time of %r.') % (dn,))

	# locking failed
	raise univention.admin.uexceptions.noLock(_('The attribute %r could not get locked.') % (type,))


def unlock(lo, position, type, value, scope='domain'):
	"""
	Unlock an |UDM| object.

	:param lo: |LDAP| connection.
	:param position: |UDM| position specifying the |LDAP| base container.
	:param type: A string describing the type of object, e.g. `user`.
	:param value: A unique value for the object, e.g. `uid`.
	:param scope: The scope for the lock, e.g. `domain`.
	"""
	_d = ud.function('admin.locking.unlock type=%s value=%s scope=%s' % (type, value, scope))  # noqa: F841
	dn = lockDn(lo, position, type, value, scope)
	try:
		lo.delete(dn, exceptions=True)
	except ldap.NO_SUCH_OBJECT:
		pass


def getLock(lo, position, type, value, scope='domain'):
	"""
	Check if an |UDM| object is locked.

	:param lo: |LDAP| connection.
	:param position: |UDM| position specifying the |LDAP| base container.
	:param type: A string describing the type of object, e.g. `user`.
	:param value: A unique value for the object, e.g. `uid`.
	:param scope: The scope for the lock, e.g. `domain`.
	:returns: Number of seconds since the UNIX epoch until which the lock is acquired or `0`.
	"""
	dn = lockDn(lo, position, type, value, scope)
	try:
		return int(lo.getAttr(dn, 'lockTime', exceptions=True)[0])
	except ldap.NO_SUCH_OBJECT:
		return 0
