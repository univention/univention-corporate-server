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

from __future__ import absolute_import

import listener
import os.path
import univention.debug as ud  # pylint: disable-msg=E0611
from json import load, dump
from base64 import b64decode
from imghdr import what
from StringIO import StringIO

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


def _save_image(obj, ldap_attr, dir_name):
	img = obj.get(ldap_attr, [''])[0]
	if img:
		cn = os.path.basename(obj['cn'][0])
		fname = os.path.join(os.path.dirname(_fname()), 'icons', dir_name, cn)
		try:
			img = b64decode(img)
			string_buffer = StringIO(img)
			suffix = what(string_buffer) or 'svg'
			fname = '%s.%s' % (fname, suffix)
			ud.debug(ud.LISTENER, ud.PROCESS, 'Writing image to %s' % fname)
			with open(fname, 'wb') as fd:
				fd.write(img)
		except (EnvironmentError, TypeError, IOError) as err:
			ud.debug(ud.LISTENER, ud.WARN, 'Failed to open %r or decode Icon: %s' % (fname, err))
		else:
			return '/univention/portal/icons/%s/%s.%s' % (dir_name, cn, suffix)


def _write_css(obj):
	# get CSS rule for body background
	background = []
	bg_img = _save_image(obj, 'univentionPortalBackground', 'backgrounds')
	if bg_img:
		background.append('url("%s") no-repeat top center / cover' % (bg_img, ))
	css = obj.get('univentionPortalCSSBackground', [''])[0].strip()
	if css:
		background.append(css)
	background = ', '.join(background)

	# write CSS file
	fname = os.path.join(os.path.dirname(_fname()), 'portal.css')
	ud.debug(ud.LISTENER, ud.PROCESS, 'Writing CSS file %s' % fname)
	try:
		with open(fname, 'wb') as fd:
			if background:
				fd.write('body.umc {\n  background: %s;\n}\n' % background)
			else:
				fd.write('/* no styling defined via UDM portal object */\n' % background)

	except (EnvironmentError, IOError) as err:
		ud.debug(ud.LISTENER, ud.WARN, 'Failed to write CSS file %s: %s' % (fname, err))


def _make_obj(obj):
	return {
		'name': _split_translation(obj.get('univentionPortalDisplayName')),
		'showMenu': obj.get('univentionPortalShowMenu', [''])[0] == 'TRUE',
		'showSearch': obj.get('univentionPortalShowSearch', [''])[0] == 'TRUE',
		'showLogin': obj.get('univentionPortalShowLogin', [''])[0] == 'TRUE',
		'showApps': obj.get('univentionPortalShowApps', [''])[0] == 'TRUE',
		'showServers': obj.get('univentionPortalShowServers', [''])[0] == 'TRUE',
		'logo': _save_image(obj, 'univentionPortalLogo', 'logos'),
	}


def _save_external_portal(dn=None):
	if dn is None:
		dn = 'cn=local,cn=portal,cn=univention,%s' % ucr.get('ldap/base')
	lo = uldap.getMachineConnection()
	try:
		dn, attrs = lo.search(base=dn)[0]
	except ldap.NO_SUCH_OBJECT:
		ud.debug(ud.LISTENER, ud.WARN, 'DN %s not found! Falling back to hard coded values' % dn)
		attrs = {
			'univentionPortalDisplayName': ['en_US Startsite for {hostname}', 'de_DE Startseite für {hostname}', 'fr_FR page d\'accueil pour {hostname}'],
			'univentionPortalShowMenu': ['TRUE'],
			'univentionPortalShowSearch': ['TRUE'],
			'univentionPortalShowLogin': ['FALSE'],
			'univentionPortalShowApps': ['TRUE'],
			'univentionPortalShowServers': ['TRUE'],
		}
	obj = _make_obj(attrs)
	_save(dn, obj)
	_write_css(attrs)


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
					_write_css(new)
	finally:
		listener.unsetuid()
