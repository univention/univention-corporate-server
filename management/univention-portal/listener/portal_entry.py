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

name = 'portal_entry'
description = 'Dump portal entry information'
filter = '(univentionObjectType=settings/portal_entry)'
attributes = []


def _fname():
	return '/usr/share/univention-portal/portal.json'


def _load():
	fname = _fname()
	if not os.path.exists(fname):
		return {}
	with open(fname) as fd:
		return load(fd)


def _save(objs):
	content = _load()
	content['entries'] = objs
	with open(_fname(), 'wb') as fd:
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


def _make_obj(obj):
	return {
		'id': obj['entryUUID'][0],
		'name': _split_translation(obj.get('univentionPortalEntryDisplayName')),
		'description': _split_translation(obj.get('univentionPortalEntryDescription')),
		'category': obj.get('univentionPortalEntryCategory', [''])[0],
		'links': obj.get('univentionPortalEntryLink'),
		'portals': obj.get('univentionPortalEntryPortal'),
		'activated': obj.get('univentionPortalEntryActivate', [''])[0] != 'FALSE',
		'favorite': obj.get('univentionPortalEntryFavorite', [''])[0] == 'TRUE',
		'authRestriction': obj.get('univentionPortalEntryAuthRestriction', [''])[0] or 'anonymous',
		'logo_name': _save_image(obj, 'univentionPortalEntryIcon', 'entries'),
	}


def handler(dn, new, old):
	listener.setuid(0)
	try:
		objs = _load().get('entries', [])
		if old and not new:
			# Remove
			idx = None
			entry_uuid = old['entryUUID'][0]
			ud.debug(ud.LISTENER, ud.PROCESS, 'Removing %s' % entry_uuid)
			for i, obj in enumerate(objs):
				if obj['id'] == entry_uuid:
					idx = i
					break
			else:
				ud.debug(ud.LISTENER, ud.PROCESS, 'Not found...')
				return
			objs.pop(idx)
		else:
			# Add or Change
			ud.debug(ud.LISTENER, ud.PROCESS, 'Add / change obj')
			new_obj = _make_obj(new)
			new_obj['dn'] = dn
			idx = None
			ud.debug(ud.LISTENER, ud.PROCESS, 'Talking about %s' % (new_obj['id']))
			for i, obj in enumerate(objs):
				if obj['id'] == new_obj['id']:
					idx = i
					ud.debug(ud.LISTENER, ud.PROCESS, 'Found in old objects. Overwriting')
					break
			else:
				ud.debug(ud.LISTENER, ud.PROCESS, 'Not found. Creating new one')
				idx = len(objs)
				objs.append(None)
			objs[idx] = new_obj
		_save(objs)
	finally:
		listener.unsetuid()
