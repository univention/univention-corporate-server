#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Admin Diary
#  CLI Tool adding diary entry into Rsyslog to be added to the DB - eventually
#
# Copyright 2019 Univention GmbH
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
#

# this is just a "one-shot", non-packaged script
# that generates the DiaryEvent objects on a live UCS Master
# python $0 2> errors >> /usr/share/pyshared/univention/admindiary/events.py

import sys

from univention.lib.i18n import Translation
from univention.udm import UDM
from univention.udm.helpers import get_all_udm_module_names

udm = UDM.admin().version(2)

translation = Translation(None)


def modules():
	for m in get_all_udm_module_names():
		yield udm.get(m)._orig_udm_module


def print_events(m):
	name = m.module
	icon = 'domain'
	if name.startswith('users/'):
		icon = 'users'
	if name.startswith('groups/'):
		icon = 'users'
	if name.startswith('computers/'):
		icon = 'devices'
	if name.startswith('nagios/'):
		icon = 'devices'
	if name.startswith('printers/'):
		icon = 'devices'
	#if name.startswith('appcenter/'):
	#	icon = 'software'
	translation.domain = m._.im_self._domain
	translation.set_language('en_US.UTF-8')
	try:
		object_name = m.object_name
	except AttributeError:
		try:
			object_name = m.short_description
		except AttributeError:
			sys.stderr.write('no short_description and no object_name in %s\n' % m)
			return
		else:
			sys.stderr.write('using short_description in %s\n' % m)
	english_name = translation.translate(object_name)
	translation.set_language('de_DE.UTF-8')
	german_name = translation.translate(object_name)
	any_printed = False
	args = []
	if name == 'users/user':
		args = ['username']
	elif name == 'groups/group':
		args = ['name']
	elif name == 'settings/license':
		args = ['name', 'keyID']
	elif name == 'mail/folder':
		args = ['nameWithMailDomain']
	elif name == 'container/dc':
		args = ['name']
	else:
		for k, v in m.property_descriptions.iteritems():
			if v.identifies or not v.may_change:
				if v.identifies:
					args.insert(0, k)
				else:
					args.append(k)
	if len(args) == 0:
		sys.stderr.write('no args in %s\n' % m)
		return
	if 'add' in m.operations:
		print_created(m, english_name, german_name, args, icon)
		any_printed = True
	if 'edit' in m.operations:
		print_modified(m, english_name, german_name, args, icon)
		any_printed = True
	if 'move' in m.operations:
		print_moved(m, english_name, german_name, args, icon)
		any_printed = True
	if 'remove' in m.operations:
		print_removed(m, english_name, german_name, args, icon)
		any_printed = True
	if any_printed:
		print


def print_created(m, english_name, german_name, args, icon):
	name = 'UDM_' + m.module.replace('/', '_')
	additional_args = ''
	if len(args) > 1:
		additional_args = '(%s) ' % ' '.join('{%s}' % arg for arg in args[1:])
	print name.upper() + '_CREATED', '=', "DiaryEvent('%s', {'en': '%s {%s} %screated', 'de': '%s {%s} %sangelegt'}, args=%r, icon='%s')" % (name.upper() + '_CREATED', english_name, args[0], additional_args, german_name, args[0], additional_args, args, icon)


def print_modified(m, english_name, german_name, args, icon):
	name = 'UDM_' + m.module.replace('/', '_')
	additional_args = ''
	if len(args) > 1:
		additional_args = '(%s) ' % ' '.join('{%s}' % arg for arg in args[1:])
	print name.upper() + '_MODIFIED', '=', "DiaryEvent('%s', {'en': '%s {%s} %smodified', 'de': '%s {%s} %sbearbeitet'}, args=%r, icon='%s')" % (name.upper() + '_MODIFIED', english_name, args[0], additional_args, german_name, args[0], additional_args, args, icon)


def print_moved(m, english_name, german_name, args, icon):
	name = 'UDM_' + m.module.replace('/', '_')
	additional_args = ''
	if len(args) > 1:
		additional_args = '(%s) ' % ' '.join('{%s}' % arg for arg in args[1:])
	print name.upper() + '_MOVED', '=', "DiaryEvent('%s', {'en': '%s {%s} %smoved to {position}', 'de': '%s {%s} %sverschoben nach {position}'}, args=%r, icon='%s')" % (name.upper() + '_MOVED', english_name, args[0], additional_args, german_name, args[0], additional_args, args, icon)


def print_removed(m, english_name, german_name, args, icon):
	name = 'UDM_' + m.module.replace('/', '_')
	additional_args = ''
	if len(args) > 1:
		additional_args = '(%s) ' % ' '.join('{%s}' % arg for arg in args[1:])
	print name.upper() + '_REMOVED', '=', "DiaryEvent('%s', {'en': '%s {%s} %sremoved', 'de': '%s {%s} %sgelöscht'}, args=%r, icon='%s')" % (name.upper() + '_REMOVED', english_name, args[0], additional_args, german_name, args[0], additional_args, args, icon)


for module in modules():
	print_events(module)
