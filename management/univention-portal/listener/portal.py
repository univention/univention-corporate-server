#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2017 Univention GmbH
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

__package__ = ''  # workaround for PEP 366
import listener
import os.path
import univention.debug as ud  # pylint: disable-msg=E0611
from json import load, dump
from base64 import b64decode
from imghdr import what
import shutil

import ldap

from univention.config_registry import ConfigRegistry
from univention import uldap

ucr = ConfigRegistry()
ucr.load()

name = 'portal'
description = 'Dump portal information'
filter = '(|(univentionObjectType=settings/portal)(&(objectClass=univentionPortalComputer)(cn=%s)))' % ucr.get('hostname')
attributes = []


def _fname():
	return '/usr/share/univention-portal/portal.json'


def _load():
	fname = _fname()
	if not os.path.exists(fname):
		return {}
	with open(fname) as fd:
		return load(fd)


def _save(dn, portal):
	fname = _fname()
	portal['dn'] = dn
	content = _load()
	content['portal'] = portal
	with open(fname, 'wb') as fd:
		dump(content, fd, indent=2)


def _split_translation(value):
	if not value:
		return {}
	return dict(val.split(' ', 1) for val in value)


def _make_obj(obj):
	icon = obj.get('univentionPortalBackground', [''])[0]
	background = None
	if icon:
		cn = obj['cn'][0]
		fname = os.path.join(os.path.dirname(_fname()), 'icons', 'backgrounds', cn)
		ud.debug(ud.LISTENER, ud.PROCESS, 'Writing image to %s' % fname)
		try:
			with open(fname, 'wb') as fd:
				fd.write(b64decode(icon))
		except (EnvironmentError, TypeError):
			ud.debug(ud.LISTENER, ud.WARN, 'Failed to decode Icon')
		else:
			if what(fname) == 'png':
				shutil.move(fname, '%s.png' % fname)
				background = '/portal/icons/backgrounds/%s.png' % cn
			else:
				shutil.move(fname, '%s.svg' % fname)
				background = '/portal/icons/backgrounds/%s.svg' % cn
	return {
		'name': _split_translation(obj.get('univentionPortalDisplayName')),
		'showMenu': obj.get('univentionPortalShowMenu', [''])[0] == 'TRUE',
		'showSearch': obj.get('univentionPortalShowSearch', [''])[0] == 'TRUE',
		'showLogin': obj.get('univentionPortalShowLogin', [''])[0] == 'TRUE',
		'showApps': obj.get('univentionPortalShowApps', [''])[0] == 'TRUE',
		'showServers': obj.get('univentionPortalShowServers', [''])[0] == 'TRUE',
		'background': background,
	}


def _save_external_portal(dn=None):
	if dn is None:
		dn = 'cn=domain,cn=portal,cn=univention,%s' % ucr.get('ldap/base')
	lo = uldap.getMachineConnection()
	try:
		dn, attrs = lo.search(base=dn)[0]
	except ldap.NO_SUCH_OBJECT:
		ud.debug(ud.LISTENER, ud.WARN, 'DN %s not found! Falling back to hard coded values' % dn)
		attrs = {
			'univentionPortalDisplayName': ['Univention Portal'],
			'univentionPortalShowMenu': ['TRUE'],
			'univentionPortalShowSearch': ['TRUE'],
			'univentionPortalShowLogin': ['TRUE'],
			'univentionPortalShowApps': ['TRUE'],
			'univentionPortalShowServers': ['TRUE'],
		}
	obj = _make_obj(attrs)
	_save(dn, obj)


def handler(dn, new, old):
	listener.setuid(0)
	try:
		portal = _load().get('portal')
		if portal is None:
			ud.debug(ud.LISTENER, ud.PROCESS, 'No file found. Saving default initially')
			_save_external_portal()
			portal = _load()['portal']
		if new:
			is_computer = 'univentionPortalComputer' in new['objectClass']
		else:
			is_computer = 'univentionPortalComputer' in old['objectClass']
		if is_computer:
			if new:
				portal_dn = new.get('univentionComputerPortal', [''])[0]
				if portal_dn != portal['dn']:
					_save_external_portal(portal_dn)
		else:
			if dn == portal['dn']:
				if old and not new:
					# Remove
					ud.debug(ud.LISTENER, ud.WARN, 'Removed Portal object! Falling back to default')
					_save_external_portal()
				else:
					# Add or Change
					ud.debug(ud.LISTENER, ud.PROCESS, 'Add / change obj')
					obj = _make_obj(new)
					_save(dn, obj)
	finally:
		listener.unsetuid()
