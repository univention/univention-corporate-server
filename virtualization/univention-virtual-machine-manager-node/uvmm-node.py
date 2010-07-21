#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Virtual Machine Manager Node
#  listener module
#
# Copyright 2010 Univention GmbH
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
"""Watch for addition or deletion of management stations and update
/etc/libvirt/libvirtd.conf and the UCR variable uvmm/managers accordingly."""

name='uvmm-node'
description='Update Univention Virtual Machine Manager permissions'
filter='(objectClass=univentionHost)'
attributes=['univentionService']

import listener
import univention.config_registry as ucr
import univention.debug as debug
import subprocess

service_name = "Virtual Machine Manager"
need_restart = False

def initialize():
	"""Called once on first initialization."""
	pass

def handler(dn, new, old):
	"""Called on each change."""
	reg = ucr.ConfigRegistry()
	reg.load()
	value = reg.get('uvmm/managers','')
	debug.debug(debug.LISTENER, debug.ALL, "old UVMM daemon: %s" % value)
	tls_allowed_dn_list = value.split()

	old_host = None
	if old and service_name in old.get('univentionService', []):
		old_host = "%s.%s" % (old['cn'][0], old['associatedDomain'][0])
		if old_host in tls_allowed_dn_list:
			debug.debug(debug.LISTENER, debug.INFO, "removing UVMM daemon %s" % (old_host,))
			tls_allowed_dn_list.remove(old_host)
	new_host = None
	if new and service_name in new.get('univentionService', []):
		new_host = "%s.%s" % (new['cn'][0], new['associatedDomain'][0])
		debug.debug(debug.LISTENER, debug.INFO, "+uvmm %s" % (new_host,))
		if new_host not in tls_allowed_dn_list:
			debug.debug(debug.LISTENER, debug.INFO, "adding UVMM daemon %s" % (new_host,))
			tls_allowed_dn_list.append(new_host)

	if old_host != new_host:
		value = ' '.join(tls_allowed_dn_list)
		debug.debug(debug.LISTENER, debug.ALL, "new UVMM daemon: %s" % value)
		key_value = 'uvmm/managers=%s' % (value,)
		listener.setuid(0)
		try:
			ucr.handler_set([key_value])
			global need_restart
			need_restart = True
		finally:
			listener.unsetuid()

def postrun():
	"""Called 15s after handler."""
	global need_restart
	if need_restart:
		listener.setuid(0)
		try:
			# "libvirtd reload" only reloads the driver state, not the config file!
			ret = subprocess.call(['invoke-rc.d', 'univention-virtual-machine-manager-node-common', 'restart'])
			need_restart = False
		finally:
			listener.unsetuid()

def clean():
	"""Called before resync."""
	pass
