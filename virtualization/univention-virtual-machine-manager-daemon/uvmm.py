#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Virtual Machine Manager Daemon
#  listener module
#
# Copyright (C) 2010 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA	 02110-1301	 USA
"""Watch for addition or deletion of virtualization nodes and notify UVMM daemon
accordingly."""

name='uvmm'
description='Univention Virtual Machine Manager'
filter='(objectClass=univentionHost)'
attributes=['univentionService']

import listener
import univention.debug as debug
from univention.uvmm.ldap import SERVICES, ldap2fqdn

def uvmm(mode, uri):
	"""Invoke UVMM CLI as root."""
	# We call the external program, because for some unknown reason pickle
	# prepends the class name with absolute path to this file.
	return listener.run("/usr/sbin/univention-virtual-machine-manager", ["univention-virtual-machine-manager", mode, uri], 0, True)

def initialize():
	"""Called once on first initialization."""
	pass

def handler(dn, new, old):
	"""Called on each change."""
	try:
		old_services = old.get('univentionService', [])
		old_fqdn = ldap2fqdn(old)
	except StandardError, e: # NameError, KeyError
		old_services = []
		old_fqdn = ""

	try:
		new_services = new.get('univentionService', [])
		new_fqdn = ldap2fqdn(new)
	except StandardError, e: # NameError, KeyError
		new_services = []
		new_fqdn = ""
	
	for service in old_services:
		if service not in SERVICES:
			continue
		if old_fqdn != new_fqdn or service not in new_services:
			uri = SERVICES[service] % (old_fqdn,)
			rc = uvmm("remove", uri)
			debug.debug(debug.LISTENER, debug.INFO, "removing node %s: %d" % (uri, rc))
	for service in new_services:
		if service not in SERVICES:
			continue
		if old_fqdn != new_fqdn or service not in old_services:
			uri = SERVICES[service] % (new_fqdn,)
			rc = uvmm("add", uri)
			debug.debug(debug.LISTENER, debug.INFO, "adding node %s: %d" % (uri, rc))

def postrun():
	"""Called 15s after handler."""
	pass

def clean():
	"""Called before resync."""
	pass

# vim:set ft=python ts=4 sw=4 noet:
