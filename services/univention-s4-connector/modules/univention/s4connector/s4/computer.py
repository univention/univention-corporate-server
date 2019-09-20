#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  computer object helper functions
#
# Copyright 2013-2019 Univention GmbH
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

import univention.debug2 as ud
import univention.s4connector.s4


def _shouldBeMacClient(attributes):
	if not attributes:
		return False

	os = attributes.get('operatingSystem', [None])[0]

	if os == 'Mac OS X':
		return True

	return False


def _isAlreadyMac(attributes):
	if not attributes:
		return False

	if attributes.get('univentionObjectType', [None])[0] == 'computers/macos':
		return True

	return False


def _replaceListElement(l, oldValue, newValue):
	return map(lambda x: x if x != oldValue else newValue, l)


def _convertWinToMac(s4connector, sync_object):
	modlist = []

	ucs_object = s4connector.get_ucs_ldap_object(sync_object['dn'])

	oldObjectClass = ucs_object.get('objectClass')
	newObjectClass = _replaceListElement(oldObjectClass, 'univentionWindows', 'univentionMacOSClient')

	modlist.append(('univentionObjectType', ucs_object.get('univentionObjectType'), ['computers/macos']))
	modlist.append(('objectClass', oldObjectClass, newObjectClass))
	modlist.append(('univentionServerRole', ucs_object.get('univentionServerRole'), []))

	ud.debug(ud.LDAP, ud.PROCESS, "Convert Windows client to Mac OS X: %s", sync_object['dn'])

	s4connector.lo.lo.modify(sync_object['dn'], modlist)


def checkAndConvertToMacOSX(s4connector, key, sync_object):
	ud.debug(ud.LDAP, ud.INFO, "checkAndConvertToMacOSX: ucs_object: %s" % sync_object)

	if _isAlreadyMac(sync_object.get('attributes')):
		ud.debug(ud.LDAP, ud.INFO, "checkAndConvertToMacOSX: The client is already a mac client, nothing to do")
		return

	if not _shouldBeMacClient(sync_object.get('attributes')):
		ud.debug(ud.LDAP, ud.INFO, "checkAndConvertToMacOSX: The client should not be a Mac Client")
		return

	_convertWinToMac(s4connector, sync_object)


def windowscomputer_sync_s4_to_ucs_check_rename(s4connector, key, sync_object):
	ud.debug(ud.LDAP, ud.INFO, "con_check_rename: sync_object: %s" % sync_object)

	attrs = sync_object.get('attributes')
	if not attrs:
		return

	try:
		sAMAccountName_vals = [_v for _k, _v in attrs.iteritems() if 'samaccountname' == _k.lower()][0]
	except IndexError:
		raise ValueError("%s has no sAMAccountName" % (sync_object['dn'],))
	else:
		sAMAccountName = sAMAccountName_vals[0]

	ucs_object = s4connector.get_ucs_ldap_object(sync_object['dn'])
	if not ucs_object:
		ud.debug(ud.LDAP, ud.WARN, "con_check_rename: ucs object not found: %s (maybe already deleted)" % sync_object['dn'])
		return
	ud.debug(ud.LDAP, ud.INFO, "con_check_rename: ucs object: %s" % ucs_object)
	ucs_uid = ucs_object.get('uid', [None])[0]
	if not ucs_uid:
		raise ValueError("ucs object has no uid: %s" % ucs_object)

	if ucs_uid.lower() == sAMAccountName.lower():
		return

	ud.debug(ud.LDAP, ud.PROCESS, "con_check_rename: Renaming client from %s to %s" % (ucs_uid, sAMAccountName))
	ucs_admin_object = univention.admin.objects.get(s4connector.modules['windowscomputer'], co='', lo=s4connector.lo, position='', dn=sync_object['dn'])
	ucs_admin_object.open()
	ucs_admin_object['name'] = sAMAccountName.rstrip('$')
	ucs_admin_object.modify()
