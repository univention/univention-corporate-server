#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# UCS Virtual Machine Manager Node
#  libvirtd listener module
#
# Copyright 2010-2019 Univention GmbH
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
"""Watch for addition or deletion of management stations and update
/etc/libvirt/libvirtd.conf and the UCR variable uvmm/managers accordingly."""

from __future__ import absolute_import

import subprocess

import listener
import univention.debug as debug
from univention.config_registry import ConfigRegistry, handler_set

name = 'libvirtd-acl'
description = 'Update UCS Virtual Machine Manager libvirtd permissions'
# filter='(|(objectClass=univentionHost)(&(objectClass=univentionVirtualMachineGroupOC)(univentionVirtualMachineGroup=1)))'
filter = '(objectClass=univentionHost)'
attributes = ['univentionService']

service_names = set(["Virtual Machine Manager", "KVM Host"])
need_restart = False


def initialize():
	"""Called once on first initialization."""


def handler(dn, new, old):
	"""Called on each change."""
	ucr = ConfigRegistry()
	ucr.load()
	value = ucr.get('uvmm/managers', '')
	debug.debug(debug.LISTENER, debug.ALL, "old hosts: %s" % value)
	tls_allowed_dn_list = value.split()

	old_host = None
	if old and service_names & set(old.get('univentionService', [])):
		try:
			domain = old['associatedDomain'][0]
		except KeyError:
			domain = ucr.get('domainname')
		old_host = "%s.%s" % (old['cn'][0], domain)
		if old_host in tls_allowed_dn_list:
			debug.debug(debug.LISTENER, debug.INFO, "removing host %s" % (old_host,))
			tls_allowed_dn_list.remove(old_host)
	new_host = None
	if new and service_names & set(new.get('univentionService', [])):
		try:
			domain = new['associatedDomain'][0]
		except KeyError:
			domain = ucr.get('domainname')
		new_host = "%s.%s" % (new['cn'][0], domain)
		debug.debug(debug.LISTENER, debug.INFO, "+uvmm %s" % (new_host,))
		if new_host not in tls_allowed_dn_list:
			debug.debug(debug.LISTENER, debug.INFO, "adding host %s" % (new_host,))
			tls_allowed_dn_list.append(new_host)

	if old_host != new_host:
		value = ' '.join(tls_allowed_dn_list)
		debug.debug(debug.LISTENER, debug.ALL, "new hosts: %s" % value)
		key_value = 'uvmm/managers=%s' % (value,)
		listener.setuid(0)
		try:
			handler_set([key_value])
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
			subprocess.call(['systemctl', 'try-restart', 'libvirtd.service'])
			need_restart = False
		finally:
			listener.unsetuid()


def clean():
	"""Called before resync."""
