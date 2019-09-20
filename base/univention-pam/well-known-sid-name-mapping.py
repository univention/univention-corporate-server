#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention custom user and group name mapping
#  listener module: mapping custom user and group names for well known sids
#
# Copyright 2014-2019 Univention GmbH
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

__package__ = ''  # workaround for PEP 366

import os
import cPickle

import listener
import univention.debug
import univention.lib.s4
import univention.config_registry
import imp

name = "well-known-sid-name-mapping"
description = "map user and group names for well known sids"
filter = "(|(objectClass=sambaSamAccount)(objectClass=sambaGroupMapping))"
attributes = ["uid", "cn", "sambaSID"]
FN_CACHE = '/var/cache/univention-directory-listener/well-known-sid-name-mapping_modrdn.pickle'
modrdn = '1'

ucr = univention.config_registry.ConfigRegistry()
ucr.load()
modified_default_names = []


def sidToName(sid):
	rid = sid.split("-")[-1]
	if univention.lib.s4.well_known_sids.get(sid):
		return univention.lib.s4.well_known_sids[sid]
	if univention.lib.s4.well_known_domain_rids.get(rid):
		return univention.lib.s4.well_known_domain_rids[rid]
	return None


def checkAndSet(new, old):

	obj = new or old
	if not obj:
		return

	# check either new or old is relevant here
	well_known_sid = None
	for candidate in (new, old):
		if not candidate:
			continue
		sambaSid = candidate.get("sambaSID", [None])[0]
		if not sambaSid:
			continue
		default_name = sidToName(sambaSid)
		if default_name:
			well_known_sid = sambaSid
			break

	if not well_known_sid:
		return

	unset = False
	if new:
		if new.get("sambaSID", [None])[0] != well_known_sid:
			unset = True
	else:
		unset = True

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

	if not obj_name:
		return

	default_name_lower = default_name.lower().replace(" ", "")
	custom_name_lower = obj_name.lower().replace(" ", "")
	if custom_name_lower == default_name_lower or unset:
		# unset ucr var if the custom name of user/group matches the default one,
		# or if object was deleted
		unset_ucr_key = "%s/%s" % (ucr_base, default_name_lower)
		ucr.load()
		ucr_value = ucr.get(unset_ucr_key)
		if ucr_value:
			univention.debug.debug(
				univention.debug.LISTENER,
				univention.debug.PROCESS,
				"%s: ucr unset %s=%s" % (name, unset_ucr_key, ucr_value)
			)
			listener.setuid(0)
			try:
				univention.config_registry.handler_unset([unset_ucr_key])
				return default_name
			finally:
				listener.unsetuid()
	else:
		ucr_key_value = "%s/%s=%s" % (ucr_base, default_name_lower, obj_name)
		univention.debug.debug(
			univention.debug.LISTENER,
			univention.debug.PROCESS,
			"%s: ucr set %s" % (name, ucr_key_value)
		)
		listener.setuid(0)
		try:
			univention.config_registry.handler_set([ucr_key_value])
			return default_name
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

		old_name = old.get(name_attr, [])
		new_name = new.get(name_attr, [])
		old_sid = old.get("sambaSID", [])
		new_sid = new.get("sambaSID", [])

		univention.debug.debug(
			univention.debug.LISTENER,
			univention.debug.INFO,
			"%s: mod (old=%r, oldSid=%s) to (new=%r, newSid=%s)" % (name, old_name, old_sid, new_name, new_sid)
		)

		return (set(old_name) == set(new_name)) and (set(old_sid) == set(new_sid))


def handler(dn, new, old, command):
	global modified_default_names

	if ucr.is_false("listener/module/wellknownsidnamemapping", False):
		univention.debug.debug(
			univention.debug.LISTENER,
			univention.debug.INFO,
			'%s: deactivated by listener/module/wellknownsidnamemapping' % (name,)
		)
		return

	if command == 'r':  # modrdn phase I: store old object
		univention.debug.debug(
			univention.debug.LISTENER,
			univention.debug.INFO,
			'%s: modrdn phase I: %s' % (name, dn))
		listener.setuid(0)
		try:
			with open(FN_CACHE, 'w+') as f:
				os.chmod(FN_CACHE, 0o600)
				cPickle.dump(old, f)
		except Exception as e:
			univention.debug.debug(
				univention.debug.LISTENER,
				univention.debug.ERROR,
				'%s: failed to open/write pickle file: %s' % (name, str(e)))
		finally:
			listener.unsetuid()
		return

	# check for modrdn phase II in case of an add
	if new and os.path.exists(FN_CACHE) and not old:
		univention.debug.debug(
			univention.debug.LISTENER,
			univention.debug.INFO,
			'%s: modrdn phase II: %s' % (name, dn))
		listener.setuid(0)
		try:
			with open(FN_CACHE, 'r') as f:
				pickled_object = cPickle.load(f)
		except Exception as e:
			univention.debug.debug(
				univention.debug.LISTENER,
				univention.debug.ERROR,
				'%s: failed to open/read pickle file: %s' % (name, str(e)))
		try:
			os.remove(FN_CACHE)
		except Exception as e:
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

		# Normally we see two steps for the modrdn operation. But in case of the selective replication we
		# might only see the first step. This was discovered first in the s4-connector listener,
		# see https://forge.univention.org/bugzilla/show_bug.cgi?id=32542
		if pickled_object and new.get('entryUUID') == pickled_object.get('entryUUID'):
			old = pickled_object
		else:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.PROCESS, "The entryUUID attribute of the saved object (%s) does not match the entryUUID attribute of the current object (%s). This can be normal in a selective replication scenario." % (pickled_object.get('entryDN'), dn))

	# handle all the usual cases: add, modify, delete
	if new:
		if not old:  # add
			univention.debug.debug(
				univention.debug.LISTENER,
				univention.debug.INFO,
				"%s: new %s" % (name, new.get("sambaSID"))
			)
			changed_default_name = checkAndSet(new, old)
			if changed_default_name:
				modified_default_names.append(changed_default_name)

		else:  # modify
			if no_relevant_change(new, old):
				return

			changed_default_name = checkAndSet(new, old)
			if changed_default_name:
				modified_default_names.append(changed_default_name)

	elif old:  # delete
		univention.debug.debug(
			univention.debug.LISTENER,
			univention.debug.INFO,
			"%s: del %s" % (name, old.get("sambaSID"))
		)
		changed_default_name = checkAndSet(new, old)
		if changed_default_name:
			modified_default_names.append(changed_default_name)


def postrun():
	global modified_default_names
	if not modified_default_names:
		return

	hook_dir = '/usr/lib/univention-pam/well-known-sid-name-mapping.d'
	if not os.path.isdir(hook_dir):
		return

	listener.setuid(0)
	try:
		for filename in os.listdir(hook_dir):
			filename_parts = filename.split('.')
			if filename_parts[1] == 'py' and not filename.startswith('__'):
				hook_filepath = os.path.join(hook_dir, filename)
				hook_module = imp.load_source(filename_parts[0], hook_filepath)
				if hasattr(hook_module, 'postrun'):
					hook_module.postrun(modified_default_names)
	finally:
		modified_default_names = []
		listener.unsetuid()
