# -*- coding: utf-8 -*-
#
# UCS Virtual Machine Manager Daemon
#  ldap integration
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
"""UVMM LDAP integration."""

from __future__ import absolute_import
import os
import errno
import pickle
import univention.config_registry as ucr
import univention.uldap
from ldap import LDAPError, SERVER_DOWN
import univention.admin.uldap
import univention.admin.modules
import univention.admin.handlers.uvmm.info as uvmm_info
from .helpers import TranslatableException, N_ as _, FQDN as HOST_FQDN
import logging

configRegistry = ucr.ConfigRegistry()
configRegistry.load()

univention.admin.modules.update()

logger = logging.getLogger('uvmmd.ldap')

# Mapping from service name to libvirt-uri
SERVICES = {
	"KVM Host": "qemu://%s/system",
}

LDAP_UVMM_RDN = "cn=Virtual Machine Manager"
LDAP_INFO_RDN = "cn=Information,%s" % LDAP_UVMM_RDN
LDAP_PROFILES_RDN = "cn=Profiles,%s" % LDAP_UVMM_RDN
LDAP_CLOUD_CONNECTION_RDN = "cn=CloudConnection,%s" % LDAP_UVMM_RDN
LDAP_CLOUD_TYPE_RDN = "cn=CloudType,%s" % LDAP_UVMM_RDN


class LdapError(TranslatableException):

	"""LDAP error."""


class LdapConfigurationError(LdapError):

	"""LDAP configuration error."""


class LdapConnectionError(LdapError):

	"""LDAP connection error."""


def ldap2fqdn(ldap_result):
	"""Convert LDAP result to fqdn."""
	if 'associatedDomain' not in ldap_result:
		domain = configRegistry.get('domainname', '')
	else:
		domain = ldap_result['associatedDomain'][0]
	return "%s.%s" % (ldap_result['cn'][0], domain)


def cached(cachefile, func, exception=LdapConnectionError):
	"""Cache result of function or return cached result on LdapConnectionException."""
	try:
		result = func()

		with open("%s.new" % (cachefile,), "w") as stream:
			p = pickle.Pickler(stream)
			p.dump(result)
		try:
			os.remove("%s.old" % (cachefile,))
		except EnvironmentError as ex:
			if ex.errno != errno.ENOENT:
				raise LdapError(_('Error removing %(file)s.old: %(msg)s'), file=cachefile, msg=ex)
		try:
			os.rename("%s" % (cachefile,), "%s.old" % (cachefile,))
		except EnvironmentError as ex:
			if ex.errno != errno.ENOENT:
				raise LdapError(_('Error renaming %(file)s: %(msg)s'), file=cachefile, msg=ex)
		try:
			os.rename("%s.new" % (cachefile,), "%s" % (cachefile,))
		except EnvironmentError as ex:
			if ex.errno != errno.ENOENT:
				raise LdapError(_('Error renaming %(file)s.new: %(msg)s'), file=cachefile, msg=ex)
	except EnvironmentError:
		pass
	except exception as msg:
		logger.info('Using cached data "%s"', cachefile)
		try:
			with open("%s" % (cachefile,), "r") as stream:
				p = pickle.Unpickler(stream)
				result = p.load()
		except EnvironmentError as ex:
			if ex.errno != errno.ENOENT:
				raise exception(_('Error reading %(file)s: %(msg)s'), file=cachefile, msg=ex)
			raise msg
		except EOFError:
			raise exception(_('Error reading incomplete %(file)s.'), file=cachefile)

	return result


def ldap_uris(ldap_uri=None):
	"""Return all nodes registered in LDAP."""
	if len(SERVICES) == 0:
		raise LdapConfigurationError(_('No SERVICES defined.'))

	# Build filter to find all Virtualization nodes
	filter_list = ["(univentionService=%s)" % service for service in SERVICES]
	if len(filter_list) > 1:
		filter = "(|%s)" % "".join(filter_list)
	else:
		filter = filter_list[0]

	# ensure that we should manage the host
	filter = '(&%s(|(!(univentionVirtualMachineManageableBy=*))(univentionVirtualMachineManageableBy=%s)))' % (filter, HOST_FQDN)
	logger.debug('Find servers to manage "%s"' % filter)
	lo, position = univention.admin.uldap.getMachineConnection(ldap_master=False)
	try:
		nodes = []
		res = lo.search(filter)
		for dn, data in res:
			fqdn = ldap2fqdn(data)
			for service in SERVICES:
				if service in data['univentionService']:
					uri = SERVICES[service] % fqdn
					nodes.append(uri)
		logger.debug('Registered URIs: %s' % ', '.join(nodes))
		return nodes
	except LDAPError:
		raise LdapConnectionError(_('Could not query "%(uri)s"'), uri=ldap_uri)


def ldap_annotation(uuid):
	"""Load annotations for domain from LDAP."""
	try:
		lo, position = univention.admin.uldap.getMachineConnection(ldap_master=False)
		base = "%s,%s" % (LDAP_INFO_RDN, position.getDn())
	except (SERVER_DOWN, EnvironmentError):
		raise LdapConnectionError(_('Could not open LDAP-Machine connection'))
	co = None
	dn = "%s=%s,%s" % (uvmm_info.mapping.mapName('uuid'), uuid, base)
	filter = "(objectclass=*)"
	logger.debug('Querying domain infos "%s"' % dn)
	try:
		res = univention.admin.modules.lookup(uvmm_info, co, lo, scope='base', base=dn, filter=filter, required=True, unique=True)
		record = res[0]
		return dict(record)
	except univention.admin.uexceptions.base:
		return {}


def ldap_modify(uuid):
	"""Modify annotations for domain from LDAP."""
	try:
		lo, position = univention.admin.uldap.getMachineConnection(ldap_master=True)
		base = "%s,%s" % (LDAP_INFO_RDN, position.getDn())
	except (SERVER_DOWN, EnvironmentError):
		raise LdapConnectionError(_('Could not open LDAP-Admin connection'))
	co = None
	dn = "%s=%s,%s" % (uvmm_info.mapping.mapName('uuid'), uuid, base)
	filter = "(objectclass=*)"
	logger.debug('Updating domain infos "%s"' % dn)
	try:
		res = univention.admin.modules.lookup(uvmm_info, co, lo, scope='base', base=dn, filter=filter, required=True, unique=True)
		record = res[0]
		record.open()
		record.commit = record.modify
	except univention.admin.uexceptions.base:
		position.setDn(base)
		record = uvmm_info.object(co, lo, position)
		record['uuid'] = uuid
		record['description'] = None
		record['contact'] = None
		record['profile'] = None
		record.commit = record.create
	return record


def ldap_cloud_connections():
	""" Return a list of all cloud connections."""
	filt = '(objectClass=univentionVirtualMachineCloudConnection)'
	# ensure that we should manage the host
	filt = '(&%s(|(!(univentionVirtualMachineManageableBy=*))(univentionVirtualMachineManageableBy=%s)))' % (filt, HOST_FQDN)
	lo, position = univention.admin.uldap.getMachineConnection(ldap_master=False)
	try:
		cloudconnections = []
		res = lo.search(filt)
		for dn, data in res:
			if 'univentionVirtualMachineCloudConnectionParameter' in data:
				c = {}
				c['dn'] = dn
				c['name'] = data['cn'][0]
				# Search cloudtype parameter
				typebase = data['univentionVirtualMachineCloudConnectionTypeRef'][0]
				res = lo.search(base=typebase)
				cloudtype = res[0][1]['cn'][0]
				c['type'] = cloudtype
				for p in data['univentionVirtualMachineCloudConnectionParameter']:
					if '=' not in p:
						logger.error('Expected "=" in cloud connection parameter. Connection %s, parameter %s', dn, p)
						continue
					p_name = p.split('=', 1)[0]
					p_value = p.split('=', 1)[1]
					c[p_name] = p_value
				c['ucs_images'] = data['univentionVirtualMachineCloudConnectionIncludeUCSImages'][0]
				c['search_pattern'] = data.get('univentionVirtualMachineCloudConnectionImageSearchPattern', [''])[0]
				c['preselected_images'] = []
				if 'univentionVirtualMachineCloudConnectionImageList' in data:
					c['preselected_images'] = data['univentionVirtualMachineCloudConnectionImageList']
				cloudconnections.append(c)

		return cloudconnections
	except LDAPError:
		raise LdapConnectionError(_('Could not open LDAP-Admin connection'))


def ldap_cloud_connection_add(cloudtype, name, parameter, ucs_images="1", search_pattern="*", preselected_images=[]):
	""" Add a new cloud connection."""
	try:
		lo, position = univention.admin.uldap.getMachineConnection()
		dn = 'cn=%s,%s,%s' % (name, LDAP_CLOUD_CONNECTION_RDN, position.getDn())
		dn_typeref = 'cn=%s,%s,%s' % (cloudtype, LDAP_CLOUD_TYPE_RDN, position.getDn())
		parameter_lst = []

		if ucs_images is True:
			ucs_images = "1"
		if ucs_images is False:
			ucs_images = "0"

		for k, v in parameter.items():
			if k and v:
				parameter_lst.append('%s=%s' % (k, v))
		attrs = {
			'objectClass': ['univentionVirtualMachineCloudConnection', 'univentionVirtualMachineHostOC', 'univentionObject'],
			'univentionObjectType': 'uvmm/cloudconnection',
			'cn': name,
			'univentionVirtualMachineCloudConnectionTypeRef': dn_typeref,
			'univentionVirtualMachineCloudConnectionParameter': parameter_lst,
			'univentionVirtualMachineCloudConnectionIncludeUCSImages': ucs_images,
			'univentionVirtualMachineCloudConnectionImageSearchPattern': search_pattern
		}
		if preselected_images:
			attrs['univentionVirtualMachineCloudConnectionImageList'] = preselected_images
		modlist = attrs.items()
		lo.add(dn, modlist)

	except LDAPError:
		raise LdapConnectionError(_('Could not open LDAP-Admin connection'))


def ldap_cloud_types():
	""" Return a list of all cloud types."""
	filt = '(objectClass=univentionVirtualMachineCloudType)'
	lo, position = univention.admin.uldap.getMachineConnection(ldap_master=False)
	try:
		cloudtypes = []
		res = lo.search(filt)
		for dn, data in res:
			c = {}
			c['name'] = data['cn'][0]
			cloudtypes.append(c)

		return cloudtypes
	except LDAPError:
		raise LdapConnectionError(_('Could not open LDAP-Admin connection'))
