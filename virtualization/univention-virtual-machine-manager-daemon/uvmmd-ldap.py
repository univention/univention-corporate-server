#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# UCS Virtual Machine Manager Daemon
#  listener module for guests
#
# Copyright 2010-2015 Univention GmbH
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
"""Watch for changes in virtualized guests and notify UVMM daemon
accordingly."""

name = 'uvmmd-ldap'
description = 'UCS Virtual Machine Manager Daemon LDAP monitor'
filter = '(objectClass=univentionVirtualMachine)'
attributes = []

__package__='' 	# workaround for PEP 366
import listener
import univention.debug as debug

def initialize():
	"""Called once on first initialization."""
	pass

def handler(dn, new, old):
	"""Called on each change."""
	uuids = set()
	if old:
		uuids |= set(old.get('univentionVirtualMachineUUID', []))
	if new:
		uuids |= set(new.get('univentionVirtualMachineUUID', []))
	for uuid in uuids:
		rc = listener.run("/usr/sbin/univention-virtual-machine-manager", ["univention-virtual-machine-manager", "domain_update", uuid, "-T", "5"], 0, False)
		debug.debug(debug.LISTENER, debug.INFO, "Requested update for %s: %d" % (', '.join(uuids), rc))


def postrun():
	"""Called 15s after handler."""
	pass

def clean():
	"""Called before resync."""
	pass

# vim:set ft=python ts=4 sw=4 noet:
