# -*- coding: utf-8 -*-
#
# Univention group name mapping
#  listener module: mapping group names for well known sids
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

name = "group-name-mapping"
description = "mapp group names for well known sids"
filter = "(univentionObjectType=groups/group)"
attributes = ["cn", "sambaSid"]
FN_CACHE='/var/cache/univention-directory-listener/group-name-mapping.pickle'
modrdn='1'

def sidToName(sid):
	rid = sid.split("-")[-1]
	if univention.lib.s4.well_known_sids.get(sid):
		return univention.lib.s4.well_known_sids[sid]
	if univention.lib.s4.well_known_domain_rids.get(rid):
		return univention.lib.s4.well_known_domain_rids[rid]
	return None

def checkAndSet(obj, delete=False):
	sambaSid = obj.get("sambaSID", [None])[0]
	cn = obj.get("cn", [None])[0]
	if cn and sambaSid:
		name = sidToName(sambaSid)
		if name:
			customName = name.lower().replace(" ", "")
			customNameCn = cn.lower().replace(" ", "")
			if not customNameCn == customName and not delete:
				# create mapping if name of group in UCS is not
				# equal to the name in the sidlist
				toSet = "groups/default/%s=%s" % (customName, cn)
				univention.debug.debug(
					univention.debug.LISTENER,
					univention.debug.ERROR,
					"group-name-mapping: setting ucrv %s" % toSet
				)
				listener.setuid(0)
				try:
					univention.config_registry.handler_set([toSet])
				finally:
					listener.unsetuid()
			else:
				# unset mapping var if name of group in UCS is equal
				# to the name in the sidlist, or if group was deleted
				toUnset = "groups/default/%s" % customName
				ucr = univention.config_registry.ConfigRegistry()
				ucr.load()
				if ucr.get(toUnset):
					univention.debug.debug(
						univention.debug.LISTENER,
						univention.debug.ERROR,
						"group-name-mapping: unsetting ucrv %s" % toUnset
					)
					listener.setuid(0)
					try:
						univention.config_registry.handler_unset([toUnset])
					finally:
						listener.unsetuid()


def handler(dn, new, old, command):

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
				'group-name-mapping: failed to open/write pickle file: %s' % str(e))
		finally:
			listener.unsetuid()
		return

	# check modrdn changes
	if os.path.exists(FN_CACHE):
		listener.setuid(0)
		try:
			with open(FN_CACHE,'r') as f:
				old = cPickle.load(f)
		except Exception, e:
			univention.debug.debug(
				univention.debug.LISTENER,
				univention.debug.ERROR,
				'group-name-mapping: failed to open/read pickle file: %s' % str(e))
		try:
		    os.remove(FN_CACHE)
		except Exception, e:
			univention.debug.debug(
				univention.debug.LISTENER,
				univention.debug.ERROR,
				'group-name-mapping: cannot remove pickle file: %s' % str(e))
			univention.debug.debug(
				univention.debug.LISTENER,
				univention.debug.ERROR,
				'group-name-mapping: for safty reasons group-name-mapping ignores change of LDAP object: %s' % dn)
			listener.unsetuid()
			return
		listener.unsetuid()


	# new
	if new and not old:
		univention.debug.debug(
			univention.debug.LISTENER,
			univention.debug.INFO,
			"group-name-mapping: new %s" % new.get("sambaSID")
		)
		checkAndSet(new)
		
	# modify
	elif new and old:
		oldCn = old.get("cn", [None])[0]
		newCn = new.get("cn", [None])[0]
		# group name has changed
		if not oldCn == newCn:
			univention.debug.debug(
				univention.debug.LISTENER,
				univention.debug.INFO,
				"group-name-mapping: mod %s %s %s" % (new.get("sambaSID"), newCn, oldCn)
			)
			checkAndSet(new)
	# delete
	elif not new and old:
		univention.debug.debug(
			univention.debug.LISTENER,
			univention.debug.INFO,
			"group-name-mapping: del %s" % old.get("sambaSID")
		)
		checkAndSet(old, delete=True)
