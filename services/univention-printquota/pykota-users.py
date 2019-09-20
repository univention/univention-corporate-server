# -*- coding: utf-8 -*-
#
# Univention pykota users
#  listener
#
# Copyright 2011-2019 Univention GmbH
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
import listener
import univention.debug
import univention.misc
import univention.config_registry

name = 'pykota-users'
description = 'manage pykota users'
filter = '(&(objectClass=posixAccount)(objectClass=person)(!(objectClass=univentionHost)))'
attributes = ["uid", "mailPrimaryAddress"]


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


def addUser(user):

	if 'uid' in user:
		uid = user['uid'][0]
		if 'mailPrimaryAddress' in user:
			uid = uid + "/" + user['mailPrimaryAddress'][0]

		cmd = ["--add", uid]
		callPkusers(cmd)

	return 0


def delUser(user):

	if 'uid' in user:
		uid = user['uid'][0]
		cmd = ["--delete", uid]
		callPkusers(cmd)


def handler(dn, new, old):

	# added
	if new and not old:
		if 'uid' in new:
			addUser(new)
	# removed
	elif old and not new:
		if 'uid' in old:
			delUser(old)
	# modified
	else:
		# uid changed -> new pykota user
		if 'uid' in old and 'uid' in new:
			if new['uid'][0] != old['uid'][0]:
				delUser(old)
				addUser(new)

		# email changed
		if 'mailPrimaryAddress' in new and 'mailPrimaryAddress' not in old:
			# email new
			addUser(new)
		elif 'mailPrimaryAddress' in new and 'mailPrimaryAddress' in old:
			if new['mailPrimaryAddress'][0] != old['mailPrimaryAddress'][0]:
				# email changed
				addUser(new)
		else:
			# no way to delete email from user with pkusers
			pass
	return


def clean():
	return


def postrun():
	return
