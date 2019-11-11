#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# UCS Virtual Machine Manager Daemon
#  listener module for nodes
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
"""Watch for addition or deletion of virtualization nodes and notify UVMM daemon
accordingly."""

from __future__ import absolute_import

import listener
import univention.debug as debug
from univention.uvmm.uvmm_ldap import SERVICES, ldap2fqdn

name = 'uvmmd-nodes'
description = 'UCS Virtual Machine Manager Daemon Nodes'
filter = '(objectClass=univentionHost)'
attributes = ['univentionService']


def uvmm(mode, uri):
	"""Invoke UVMM CLI as root."""
	# Bug #21534: listener breaks pickle, using external CLI instead
	return listener.run("/usr/sbin/univention-virtual-machine-manager", ["univention-virtual-machine-manager", "-T", "5", mode, uri], 0, True)


def initialize():
	"""Called once on first initialization."""


def handler(dn, new, old):
	"""Called on each change."""
	try:
		old_services = old.get('univentionService', [])
		old_fqdn = ldap2fqdn(old)
	except Exception:  # NameError, KeyError
		old_services = []
		old_fqdn = ""

	try:
		new_services = new.get('univentionService', [])
		new_fqdn = ldap2fqdn(new)
	except Exception:  # NameError, KeyError
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


def clean():
	"""Called before resync."""

# vim:set ft=python ts=4 sw=4 noet:
