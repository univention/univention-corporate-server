#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Virtual Machine Manager Daemon
#  ldap integration
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
"""UVMM LDAP integration."""

# Mapping from service name to libvirt-uri
SERVICES = {
		"XEN Host": "xen://%s/",
		"KVM Host": "qemu://%s/system",
		}

class LdapError(Exception):
	"""LDAP configuration error."""
	pass

def ldap2fqdn(ldap_result):
	"""Convert LDAP result to fqdn."""
	return "%s.%s" % (ldap_result['cn'][0], ldap_result['associatedDomain'][0])

def ldap2uri():
	"""Add all nodes registered in LDAP."""
	import univention_baseconfig
	import univention.uldap

	if len(SERVICES) == 0:
		raise LdapError("No SERVICES defined.")
	baseConfig = univention_baseconfig.baseConfig()
	baseConfig.load()
	ldap_base = baseConfig.get('ldap/base')
	if not ldap_base:
		raise LdapError("No LDAP base in ldap/base.")
	ldap_server = baseConfig.get('ldap/server/name')
	if not ldap_server:
		raise LdapError("No LDAP server in ldap/server/name.")
	ldap_conn = univention.uldap.access(host=ldap_server, base=ldap_base)
	if not ldap_conn:
		raise LdapError("Could not connect '%s' for '%s'" % (ldap_server, ldap_base))

	# Build fuilter to find all Virtualization nodes
	filter_list = ["(univentionService=%s)" % service for service in SERVICES]
	if len(filter_list) > 1:
		filter = "(|%s)" % "".join(filter_list)
	else:
		filter = filter_list[0]

	nodes = []
	res = ldap_conn.search(filter)
	for dn, data in res:
		fqdn = ldap2fqdn(data)
		for service in SERVICES:
			if service in data['univentionService']:
				uri = SERVICES[service] % fqdn
				nodes.append(uri)
	ldap_conn.lo.unbind()

	return nodes
