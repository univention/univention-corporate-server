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

import os
import errno
try:
	import cPickle as pickle
except ImportError:
	import pickle
import univention.baseconfig
import univention.uldap
from ldap import LDAPError
import ldapurl
from helpers import TranslatableException, N_ as _
import logging

logger = logging.getLogger('uvmmd.ldap')

# Mapping from service name to libvirt-uri
SERVICES = {
		"XEN Host": "xen://%s/",
		"KVM Host": "qemu://%s/system",
		}

class LdapError(TranslatableException):
	"""LDAP error."""
	pass

class LdapConfigurationError(LdapError):
	"""LDAP configuration error."""
	pass

class LdapConnectionError(LdapError):
	"""LDAP connection error."""
	pass

def ldap2fqdn(ldap_result):
	"""Convert LDAP result to fqdn."""
	return "%s.%s" % (ldap_result['cn'][0], ldap_result['associatedDomain'][0])

class _ldap_uri(object):
	"""LDAP URI."""
	def __init__(self, uri, rdn=None):
		"""Create LDAP uri with default host and base from Univention Config Registry."""
		try:
			u = ldapurl.LDAPUrl(uri)
		except ValueError, e:
			raise LdapConfigurationError(_('Illegal URI: %(uri)s'), uri=uri)
		
		baseConfig = univention.baseconfig.baseConfig()
		baseConfig.load()
		if not u.hostport:
			u.hostport = baseConfig['ldap/server/name']
			logger.debug('Retrieved ldap-host %s' % (u.hostport,))
			if not u.hostport:
				raise LdapConfigurationError(_('No LDAP server in ldap/server/name.'))
		if ':' in u.hostport:
			self.host, port = u.hostport.rsplit(':', 1)
			u.port = int(port)
		else:
			self.host = u.hostport
			import socket
			self.port = socket.getservbyname(u.urlscheme)
		if not u.dn:
			u.dn = baseConfig['ldap/base']
			logger.debug('Retrieved ldap-dn %s' % (u.dn,))
			if not u.dn:
				raise LdapConfigurationError(_('No LDAP base in ldap/base.'))
		if rdn:
			self.dn = "%s,%s" % (rdn, u.dn)
		else:
			self.dn = u.dn
	
	def connect(self):
		"""Connect to ldap://host/base."""
		try:
			conn = univention.uldap.access(host=self.host, port=self.port, base=self.dn)
			if not conn:
				raise LDAPError() # catched below
		except LDAPError, e:
			raise LdapConnectionError(_('Could not connect to "%(uri)s""'), uri=str(self))
		return conn
	
	def __str__(self):
		return "ldap://%s:%d/%s" % (self.host, self.port, self.dn)
	__repr__ = __str__

def ldap_cached(cachefile, func):
	"""Cache result of function or return cached result on LdapConnectionException."""
	try:
		result = func()

		data = pickle.dumps(result)
		file = open("%s.new" % (cachefile,), "w")
		try:
			file.write(data)
		finally:
			file.close()
		try:
			os.remove("%s.old" % (cachefile,))
		except OSError, e:
			if e.errno != errno.ENOENT:
				raise LdapError(_('Error removing %(file)s.old: %(msg)s'), file=cachefile, msg=e)
		try:
			os.rename("%s" % (cachefile,), "%s.old" % (cachefile,))
		except OSError, e:
			if e.errno != errno.ENOENT:
				raise LdapError(_('Error renaming %(file)s: %(msg)s'), file=cachefile, msg=e)
		try:
			os.rename("%s.new" % (cachefile,), "%s" % (cachefile,))
		except OSError, e:
			if e.errno != errno.ENOENT:
				raise LdapError(_('Error renaming %(file)s.new: %(msg)s'), file=cachefile, msg=e)
	except OSError, e:
		# LdapError("Error writing %(file)s: %(msg)e", file=cachefile, msg=e)
		pass
	except LdapConnectionError, msg:
		logger.info('Using cached LDAP data "%s"' % (cachefile,))
		try:
			file = open("%s" % (cachefile,), "r")
			try:
				data = file.read()
			finally:
				file.close()
			result = pickle.loads(data)
		except OSError, e:
			if e.errno != errno.ENOENT:
				raise LdapConnectionError(_('Error reading %(file)s: %(msg)s'), file=cachefile, msg=e)
			raise msg

	return result

def ldap_uris(ldap_uri=None):
	"""Return all nodes registered in LDAP."""
	if len(SERVICES) == 0:
		raise LdapConfigurationError(_('No SERVICES defined.'))
	
	# Build fuilter to find all Virtualization nodes
	filter_list = ["(univentionService=%s)" % service for service in SERVICES]
	if len(filter_list) > 1:
		filter = "(|%s)" % "".join(filter_list)
	else:
		filter = filter_list[0]
	
	ldap_uri = _ldap_uri(ldap_uri)
	ldap_conn = ldap_uri.connect()
	try:
		try:
			nodes = []
			res = ldap_conn.search(filter)
			for dn, data in res:
				fqdn = ldap2fqdn(data)
				for service in SERVICES:
					if service in data['univentionService']:
						uri = SERVICES[service] % fqdn
						nodes.append(uri)
			return nodes
		except LDAPError, e:
			raise LdapConnectionError(_('Could not query "%(uri)s"'), uri=ldap_uri)
	finally:
		ldap_conn.lo.unbind()

def ldap_annotation(uuid, ldap_uri=None):
	"""Load anntonations for domain from LDAP."""
	filter = "(&(objectClass=univentionVirtualMachine)(univentionVirtualMachineUUID=%s))" % (uuid,)
	
	ldap_uri = _ldap_uri(ldap_uri, 'cn=Virtual Machine Manager')
	ldap_conn = ldap_uri.connect()
	try:
		try:
			res = ldap_conn.search(filter)
			if len(res) != 1:
				return {}
			dn, data = res[0]
			del data['objectClass']
	
			return data
		except ldap.LDAPError, e:
			raise LdapConnectionError(_('Could not query "%(uri)s"'), uri=ldap_uri)
	finally:
		ldap_conn.lo.unbind()
