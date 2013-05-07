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
# Copyright 2013 Univention GmbH
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
import univention.testing.ucr
import univention.testing.strings as uts

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
class UCSTestUDM_NoModification(UCSTestUDM_Exception):
	pass
class UCSTestUDM_ModifyUDMUnknownDN(UCSTestUDM_Exception):
	pass
class UCSTestUDM_CleanupFailed(UCSTestUDM_Exception):
	pass
class UCSTestUDM_CannotModifyExistingObject(UCSTestUDM_Exception):
	pass



class UCSTestUDM(object):
	PATH_UDM_CLI_SERVER = '/usr/share/univention-directory-manager-tools/univention-cli-server'

	def __init__(self):
		self.ucr = univention.testing.ucr.UCSTestConfigRegistry()
		self.ucr.load()
		self._reinit_cleanup()


	def _reinit_cleanup(self):
		self._cleanup = {}


	def _build_udm_cmdline(self, modulename, action, kwargs):
		"""
		Pass modulename, action (create, modify, delete) and a bunch of keyword arguments
		to _build_udm_cmdline to build a command for UDM CLI.
		>>> _build_udm_cmdline('users/user', 'create', username='foobar', password='univention', lastname='bar')
		>>> ['/usr/sbin/univention-directory-manager', 'users/user', 'create', …]
		"""
		cmd = [ '/usr/sbin/univention-directory-manager', modulename, action ]

		if action == 'create':
			if 'position' in kwargs:
				cmd.extend( [ '--position', kwargs['position'] ] )
		else:
			cmd.extend( [ '--dn', kwargs.get('dn') ] )

		if 'superordinate' in kwargs:
			cmd.extend( ['--superordinate', kwargs.get('superordinate')] )
		
		for option in kwargs.get('options', []):
			cmd.extend(['--option', option ])

		# set all other properties
		for arg in kwargs:
			if not arg in ('position', 'superordinate', 'dn', 'options'):
				if type(kwargs.get(arg)) == list:
					for item in kwargs.get(arg):
						cmd.extend( [ '--append', '%s=%s' % (arg, item) ] )
				else:
					cmd.extend( [ '--set', '%s=%s' % (arg, kwargs.get(arg)) ] )
		return cmd


	def create_object(self, modulename, **kwargs):
		"""
		Creates a LDAP object via UDM. Values for UDM properties can be passed via keyword arguments
		only and have to exactly match UDM property names (case-sensitive!).

		modulename: name of UDM module (e.g. 'users/user')

		"""
		dn = None
		if not modulename:
			raise UCSTestUDM_MissingModulename()

		cmd = self._build_udm_cmdline(modulename, 'create', kwargs)

		print 'Creating %s object with %r' % (modulename, kwargs)
		child = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=False)
		(stdout, stderr) = child.communicate()

		if child.returncode:
			print 'UDM-CLI returned exitcode %s while creating object' % (child.returncode,)
			raise UCSTestUDM_CreateUDMObjectFailed(modulename, kwargs, stdout, stderr)
		
		# find DN of freshly created object and add it to cleanup list
		for line in stdout.splitlines(): # :pylint: disable-msg=E1103
			if line.startswith('Object created: '):
				dn = line.split('Object created: ', 1)[-1]
				self._cleanup.setdefault(modulename, []).append(dn)
				break
		else:
			raise UCSTestUDM_CreateUDMUnknownDN(modulename, kwargs, stdout, stderr)
		return dn


	def modify_object(self, modulename, **kwargs):
		"""
		Modifies a LDAP object via UDM. Values for UDM properties can be passed via keyword arguments
		only and have to exactly match UDM property names (case-sensitive!).
		Please note: the object has to be created by create_object otherwise this call will raise an exception!

		modulename: name of UDM module (e.g. 'users/user')

		"""
		dn = None
		if not modulename:
			raise UCSTestUDM_MissingModulename()
		if not kwargs.get('dn'):
			raise UCSTestUDM_MissingDn()
		if not kwargs.get('dn') in self._cleanup.get(modulename, []):
			raise UCSTestUDM_CannotModifyExistingObject(kwargs.get('dn'))

		cmd = self._build_udm_cmdline(modulename, 'modify', kwargs)
		print 'Modifying %s object with %r' % (modulename, kwargs)
		child = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=False)
		(stdout, stderr) = child.communicate()

		if child.returncode:
			print 'UDM-CLI returned exitcode %s while modifying object: ''' % (child.returncode,)
			raise UCSTestUDM_ModifyUDMObjectFailed(modulename, kwargs, stdout, stderr)
		else:
			# find DN of freshly created object
			for line in stdout.splitlines(): # :pylint: disable-msg=E1103
				if line.startswith('Object modified: '):
					dn = line.split('Object modified: ', 1)[-1]
					assert(dn in self._cleanup.get(modulename, []))
					break
				elif line.startswith('No modification: '):
					raise UCSTestUDM_NoModification(modulename, kwargs, stdout, stderr)
			else:
				raise UCSTestUDM_ModifyUDMUnknownDN(modulename, kwargs, stdout, stderr)
		return dn


	def create_user(self, **kwargs): # :pylint: disable-msg=W0613
		"""
		Creates an user via UDM CLI. Values for UDM properties can be passed via keyword arguments only and
		have to exactly match UDM property names (case-sensitive!). Some properties have default values:
		position: 'cn=users,$ldap_base'
		password: 'univention'
		firstname: 'Foo Bar'
		lastname: <same as 'username'>
		username: <random string>

		If username is missing, a random user name will be used.

		Return value: (username, dn)
		"""

		if not 'username' in kwargs:
			kwargs['username'] = uts.random_username()

		for prop, default in (('position', 'cn=users,%s' % self.ucr.get('ldap/base')),
							  ('password', 'univention'),
							  ('firstname', 'Foo Bar'),
							  ('lastname', kwargs.get('username'))):
			if not prop in kwargs:
				kwargs[prop] = default

		return (kwargs['username'], self.create_udm_object('users/user', **kwargs))


	def create_group(self, **kwargs): # :pylint: disable-msg=W0613
		"""
		Creates a group via UDM CLI. Values for UDM properties can be passed via keyword arguments only and
		have to exactly match UDM property names (case-sensitive!). Some properties have default values:
		position: 'cn=users,$ldap_base'
		name: <random value>

		If "name" is missing, a random group name will be used.

		Return value: (groupname, dn)
		"""

		if not 'groupname' in kwargs:
			kwargs['name'] = uts.random_string(length=1, alpha=True, numeric=False) + uts.random_string(length=9, alpha=True, numeric=True)
		if not 'position' in kwargs:
			kwargs['position'] = 'cn=groups,%s' % self.ucr.get('ldap/base')

		return (kwargs['name'], self.create_udm_object('groups/group', **kwargs))


	def cleanup(self):
		"""
		Automatically removes LDAP objects via UDM CLI that have been created before.
		"""

		failedObjects = []
		print 'Performing UCSTestUDM cleanup...'
		for module in self._cleanup:
			for dn in self._cleanup[module]:
				print 'Removing object of type %s: %s' % (module, dn)
				cmd = [ '/usr/sbin/univention-directory-manager', module, 'remove', '--dn', dn ]

				child = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=False)
				(stdout, stderr) = child.communicate()

#				if child.returncode or not 'Object removed:' in stdout:
#					print 'UDM-CLI returned exitcode %s while removing object %s''' % (child.returncode, dn)
#					failedObjects.append((module, dn))

		print 'UCSTestUDM cleanup done'
		# reinit list of objects to cleaned up
		self._reinit_cleanup()


	def stop_cli_server(self):
		""" restart UDM CLI server """
		print 'trying to restart UDM CLI server'
		for signal in (15, 9):
			for proc in psutil.process_iter():
				if len(proc.cmdline) >= 2 and proc.cmdline[0].startswith('/usr/bin/python') and proc.cmdline[1] == self.PATH_UDM_CLI_SERVER:
					print 'sending signal %s to process %s (%r)''' % (signal, proc.pid, proc.cmdline,)
					os.kill(proc.pid, signal)

#	def __enter__(self):
#		return self
#	def __exit__(self, exc_type, exc_value, traceback):
#		self.cleanup()


if __name__ == '__main__':
	with UCSTestUDM() as udm:
		# create user
		username, dnUser = udm.create_user()

		# stop CLI daemon
		udm.stop_cli_server()

		# create group
		groupname, dnGroup = udm.create_group()

		# modify user from above
		udm.modify_object('users/user', dn=dnUser, description='Foo Bar')

		# test with malformed arguments
		try:
			username, dnUser = udm.create_user(username='')
		except UCSTestUDM_CreateUDMObjectFailed, ex:
			print 'Caught anticipated exception UCSTestUDM_CreateUDMObjectFailed - SUCCESS'

		# try to modify object not created by create_udm_object()
		try:
			udm.modify_object('users/user', dn='uid=Administrator,cn=users,%s' % udm.ucr.get('ldap/base'), description='Foo Bar')
		except UCSTestUDM_CannotModifyExistingObject, ex:
			print 'Caught anticipated exception UCSTestUDM_CannotModifyExistingObject - SUCCESS'
