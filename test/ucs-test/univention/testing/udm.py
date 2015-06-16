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
# Copyright 2013-2015 Univention GmbH
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

import subprocess
import os
import psutil
import copy
import univention.testing.ucr
import univention.testing.strings as uts
import univention.testing.utils as utils
import ldap

class UCSTestUDM_Exception(Exception):
	pass
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





class UCSTestUDM(object):
	_lo = utils.get_ldap_connection()
	_ucr = univention.testing.ucr.UCSTestConfigRegistry()
	_ucr.load()

	PATH_UDM_CLI_SERVER = '/usr/share/univention-directory-manager-tools/univention-cli-server'
	PATH_UDM_CLI_CLIENT = '/usr/sbin/udm'
	PATH_UDM_CLI_CLIENT_WRAPPED = '/usr/sbin/udm-test'

	COMPUTER_MODULES = ('computers/ubuntu',
						'computers/linux',
						'computers/windows',
						'computers/windows_domaincontroller',
						'computers/domaincontroller_master',
						'computers/domaincontroller_backup',
						'computers/domaincontroller_slave',
						'computers/memberserver',
						'computers/macos',
						'computers/ipmanagedclient')


	LDAP_BASE = _ucr['ldap/base']
	UNIVENTION_CONTAINER = 'cn=univention,%s' % LDAP_BASE
	UNIVENTION_TEMPORARY_CONTAINER = 'cn=temporary,cn=univention,%s' % LDAP_BASE


	def __init__(self):
		self._cleanup = {}
		self._cleanupLocks = {}


	@staticmethod
	def _build_udm_cmdline(modulename, action, kwargs):
		"""
		Pass modulename, action (create, modify, delete) and a bunch of keyword arguments
		to _build_udm_cmdline to build a command for UDM CLI.
		>>> UCSTestUDM._build_udm_cmdline('users/user', 'create', {'username': 'foobar'})
		['/usr/sbin/udm-test', 'users/user', 'create', '--set', 'username=foobar']
		"""
		cmd = [ UCSTestUDM.PATH_UDM_CLI_CLIENT_WRAPPED, modulename, action ]
		args = copy.deepcopy(kwargs)

		for arg in ('binddn', 'bindpwd', 'bindpwdfile', 'dn', 'position', 'superordinate', 'policy_reference', 'policy_dereference'):
			if arg in args:
				cmd.extend(['--%s' % arg.replace('_', '-'), args[arg]])
				del args[arg]

		if 'options' in args:
			for option in args['options']:
				cmd.extend(['--option', option ])
			del args['options']

		if 'set' in args:
			for key, value in args['set'].items():
				cmd.extend(['--set', '%s=%s' % (key, value)])
			del args['set']

		for operation in ('append', 'remove'):
			if operation in args:
				for key, values in args[operation].items():
					for value in values:
						cmd.extend(['--%s' % operation, '%s=%s' % (key, value)])
				del args[operation]

		if action == 'remove':
			if args.get('remove_referring', True):
				cmd.append('--remove_referring')
				if 'remove_referring' in args:
					del args['remove_referring']

		# set all other remaining properties
		for key, value in args.items():
			if isinstance(value, (list, tuple)):
				for item in value:
					cmd.extend( [ '--append', '%s=%s' % (key, item) ] )
			elif value:
				cmd.extend( [ '--set', '%s=%s' % (key, value) ] )

		return cmd


	def create_object(self, modulename, wait_for_replication = True, **kwargs):
		"""
		Creates a LDAP object via UDM. Values for UDM properties can be passed via keyword arguments
		only and have to exactly match UDM property names (case-sensitive!).

		modulename: name of UDM module (e.g. 'users/user')

		"""
		if not modulename:
			raise UCSTestUDM_MissingModulename()


		dn = None
		cmd = self._build_udm_cmdline(modulename, 'create', kwargs)

		print 'Creating %s object with %r' % (modulename, kwargs)
		child = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = False)
		(stdout, stderr) = child.communicate()

		if child.returncode:
			raise UCSTestUDM_CreateUDMObjectFailed({'module': modulename, 'kwargs': kwargs, 'returncode': child.returncode, 'stdout': stdout, 'stderr': stderr})

		# find DN of freshly created object and add it to cleanup list
		for line in stdout.splitlines(): # :pylint: disable-msg=E1103
			if line.startswith('Object created: '):
				dn = line.split('Object created: ', 1)[-1]
				self._cleanup.setdefault(modulename, []).append(dn)
				break
		else:
			raise UCSTestUDM_CreateUDMUnknownDN({'module': modulename, 'kwargs': kwargs, 'stdout': stdout, 'stderr': stderr})

		if wait_for_replication:
			utils.wait_for_replication()
		return dn


	def modify_object(self, modulename, wait_for_replication = True, **kwargs):
		"""
		Modifies a LDAP object via UDM. Values for UDM properties can be passed via keyword arguments
		only and have to exactly match UDM property names (case-sensitive!).
		Please note: the object has to be created by create_object otherwise this call will raise an exception!

		modulename: name of UDM module (e.g. 'users/user')

		"""
		if not modulename:
			raise UCSTestUDM_MissingModulename()
		dn = kwargs.get('dn')
		if not dn:
			raise UCSTestUDM_MissingDn()
		if dn not in self._cleanup.get(modulename, set()):
			raise UCSTestUDM_CannotModifyExistingObject(dn)

		cmd = self._build_udm_cmdline(modulename, 'modify', kwargs)
		print 'Modifying %s object with %r' % (modulename, kwargs)
		child = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = False)
		(stdout, stderr) = child.communicate()

		if child.returncode:
			raise UCSTestUDM_ModifyUDMObjectFailed({'module': modulename, 'kwargs': kwargs, 'returncode': child.returncode, 'stdout': stdout, 'stderr': stderr})

		for line in stdout.splitlines(): # :pylint: disable-msg=E1103
			if line.startswith('Object modified: '):
				dn = line.split('Object modified: ', 1)[-1]
				assert dn in self._cleanup.get(modulename, [])
				break
			elif line.startswith('No modification: '):
				raise UCSTestUDM_NoModification({'module': modulename, 'kwargs': kwargs, 'stdout': stdout, 'stderr': stderr})
		else:
			raise UCSTestUDM_ModifyUDMUnknownDN({'module': modulename, 'kwargs': kwargs, 'stdout': stdout, 'stderr': stderr})

		if wait_for_replication:
			utils.wait_for_replication()
		return dn

	def move_object(self, modulename, wait_for_replication = True, **kwargs):
		if not modulename:
			raise UCSTestUDM_MissingModulename()
		dn = kwargs.get('dn')
		if not dn:
			raise UCSTestUDM_MissingDn()
		if dn not in self._cleanup.get(modulename, set()):
			raise UCSTestUDM_CannotModifyExistingObject(dn)

		cmd = self._build_udm_cmdline(modulename, 'move', kwargs)
		print 'Moving %s object %r' % (modulename, kwargs)
		child = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = False)
		(stdout, stderr) = child.communicate()

		if child.returncode:
			raise UCSTestUDM_MoveUDMObjectFailed({'module': modulename, 'kwargs': kwargs, 'returncode': child.returncode, 'stdout': stdout, 'stderr': stderr})

		for line in stdout.splitlines(): # :pylint: disable-msg=E1103
			if line.startswith('Object modified: '):
				self._cleanup.get(modulename, []).remove(dn)

				new_dn = ldap.dn.dn2str(ldap.dn.str2dn(dn)[0:1] + ldap.dn.str2dn(kwargs.get('position', '')))
				self._cleanup.setdefault(modulename, []).append(new_dn)
				break
		else:
			raise UCSTestUDM_ModifyUDMUnknownDN({'module': modulename, 'kwargs': kwargs, 'stdout': stdout, 'stderr': stderr})

		if wait_for_replication:
			utils.wait_for_replication()


	def remove_object(self, modulename, wait_for_replication = True, **kwargs):
		if not modulename:
			raise UCSTestUDM_MissingModulename()
		dn = kwargs.get('dn')
		if not dn:
			raise UCSTestUDM_MissingDn()
		if dn not in self._cleanup.get(modulename, set()):
			raise UCSTestUDM_CannotModifyExistingObject(dn)

		cmd = self._build_udm_cmdline(modulename, 'remove', kwargs)
		print 'Removing %s object %r' % (modulename, kwargs)
		child = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = False)
		(stdout, stderr) = child.communicate()

		if child.returncode:
			raise UCSTestUDM_RemoveUDMObjectFailed({'module': modulename, 'kwargs': kwargs, 'returncode': child.returncode, 'stdout': stdout, 'stderr': stderr})

		if dn in self._cleanup.get(modulename, []):
			self._cleanup[modulename].remove(dn)

		if wait_for_replication:
			utils.wait_for_replication()



	def create_user(self, wait_for_replication = True, **kwargs): # :pylint: disable-msg=W0613
		"""
		Creates a user via UDM CLI. Values for UDM properties can be passed via keyword arguments only and
		have to exactly match UDM property names (case-sensitive!). Some properties have default values:
		position: 'cn=users,$ldap_base'
		password: 'univention'
		firstname: 'Foo Bar'
		lastname: <random string>
		username: <random string>

		If username is missing, a random user name will be used.

		Return value: (dn, username)
		"""

		attr = self._set_module_default_attr(kwargs, (( 'position', 'cn=users,%s' % self.LDAP_BASE ),
											    ( 'password', 'univention' ),
											    ( 'username', uts.random_username()),
											    ( 'lastname', uts.random_name()),
											    ( 'firstname', uts.random_name()) ))

		return (self.create_object('users/user', wait_for_replication, **attr), attr['username'])


	def create_group(self, wait_for_replication = True, **kwargs): # :pylint: disable-msg=W0613
		"""
		Creates a group via UDM CLI. Values for UDM properties can be passed via keyword arguments only and
		have to exactly match UDM property names (case-sensitive!). Some properties have default values:
		position: 'cn=users,$ldap_base'
		name: <random value>

		If "groupname" is missing, a random group name will be used.

		Return value: (dn, groupname)
		"""
		attr = self._set_module_default_attr(kwargs, (( 'position', 'cn=groups,%s' % self.LDAP_BASE ),
											   ( 'name', uts.random_groupname() ) ))

		return (self.create_object('groups/group', wait_for_replication, **attr), attr['name'])

	def _set_module_default_attr(self, attributes, defaults):
		"""
		Returns the given attributes, extented by every property given in defaults if not yet set.
		"defaults" should be a tupel containing tupels like "('username', <default_value>)".
		"""
		attr = copy.deepcopy(attributes)
		for prop, value in defaults:
			attr.setdefault(prop, value)
		return attr


	def addCleanupLock(self, lockType, lockValue):
			self._cleanupLocks.setdefault(lockType, []).append(lockValue)

	def cleanup(self):
		"""
		Automatically removes LDAP objects via UDM CLI that have been created before.
		"""

		failedObjects = {}
		print 'Performing UCSTestUDM cleanup...'
		for module, objects in self._cleanup.items():
			for dn in objects:
				cmd = [ '/usr/sbin/udm-test', module, 'remove', '--dn', dn, '--remove_referring']

				child = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = False)
				(stdout, stderr) = child.communicate()

				if child.returncode or not 'Object removed:' in stdout:
					failedObjects.setdefault(module, []).append(dn)


		# simply iterate over the remaining objects again, removing them might just have failed for chronology reasons
		# (e.g groups can not be removed while there are still objects using it as primary group)
		for module, objects in failedObjects.items():
			for dn in objects:
				cmd = [ '/usr/sbin/udm-test', module, 'remove', '--dn', dn, '--remove_referring']

				child = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = False)
				(stdout, stderr) = child.communicate()
		self._cleanup = {}

		for lock_type, values in self._cleanupLocks.items():
			for value in values:
				lockDN = 'cn=%s,cn=%s,%s' % (value, lock_type, self.UNIVENTION_TEMPORARY_CONTAINER)
				try:
					self._lo.delete(lockDN)
				except ldap.NO_SUCH_OBJECT:
					pass
				except Exception as ex:
					print 'Failed to remove locking object "%s" during cleanup: %r' % (lockDN, ex)
		self._cleanupLocks = {}

		print 'UCSTestUDM cleanup done'


	def stop_cli_server(self):
		""" restart UDM CLI server """
		print 'trying to restart UDM CLI server'
		for signal in (15, 9):
			try:
				for proc in psutil.process_iter():
					if len(proc.cmdline) >= 2 and proc.cmdline[0].startswith('/usr/bin/python') and proc.cmdline[1] == self.PATH_UDM_CLI_SERVER:
						print 'sending signal %s to process %s (%r)' % (signal, proc.pid, proc.cmdline,)
						os.kill(proc.pid, signal)
			except (psutil.NoSuchProcess, IOError):
				# process not running anymore
				print 'process already terminated'

	def __enter__(self):
		return self
	def __exit__(self, exc_type, exc_value, traceback):
		if exc_type:
			print 'Cleanup after exception: %s %s' % (exc_type, exc_value)
		self.cleanup()


if __name__ == '__main__':
	import doctest
	print doctest.testmod()

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
		except UCSTestUDM_CreateUDMObjectFailed, ex:
			print 'Caught anticipated exception UCSTestUDM_CreateUDMObjectFailed - SUCCESS'

		# try to modify object not created by create_udm_object()
		try:
			udm.modify_object('users/user', dn='uid=Administrator,cn=users,%s' % ucr.get('ldap/base'), description='Foo Bar')
		except UCSTestUDM_CannotModifyExistingObject, ex:
			print 'Caught anticipated exception UCSTestUDM_CannotModifyExistingObject - SUCCESS'
