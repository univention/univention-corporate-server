#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2018-2019 Univention GmbH
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

name = 'portal_category'
description = 'Dump portal category information'
filter = '(univentionObjectType=settings/portal_category)'
attributes = []


def _fname():
	return '/usr/share/univention-portal/portal.json'


def _load():
	fname = _fname()
	if not os.path.exists(fname):
		return {}
	with open(fname) as fd:
		return load(fd)


def _save(categories):
	content = _load()
	content['categories'] = categories
	with open(_fname(), 'wb') as fd:
		dump(content, fd, indent=2)


def _split_translation(value):
	if not value:
		return {}
	return dict(val.split(' ', 1) for val in value)


def _make_obj(obj):
	return {
		'dn': obj.get('entryDN')[0],
		'display_name': _split_translation(obj.get('univentionPortalCategoryDisplayName')),
	}


def handler(dn, new, old):
	listener.setuid(0)
	try:
		categories = _load().get('categories', {})
		if old and not new:
			# Remove
			try:
				ud.debug(ud.LISTENER, ud.PROCESS, 'Removing: %s' % dn)
				del categories[dn]
			except KeyError:
				ud.debug(ud.LISTENER, ud.PROCESS, 'Not found...')
		else:
			# Add or Change
			ud.debug(ud.LISTENER, ud.PROCESS, 'Add or change: %s' % dn)
			categories[dn] = _make_obj(new)
		_save(categories)
	finally:
		listener.unsetuid()
