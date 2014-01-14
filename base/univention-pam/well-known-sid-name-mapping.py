#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention custom user and group name mapping
#  listener module: mapping custom user and group names for well known sids
#
# Copyright 2013 Univention GmbH
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

__package__=''  # workaround for PEP 366

import os
import re
import copy
import cPickle

import listener
import univention.debug
import univention.lib.s4
import univention.config_registry

name = "well-known-sid-name-mapping"
description = "map user and group names for well known sids"
filter = "(|(objectClass=sambaSamAccount)(objectClass=sambaGroupMapping))"
attributes = ["cn", "sambaSid"]
FN_CACHE = '/var/cache/univention-directory-listener/well-known-sid-name-mapping_modrdn.pickle'
modrdn = '1'

ucr = univention.config_registry.ConfigRegistry()
ucr.load()

def sidToName(sid):
	rid = sid.split("-")[-1]
	if univention.lib.s4.well_known_sids.get(sid):
		return univention.lib.s4.well_known_sids[sid]
	if univention.lib.s4.well_known_domain_rids.get(rid):
		return univention.lib.s4.well_known_domain_rids[rid]
	return None

def checkAndSet(obj, delete=False):
	ocs = obj.get('objectClass', [])
	if 'sambaSamAccount' in ocs:
		obj_name = obj.get('uid', [None])[0]
		ucr_base = 'users/default'
	elif 'sambaGroupMapping' in ocs:
		obj_name = obj.get('cn', [None])[0]
		ucr_base = 'groups/default'
	else:
		univention.debug.debug(
			univention.debug.LISTENER,
			univention.debug.ERROR,
			"%s: invalid object: %s" % (name, obj)
		)
		return

	sambaSid = obj.get("sambaSID", [None])[0]

	if obj_name and sambaSid:
		default_name = sidToName(sambaSid)
		if default_name:
			default_name_lower = default_name.lower().replace(" ", "")
			custom_name_lower = obj_name.lower().replace(" ", "")
			if not custom_name_lower == default_name_lower and not delete:
				ucr_key_value = "%s/%s=%s" % (ucr_base, default_name_lower, obj_name)
				univention.debug.debug(
					univention.debug.LISTENER,
					univention.debug.PROCESS,
					"%s: ucr set %s" % (name, ucr_key_value)
				)
				listener.setuid(0)
				try:
					univention.config_registry.handler_set([ucr_key_value])
				finally:
					listener.unsetuid()
			else:
				# unset ucr var if the custom name of user/group matches the default one,
				# or if object was deleted
				unset_ucr_key = "%s/%s" % (ucr_base, default_name)
				ucr = univention.config_registry.ConfigRegistry()
				ucr.load()
				if ucr.get(unset_ucr_key):
					univention.debug.debug(
						univention.debug.LISTENER,
						univention.debug.PROCESS,
						"%s: ucr unset %s" % (name, unset_ucr_key)
					)
					listener.setuid(0)
					try:
						univention.config_registry.handler_unset([unset_ucr_key])
					finally:
						listener.unsetuid()


def no_relevant_change(new, old):
		assert new
		assert old

		ocs = new.get('objectClass', [])

		if 'sambaSamAccount' in ocs:
			name_attr = 'uid'
		else:
			name_attr = 'cn'
		
		old_name = old.get(name_attr, [None])[0]
		new_name = new.get(name_attr, [None])[0]

		if old_name == new_name:
			return True
		else:
			return False

def handler(dn, new, old, command):

	if ucr.is_false("listener/module/wellknownsidnamemapping", False):
		univention.debug.debug(
			univention.debug.LISTENER,
			univention.debug.INFO,
			'%s: deactivated by listener/module/wellknownsidnamemapping' % (name,)
		)
		return

	old = copy.deepcopy(old)

	# do nothing if command is 'r' ==> modrdn
	if command == 'r':
		listener.setuid(0)
		try:
			with open(FN_CACHE, 'w+') as f:
				os.chmod(FN_CACHE, 0600)
				cPickle.dump(old, f)
		except Exception, e:
			univention.debug.debug(
				univention.debug.LISTENER,
				univention.debug.ERROR,
				'%s: failed to open/write pickle file: %s' % (name, str(e)))
		finally:
			listener.unsetuid()
		return

	# check modrdn changes
	if new and os.path.exists(FN_CACHE) and not old:
		listener.setuid(0)
		try:
			with open(FN_CACHE,'r') as f:
				old = cPickle.load(f)
		except Exception, e:
			univention.debug.debug(
				univention.debug.LISTENER,
				univention.debug.ERROR,
				'%s: failed to open/read pickle file: %s' % (name, str(e)))
		try:
		    os.remove(FN_CACHE)
		except Exception, e:
			univention.debug.debug(
				univention.debug.LISTENER,
				univention.debug.ERROR,
				'%s: cannot remove pickle file: %s' % (name, str(e)))
			univention.debug.debug(
				univention.debug.LISTENER,
				univention.debug.ERROR,
				'%s: for safety reasons well-known-sid-name-mapping ignores change of LDAP object: %s' % (name, dn))
			listener.unsetuid()
			return
		listener.unsetuid()

	if new:
		if not old:	# add
			univention.debug.debug(
				univention.debug.LISTENER,
				univention.debug.INFO,
				"%s: new %s" % (name, new.get("sambaSID"))
			)
			checkAndSet(new)

		else:	# modify
			if no_relevant_change(new, old):
				return

			univention.debug.debug(
				univention.debug.LISTENER,
				univention.debug.INFO,
				"%s: mod %s %s %s" % (name, new.get("sambaSID"), new_name, old_name)
			)
			checkAndSet(new)

	elif old:	# delete
		univention.debug.debug(
			univention.debug.LISTENER,
			univention.debug.INFO,
			"%s: del %s" % (name, old.get("sambaSID"))
		)
		checkAndSet(old, delete=True)
