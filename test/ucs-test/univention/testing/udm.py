# -*- coding: utf-8 -*-
#
# UCS test
"""
ALPHA VERSION

Wrapper around Univention Directory Manager CLI to simplify
creation/modification of UDM objects in python. The wrapper automatically
removed created objects during wrapper destruction.
For usage examples look at the end of this file.

WARNING:
The API currently allows only modifications to objects created by the wrapper
itself. Also the deletion of objects is currently unsupported. Also not all
UDM object types are currently supported.

WARNING2:
The API is currently under heavy development and may/will change before next UCS release!
"""
from __future__ import print_function
# Copyright 2013-2020 Univention GmbH
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

import os
import sys
import copy
import time
import pipes
import subprocess

import bz2
import base64
import ldap
import ldap.filter
import psutil
import six

import univention.admin.uldap
import univention.admin.modules
import univention.admin.objects

import univention.testing.ucr
import univention.testing.strings as uts
import univention.testing.utils as utils
from univention.testing.ucs_samba import wait_for_drs_replication, DRSReplicationFailed


class UCSTestUDM_Exception(Exception):

	def __str__(self):
		if self.args and len(self.args) == 1 and isinstance(self.args[0], dict):
			return '\n'.join('%s=%s' % (key, value) for key, value in self.args[0].items())
		else:
			return Exception.__str__(self)
	__repr__ = __str__


class UCSTestUDM_MissingModulename(UCSTestUDM_Exception):
	pass


class UCSTestUDM_MissingDn(UCSTestUDM_Exception):
	pass


class UCSTestUDM_CreateUDMObjectFailed(UCSTestUDM_Exception):
	pass


class UCSTestUDM_CreateUDMUnknownDN(UCSTestUDM_Exception):
	pass


class UCSTestUDM_ModifyUDMObjectFailed(UCSTestUDM_Exception):
	pass


class UCSTestUDM_MoveUDMObjectFailed(UCSTestUDM_Exception):
	pass


class UCSTestUDM_NoModification(UCSTestUDM_Exception):
	pass


class UCSTestUDM_ModifyUDMUnknownDN(UCSTestUDM_Exception):
	pass


class UCSTestUDM_RemoveUDMObjectFailed(UCSTestUDM_Exception):
	pass


class UCSTestUDM_CleanupFailed(UCSTestUDM_Exception):
	pass


class UCSTestUDM_CannotModifyExistingObject(UCSTestUDM_Exception):
	pass


class UCSTestUDM_ListUDMObjectFailed(UCSTestUDM_Exception):
	pass


class UCSTestUDM(object):
	PATH_UDM_CLI_SERVER = '/usr/share/univention-directory-manager-tools/univention-cli-server'
	PATH_UDM_CLI_CLIENT = '/usr/sbin/udm'
	PATH_UDM_CLI_CLIENT_WRAPPED = '/usr/sbin/udm-test'

	COMPUTER_MODULES = (
		'computers/ubuntu',
		'computers/linux',
		'computers/windows',
		'computers/windows_domaincontroller',
		'computers/domaincontroller_master',
		'computers/domaincontroller_backup',
		'computers/domaincontroller_slave',
		'computers/memberserver',
		'computers/macos',
		'computers/ipmanagedclient')

	# map identifying UDM module or rdn-attribute to samba4 rdn attribute
	def ad_object_identifying_filter(self, modulename, dn):
		udm_mainmodule, udm_submodule = modulename.split('/', 1)
		objname = ldap.dn.str2dn(dn)[0][0][1]

		attr = ''
		ad_ldap_controls = None
		con_search_filter = ''
		match_filter = ''

		if udm_mainmodule == 'users':
			attr = 'sAMAccountName'
			con_search_filter = '(&(objectClass=user)(!(objectClass=computer))(userAccountControl:1.2.840.113556.1.4.803:=512))'
			match_filter = '(&(|(&(objectClass=posixAccount)(objectClass=krb5Principal))(objectClass=user))(!(objectClass=univentionHost)))'
		elif udm_mainmodule == 'groups':
			attr = 'sAMAccountName'
			con_search_filter = '(objectClass=group)'
		elif udm_mainmodule == 'computers':
			if udm_submodule.startswith('domaincontroller_') or udm_submodule == 'windows_domaincontroller':
				attr = 'cn'
				con_search_filter = '(&(objectClass=computer)(userAccountControl:1.2.840.113556.1.4.803:=532480))'
				match_filter = '(|(&(objectClass=univentionDomainController)(univentionService=Samba 4))(objectClass=computer)(univentionServerRole=windows_domaincontroller))'
			elif udm_submodule in ('windows', 'memberserver', 'ucc', 'linux', 'ubuntu', 'macos'):
				attr = 'cn'
				con_search_filter = '(&(objectClass=computer)(userAccountControl:1.2.840.113556.1.4.803:=4096))'
				match_filter = '(|(&(objectClass=univentionWindows)(!(univentionServerRole=windows_domaincontroller)))(objectClass=computer)(objectClass=univentionMemberServer)(objectClass=univentionUbuntuClient)(objectClass=univentionLinuxClient)(objectClass=univentionMacOSClient)(objectClass=univentionCorporateClient))'
		elif modulename == 'containers/cn':
			attr = 'cn'
			con_search_filter = '(&(|(objectClass=container)(objectClass=builtinDomain))(!(objectClass=groupPolicyContainer)))'
		elif modulename == 'container/msgpo':
			attr = 'cn'
			con_search_filter = '(&(objectClass=container)(objectClass=groupPolicyContainer))'
		elif modulename == 'containers/ou':
			attr = 'ou'
			con_search_filter = 'objectClass=organizationalUnit'
		elif udm_mainmodule == 'dns':
			attr = 'dc'
			ad_ldap_controls = ["search_options:1:2"]
			if udm_submodule in ('alias', 'host_record', 'ptr_record', 'srv_record', 'txt_record', 'ns_record', 'host_record'):
				con_search_filter = '(&(objectClass=dnsNode)(!(dNSTombstoned=TRUE)))'
			elif udm_submodule in ('forward_zone', 'reverse_zone'):
				con_search_filter = '(objectClass=dnsZone)'  # partly true, actually we map the SOA too

		if match_filter:
			try:
				res = self._lo.search(base=dn, filter=match_filter, scope='base', attr=[])
			except ldap.NO_SUCH_OBJECT:
				print("OpenLDAP object to check against S4-Connector match_filter doesn't exist: %s" % (dn, ))
				res = None  # TODO: This happens during delete. By setting res=None here, we will not wait for DRS replication for deletes!
			except Exception as ex:
				print("OpenLDAP search with S4-Connector match_filter failed: %s" % (ex, ))
				raise
			if not res:
				print("DRS wait not required, S4-Connector match_filter did not match the OpenLDAP object: %s" % (dn,))
				return

		if attr:
			filter_template = '(&(%s=%%s)%s)' % (attr, con_search_filter)
			ad_ldap_search_args = {'ldap_filter': ldap.filter.filter_format(filter_template, (objname,)), 'controls': ad_ldap_controls}
			return ad_ldap_search_args

	__lo = None
	__ucr = None

	@property
	def _lo(self):
		if self.__lo is None:
			self.__lo = utils.get_ldap_connection()
		return self.__lo

	@property
	def _ucr(self):
		if self.__ucr is None:
			self.__ucr = univention.testing.ucr.UCSTestConfigRegistry()
			self.__ucr.load()
		return self.__ucr

	@property
	def LDAP_BASE(self):
		return self._ucr['ldap/base']

	@property
	def FQHN(self):
		return '%(hostname)s.%(domainname)s.' % self._ucr

	@property
	def UNIVENTION_CONTAINER(self):
		return 'cn=univention,%(ldap/base)s' % self._ucr

	@property
	def UNIVENTION_TEMPORARY_CONTAINER(self):
		return 'cn=temporary,cn=univention,%(ldap/base)s' % self._ucr

	def __init__(self):
		self._cleanup = {}
		self._cleanupLocks = {}

	@classmethod
	def _build_udm_cmdline(cls, modulename, action, kwargs):
		"""
		Pass modulename, action (create, modify, delete) and a bunch of keyword arguments
		to _build_udm_cmdline to build a command for UDM CLI.

		:param str modulename: name of UDM module (e.g. 'users/user')
		:param str action: An action, like 'create', 'modify', 'delete'.
		:param dict kwargs: A dictionary containing properties or one of the following special keys:

		:param str binddn: The LDAP simple-bind DN.
		:param str bindpwd: The LDAP simple-bind password.
		:param str bindpwdfile: A pathname to a file containing the LDAP simple-bind password.
		:param str dn: The LDAP distinguished name to operate on.
		:param str position: The LDAP distinguished name of the parent container.
		:param str superordinate: The LDAP distinguished name of the logical parent.
		:param str policy_reference: The LDAP distinguished name of the UDM policy to add.
		:param str policy_dereference: The LDAP distinguished name of the UDM policy to remove.
		:param str append_option: The name of an UDM option group to add.
		:param list options: A list of UDM option group to set.
		:param str_or_list set: A list or one single *name=value* property.
		:param list append: A list of *name=value* properties to add.
		:param list remove: A list of *name=value* properties to remove.
		:param boolean remove_referring: Remove other LDAP entries referred by this entry.
		:param boolean ignore_exists: Ignore error on creation if entry already exists.
		:param boolean ignore_not_exists: Ignore error on deletion if entry does not exists.

		>>> UCSTestUDM._build_udm_cmdline('users/user', 'create', {'username': 'foobar'})
		['/usr/sbin/udm-test', 'users/user', 'create', '--set', 'username=foobar']
		"""
		cmd = [cls.PATH_UDM_CLI_CLIENT_WRAPPED, modulename, action]
		args = copy.deepcopy(kwargs)

		for arg in ('binddn', 'bindpwd', 'bindpwdfile', 'dn', 'position', 'superordinate', 'policy_reference', 'policy_dereference', 'append_option'):
			if arg not in args:
				continue
			value = args.pop(arg)
			if not isinstance(value, (list, tuple)):
				value = (value,)
			for item in value:
				cmd.extend(['--%s' % arg.replace('_', '-'), item])

		if action == 'list' and 'policies' in args:
			cmd.extend(['--policies=%s' % (args.pop('policies'),)])

		for option in args.pop('options', ()):
			cmd.extend(['--option', option])

		for key, value in args.pop('set', {}).items():
			if isinstance(value, (list, tuple)):
				for item in value:
					cmd.extend(['--set', '%s=%s' % (key, item)])
			else:
				cmd.extend(['--set', '%s=%s' % (key, value)])

		for operation in ('append', 'remove'):
			for key, values in args.pop(operation, {}).items():
				for value in values:
					cmd.extend(['--%s' % operation, '%s=%s' % (key, value)])

		if args.pop('remove_referring', True) and action == 'remove':
			cmd.append('--remove_referring')

		if args.pop('ignore_exists', False) and action == 'create':
			cmd.append('--ignore_exists')

		if args.pop('ignore_not_exists', False) and action == 'remove':
			cmd.append('--ignore_not_exists')

		# set all other remaining properties
		for key, value in args.items():
			if isinstance(value, (list, tuple)):
				for item in value:
					cmd.extend(['--append', '%s=%s' % (key, item)])
			elif value:
				cmd.extend(['--set', '%s=%s' % (key, value)])

		return cmd

	def create_object(self, modulename, wait_for_replication=True, check_for_drs_replication=False, wait_for=False, **kwargs):
		r"""
		Creates a LDAP object via UDM. Values for UDM properties can be passed via keyword arguments
		only and have to exactly match UDM property names (case-sensitive!).

		:param str modulename: name of UDM module (e.g. 'users/user')
		:param bool wait_for_replication: delay return until Listener has settled.
		:param bool check_for_drs_replication: delay return until Samab4 has settled.
		:param \*\*kwargs:
		"""
		if not modulename:
			raise UCSTestUDM_MissingModulename()

		dn = None
		cmd = self._build_udm_cmdline(modulename, 'create', kwargs)
		print('Creating %s object with %s' % (modulename, _prettify_cmd(cmd)))
		child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
		(stdout, stderr) = child.communicate()

		if six.PY3:
			stdout, stderr = stdout.decode('utf-8', 'replace'), stderr.decode('utf-8', 'replace')

		if child.returncode:
			raise UCSTestUDM_CreateUDMObjectFailed({'module': modulename, 'kwargs': kwargs, 'returncode': child.returncode, 'stdout': stdout, 'stderr': stderr})

		# find DN of freshly created object and add it to cleanup list
		for line in stdout.splitlines():  # :pylint: disable-msg=E1103
			if line.startswith('Object created: ') or line.startswith('Object exists: '):
				dn = line.split(': ', 1)[-1]
				if not line.startswith('Object exists: '):
					self._cleanup.setdefault(modulename, []).append(dn)
				break
		else:
			raise UCSTestUDM_CreateUDMUnknownDN({'module': modulename, 'kwargs': kwargs, 'stdout': stdout, 'stderr': stderr})

		self.wait_for(modulename, dn, wait_for_replication, everything=wait_for)
		return dn

	def modify_object(self, modulename, wait_for_replication=True, check_for_drs_replication=False, wait_for=False, **kwargs):
		"""
		Modifies a LDAP object via UDM. Values for UDM properties can be passed via keyword arguments
		only and have to exactly match UDM property names (case-sensitive!).
		Please note: the object has to be created by create_object otherwise this call will raise an exception!

		:param str modulename: name of UDM module (e.g. 'users/user')
		"""
		if not modulename:
			raise UCSTestUDM_MissingModulename()
		dn = kwargs.get('dn')
		if not dn:
			raise UCSTestUDM_MissingDn()
		if dn not in self._cleanup.get(modulename, set()):
			raise UCSTestUDM_CannotModifyExistingObject(dn)

		cmd = self._build_udm_cmdline(modulename, 'modify', kwargs)
		print('Modifying %s object with %s' % (modulename, _prettify_cmd(cmd)))
		child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
		(stdout, stderr) = child.communicate()

		if six.PY3:
			stdout, stderr = stdout.decode('utf-8', 'replace'), stderr.decode('utf-8', 'replace')

		if child.returncode:
			raise UCSTestUDM_ModifyUDMObjectFailed({'module': modulename, 'kwargs': kwargs, 'returncode': child.returncode, 'stdout': stdout, 'stderr': stderr})

		for line in stdout.splitlines():  # :pylint: disable-msg=E1103
			if line.startswith('Object modified: '):
				dn = line.split('Object modified: ', 1)[-1]
				if dn != kwargs.get('dn'):
					print('modrdn detected: %r ==> %r' % (kwargs.get('dn'), dn))
					if kwargs.get('dn') in self._cleanup.get(modulename, []):
						self._cleanup.setdefault(modulename, []).append(dn)
						self._cleanup[modulename].remove(kwargs.get('dn'))
				break
			elif line.startswith('No modification: '):
				raise UCSTestUDM_NoModification({'module': modulename, 'kwargs': kwargs, 'stdout': stdout, 'stderr': stderr})
		else:
			raise UCSTestUDM_ModifyUDMUnknownDN({'module': modulename, 'kwargs': kwargs, 'stdout': stdout, 'stderr': stderr})

		self.wait_for(modulename, dn, wait_for_replication, everything=wait_for)
		return dn

	def move_object(self, modulename, wait_for_replication=True, check_for_drs_replication=False, wait_for=False, **kwargs):
		if not modulename:
			raise UCSTestUDM_MissingModulename()
		dn = kwargs.get('dn')
		if not dn:
			raise UCSTestUDM_MissingDn()
		if dn not in self._cleanup.get(modulename, set()):
			raise UCSTestUDM_CannotModifyExistingObject(dn)

		cmd = self._build_udm_cmdline(modulename, 'move', kwargs)
		print('Moving %s object %s' % (modulename, _prettify_cmd(cmd)))
		child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
		(stdout, stderr) = child.communicate()

		if six.PY3:
			stdout, stderr = stdout.decode('utf-8', 'replace'), stderr.decode('utf-8', 'replace')

		if child.returncode:
			raise UCSTestUDM_MoveUDMObjectFailed({'module': modulename, 'kwargs': kwargs, 'returncode': child.returncode, 'stdout': stdout, 'stderr': stderr})

		for line in stdout.splitlines():  # :pylint: disable-msg=E1103
			if line.startswith('Object modified: '):
				self._cleanup.get(modulename, []).remove(dn)

				new_dn = ldap.dn.dn2str(ldap.dn.str2dn(dn)[0:1] + ldap.dn.str2dn(kwargs.get('position', '')))
				self._cleanup.setdefault(modulename, []).append(new_dn)
				break
		else:
			raise UCSTestUDM_ModifyUDMUnknownDN({'module': modulename, 'kwargs': kwargs, 'stdout': stdout, 'stderr': stderr})

		self.wait_for(modulename, dn, wait_for_replication, everything=wait_for)
		return new_dn

	def remove_object(self, modulename, wait_for_replication=True, wait_for=False, **kwargs):
		if not modulename:
			raise UCSTestUDM_MissingModulename()
		dn = kwargs.get('dn')
		if not dn:
			raise UCSTestUDM_MissingDn()
		if dn not in self._cleanup.get(modulename, set()):
			raise UCSTestUDM_CannotModifyExistingObject(dn)

		cmd = self._build_udm_cmdline(modulename, 'remove', kwargs)
		print('Removing %s object %s' % (modulename, _prettify_cmd(cmd)))
		child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
		(stdout, stderr) = child.communicate()

		if six.PY3:
			stdout, stderr = stdout.decode('utf-8', 'replace'), stderr.decode('utf-8', 'replace')

		if child.returncode:
			raise UCSTestUDM_RemoveUDMObjectFailed({'module': modulename, 'kwargs': kwargs, 'returncode': child.returncode, 'stdout': stdout, 'stderr': stderr})

		if dn in self._cleanup.get(modulename, []):
			self._cleanup[modulename].remove(dn)

		self.wait_for(modulename, dn, wait_for_replication, everything=wait_for)

	def wait_for(self, modulename, dn, wait_for_replication=True, wait_for_drs_replication=False, wait_for_s4connector=False, everything=False):
		# the order of the conditions is imporant
		conditions = []
		if wait_for_replication:
			conditions.append((utils.ReplicationType.LISTENER, wait_for_replication))

		if everything:
			wait_for_drs_replication = True
			wait_for_s4connector = True
		drs_replication = wait_for_drs_replication
		ad_ldap_search_args = self.ad_object_identifying_filter(modulename, dn)
		if wait_for_drs_replication and not isinstance(wait_for_drs_replication, six.string_types):
			drs_replication = False
			if ad_ldap_search_args:
				drs_replication = ad_ldap_search_args

		if wait_for_s4connector and ad_ldap_search_args:
			if self._ucr.get('samba4/ldap/base'):
				conditions.append((utils.ReplicationType.S4C_FROM_UCS, ad_ldap_search_args))

		if drs_replication:
			if not wait_for_replication:
				conditions.append((utils.ReplicationType.LISTENER, wait_for_replication))

			if self._ucr.get('server/role') in ('domaincontroller_backup', 'domaincontroller_slave', 'memberserver'):
				conditions.append((utils.ReplicationType.DRS, drs_replication))

		return utils.wait_for(conditions, verbose=False)

	def create_user(self, wait_for_replication=True, check_for_drs_replication=True, wait_for=True, **kwargs):  # :pylint: disable-msg=W0613
		"""
		Creates a user via UDM CLI. Values for UDM properties can be passed via keyword arguments only and
		have to exactly match UDM property names (case-sensitive!). Some properties have default values:

		:param str position: 'cn=users,$ldap_base'
		:param str password: 'univention'
		:param str firstname: 'Foo Bar'
		:param str lastname: <random string>
		:param str username: <random string> If username is missing, a random user name will be used.
		:return: (dn, username)
		"""

		attr = self._set_module_default_attr(kwargs, (
			('position', 'cn=users,%s' % self.LDAP_BASE),
			('password', 'univention'),
			('username', uts.random_username()),
			('lastname', uts.random_name()),
			('firstname', uts.random_name())
		))

		return (self.create_object('users/user', wait_for_replication, check_for_drs_replication, wait_for=wait_for, **attr), attr['username'])

	def create_ldap_user(self, wait_for_replication=True, check_for_drs_replication=False, **kwargs):  # :pylint: disable-msg=W0613
		# check_for_drs_replication=False -> ldap users are not replicated to s4
		attr = self._set_module_default_attr(kwargs, (
			('position', 'cn=users,%s' % self.LDAP_BASE),
			('password', 'univention'),
			('username', uts.random_username()),
			('lastname', uts.random_name()),
			('name', uts.random_name())
		))

		return (self.create_object('users/ldap', wait_for_replication, check_for_drs_replication, **attr), attr['username'])

	def remove_user(self, username, wait_for_replication=True):
		"""Removes a user object from the ldap given it's username."""
		kwargs = {
			'dn': 'uid=%s,cn=users,%s' % (username, self.LDAP_BASE)
		}
		self.remove_object('users/user', wait_for_replication, **kwargs)

	def create_with_defaults(self, module_name, wait_for_replication=True, check_for_drs_replication=True, **kwargs):  # :pylint: disable-msg=W0613
		modules_dict = {
			'appcenter': self.create_appcenter,
			'computers': self.create_computer,
			'container': self.create_container,
			'dhcp': self.create_dhcp,
			'dns': self.create_dns,
			'groups': self.create_groups,
			'kerberos': self.create_kerberos,
			'mail': self.create_mail,
			'nagios': self.create_nagios,
			'networks': self.create_networks,
			'policies': self.create_policies,
			'saml': self.create_saml,
			'settings': self.create_settings,
			'shares': self.create_shares,
			'users': self.create_users,
			'uvnm': self.create_uvmm,
		}
		return modules_dict[module_name.split('/')[0]](module_name, wait_for_replication, check_for_drs_replication, **kwargs)

	def create_group(self, wait_for_replication=True, check_for_drs_replication=True, **kwargs):  # :pylint: disable-msg=W0613
		"""
		Creates a group via UDM CLI. Values for UDM properties can be passed via keyword arguments only and
		have to exactly match UDM property names (case-sensitive!). Some properties have default values:

		:param str position: `cn=users,$ldap_base`
		:param str name: <random value>
		:return: (dn, groupname)

		If "groupname" is missing, a random group name will be used.
		"""
		attr = self._set_module_default_attr(kwargs, (
			('position', 'cn=groups,%s' % self.LDAP_BASE),
			('name', uts.random_groupname())
		))

		return self.create_object('groups/group', wait_for_replication, check_for_drs_replication, **attr)

	def create_groups(self, module_name, wait_for_replication=True, check_for_drs_replication=True, **kwargs):  # :pylint: disable-msg=W0613
		"""
		Creates a group via UDM CLI. Values for UDM properties can be passed via keyword arguments only and
		have to exactly match UDM property names (case-sensitive!). Some properties have default values:

		:param str position: `cn=users,$ldap_base`
		:param str name: <random value>
		:return: (dn, groupname)

		If "groupname" is missing, a random group name will be used.
		"""
		attr = self._set_module_default_attr(kwargs, (
			('position', 'cn=groups,%s' % self.LDAP_BASE),
			('name', uts.random_groupname())
		))

		return self.create_object(module_name, wait_for_replication, check_for_drs_replication, **attr)

	def create_appcenter(self, module_name, wait_for_replication=True, check_for_drs_replication=True, **kwargs):  # :pylint: disable-msg=W0613
		attr = self.__set_module_default_attr(kwargs, (('position', 'cn=appcenter,%s' % self.LDAP_BASE),
													   ('id', -1),
													   ('name', uts.random_name()),
													   ('version', '%i.%i' % (uts.random_int(bottom_end=0, top_end=9), uts.random_int(bottom_end=0, top_end=9)))
													   )
											  )

		return self.create_object(module_name, wait_for_replication, check_for_drs_replication, **attr)

	def create_kerberos(self, module_name, wait_for_replication=True, check_for_drs_replication=True, **kwargs):  # :pylint: disable-msg=W0613
		attr = self.__set_module_default_attr(kwargs, (
			('position', 'cn=kerberos,%s' % self.LDAP_BASE),
			('name', uts.random_element_name)
		))

		return self.create_object(module_name, wait_for_replication, check_for_drs_replication, **attr)

	def create_networks(self, module_name, wait_for_replication=True, check_for_drs_replication=True, **kwargs):  # :pylint: disable-msg=W0613
		attr = self.__set_module_default_attr(kwargs, (
			('position', 'cn=networks,%s' % self.LDAP_BASE),
			('name', uts.random_element_name),
			('network', '%i.%i.%i.%i' % (
				uts.random_int(bottom_end=0, top_end=256),
				uts.random_int(bottom_end=0, top_end=256),
				uts.random_int(bottom_end=0, top_end=256),
				uts.random_int(bottom_end=0, top_end=256)
			)),
			('networkmask', '%i.%i.%i.%i' % (
				uts.random_int(bottom_end=0, top_end=256),
				uts.random_int(bottom_end=0, top_end=256),
				uts.random_int(bottom_end=0, top_end=256),
				uts.random_int(bottom_end=0, top_end=256)
			))
		))

		return self.create_object(module_name, wait_for_replication, check_for_drs_replication, **attr)

	def create_dns(self, module_name, wait_for_replication=True, check_for_drs_replication=True, **kwargs):  # :pylint: disable-msg=W0613
		attr_dict = {
			'alias': (('position', 'cn=dns,%s' % self.LDAP_BASE),
					  ('name', uts.random_name()),
					  ('cname', uts.random_name())),
			'dns': (('position', 'cn=dns,%s' % self.LDAP_BASE),
					('name', uts.random_name())),
			'forward_zone': (('position', 'cn=dns,%s' % self.LDAP_BASE),
							 ('zone', uts.random_name()),
							 ('nameserver', udm.FQHN),
							 ('zonettl', '%s' % (uts.random_int(bottom_end=100, top_end=999))),
							 ('contact', '%s@%s.%s' % (uts.random_name(), uts.random_name(), uts.random_name())),
							 ('serial', '%s' % (uts.random_int())),
							 ('refresh', '%s' % (uts.random_int(bottom_end=10, top_end=99))),
							 ('expire', '%s' % (uts.random_int(bottom_end=10, top_end=99))),
							 ('ttl', '%s' % (uts.random_int(bottom_end=10, top_end=99))),
							 ('retry', '%s' % (uts.random_int()))),
			'host_record': (('position', 'cn=dns,%s' % self.LDAP_BASE),
							('name', uts.random_name()),
							('zone', uts.random_name()),
							('nameserver', udm.FQHN),
							('zonettl', '%s' % (uts.random_int(bottom_end=100, top_end=999))),
						 	('contact', '%s@%s.%s' % (uts.random_name(), uts.random_name(), uts.random_name())),
					 		('serial', '%s' % (uts.random_int())),
						 	('refresh', '%s' % (uts.random_int(bottom_end=10, top_end=99))),
						 	('expire', '%s' % (uts.random_int(bottom_end=10, top_end=99))),
						 	('ttl', '%s' % (uts.random_int(bottom_end=10, top_end=99))),
						 	('retry', '%s' % (uts.random_int()))),
			'ns_record': (('position', 'cn=dns,%s' % self.LDAP_BASE),
						  ('zone', uts.random_name()),
						  ('nameserver', udm.FQHN)),
			'ptr_record': (('position', 'cn=dns,%s' % self.LDAP_BASE),
						   ('address', uts.random_ip().split('.')),
						   ('ptr_record', '%s.%s.' % (uts.random_name(), uts.random_name()))),
			'srv_record': (('position', 'cn=dns,%s' % self.LDAP_BASE),
						   ('name', uts.random_name()),
						   ('location', '0 1 2 %s.%s' % (uts.random_name(), uts.random_name()))),
			'txt_record': (('position', 'cn=dns,%s' % self.LDAP_BASE),
						   ('name', uts.random_name()),
						   ('txt', uts.random_name())),
		}
		attr = self.__set_module_default_attr(kwargs, attr_dict[module_name.spliit('/')[1]])

		return self.create_object(module_name, wait_for_replication, check_for_drs_replication, **attr)

	def create_nagios(self, module_name, wait_for_replication=True, check_for_drs_replication=True, **kwargs):  # :pylint: disable-msg=W0613
		attr_dict = {
			'service': (('position', 'cn=nagios,%s' % self.LDAP_BASE),
						('name', uts.random_name()),
						('checkCommand', uts.random_name())),
			'timeperiod': (('position', 'cn=nagios,%s' % self.LDAP_BASE),
						   ('name', uts.random_name()),
						   ('description', uts.random_name()))
		}
		attr = self.__set_module_default_attr(kwargs, attr_dict[module_name.split('/')[1]])

		return self.create_object(module_name, wait_for_replication, check_for_drs_replication, **attr)

	def create_users(self, module_name, wait_for_replication=True, check_for_drs_replication=True, **kwargs):  # :pylint: disable-msg=W0613
		attr_dict = {
			'contact': (('position', 'cn=users,%s' % self.LDAP_BASE),
						('lastname', uts.random_name()),
						('homePostalAddress', [udm.random_name()])),
			'ldap': (('position', 'cn=users,%s' % self.LDAP_BASE),
					 ('username', uts.random_name()),
					 ('password', uts.random_name())),
			'user': (('position', 'cn=users,%s' % self.LDAP_BASE),
					 ('lastname', uts.random_name()),
					 ('username', uts.random_name()),
					 ('password', uts.random_name()),
					 ('umcProperty', [udm.random_name()]),
					 ('disabled', bool(uts.random_int(bottom_end=0, top_end=1))))
		}
		attr = self.__set_module_default_attr(kwargs, attr_dict[module_name.split('/')[1]])

		return self.create_object(module_name, wait_for_replication, check_for_drs_replication, **attr)

	def create_uvmm(self, module_name, wait_for_replication=True, check_for_drs_replication=True, **kwargs):  # :pylint: disable-msg=W0613
		attr_dict = {
			'cloudconnection': (('position', 'cn=uvmm,%s' % self.LDAP_BASE),
								('name', uts.random_name()),
								('type', "cn=%s,cn=CloudType,cn=Virtual Machine Manager,dc=ucs,dc=local" % uts.random_name()),
								('searchPattern', uts.random_name()),
								('includeUCSimages', 0),
								('parameter', ["password %s" % uts.random_name()])),
			'cloudtype': (('position', 'cn=uvmm,%s' % self.LDAP_BASE),
						  ('name', uts.random_name())),
			'info': (('position', 'cn=uvmm,%s' % self.LDAP_BASE),
					 ('uuid', uts.random_name())),
			"profile": (('position', 'cn=uvmm,%s' % self.LDAP_BASE),
						('name', uts.random_name()))
		}
		attr = self.__set_module_default_attr(kwargs, attr_dict[module_name.split('/')[1]])

		return self.create_object(module_name, wait_for_replication, check_for_drs_replication, **attr)

	def create_policies(self, module_name, wait_for_replication=True, check_for_drs_replication=True, **kwargs):  # :pylint: disable-msg=W0613
		attr_dict = {
			'admin_container': (('position', 'cn=policies,%s' % self.LDAP_BASE),
								('name', uts.random_name())),
			'autostart': (('position', 'cn=policies,%s' % self.LDAP_BASE),
						  ('name', uts.random_name())),
			'desktop': (('position', 'cn=policies,%s' % self.LDAP_BASE),
						('name', uts.random_name())),
			'dhcp_boot': (('position', 'cn=policies,%s' % self.LDAP_BASE),
						  ('name', uts.random_name())),
			'dhcp_dns': (('position', 'cn=policies,%s' % self.LDAP_BASE),
						 ('name', uts.random_name())),
			'dhcp_dnsupdate': (('position', 'cn=policies,%s' % self.LDAP_BASE),
							   ('name', uts.random_name())),
			'dhcp_leasetime': (('position', 'cn=policies,%s' % self.LDAP_BASE),
							   ('name', uts.random_name())),
			'dhcp_netbios': (('position', 'cn=policies,%s' % self.LDAP_BASE),
							 ('name', uts.random_name())),
			'dhcp_routing': (('position', 'cn=policies,%s' % self.LDAP_BASE),
							 ('name', uts.random_name()),
							 ('routers', '%i.%i.%i.%i' % (
								 uts.random_int(bottom_end=0, top_end=256),
								 uts.random_int(bottom_end=0, top_end=256),
								 uts.random_int(bottom_end=0, top_end=256),
								 uts.random_int(bottom_end=0, top_end=256)
							 ))),
			'dhcp_scope': (('position', 'cn=policies,%s' % self.LDAP_BASE),
						   ('name', uts.random_name())),
			'dhcp_statements': (('position', 'cn=policies,%s' % self.LDAP_BASE),
								('name', uts.random_name())),
			'ldapserver': (('position', 'cn=policies,%s' % self.LDAP_BASE),
						   ('name', uts.random_name())),
			'maintenance': (('position', 'cn=policies,%s' % self.LDAP_BASE),
							('name', uts.random_name()),
							('minute', uts.random_int())),
			'masterpackages': (('position', 'cn=policies,%s' % self.LDAP_BASE),
							   ('name', uts.random_name())),
			'memberpackages': (('position', 'cn=policies,%s' % self.LDAP_BASE),
							   ('name', uts.random_name())),
			'nfsmounts': (('position', 'cn=policies,%s' % self.LDAP_BASE),
						  ('name', uts.random_name())),
			'policy': (('position', 'cn=policies,%s' % self.LDAP_BASE),
					   ('name', uts.random_name())),
			'print_quota': (('position', 'cn=policies,%s' % self.LDAP_BASE),
							('name', uts.random_name())),
			'printserver': (('position', 'cn=policies,%s' % self.LDAP_BASE),
							('name', uts.random_name())),
			'pwhistory': (('position', 'cn=policies,%s' % self.LDAP_BASE),
						  ('name', uts.random_name())),
			'registry': (('position', 'cn=policies,%s' % self.LDAP_BASE),
						 ('name', uts.random_name())),
			'release': (('position', 'cn=policies,%s' % self.LDAP_BASE),
						('name', uts.random_name())),
			'repositoryserver': (('position', 'cn=policies,%s' % self.LDAP_BASE),
								 ('name', uts.random_name())),
			'repositorysync': (('position', 'cn=policies,%s' % self.LDAP_BASE),
							   ('name', uts.random_name()),
							   ('minute', uts.random_int())),
			'share_userquota': (('position', 'cn=policies,%s' % self.LDAP_BASE),
								('name', uts.random_name())),
			'slavepackages': (('position', 'cn=policies,%s' % self.LDAP_BASE),
							  ('name', uts.random_name())),
			'umc': (('position', 'cn=policies,%s' % self.LDAP_BASE),
					('name', uts.random_name()),
					('allow', [['create', 'add', 'list'][uts.random_int(bottom_end=0, top_end=2)]]))
		}
		attr = self.__set_module_default_attr(kwargs, attr_dict[module_name.split('/')[1]])

		return self.create_object(module_name, wait_for_replication, check_for_drs_replication, **attr)

	def create_settings(self, module_name, wait_for_replication=True, check_for_drs_replication=True, **kwargs):  # :pylint: disable-msg=W0613
		attr_dict = {
			'data': (('position', 'cn=settings,%s' % self.LDAP_BASE),
					 ('name', uts.random_name()),
					 ('data_type', uts.random_name()),
					 ('meta', [uts.random_name(), uts.random_name()]),
					 ('ucsversionend', uts.random_ucs_version())),
			'default': (('position', 'cn=settings,%s' % self.LDAP_BASE),
						('name', uts.random_name())),
			'directory': (('position', 'cn=settings,%s' % self.LDAP_BASE),
						  ('name', uts.random_name()),
						  ('users', 'dc=foo,dc=bar,dc=%s' % uts.random_name())),
			'extended_attributes': (('position', 'cn=settings,%s' % self.LDAP_BASE),
									('name', uts.random_name()),
									('shortDescription', uts.random_name())),
			'extended_options': (('position', 'cn=settings,%s' % self.LDAP_BASE),
								 ('name', uts.random_name()),
									('shortDescription', uts.random_name()),
								 ('module', [uts.random_name()])),
			'ldapacl': (('position', 'cn=settings,%s' % self.LDAP_BASE),
						('name', uts.random_name()),
						('filename', uts.random_name()),
						('data', base64.encodebytes(bz2.compress(uts.random_name()))),
						('appidentifier', udm.random_name())),
			'ldapschema': (('position', 'cn=settings,%s' % self.LDAP_BASE),
						   ('name', uts.random_name()),
						   ('filename', uts.random_name()),
						   ('data', uts.random_name()),
						   ('appidentifier', udm.random_name())),
			'license': (('position', 'cn=settings,%s' % self.LDAP_BASE),
						('name', uts.random_name()),
						('expires', uts.random_name()),
						('module', uts.random_name()),
						('base', uts.random_name()),
						('signature', uts.random_name()),
						('expires', uts.random_name())),
			'lock': (('position', 'cn=settings,%s' % self.LDAP_BASE),
					 ('name', uts.random_name()),
					 ('locktime', uts.random_name())),
			'packages': (('position', 'cn=settings,%s' % self.LDAP_BASE),
						 ('name', uts.random_name()),
						 ('packagelist', [uts.random_name()])),
			'portal': (('position', 'cn=settings,%s' % self.LDAP_BASE),
					   ('name', uts.random_name()),
					   ('displayName', ['de', uts.random_name()])),
			'portal_all': (('position', 'cn=settings,%s' % self.LDAP_BASE),
						   ('name', uts.random_name())),
			'portal_category': (('position', 'cn=settings,%s' % self.LDAP_BASE),
								('name', uts.random_name()),
								('displayName', ['de', uts.random_name()])),
			'portal_entry': (('position', 'cn=settings,%s' % self.LDAP_BASE),
							 ('name', uts.random_name()),
							 ('displayName', ['de', uts.random_name()]),
							 ('description', ['de', uts.random_name()]),
							 ('link', [uts.random_name()])),
			'printermodel': (('position', 'cn=settings,%s' % self.LDAP_BASE),
							 ('name', uts.random_name()),
							 ('printmodel', [uts.random_name()])),
			'printeruri': (('position', 'cn=settings,%s' % self.LDAP_BASE),
						   ('name', uts.random_name()),
						   ('printeruri', [udm.random_name()])),
			'prohibited_username': (('position', 'cn=settings,%s' % self.LDAP_BASE),
									('name', uts.random_name()),
									('usernames', [udm.random_name()])),
			'sambaconfig': (('position', 'cn=settings,%s' % self.LDAP_BASE),
							('name', uts.random_name()),
							('SID', uts.random_name())),
			'sambadomain': (('position', 'cn=settings,%s' % self.LDAP_BASE),
							('name', uts.random_name()),
							('SID', uts.random_name())),
			'service': (('position', 'cn=settings,%s' % self.LDAP_BASE),
						('name', uts.random_name())),
			'syntax': (('position', 'cn=settings,%s' % self.LDAP_BASE),
					   ('name', uts.random_name()),
					   ('filter', uts.random_name()),
					   ('attribute', 'computers/memberserver: %s' % uts.random_name())),
			'udm_hook': (('position', 'cn=settings,%s' % self.LDAP_BASE),
						 ('name', uts.random_name()),
						 ('filename', uts.random_name()),
						 ('data', uts.random_name()),
						 ('appidentifier', udm.random_name())),
			'udm_module': (('position', 'cn=settings,%s' % self.LDAP_BASE),
						   ('name', uts.random_name()),
						   ('filename', uts.random_name()),
						   ('data', uts.random_name()),
						   ('appidentifier', udm.random_name())),
			'udm_syntax': (('position', 'cn=settings,%s' % self.LDAP_BASE),
						   ('name', uts.random_name()),
						   ('filename', uts.random_name()),
						   ('data', uts.random_name()),
						   ('appidentifier', udm.random_name())),
			'umc_operationset': (('position', 'cn=settings,%s' % self.LDAP_BASE),
								 ('name', uts.random_name()),
								 ('description', uts.random_name()),
								 ('operation', ["lib/%s/*" % uts.random_name()])),
			'usertemplate': (('position', 'cn=settings,%s' % self.LDAP_BASE),
							 ('name', uts.random_name()),
							 ('e-mail', ['%s@univention.com' % uts.random_name()]),
							 ('departmentNumbuer', [uts.random_int()]),
							 ('disabled', bool(uts.random_int(bottom_end=0, top_end=1)))),
			'xconfig_choices': (('position', 'cn=settings,%s' % self.LDAP_BASE),
								('name', uts.random_name()))
		}
		attr = self.__set_module_default_attr(kwargs, attr_dict[module_name].split('/')[1])

		return self.create_object(module_name, wait_for_replication, check_for_drs_replication, **attr)

	def create_saml(self, module_name, wait_for_replication=True, check_for_drs_replication=True, **kwargs):  # :pylint: disable-msg=W0613
		attr_dict = {
			'idconfig': (('position', 'cn=saml,%s' % self.LDAP_BASE),
						 ('id', 0)),
			'serviceprovider': (('position', 'cn=saml,%s' % self.LDAP_BASE),
								('Identifier', uts.random_int()),
								('AssertionConsumerService', [uts.random_name()]))
		}
		attr = self.__set_module_default_attr(kwargs, attr_dict[module_name.split('/')[1]])

		return self.create_object(module_name, wait_for_replication, check_for_drs_replication, **attr)

	def create_shares(self, module_name, wait_for_replication=True, check_for_drs_replication=True, **kwargs):  # :pylint: disable-msg=W0613
		attr_dict = {
			'printer': (('position', 'cn=printer,%s' % self.LDAP_BASE),
						('name', uts.random_name()),
						('spoolHost', [uts.random_name()]),
						('uri', "uri=socket:// 127.0.0.1:%i" % uts.random_int()),
						('model', uts.random_name())),
			'printergroup': (('position', 'cn=printer,%s' % self.LDAP_BASE),
							 ('name', uts.random_name()),
							 ('sppoolHost', [uts.random_domain_name()]),
							 ('groupMember', [uts.random_name()])),
			'share': (('position', 'cn=printer,%s' % self.LDAP_BASE),
					  ('name', uts.random_name()),
					  ('host', uts.random_name()),
					  ('path', uts.random_name()),
					  ('writeable', bool(uts.random_int(bottom_end=0, top_end=1)))),
		}
		attr = self.__set_module_default_attr(kwargs, attr_dict[module_name.split('/')[1]])

		return self.create_object(module_name, wait_for_replication, check_for_drs_replication, **attr)

	def create_computer(self, module_name, wait_for_replication=True, check_for_drs_replication=True, **kwargs):  # :pylint: disable-msg=W0613
		attr_dict = {
			'domaincontroller_backup': (('position', 'cn=computers,%s' % self.LDAP_BASE),
										('name', uts.random_name()),
										('service', [uts.random_name(), uts.random_name()]),
										('inventoryNumber', [str(uts.random_int())]),
										('reinstall', bool(uts.random_int(bottom_end=0, top_end=1)))),
			'domaincontroller_master': (('position', 'cn=computers,%s' % self.LDAP_BASE),
										('name', uts.random_name()),
										('service', [uts.random_name(), uts.random_name()]),
										('inventoryNumber', [str(uts.random_int())]),
										('reinstall', bool(uts.random_int(bottom_end=0, top_end=1)))),
			'domaincontroller_slave': (('position', 'cn=computers,%s' % self.LDAP_BASE),
										('name', uts.random_name()),
										('service', [uts.random_name(), uts.random_name()]),
										('inventoryNumber', [str(uts.random_int())]),
										('reinstall', bool(uts.random_int(bottom_end=0, top_end=1)))),
			'ipmanagedclient': (('position', 'cn=computers,%s' % self.LDAP_BASE),
								('name', uts.random_name()),
								('ip', ['%i.%i.%i.%i' % (
									uts.random_int(bottom_end=0, top_end=256),
									uts.random_int(bottom_end=0, top_end=256),
									uts.random_int(bottom_end=0, top_end=256),
									uts.random_int(bottom_end=0, top_end=256)
								)]),
								('inventoryNumber', [str(uts.random_int())]),
								('network', uts.random_name())),
			'linux': (('position', 'cn=computers,%s' % self.LDAP_BASE),
						('name', uts.random_name()),
						('ip', ['%i.%i.%i.%i' % (
							uts.random_int(bottom_end=0, top_end=256),
							uts.random_int(bottom_end=0, top_end=256),
							uts.random_int(bottom_end=0, top_end=256),
							uts.random_int(bottom_end=0, top_end=256)
						)]),
						('inventoryNumber', [str(uts.random_int())]),
						('unixhome', '/%s' % (uts.random_name()))),
			'macos': (('position', 'cn=computers,%s' % self.LDAP_BASE),
						('name', uts.random_name()),
						('ip', ['%i.%i.%i.%i' % (
							uts.random_int(bottom_end=0, top_end=256),
							uts.random_int(bottom_end=0, top_end=256),
							uts.random_int(bottom_end=0, top_end=256),
							uts.random_int(bottom_end=0, top_end=256)
						)]),
						('inventoryNumber', [str(uts.random_int())]),
						('unixhome', '/%s' % uts.random_name())),
			'memberserver': (('position', 'cn=computers,%s' % self.LDAP_BASE),
							('name', uts.random_name()),
							('ip', ['%i.%i.%i.%i' % (
								uts.random_int(bottom_end=0, top_end=256),
								uts.random_int(bottom_end=0, top_end=256),
								uts.random_int(bottom_end=0, top_end=256),
								uts.random_int(bottom_end=0, top_end=256)
							)]),
							('inventoryNumber', [str(uts.random_int())]),
							('unixhome', '/%s' % uts.random_name())),
			'trustaccount': (('position', 'cn=computers,%s' % self.LDAP_BASE),
							 ('name', uts.random_name()),
							 ('password', uts.random_name())),
			'ubuntu': (('position', 'cn=computers,%s' % self.LDAP_BASE),
						('name', uts.random_name()),
						('ip', ['%i.%i.%i.%i' % (
							uts.random_int(bottom_end=0, top_end=256),
							uts.random_int(bottom_end=0, top_end=256),
							uts.random_int(bottom_end=0, top_end=256),
							uts.random_int(bottom_end=0, top_end=256)
						)]),
						('inventoryNumber', [str(uts.random_int())]),
						('unixhome', '/%s' % uts.random_name())),
			'windows': (('position', 'cn=computers,%s' % self.LDAP_BASE),
						('name', uts.random_name()),
						('ip', ['%i.%i.%i.%i' % (
							uts.random_int(bottom_end=0, top_end=256),
							uts.random_int(bottom_end=0, top_end=256),
							uts.random_int(bottom_end=0, top_end=256),
							uts.random_int(bottom_end=0, top_end=256)
						)]),
						('inventoryNumber', [str(uts.random_int())]),
						('unixhome', '/%s' % (uts.random_name()))),
			'wwindows_domaincontroller': (('position', 'cn=computers,%s' % self.LDAP_BASE),
											('name', uts.random_name()),
											('ip', ['%i.%i.%i.%i' % (
												uts.random_int(bottom_end=0, top_end=256),
												uts.random_int(bottom_end=0, top_end=256),
												uts.random_int(bottom_end=0, top_end=256),
												uts.random_int(bottom_end=0, top_end=256)
											)]),
											('inventoryNumber', [str(uts.random_int())]),
											('unixhome', '/%s' % (uts.random_name())))
		}
		attr = self.__set_module_default_attr(kwargs, attr_dict[module_name.split('/')[1]])

		return self.create_object(module_name, wait_for_replication, check_for_drs_replication, **attr)

	def create_container(self, module_name, wait_for_replication=True, check_for_drs_replication=True, **kwargs):  # :pylint: disable-msg=W0613
		attr_dict = {
			'cn': (('position', 'cn=container,%s' % self.LDAP_BASE),
				   ('name', uts.random_name()),
				   ('dnsForwardZone', ['%i.%i.%i.%i' % (
					   uts.random_int(bottom_end=0, top_end=256),
					   uts.random_int(bottom_end=0, top_end=256),
					   uts.random_int(bottom_end=0, top_end=256),
					   uts.random_int(bottom_end=0, top_end=256)
				   )])),
			'dc': (('position', 'cn=container,%s' % self.LDAP_BASE),
				   ('name', uts.random_name()),
				   ('sambaSID', uts.random_int())),
			'ou': (('position', 'cn=container,%s' % self.LDAP_BASE),
				   ('name', uts.random_name()))
		}
		attr = self.__set_module_default_attr(kwargs, attr_dict[module_name.split('/')[1]])

		return self.create_object(module_name, wait_for_replication, check_for_drs_replication, **attr)

	def create_mail(self, module_name, wait_for_replication=True, check_for_drs_replication=True, **kwargs):  # :pylint: disable-msg=W0613
		attr_dict = {
			'domain': (('position', 'cn=mail,%s' % self.LDAP_BASE),
					   ('name', uts.random_name())),
			'folder': (('position', 'cn=mail,%s' % self.LDAP_BASE),
					   ('name', uts.random_name()),
					   ('mailDomain', uts.random_name()),
					   ('mailHomeServer', uts.random_domain_name())),
			'lists': (('position', 'cn=mail,%s' % self.LDAP_BASE),
					  ('name', uts.random_name())),
		}
		attr = self.__set_module_default_attr(kwargs, attr_dict[module_name.split('/')[1]])

		return self.create_object(module_name, wait_for_replication, check_for_drs_replication, **attr)

	def create_dhcp(self, module_name, wait_for_replication=True, check_for_drs_replication=True, **kwargs):  # :pylint: disable-msg=W0613
		attr_dict = {
			'pool': (('position', 'cn=dhcp,%s' % self.LDAP_BASE),
					 ('name', uts.random_name()),
					 ('range', ['%i.%i.%i.%i' % (
						 uts.random_int(bottom_end=0, top_end=256),
						 uts.random_int(bottom_end=0, top_end=256),
						 uts.random_int(bottom_end=0, top_end=256),
						 uts.random_int(bottom_end=0, top_end=256)
					 ), '%i.%i.%i.%i' % (
						 uts.random_int(bottom_end=0, top_end=256),
						 uts.random_int(bottom_end=0, top_end=256),
						 uts.random_int(bottom_end=0, top_end=256),
						 uts.random_int(bottom_end=0, top_end=256)
					 )])),
			'host': (('position', 'cn=dhcp,%s' % self.LDAP_BASE),
					 ('host', uts.random_name()),
					 ('fixedaddress', ['%i.%i.%i.%i' % (
						 uts.random_int(bottom_end=0, top_end=256),
						 uts.random_int(bottom_end=0, top_end=256),
						 uts.random_int(bottom_end=0, top_end=256),
						 uts.random_int(bottom_end=0, top_end=256)
					 )]),
					 ('hwaddress', 'ethernet 00:11:22:%i:%i:%i' % (
						 uts.random_int(bottom_end=10, top_end=99),
						 uts.random_int(bottom_end=10, top_end=99),
						 uts.random_int(bottom_end=10, top_end=99)
					 ))),
			'subnet': (('position', 'cn=dhcp,%s' % self.LDAP_BASE),
					   ('subnet', '%i.%i.%i.%i' % (
						   uts.random_int(bottom_end=0, top_end=256),
						   uts.random_int(bottom_end=0, top_end=256),
						   uts.random_int(bottom_end=0, top_end=256),
						   uts.random_int(bottom_end=0, top_end=256)
					   )),
					   ('subnetmask', '%i.%i.%i.%i' % (
						   uts.random_int(bottom_end=0, top_end=256),
						   uts.random_int(bottom_end=0, top_end=256),
						   uts.random_int(bottom_end=0, top_end=256),
						   uts.random_int(bottom_end=0, top_end=256)
					   )),
					   ('range', ['%i.%i.%i.%i' % (
						 uts.random_int(bottom_end=0, top_end=256),
						 uts.random_int(bottom_end=0, top_end=256),
						 uts.random_int(bottom_end=0, top_end=256),
						 uts.random_int(bottom_end=0, top_end=256)
					 ), '%i.%i.%i.%i' % (
						 uts.random_int(bottom_end=0, top_end=256),
						 uts.random_int(bottom_end=0, top_end=256),
						 uts.random_int(bottom_end=0, top_end=256),
						 uts.random_int(bottom_end=0, top_end=256)
					 )])),
			'shared': (('position', 'cn=dhcp,%s' % self.LDAP_BASE),
					   ('name', uts.random_name())),
			'service': (('position', 'cn=dhcp,%s' % self.LDAP_BASE),
						('service', uts.random_name())),
			'sharedsubnet': (('position', 'cn=dhcp,%s' % self.LDAP_BASE),
							 ('subnet', '%i.%i.%i.%i' % (
								 uts.random_int(bottom_end=0, top_end=256),
								 uts.random_int(bottom_end=0, top_end=256),
								 uts.random_int(bottom_end=0, top_end=256),
								 uts.random_int(bottom_end=0, top_end=256)
							 )),
							 ('subnetmask', '%i.%i.%i.%i' % (
								 uts.random_int(bottom_end=0, top_end=256),
								 uts.random_int(bottom_end=0, top_end=256),
								 uts.random_int(bottom_end=0, top_end=256),
								 uts.random_int(bottom_end=0, top_end=256)
							 )),
							 ('range', ['%i.%i.%i.%i' % (
						 uts.random_int(bottom_end=0, top_end=256),
						 uts.random_int(bottom_end=0, top_end=256),
						 uts.random_int(bottom_end=0, top_end=256),
						 uts.random_int(bottom_end=0, top_end=256)
					 ), '%i.%i.%i.%i' % (
						 uts.random_int(bottom_end=0, top_end=256),
						 uts.random_int(bottom_end=0, top_end=256),
						 uts.random_int(bottom_end=0, top_end=256),
						 uts.random_int(bottom_end=0, top_end=256)
					 )]))
		}
		attr = self.__set_module_default_attr(kwargs, attr_dict[module_name.split('/')[1]])

		return self.create_object(module_name, wait_for_replication, check_for_drs_replication, **attr)

	def _set_module_default_attr(self, attributes, defaults):
		"""
		Returns the given attributes, extended by every property given in defaults if not yet set.

		:param tuple defaults: should be a tupel containing tupels like "('username', <default_value>)".
		"""
		attr = copy.deepcopy(attributes)
		for prop, value in defaults:
			attr.setdefault(prop, value)
		return attr

	def addCleanupLock(self, lockType, lockValue):
		self._cleanupLocks.setdefault(lockType, []).append(lockValue)

	def _wait_for_drs_removal(self, modulename, dn, verbose=True):
		ad_ldap_search_args = self.ad_object_identifying_filter(modulename, dn)
		if ad_ldap_search_args:
			wait_for_drs_replication(should_exist=False, verbose=verbose, timeout=20, **ad_ldap_search_args)

	def list_objects(self, modulename, **kwargs):
		cmd = self._build_udm_cmdline(modulename, 'list', kwargs)
		print('Listing %s objects %s' % (modulename, _prettify_cmd(cmd)))
		child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
		(stdout, stderr) = child.communicate()

		if six.PY3:
			stdout, stderr = stdout.decode('utf-8', 'replace'), stderr.decode('utf-8', 'replace')

		if child.returncode:
			raise UCSTestUDM_ListUDMObjectFailed(child.returncode, stdout, stderr)

		objects = []
		dn = None
		attrs = {}
		pattr = None
		pvalue = None
		pdn = None
		current_policy_type = None
		for line in stdout.splitlines():
			if line.startswith('DN: '):
				if dn:
					objects.append((dn, attrs))
					dn = None
					attrs = {}
				dn = line[3:].strip()
			elif not line.strip():
				continue
			elif line.startswith('    ') and ':' in line:  # list --policies=1
				name, value = line.split(':', 1)
				if name.strip() == 'Policy':
					pvalue = pattr = None
					pdn = value
				elif name.strip() == 'Attribute':
					pattr = value
				elif name.strip() == 'Value':
					pvalue = value
					attrs.setdefault(current_policy_type, {}).setdefault(pdn.strip(), {}).setdefault(pattr.strip(), []).append(pvalue.strip())
			elif line.startswith('    ') and '=' in line:  # list --policies=2
				name, value = line.split('=', 1)
				attrs.setdefault(current_policy_type, {}).setdefault(name.strip(), []).append(value.strip().strip('"'))
			elif any(x in line for x in ('Policy-based Settings', 'Subnet-based Settings', 'Merged Settings')):
				current_policy_type = line.split(':')[0].strip()
			elif line.startswith(' ') and ':' in line:
				name, value = line.split(':', 1)
				attrs.setdefault(name.strip(), []).append(value.strip())
		if dn:
			objects.append((dn, attrs))
		return objects

	def cleanup(self):
		"""
		Automatically removes LDAP objects via UDM CLI that have been created before.
		"""
		failedObjects = {}
		print('Performing UCSTestUDM cleanup...')
		objects = []
		removed = []
		for modulename, objs in self._cleanup.items():
			objects.extend((modulename, dn) for dn in objs)

		for modulename, dn in sorted(objects, key=lambda x: len(x[1]), reverse=True):
			cmd = ['/usr/sbin/udm-test', modulename, 'remove', '--dn', dn, '--remove_referring']

			print('removing DN:', dn)
			child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
			(stdout, stderr) = child.communicate()
			if six.PY3:
				stdout, stderr = stdout.decode('utf-8', 'replace'), stderr.decode('utf-8', 'replace')
			if child.returncode or 'Object removed:' not in stdout:
				failedObjects.setdefault(modulename, []).append(dn)
			else:
				removed.append((modulename, dn))

		# simply iterate over the remaining objects again, removing them might just have failed for chronology reasons
		# (e.g groups can not be removed while there are still objects using it as primary group)
		for modulename, objects in failedObjects.items():
			for dn in objects:
				cmd = ['/usr/sbin/udm-test', modulename, 'remove', '--dn', dn, '--remove_referring']

				child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
				(stdout, stderr) = child.communicate()
				if six.PY3:
					stdout, stderr = stdout.decode('utf-8', 'replace'), stderr.decode('utf-8', 'replace')

				if child.returncode or 'Object removed:' not in stdout:
					print('Warning: Failed to remove %r object %r' % (modulename, dn), file=sys.stderr)
					print('stdout=%r %r %r' % (stdout, stderr, self._lo.get(dn)), file=sys.stderr)
				else:
					removed.append((modulename, dn))
		self._cleanup = {}

		for lock_type, values in self._cleanupLocks.items():
			for value in values:
				lockDN = 'cn=%s,cn=%s,%s' % (value, lock_type, self.UNIVENTION_TEMPORARY_CONTAINER)
				try:
					self._lo.delete(lockDN)
				except ldap.NO_SUCH_OBJECT:
					pass
				except Exception as ex:
					print('Failed to remove locking object "%s" during cleanup: %r' % (lockDN, ex))
		self._cleanupLocks = {}

		print('Cleanup: wait for replication and drs removal')
		utils.wait_for_replication(verbose=False)
		for module, dn in removed:
			try:
				self._wait_for_drs_removal(module, dn, verbose=True)
			except DRSReplicationFailed as exc:
				print('Cleanup: DRS replication failed:', exc)

		self.stop_cli_server()
		print('UCSTestUDM cleanup done')

	def lookup(self, module_element_name, base, filter_s=None):
		udm_module = univention.admin.modules.get(module_element_name)
		if filter_s is None:
			lookup_list = udm_module.lookup(base=base)
		else:
			lookup_list = udm_module.lookup(base=base, filter=filter_s)
		return lookup_list

	def stop_cli_server(self):
		""" restart UDM CLI server """
		print('trying to restart UDM CLI server')
		procs = []
		for proc in psutil.process_iter():
			try:
				cmdline = proc.cmdline()
				if len(cmdline) >= 2 and cmdline[0].startswith('/usr/bin/python') and cmdline[1] == self.PATH_UDM_CLI_SERVER:
					procs.append(proc)
			except psutil.NoSuchProcess:
				pass
		for signal in (15, 9):
			for proc in procs:
				try:
					print('sending signal %s to process %s (%r)' % (signal, proc.pid, proc.cmdline(),))
					os.kill(proc.pid, signal)
				except (psutil.NoSuchProcess, EnvironmentError):
					print('process already terminated')
					procs.remove(proc)
			if signal == 15:
				time.sleep(1)

	def verify_udm_object(self, *args, **kwargs):
		return verify_udm_object(*args, **kwargs)

	def verify_ldap_object(self, *args, **kwargs):
		return utils.verify_ldap_object(*args, **kwargs)

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		if exc_type:
			print('Cleanup after exception: %s %s' % (exc_type, exc_value))
		self.cleanup()


class UDM(UCSTestUDM):
	"""UDM interface using the REST API"""

	PATH_UDM_CLI_CLIENT_WRAPPED = '/usr/sbin/udm-test-rest'

	def stop_cli_server(self):
		super(UDM, self).stop_cli_server()
		subprocess.call(['systemctl', 'reload', 'univention-directory-manager-rest.service'])


def verify_udm_object(module, dn, expected_properties):
	"""
	Verify an object exists with the given `dn` in the given UDM `module` with
	some properties. Setting `expected_properties` to `None` requires the
	object to not exist.
	:param dict expected_properties: is a dictionary of (property,value) pairs.

	:raises AssertionError: in case of a mismatch.
	"""
	lo = utils.get_ldap_connection(admin_uldap=True)
	try:
		position = univention.admin.uldap.position(lo.base)
		udm_module = univention.admin.modules.get(module)
		if not udm_module:
			univention.admin.modules.update()
			udm_module = univention.admin.modules.get(module)
		udm_object = univention.admin.objects.get(udm_module, None, lo, position, dn)
		udm_object.open()
	except univention.admin.uexceptions.noObject:
		if expected_properties is None:
			return
		raise

	if expected_properties is None:
		raise AssertionError("UDM object {} should not exist".format(dn))

	difference = {}
	for (key, value) in expected_properties.iteritems():
		udm_value = udm_object.info.get(key, [])
		if udm_value is None:
			udm_value = []
		if isinstance(udm_value, (bytes, six.string_types)):
			udm_value = set([udm_value])
		if not isinstance(value, (tuple, list)):
			value = set([value])
		value = set(_to_unicode(v).lower() for v in value)
		udm_value = set(_to_unicode(v).lower() for v in udm_value)
		if udm_value != value:
			try:
				value = set(_normalize_dn(dn) for dn in value)
				udm_value = set(_normalize_dn(dn) for dn in udm_value)
			except ldap.DECODING_ERROR:
				pass
		if udm_value != value:
			difference[key] = (udm_value, value)
	assert not difference, '\n'.join('{}: {} != expected {}'.format(key, udm_value, value) for key, (udm_value, value) in difference.items())


def _prettify_cmd(cmd):
	cmd = ' '.join(pipes.quote(x) for x in cmd)
	if set(cmd) & set(['\x00', '\n']):
		cmd = repr(cmd)
	return cmd


def _to_unicode(string):
	if isinstance(string, bytes):
		return string.decode('utf-8')
	return string


def _normalize_dn(dn):
	"""
	Normalize a given dn. This removes some escaping of special chars in the
	DNs. Note: The CON-LDAP returns DNs with escaping chars, OpenLDAP does not.

	>>> normalize_dn("cn=peter\#,cn=groups")
	'cn=peter#,cn=groups'
	"""
	return ldap.dn.dn2str(ldap.dn.str2dn(dn))


if __name__ == '__main__':
	import doctest
	print(doctest.testmod())

if __name__ == '__disabled__':
	ucr = univention.testing.ucr.UCSTestConfigRegistry()
	ucr.load()

	with UCSTestUDM() as udm:
		# create user
		dnUser, _username = udm.create_user()

		# stop CLI daemon
		udm.stop_cli_server()

		# create group
		_dnGroup, _groupname = udm.create_group()

		# modify user from above
		udm.modify_object('users/user', dn=dnUser, description='Foo Bar')

		# test with malformed arguments
		try:
			_dnUser, _username = udm.create_user(username='')
		except UCSTestUDM_CreateUDMObjectFailed as ex:
			print('Caught anticipated exception UCSTestUDM_CreateUDMObjectFailed - SUCCESS')

		# try to modify object not created by create_udm_object()
		try:
			udm.modify_object('users/user', dn='uid=Administrator,cn=users,%s' % ucr.get('ldap/base'), description='Foo Bar')
		except UCSTestUDM_CannotModifyExistingObject as ex:
			print('Caught anticipated exception UCSTestUDM_CannotModifyExistingObject - SUCCESS')
