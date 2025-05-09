#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|LDAP| locking methods for |UDM|."""

import time

import ldap

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
    dn = lockDn(lo, position, type, value.decode('utf-8'), scope)

    now = int(time.time())
    locktime = now + timeout if timeout > 0 else 0

    al = [
        ('objectClass', [b'top', b'lock']),
        ('cn', [value]),
        ('lockTime', [str(locktime).encode('ascii')]),
    ]
    if not lo.authz_connection.get(dn, ['lockTime']):
        try:
            lo.authz_connection.add(dn, al)
            return locktime
        except ldap.ALREADY_EXISTS:
            pass
        except univention.admin.uexceptions.permissionDenied:
            raise univention.admin.uexceptions.permissionDenied(_('Can not modify lock time of %r.') % (dn,))

    oldlocktime = lo.authz_connection.getAttr(dn, 'lockTime')
    oldlocktime = int(oldlocktime[0]) if oldlocktime and oldlocktime[0] else 0

    # lock is old, try again
    if oldlocktime > 0 and oldlocktime < now:
        ml = [
            ('lockTime', str(oldlocktime).encode('ascii'), str(locktime).encode('ascii')),
        ]
        try:
            lo.authz_connection.modify(dn, ml, exceptions=True)
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
    dn = lockDn(lo, position, type, value.decode('utf-8'), scope)

    now = int(time.time())
    locktime = now + timeout if timeout > 0 else 0
    ml = [
        ('lockTime', b'1', str(locktime).encode('ASCII')),
    ]
    try:
        lo.authz_connection.modify(dn, ml, exceptions=True)
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
    dn = lockDn(lo, position, type, value.decode('utf-8'), scope)
    try:
        lo.authz_connection.delete(dn, exceptions=True)
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
    dn = lockDn(lo, position, type, value.decode('utf-8'), scope)
    try:
        return int(lo.authz_connection.getAttr(dn, 'lockTime', exceptions=True)[0])
    except ldap.NO_SUCH_OBJECT:
        return 0
