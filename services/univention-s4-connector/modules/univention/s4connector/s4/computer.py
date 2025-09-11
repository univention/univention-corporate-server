#!/usr/bin/python3
#
# Univention S4 Connector
#  computer object helper functions
#
# SPDX-FileCopyrightText: 2013-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from logging import getLogger

import univention.s4connector.s4
from univention.logging import Structured


log = Structured(getLogger("LDAP").getChild(__name__))


def _shouldBeMacClient(attributes):
    if not attributes:
        return False

    return b'Mac OS X' in attributes.get('operatingSystem', [])  # FIXME: shouldn't it be univentionOperationSystem?! # FIXME: macOS ?


def _isAlreadyMac(attributes):
    if not attributes:
        return False

    return b'computers/macos' in attributes.get('univentionObjectType', [])


def _replaceListElement(le, oldValue, newValue):
    return [x if x != oldValue else newValue for x in le]


def _convertWinToMac(s4connector, sync_object):
    modlist = []

    ucs_object = s4connector.get_ucs_ldap_object(sync_object['dn'])

    oldObjectClass = ucs_object.get('objectClass')
    newObjectClass = _replaceListElement(oldObjectClass, b'univentionWindows', b'univentionMacOSClient')

    modlist.append(('univentionObjectType', ucs_object.get('univentionObjectType'), [b'computers/macos']))
    modlist.append(('objectClass', oldObjectClass, newObjectClass))
    modlist.append(('univentionServerRole', ucs_object.get('univentionServerRole'), []))

    log.process("Convert Windows client to macOS: %r", sync_object['dn'])

    s4connector.lo.lo.modify(sync_object['dn'], modlist)


def checkAndConvertToMacOSX(s4connector, key, sync_object):
    log.debug("checkAndConvertToMacOSX", ucs_object=repr(sync_object))

    if _isAlreadyMac(sync_object.get('attributes')):
        log.debug("checkAndConvertToMacOSX: The client is already a mac client, nothing to do")
        return

    if not _shouldBeMacClient(sync_object.get('attributes')):
        log.debug("checkAndConvertToMacOSX: The client should not be a Mac Client")
        return

    _convertWinToMac(s4connector, sync_object)


def windowscomputer_sync_s4_to_ucs_check_rename(s4connector, key, sync_object):
    log.debug("con_check_rename: sync_object: %s", sync_object)

    attrs = sync_object.get('attributes')
    if not attrs:
        return

    try:
        sAMAccountName_vals = [_v for _k, _v in attrs.items() if _k.lower() == 'samaccountname'][0]  # noqa: RUF015
    except IndexError:
        raise ValueError("{} has no sAMAccountName".format(sync_object['dn']))
    else:
        sAMAccountName = sAMAccountName_vals[0]

    ucs_object = s4connector.get_ucs_ldap_object(sync_object['dn'])
    if not ucs_object:
        log.warning("con_check_rename: ucs object not found: %s (maybe already deleted)", sync_object['dn'])
        return
    log.debug("con_check_rename: ucs object: %s", ucs_object)
    ucs_uid = ucs_object.get('uid', [None])[0]
    if not ucs_uid:
        raise ValueError(f"ucs object has no uid: {ucs_object}")

    if ucs_uid.lower() == sAMAccountName.lower():
        return

    log.process("con_check_rename: Renaming client from %s to %s", ucs_uid, sAMAccountName)
    ucs_admin_object = univention.admin.objects.get(s4connector.modules['windowscomputer'], co='', lo=s4connector.lo, position='', dn=sync_object['dn'])
    ucs_admin_object.open()
    ucs_admin_object['name'] = sAMAccountName.decode('UTF-8').rstrip('$')
    ucs_admin_object.modify()
