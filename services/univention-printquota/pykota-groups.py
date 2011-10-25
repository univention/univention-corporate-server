# -*- coding: utf-8 -*-
#
# Univention pykota groups
#  listener
#
# Copyright 2011 Univention GmbH
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

__package__='' 	# workaround for PEP 366
import listener
import univention.debug
import univention.misc
import univention.config_registry
import os

name='pykota-groups'
description='manage pykota groups'
filter='(objectClass=univentionGroup)'
attributes=["cn", "memberUid"]

def initialize():
	univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, '%s: Initialize' % name)
	return

def callPkusers(cmd):

	cmd.insert(0, "pkusers")
	univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, '%s: calling pkusers with %s' % (name, cmd))
	listener.setuid(0)
	try:
		listener.run('/usr/bin/pkusers', cmd, uid=0, wait=1)
	finally:
		listener.unsetuid()

	return 0

def addGroup(group):

	if group.has_key('cn'):
		cn = group['cn'][0]
		if group.has_key('memberUid'):
			# create group only if there are members
			cmd = ["--groups", "--add", cn]
			callPkusers(cmd)
			users = ",".join(group['memberUid'])
			cmd = ["--ingroups", cn, users]
			callPkusers(cmd)
	return 0

def delGroup(group):

	if group.has_key('cn'):
		cn = group['cn'][0]
		cmd = ["--groups", "--delete", cn]
		callPkusers(cmd)

def handler(dn, new, old):

	# added
	if new and not old:
		addGroup(new)
	# removed
	elif old and not new:
		delGroup(old)
	# modified
	else:
		delGroup(old)
		addGroup(new)
	return

def clean():
	return

def postrun():
	return

