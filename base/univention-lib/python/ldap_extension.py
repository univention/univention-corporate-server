#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
Python function to register |UDM| extensions in |LDAP|.
"""
# Copyright 2011-2021 Univention GmbH
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

from __future__ import absolute_import
from __future__ import print_function

import inspect
import json
import os
import shutil
import re
import sys
import imp
import subprocess
import bz2
import base64
import time
import tempfile
import datetime
from optparse import OptionParser, OptionGroup, Option, OptionValueError
from copy import copy
from abc import ABCMeta, abstractproperty, abstractmethod

import six
import apt
import listener
from ldap.filter import filter_format
from ldap.dn import escape_dn_chars

import univention.debug as ud
from univention.config_registry import configHandlers, ConfigRegistry
from univention.admin import uldap as udm_uldap
from univention.admin import modules as udm_modules
from univention.admin import uexceptions as udm_errors
from univention.lib.ucs import UCS_Version
from univention.lib.umc_module import MIME_DESCRIPTION


class BaseDirRestriction(Exception):
	pass


def safe_path_join(basedir, filename):
	path = os.path.join(basedir, filename)
	if not os.path.abspath(path).startswith(basedir):
		raise BaseDirRestriction('filename %r invalid, not underneath of %r' % (filename, basedir))
	if set(filename) & {'\x00', '/'}:  # also restrict subdirectories, and ../local-schema/foo
		raise BaseDirRestriction('invalid filename: %r' % (filename,))
	return path


def _verify_handler_message_container(lo, position):
	position_dn = 'cn=univention,{}'.format(listener.configRegistry.get('ldap/base'))
	udm_modules.update()
	cn_module = udm_modules.get('container/cn')
	udm_modules.init(lo, position, cn_module)
	try:
		cn_object = cn_module.object(None, lo, position, dn='cn=handler_messages,{}'.format(position_dn))
	except udm_errors.noObject:
		position.setDn(position_dn)
		cn_object = cn_module.object(None, lo, position)
		cn_object.open()
		cn_object['name'] = 'handler_messages'
		cn_object.create()


def _get_handler_message_object(lo, position, handler_name, create=False):
	position_dn = 'cn=handler_messages,cn=univention,{}'.format(listener.configRegistry.get('ldap/base'))
	udm_modules.update()
	data_module = udm_modules.get('settings/data')
	udm_modules.init(lo, position, data_module)
	data_object_dn = 'cn={},{}'.format(escape_dn_chars(handler_name), position_dn)
	try:
		data_object = data_module.object(None, lo, position, dn=data_object_dn)
	except udm_errors.noObject:
		position.setDn(position_dn)
		data_object = data_module.object(None, lo, position)
		data_object.open()
		data_object['name'] = handler_name
		data_object['data_type'] = 'handlerMessage'
		data_object.create()
	data_object.open()
	return data_object


def set_handler_message(name, dn, msg):
	# currently only on master
	if listener.configRegistry.get('server/role') in ('domaincontroller_master',):
		ud.debug(ud.LISTENER, ud.INFO, 'set_handler_message for {}'.format(name))
		setuid = False if os.geteuid() == 0 else True
		if setuid:
			listener.setuid(0)
		try:
			lo, position = udm_uldap.getAdminConnection()
			_verify_handler_message_container(lo, position)
			data_obj = _get_handler_message_object(lo, position, name)
			data = dict()
			try:
				data = json.loads(bz2.decompress(base64.b64decode(data_obj.get('data', ''))))
			except ValueError:
				pass
			hostname = listener.configRegistry.get('hostname')
			if not data.get(hostname):
				data[hostname] = dict()
			data[hostname][dn] = msg
			json_data = json.dumps(data).encode('ASCII')
			data_obj['data'] = base64.b64encode(bz2.compress(json_data))
			data_obj.modify()
		except Exception as err:
			ud.debug(ud.LISTENER, ud.ERROR, 'Error set_handler_message for handler %s: %s' % (name, err,))
		finally:
			if setuid:
				listener.unsetuid()


def get_handler_message(name, binddn, bindpw):
	msg = dict()
	try:
		lo = udm_uldap.access(
			host=listener.configRegistry.get('ldap/master'),
			base=listener.configRegistry.get('ldap/base'),
			binddn=binddn, bindpw=bindpw)
		position = udm_uldap.position(lo.base)
		position_dn = 'cn=handler_messages,cn=univention,{}'.format(listener.configRegistry.get('ldap/base'))
		udm_modules.update()
		data_module = udm_modules.get('settings/data')
		udm_modules.init(lo, position, data_module)
		data_object_dn = 'cn={},{}'.format(escape_dn_chars(name), position_dn)
		try:
			data_object = data_module.object(None, lo, position, dn=data_object_dn)
			data_object.open()
			if data_object.get('data', False):
				msg = json.loads(bz2.decompress(base64.b64decode(data_object['data'])))
		except udm_errors.noObject:
			msg = dict(err='No object {} found'.format(data_object_dn))
	except Exception as err:
		msg = dict(err='Error get_handler_message for handler {}: {}'.format(name, err))
	return msg


class UniventionLDAPExtension(six.with_metaclass(ABCMeta)):

	@abstractproperty
	def udm_module_name(self):
		pass

	@abstractproperty
	def target_container_name(self):
		pass

	@abstractproperty
	def active_flag_attribute(self):
		pass

	@abstractproperty
	def filesuffix(self):
		pass

	def __init__(self, ucr):
		self.target_container_dn = "cn=%s,cn=univention,%s" % (self.target_container_name, ucr["ldap/base"],)

	@classmethod
	def create_base_container(cls, ucr, udm_passthrough_options):
		cmd = ["univention-directory-manager", "container/cn", "create"] + udm_passthrough_options + [
			"--ignore_exists",
			"--set", "name=%s" % cls.target_container_name,
			"--position", "cn=univention,%s" % ucr['ldap/base']
		]
		return subprocess.call(cmd)

	def is_local_active(self):
		object_dn = None

		cmd = ["univention-ldapsearch", "-LLL", "-b", self.object_dn, "-s", "base", filter_format("(&(cn=%s)(%s=TRUE))", (self.objectname, self.active_flag_attribute))]
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		(stdout, stderr) = p.communicate()
		if p.returncode:
			return (p.returncode, object_dn)
		regex = re.compile(b'^dn: (.*)$', re.M)
		m = regex.search(stdout)
		if m:
			object_dn = m.group(1).decode('UTF-8')
		return (p.returncode, object_dn)

	def wait_for_activation(self, timeout=180):
		print("Waiting for activation of the extension object %s:" % (self.objectname,), end=' ')
		t0 = time.time()
		while not self.is_local_active()[1]:
			if time.time() - t0 > timeout:
				print("ERROR")
				print("ERROR: Master did not mark the extension object active within %s seconds." % (timeout,), file=sys.stderr)
				return False
			sys.stdout.write(".")
			sys.stdout.flush()
			time.sleep(3)
		print("OK")
		return True

	def udm_find_object(self):
		cmd = ["univention-directory-manager", self.udm_module_name, "list"] + self.udm_passthrough_options + [
			"--filter", filter_format("name=%s", [self.objectname]),
		]
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
		(stdout, stderr) = p.communicate()
		return (p.returncode, stdout.decode('UTF-8', 'replace'))

	def udm_find_object_dn(self):
		object_dn = None

		rc, stdout = self.udm_find_object()
		if rc:
			return (rc, object_dn, stdout)
		regex = re.compile('^DN: (.*)$', re.M)
		m = regex.search(stdout)
		if m:
			object_dn = m.group(1)
		return (rc, object_dn, stdout)

	def register(self, filename, options, udm_passthrough_options, target_filename=None):
		self.filename = filename
		self.options = options
		self.udm_passthrough_options = udm_passthrough_options
		self.target_filename = target_filename or os.path.basename(filename)
		self.objectname = options.objectname

		if not self.objectname:
			target_filename_parts = os.path.splitext(self.target_filename)
			if target_filename_parts[1] == self.filesuffix and self.filesuffix:
				self.objectname = target_filename_parts[0]
			else:
				self.objectname = self.target_filename

		try:
			with open(self.filename, 'rb') as f:
				compressed_data = bz2.compress(f.read())
		except Exception as e:
			print("Compression of file %s failed: %s" % (self.filename, e), file=sys.stderr)
			sys.exit(1)

		new_data = base64.b64encode(compressed_data).decode('ASCII')

		active_change_udm_options = [
			"--set", "filename=%s" % self.target_filename,
			"--set", "data=%s" % new_data,
		]
		if self.udm_module_name != "settings/data":
			active_change_udm_options.extend([
				"--set", "active=FALSE",
			])

		common_udm_options = [
			"--set", "package=%s" % (options.packagename,),
			"--set", "packageversion=%s" % (options.packageversion,),
		]

		if self.udm_module_name == "settings/data":
			common_udm_options.extend(["--set", "data_type={}".format(options.data_type), ])
			for meta in options.data_meta:
				common_udm_options.extend(["--set", "meta={}".format(meta), ])

		if self.udm_module_name != "settings/ldapschema":
			if options.ucsversionstart:
				common_udm_options.extend(["--set", "ucsversionstart=%s" % (options.ucsversionstart,), ])
			if options.ucsversionend:
				common_udm_options.extend(["--set", "ucsversionend=%s" % (options.ucsversionend,), ])

		if self.udm_module_name == "settings/udm_module":
			for udm_module_messagecatalog in options.udm_module_messagecatalog:
				filename_parts = os.path.splitext(os.path.basename(udm_module_messagecatalog))
				language = filename_parts[0]
				with open(udm_module_messagecatalog, 'rb') as f:
					common_udm_options.extend(["--append", "messagecatalog=%s %s" % (language, base64.b64encode(f.read()).decode('ASCII'),), ])

			for umcmessagecatalog in options.umcmessagecatalog:
				filename_parts = os.path.splitext(os.path.basename(umcmessagecatalog))
				if not ('-' in filename_parts[0] and len(filename_parts[0].split('-', 1)) == 2):
					raise OptionValueError("%s: Is not a valid umcmessagecatalog filename. Must be the locale and the UMCModuleID seperated by '-'" % (filename_parts[0],))
				with open(umcmessagecatalog, 'rb') as f:
					common_udm_options.extend(["--append", "umcmessagecatalog=%s %s" % (filename_parts[0], base64.b64encode(f.read()).decode('ASCII'),), ])

			if options.umcregistration:
				try:
					with open(options.umcregistration, 'rb') as f:
						compressed_data = bz2.compress(f.read())
				except Exception as e:
					print("Compression of file %s failed: %s" % (options.umcregistration, e), file=sys.stderr)
					sys.exit(1)
				common_udm_options.extend(["--set", "umcregistration=%s" % (base64.b64encode(compressed_data).decode('ASCII'),), ])
			for icon in options.icon:
				with open(icon, 'rb') as f:
					common_udm_options.extend(["--append", "icon=%s" % (base64.b64encode(f.read()).decode('ASCII'),), ])

		if self.udm_module_name == "settings/udm_syntax":
			for udm_syntax_messagecatalog in options.udm_syntax_messagecatalog:
				filename_parts = os.path.splitext(os.path.basename(udm_syntax_messagecatalog))
				language = filename_parts[0]
				with open(udm_syntax_messagecatalog, 'rb') as f:
					common_udm_options.extend(["--append", "messagecatalog=%s %s" % (language, base64.b64encode(f.read()).decode('ASCII'),), ])

		if self.udm_module_name == "settings/udm_hook":
			for udm_hook_messagecatalog in options.udm_hook_messagecatalog:
				filename_parts = os.path.splitext(os.path.basename(udm_hook_messagecatalog))
				language = filename_parts[0]
				with open(udm_hook_messagecatalog, 'rb') as f:
					common_udm_options.extend(["--append", "messagecatalog=%s %s" % (language, base64.b64encode(f.read()).decode('ASCII'),), ])

		rc, self.object_dn, stdout = self.udm_find_object_dn()
		if not self.object_dn:

			cmd = ["univention-directory-manager", self.udm_module_name, "create"] + self.udm_passthrough_options + [
				"--set", "name=%s" % self.objectname,
				"--position", self.target_container_dn,
			] + common_udm_options + active_change_udm_options
			p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			(stdout, stderr) = p.communicate()
			stdout = stdout.decode('UTF-8', 'replace')
			print(stdout)
			if p.returncode == 0:
				regex = re.compile('^Object created: (.*)$', re.M)
				m = regex.search(stdout)
				if m:
					new_object_dn = m.group(1)
				else:
					new_object_dn = None

				appidentifier = os.environ.get('UNIVENTION_APP_IDENTIFIER')
				if appidentifier:
					cmd = ["univention-directory-manager", self.udm_module_name, "modify"] + self.udm_passthrough_options + [
						"--set", "appidentifier=%s" % (appidentifier,),
						"--dn", new_object_dn,
					]
					p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
					(stdout, stderr) = p.communicate()
					stdout = stdout.decode('UTF-8', 'replace')
					print(stdout)
			else:  # check again, might be a race
				rc, self.object_dn, stdout = self.udm_find_object_dn()
				if not self.object_dn:
					print("ERROR: Failed to create %s object." % (self.udm_module_name,), file=sys.stderr)
					sys.exit(1)

		if self.object_dn:  # object exists already, modify it
			regex = re.compile('^ *package: (.*)$', re.M)
			m = regex.search(stdout)
			if m:
				registered_package = m.group(1)
				if registered_package == "None":
					registered_package = None
			else:
				registered_package = None

			regex = re.compile('^ *packageversion: (.*)$', re.M)
			m = regex.search(stdout)
			if m:
				registered_package_version = m.group(1)
				if registered_package_version == "None":
					registered_package_version = None
			else:
				registered_package_version = None

			if registered_package == options.packagename:
				rc = apt.apt_pkg.version_compare(options.packageversion, registered_package_version)
				if not rc > -1:
					print("WARNING: Registered package version %s is newer, refusing registration." % (registered_package_version,), file=sys.stderr)
					sys.exit(4)
			else:
				print("WARNING: Object %s was registered by package %s version %s, changing ownership." % (self.objectname, registered_package, registered_package_version,), file=sys.stderr)

			regex = re.compile('^ *data: (.*)$', re.M)
			m = regex.search(stdout)
			if m:
				old_data = m.group(1)
				if old_data == "None":
					old_data = None
			else:
				old_data = None

			regex = re.compile('^ *filename: (.*)$', re.M)
			m = regex.search(stdout)
			if m:
				old_filename = m.group(1)
				if old_filename == "None":
					old_filename = None
			else:
				old_filename = None
			if new_data == old_data and self.target_filename == old_filename:
				print("INFO: No change of core data of object %s." % (self.objectname,), file=sys.stderr)
				active_change_udm_options = []

			cmd = ["univention-directory-manager", self.udm_module_name, "modify"] + self.udm_passthrough_options + [
				"--dn", self.object_dn,
			] + common_udm_options + active_change_udm_options
			p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			(stdout, stderr) = p.communicate()
			stdout = stdout.decode('UTF-8', 'replace')
			print(stdout)
			if p.returncode != 0:
				print("ERROR: Modification of %s object failed." % (self.udm_module_name,), file=sys.stderr)
				sys.exit(1)

			appidentifier = os.environ.get('UNIVENTION_APP_IDENTIFIER')
			if appidentifier:
				cmd = ["univention-directory-manager", self.udm_module_name, "modify"] + self.udm_passthrough_options + [
					"--append", "appidentifier=%s" % (appidentifier,),
					"--dn", self.object_dn,
				]
				p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
				(stdout, stderr) = p.communicate()
				stdout = stdout.decode('UTF-8', 'replace')
				print(stdout)

		if not self.object_dn:
			self.object_dn = new_object_dn

	def unregister(self, objectname, options, udm_passthrough_options):
		self.objectname = objectname
		self.options = options
		self.udm_passthrough_options = udm_passthrough_options

		rc, object_dn, stdout = self.udm_find_object_dn()
		if not object_dn:
			print("ERROR: Object not found in UDM.", file=sys.stderr)
			return

		app_filter = ""
		regex = re.compile('^ *appidentifier: (.*)$', re.M)
		for appidentifier in regex.findall(stdout):
			if appidentifier != "None":
				app_filter = app_filter + filter_format("(cn=%s)", [appidentifier])

		if app_filter:
			cmd = ["univention-ldapsearch", "-LLL", "(&(objectClass=univentionApp)%s)" % (app_filter,), "cn"]
			p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			(stdout, stderr) = p.communicate()
			stdout = stdout.decode('UTF-8', 'replace')
			if p.returncode:
				print("ERROR: LDAP search failed: %s" % (stdout,), file=sys.stderr)
				sys.exit(1)
			if stdout:
				regex = re.compile('^cn: (.*)$', re.M)
				apps = ",".join(regex.findall(stdout))
				print("INFO: The object %s is still registered by the following apps: %s" % (objectname, apps,), file=sys.stderr)
				sys.exit(2)

		cmd = ["univention-directory-manager", self.udm_module_name, "delete"] + self.udm_passthrough_options + [
			"--dn", object_dn,
		]
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		(stdout, stderr) = p.communicate()
		stdout = stdout.decode('UTF-8', 'replace')
		print(stdout)

	def mark_active(self, handler_name=None):
		if self._todo_list:
			try:
				lo, ldap_position = udm_uldap.getAdminConnection()
				udm_modules.update()
				udm_module = udm_modules.get(self.udm_module_name)
				udm_modules.init(lo, ldap_position, udm_module)

				for object_dn in self._todo_list:
					try:
						udm_object = udm_module.object(None, lo, ldap_position, object_dn)
						udm_object.open()
						udm_object['active'] = True
						udm_object.modify()
					except udm_errors.noObject:
						ud.debug(ud.LISTENER, ud.ERROR, 'Error modifying %s: object not found.' % (object_dn,))
					except udm_errors.ldapError as e:
						ud.debug(ud.LISTENER, ud.ERROR, 'Error modifying %s: %s.' % (object_dn, e))
						raise
				if handler_name:
					for object_dn in self._todo_list:
						set_handler_message(handler_name, object_dn, 'active')
				self._todo_list = []
			except udm_errors.ldapError as e:
				ud.debug(ud.LISTENER, ud.ERROR, 'Error accessing UDM: %s' % (e,))
				if handler_name:
					for object_dn in self._todo_list:
						set_handler_message(handler_name, object_dn, 'Error accessing UDM: {}'.format(e))


class UniventionLDAPExtensionWithListenerHandler(six.with_metaclass(ABCMeta, UniventionLDAPExtension)):

	def __init__(self, ucr):
		super(UniventionLDAPExtensionWithListenerHandler, self).__init__(ucr)
		self._do_reload = False
		self._todo_list = []
		self.ucr_template_dir = '/etc/univention/templates'
		self.ucr_slapd_conf_subfile_dir = '%s/files/etc/ldap/slapd.conf.d' % self.ucr_template_dir
		self.ucr_info_basedir = '%s/info' % self.ucr_template_dir

	@abstractmethod
	def handler(self, dn, new, old, name=None):
		pass


class UniventionLDAPSchema(UniventionLDAPExtensionWithListenerHandler):
	target_container_name = "ldapschema"
	udm_module_name = "settings/ldapschema"
	active_flag_attribute = "univentionLDAPSchemaActive"
	filesuffix = ".schema"
	basedir = '/var/lib/univention-ldap/local-schema'

	def handler(self, dn, new, old, name=None):
		try:
			return self._handler(dn, new, old, name)
		except BaseDirRestriction as exc:
			ud.debug(ud.LISTENER, ud.ERROR, '%r basedir conflict: %s' % (dn, exc))

	def _handler(self, dn, new, old, name=None):
		"""Handle LDAP schema extensions on Master and Backup"""
		if not listener.configRegistry.get('server/role') in ('domaincontroller_master', 'domaincontroller_backup'):
			return

		if new:  # create / modify
			new_version = new.get('univentionOwnedByPackageVersion', [b''])[0].decode('UTF-8')
			if not new_version:
				return

			new_pkgname = new.get('univentionOwnedByPackage', [None])[0]
			if not new_pkgname:
				return

			if old:  # check for trivial changes
				diff_keys = [key for key in new.keys() if new.get(key) != old.get(key) and key not in ('entryCSN', 'modifyTimestamp', 'modifiersName')]
				if diff_keys == ['univentionLDAPSchemaActive'] and new.get('univentionLDAPSchemaActive') == [b'TRUE']:
					ud.debug(ud.LISTENER, ud.INFO, '%s: extension %s: activation status changed.' % (name, new['cn'][0].decode('UTF-8')))
					return
				elif diff_keys == ['univentionAppIdentifier']:
					ud.debug(ud.LISTENER, ud.INFO, '%s: extension %s: App identifier changed.' % (name, new['cn'][0].decode('UTF-8')))
					return
				ud.debug(ud.LISTENER, ud.INFO, '%s: extension %s: changed attributes: %s' % (name, new['cn'][0].decode('UTF-8'), diff_keys))

				if new_pkgname == old.get('univentionOwnedByPackage', [None])[0]:
					old_version = old.get('univentionOwnedByPackageVersion', [b'0'])[0].decode('UTF-8')
					rc = apt.apt_pkg.version_compare(new_version, old_version)
					if not rc > -1:
						ud.debug(ud.LISTENER, ud.WARN, '%s: New version is lower than version of old object (%s), skipping update.' % (name, old_version))
						return

			set_handler_message(name, dn, 'handler start')

			try:
				new_object_data = bz2.decompress(new['univentionLDAPSchemaData'][0])
			except TypeError:
				ud.debug(ud.LISTENER, ud.ERROR, '%s: Error uncompressing data of object %s.' % (name, dn))
				set_handler_message(name, dn, 'Error uncompressing data of object {}.'.format(dn))
				return

			try:
				new_filename = safe_path_join(self.basedir, new['univentionLDAPSchemaFilename'][0].decode('UTF-8'))
			except BaseDirRestriction as exc:
				if old:
					ud.debug(ud.LISTENER, ud.ERROR, 'invalid filename detected during modification. removing file!')
					set_handler_message(name, dn, 'invalid filename detected during modification. removing file!')
					self._handler(dn, [], old, name)
				raise exc

			listener.setuid(0)
			try:
				backup_filename = None
				if old:
					old_filename = safe_path_join(self.basedir, old['univentionLDAPSchemaFilename'][0].decode('UTF-8'))
					if os.path.exists(old_filename):
						backup_fd, backup_filename = tempfile.mkstemp()
						ud.debug(ud.LISTENER, ud.INFO, '%s: Moving old file %s to %s.' % (name, old_filename, backup_filename))
						try:
							shutil.move(old_filename, backup_filename)
						except IOError:
							ud.debug(ud.LISTENER, ud.WARN, '%s: Error renaming old file %s, removing it.' % (name, old_filename))
							os.unlink(old_filename)  # no choice
							backup_filename = None
							os.close(backup_fd)

				if not os.path.isdir(self.basedir):
					if os.path.exists(self.basedir):
						ud.debug(ud.LISTENER, ud.WARN, '%s: Directory name %s occupied, renaming blocking file.' % (name, self.basedir))
						shutil.move(self.basedir, "%s.bak" % self.basedir)
					ud.debug(ud.LISTENER, ud.INFO, '%s: Create directory %s.' % (name, self.basedir))
					os.makedirs(self.basedir, 0o755)

				# Create new extension file
				try:
					ud.debug(ud.LISTENER, ud.INFO, '%s: Writing new extension file %s.' % (name, new_filename))
					with open(new_filename, 'wb') as f:
						f.write(new_object_data)
				except IOError:
					ud.debug(ud.LISTENER, ud.ERROR, '%s: Error writing file %s.' % (name, new_filename))
					set_handler_message(name, dn, 'Error writing file {}.'.format(new_filename))
					return

				ucr = ConfigRegistry()
				ucr.load()
				ucr_handlers = configHandlers()
				ucr_handlers.load()
				ucr_handlers.update()
				ucr_handlers.commit(ucr, ['/etc/ldap/slapd.conf'])

				# validate
				# Slapschema doesn't fail on schema errors, errors are printed to stdout (Bug #45571)
				p = subprocess.Popen(['/usr/sbin/slaptest', '-u'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
				stdout, stderr = p.communicate()
				stdout, stderr = stdout.decode('UTF-8', 'replace'), stderr.decode('UTF-8', 'replace')
				if p.returncode != 0:
					ud.debug(ud.LISTENER, ud.ERROR, '%s: validation failed (%s):\n%s\n%s.' % (name, p.returncode, stdout, stderr))
					set_handler_message(name, dn, 'slaptest validation failed {} {} {}'.format(stdout, stderr, p.returncode))
					# Revert changes
					ud.debug(ud.LISTENER, ud.ERROR, '%s: Removing new file %s.' % (name, new_filename))
					os.unlink(new_filename)
					if backup_filename:
						ud.debug(ud.LISTENER, ud.ERROR, '%s: Restoring previous file %s.' % (name, old_filename))
						try:
							shutil.move(backup_filename, old_filename)
							os.close(backup_fd)
						except IOError:
							ud.debug(ud.LISTENER, ud.ERROR, '%s: Error reverting to old file %s.' % (name, old_filename))
					# Commit and exit
					ucr_handlers.commit(ucr, ['/etc/ldap/slapd.conf'])
					return
				ud.debug(ud.LISTENER, ud.INFO, '%s: validation successful.' % (name,))

				# cleanup backup
				if backup_filename:
					ud.debug(ud.LISTENER, ud.INFO, '%s: Removing backup of old file %s.' % (name, backup_filename))
					os.unlink(backup_filename)
					os.close(backup_fd)

				self._todo_list.append(dn)
				self._do_reload = True

			finally:
				listener.unsetuid()
		elif old:  # remove
			old_filename = safe_path_join(self.basedir, old['univentionLDAPSchemaFilename'][0].decode('UTF-8'))
			if os.path.exists(old_filename):
				listener.setuid(0)
				try:
					backup_fd, backup_filename = tempfile.mkstemp()
					ud.debug(ud.LISTENER, ud.INFO, '%s: Moving old file %s to %s.' % (name, old_filename, backup_filename))
					try:
						shutil.move(old_filename, backup_filename)
					except IOError:
						ud.debug(ud.LISTENER, ud.WARN, '%s: Error renaming old file %s, leaving it untouched.' % (name, old_filename))
						set_handler_message(name, dn, 'Error renaming old file {}, leaving it untouched.'.format(old_filename))
						os.close(backup_fd)
						return

					ucr = ConfigRegistry()
					ucr.load()
					ucr_handlers = configHandlers()
					ucr_handlers.load()
					ucr_handlers.update()
					ucr_handlers.commit(ucr, ['/etc/ldap/slapd.conf'])

					# Slapschema doesn't fail on schema errors, errors are printed to stdout (Bug #45571)
					p = subprocess.Popen(['/usr/sbin/slaptest', '-u'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
					stdout, stderr = p.communicate()
					stdout, stderr = stdout.decode('UTF-8', 'replace'), stderr.decode('UTF-8', 'replace')
					if p.returncode != 0:
						ud.debug(ud.LISTENER, ud.ERROR, '%s: validation failed (%s):\n%s\n%s.' % (name, p.returncode, stdout, stderr))
						set_handler_message(name, dn, 'slaptest validation failed {} {} {}'.format(stdout, stderr, p.returncode))
						ud.debug(ud.LISTENER, ud.WARN, '%s: Restoring %s.' % (name, old_filename))
						# Revert changes
						try:
							with open(backup_filename, 'rb') as original:
								file_data = original.read()
							with open(old_filename, 'wb') as target_file:
								target_file.write(b"### %s: Leftover of removed settings/ldapschema\n" % (str(datetime.datetime.now()).encode('ASCII'), ) + file_data)
							os.unlink(backup_filename)
							os.close(backup_fd)
						except IOError:
							ud.debug(ud.LISTENER, ud.ERROR, '%s: Error reverting removal of %s.' % (name, old_filename))
						# Commit and exit
						ucr_handlers.commit(ucr, ['/etc/ldap/slapd.conf'])
						return

					ud.debug(ud.LISTENER, ud.INFO, '%s: validation successful, removing backup of old file %s.' % (name, backup_filename))
					os.unlink(backup_filename)
					os.close(backup_fd)

					self._todo_list.append(dn)
					self._do_reload = True

				finally:
					listener.unsetuid()


class UniventionLDAPACL(UniventionLDAPExtensionWithListenerHandler):
	target_container_name = "ldapacl"
	udm_module_name = "settings/ldapacl"
	active_flag_attribute = "univentionLDAPACLActive"
	filesuffix = ".acl"
	file_prefix = 'ldapacl_'

	def handler(self, dn, new, old, name=None):
		try:
			return self._handler(dn, new, old, name)
		except BaseDirRestriction as exc:
			ud.debug(ud.LISTENER, ud.ERROR, '%r basedir conflict: %s' % (dn, exc))

	def _handler(self, dn, new, old, name=None):
		"""Handle LDAP ACL extensions on Master, Backup and Slave"""

		if not listener.configRegistry.get('ldap/server/type'):
			return

		if not listener.configRegistry.get('server/role') in ('domaincontroller_master',):
			# new, ignore first *inactive* appearance, has to be activated on master first
			if new and not old and new.get('univentionLDAPACLActive', [b'FALSE'])[0] != b'TRUE':
				ud.debug(ud.LISTENER, ud.PROCESS, '%s: ignore first appearance of %s, not yet activated' % (name, dn))
				return
			# ignore change unless (re) activated
			if new and old:
				if not new.get('univentionLDAPACLActive', [b'FALSE'])[0] == b'TRUE':
					ud.debug(ud.LISTENER, ud.PROCESS, '%s: ignore modify of %s, not yet activated' % (name, dn))
					return

		# Check UCS version requirements first and skip new if they are not met.
		if new:
			univentionUCSVersionStart = new.get('univentionUCSVersionStart', [b''])[0].decode('UTF-8')
			univentionUCSVersionEnd = new.get('univentionUCSVersionEnd', [b''])[0].decode('UTF-8')
			current_UCS_version = "%s-%s" % (listener.configRegistry.get('version/version'), listener.configRegistry.get('version/patchlevel'))
			if univentionUCSVersionStart and UCS_Version(current_UCS_version) < UCS_Version(univentionUCSVersionStart):
				ud.debug(ud.LISTENER, ud.INFO, '%s: extension %s requires at least UCR version %s.' % (name, new['cn'][0].decode('UTF-8'), univentionUCSVersionStart))
				new = None
			elif univentionUCSVersionEnd and UCS_Version(current_UCS_version) > UCS_Version(univentionUCSVersionEnd):
				ud.debug(ud.LISTENER, ud.INFO, '%s: extension %s specifies compatibility only up to and including UCR version %s.' % (name, new['cn'][0].decode('UTF-8'), univentionUCSVersionEnd))
				new = None

		if new:
			new_version = new.get('univentionOwnedByPackageVersion', [b''])[0].decode('UTF-8')
			if not new_version:
				return

			new_pkgname = new.get('univentionOwnedByPackage', [None])[0]
			if not new_pkgname:
				return

			ud.debug(ud.LISTENER, ud.PROCESS, '%s: %s active? %s' % (name, dn, new.get('univentionLDAPACLActive')))

			if old:  # check for trivial changes
				diff_keys = [key for key in new.keys() if new.get(key) != old.get(key) and key not in ('entryCSN', 'modifyTimestamp', 'modifiersName')]
				if diff_keys == ['univentionLDAPACLActive'] and new['univentionLDAPACLActive'][0] == b'TRUE':
					# ignore status change on master, already activated
					if listener.configRegistry.get('server/role') in ('domaincontroller_master',):
						ud.debug(ud.LISTENER, ud.INFO, '%s: extension %s: activation status changed.' % (name, new['cn'][0].decode('UTF-8')))
						return
				elif diff_keys == ['univentionAppIdentifier']:
					ud.debug(ud.LISTENER, ud.INFO, '%s: extension %s: App identifier changed.' % (name, new['cn'][0].decode('UTF-8')))
					return
				ud.debug(ud.LISTENER, ud.INFO, '%s: extension %s: changed attributes: %s' % (name, new['cn'][0].decode('UTF-8'), diff_keys))

				if new_pkgname == old.get('univentionOwnedByPackage', [None])[0]:
					old_version = old.get('univentionOwnedByPackageVersion', [b'0'])[0].decode('UTF-8')
					rc = apt.apt_pkg.version_compare(new_version, old_version)
					if not rc > -1:
						ud.debug(ud.LISTENER, ud.WARN, '%s: New version is lower than version of old object (%s), skipping update.' % (name, old_version))
						return

			set_handler_message(name, dn, 'handler start')

			try:
				new_object_data = bz2.decompress(new['univentionLDAPACLData'][0])
			except TypeError:
				ud.debug(ud.LISTENER, ud.ERROR, '%s: Error uncompressing data of object %s.' % (name, dn))
				set_handler_message(name, dn, 'Error uncompressing data of object {}.'.format(dn))
				return

			new_basename = new['univentionLDAPACLFilename'][0].decode('UTF-8')
			try:
				new_filename = safe_path_join(self.ucr_slapd_conf_subfile_dir, new_basename)
			except BaseDirRestriction as exc:
				if old:
					ud.debug(ud.LISTENER, ud.ERROR, 'invalid filename detected during modification. removing file!')
					set_handler_message(name, dn, 'invalid filename detected during modification. removing file!')
					self._handler(dn, [], old, name)
				raise exc
			listener.setuid(0)
			try:
				backup_filename = None
				backup_ucrinfo_filename = None
				backup_backlink_filename = None
				if old:
					old_filename = safe_path_join(self.ucr_slapd_conf_subfile_dir, old['univentionLDAPACLFilename'][0].decode('UTF-8'))
					if os.path.exists(old_filename):
						backup_fd, backup_filename = tempfile.mkstemp()
						ud.debug(ud.LISTENER, ud.INFO, '%s: Moving old file %s to %s.' % (name, old_filename, backup_filename))
						try:
							shutil.move(old_filename, backup_filename)
						except IOError:
							ud.debug(ud.LISTENER, ud.WARN, '%s: Error renaming old file %s, removing it.' % (name, old_filename))
							os.unlink(old_filename)
							backup_filename = None
							os.close(backup_fd)

					# plus the old backlink file
					old_backlink_filename = "%s.info" % old_filename
					if os.path.exists(old_backlink_filename):
						backup_backlink_fd, backup_backlink_filename = tempfile.mkstemp()
						ud.debug(ud.LISTENER, ud.INFO, '%s: Moving old backlink file %s to %s.' % (name, old_backlink_filename, backup_backlink_filename))
						try:
							shutil.move(old_backlink_filename, backup_backlink_filename)
						except IOError:
							ud.debug(ud.LISTENER, ud.WARN, '%s: Error renaming old backlink file %s, removing it.' % (name, old_backlink_filename))
							os.unlink(old_backlink_filename)
							backup_backlink_filename = None
							os.close(backup_backlink_fd)

					# and the old UCR registration
					old_ucrinfo_filename = safe_path_join(self.ucr_info_basedir, "%s%s.info" % (self.file_prefix, old['univentionLDAPACLFilename'][0].decode('UTF-8')))
					if os.path.exists(old_ucrinfo_filename):
						backup_ucrinfo_fd, backup_ucrinfo_filename = tempfile.mkstemp()
						ud.debug(ud.LISTENER, ud.INFO, '%s: Moving old UCR info file %s to %s.' % (name, old_ucrinfo_filename, backup_ucrinfo_filename))
						try:
							shutil.move(old_ucrinfo_filename, backup_ucrinfo_filename)
						except IOError:
							ud.debug(ud.LISTENER, ud.WARN, '%s: Error renaming old UCR info file %s, removing it.' % (name, old_ucrinfo_filename))
							os.unlink(old_ucrinfo_filename)
							backup_ucrinfo_filename = None
							os.close(backup_ucrinfo_fd)

				if not os.path.isdir(self.ucr_slapd_conf_subfile_dir):
					if os.path.exists(self.ucr_slapd_conf_subfile_dir):
						ud.debug(ud.LISTENER, ud.WARN, '%s: Directory name %s occupied, renaming blocking file.' % (name, self.ucr_slapd_conf_subfile_dir))
						shutil.move(self.ucr_slapd_conf_subfile_dir, "%s.bak" % self.ucr_slapd_conf_subfile_dir)
					ud.debug(ud.LISTENER, ud.INFO, '%s: Create directory %s.' % (name, self.ucr_slapd_conf_subfile_dir))
					os.makedirs(self.ucr_slapd_conf_subfile_dir, 0o755)

				# Create new extension file
				try:
					ud.debug(ud.LISTENER, ud.INFO, '%s: Writing new extension file %s.' % (name, new_filename))
					with open(new_filename, 'wb') as f:
						f.write(new_object_data)
				except IOError:
					ud.debug(ud.LISTENER, ud.ERROR, '%s: Error writing file %s.' % (name, new_filename))
					set_handler_message(name, dn, 'Error writing file {}.'.format(new_filename))
					return

				# plus backlink file
				try:
					new_backlink_filename = "%s.info" % new_filename
					ud.debug(ud.LISTENER, ud.INFO, '%s: Writing backlink file %s.' % (name, new_backlink_filename))
					with open(new_backlink_filename, 'w') as f:
						f.write("%s\n" % dn)
				except IOError:
					ud.debug(ud.LISTENER, ud.ERROR, '%s: Error writing backlink file %s.' % (name, new_backlink_filename))
					set_handler_message(name, dn, 'Error writing backlink file %s.'.format(new_backlink_filename))
					return

				# and UCR registration
				try:
					new_ucrinfo_filename = safe_path_join(self.ucr_info_basedir, "%s%s.info" % (self.file_prefix, new['univentionLDAPACLFilename'][0].decode('UTF-8')))
					ud.debug(ud.LISTENER, ud.INFO, '%s: Writing UCR info file %s.' % (name, new_ucrinfo_filename))
					with open(new_ucrinfo_filename, 'w') as f:
						f.write("Type: multifile\nMultifile: etc/ldap/slapd.conf\n\nType: subfile\nMultifile: etc/ldap/slapd.conf\nSubfile: etc/ldap/slapd.conf.d/%s\n" % new_basename)
				except IOError:
					ud.debug(ud.LISTENER, ud.ERROR, '%s: Error writing UCR info file %s.' % (name, new_ucrinfo_filename))
					set_handler_message(name, dn, 'Error writing UCR info file {}.'.format(new_ucrinfo_filename))
					return

				# Commit to slapd.conf
				ucr = ConfigRegistry()
				ucr.load()
				ucr_handlers = configHandlers()
				ucr_handlers.load()
				ucr_handlers.update()
				ucr_handlers.commit(ucr, ['/etc/ldap/slapd.conf'])

				# validate
				p = subprocess.Popen(['/usr/sbin/slaptest', '-u'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
				stdout, stderr = p.communicate()
				stdout, stderr = stdout.decode('UTF-8', 'replace'), stderr.decode('UTF-8', 'replace')
				if p.returncode != 0:
					ud.debug(ud.LISTENER, ud.ERROR, '%s: slapd.conf validation failed:\n%s.' % (name, stdout))
					set_handler_message(name, dn, 'slaptest validation failed {} {} {}'.format(stdout, stderr, p.returncode))
					# Revert changes
					ud.debug(ud.LISTENER, ud.ERROR, '%s: Removing new file %s.' % (name, new_filename))
					os.unlink(new_filename)
					os.unlink(new_backlink_filename)
					os.unlink(new_ucrinfo_filename)
					if backup_filename:
						ud.debug(ud.LISTENER, ud.ERROR, '%s: Restoring previous file %s.' % (name, old_filename))
						try:
							shutil.move(backup_filename, old_filename)
							os.close(backup_fd)
						except IOError:
							ud.debug(ud.LISTENER, ud.ERROR, '%s: Error reverting to old file %s.' % (name, old_filename))
					# plus backlink file
					if backup_backlink_filename:
						ud.debug(ud.LISTENER, ud.ERROR, '%s: Restoring previous backlink file %s.' % (name, old_backlink_filename))
						try:
							shutil.move(backup_backlink_filename, old_backlink_filename)
							os.close(backup_backlink_fd)
						except IOError:
							ud.debug(ud.LISTENER, ud.ERROR, '%s: Error reverting to old backlink file %s.' % (name, old_backlink_filename))
					# and the old UCR registration
					if backup_ucrinfo_filename:
						ud.debug(ud.LISTENER, ud.ERROR, '%s: Restoring previous UCR info file %s.' % (name, old_ucrinfo_filename))
						try:
							shutil.move(backup_ucrinfo_filename, old_ucrinfo_filename)
							os.close(backup_ucrinfo_fd)
						except IOError:
							ud.debug(ud.LISTENER, ud.ERROR, '%s: Error reverting to old UCR info file %s.' % (name, old_ucrinfo_filename))
					# Commit and exit
					ucr_handlers.commit(ucr, ['/etc/ldap/slapd.conf'])
					return
				ud.debug(ud.LISTENER, ud.INFO, '%s: validation successful.' % (name,))

				# cleanup backup
				if backup_filename:
					ud.debug(ud.LISTENER, ud.INFO, '%s: Removing backup of old file %s.' % (name, backup_filename))
					os.unlink(backup_filename)
					os.close(backup_fd)
				# plus backlink file
				if backup_backlink_filename:
					ud.debug(ud.LISTENER, ud.INFO, '%s: Removing backup of old backlink file %s.' % (name, backup_backlink_filename))
					os.unlink(backup_backlink_filename)
					os.close(backup_backlink_fd)
				# and the old UCR registration
				if backup_ucrinfo_filename:
					ud.debug(ud.LISTENER, ud.INFO, '%s: Removing backup of old UCR info file %s.' % (name, backup_ucrinfo_filename))
					os.unlink(backup_ucrinfo_filename)
					os.close(backup_ucrinfo_fd)

				self._todo_list.append(dn)
				self._do_reload = True

			finally:
				listener.unsetuid()
		elif old:
			old_filename = safe_path_join(self.ucr_slapd_conf_subfile_dir, old['univentionLDAPACLFilename'][0].decode('UTF-8'))
			# plus backlink file
			old_backlink_filename = "%s.info" % old_filename
			# and the old UCR registration
			old_ucrinfo_filename = safe_path_join(self.ucr_info_basedir, "%s%s.info" % (self.file_prefix, old['univentionLDAPACLFilename'][0].decode('UTF-8')))
			if os.path.exists(old_filename):
				listener.setuid(0)
				try:
					ud.debug(ud.LISTENER, ud.INFO, '%s: Removing extension %s.' % (name, old['cn'][0].decode('UTF-8')))
					if os.path.exists(old_ucrinfo_filename):
						os.unlink(old_ucrinfo_filename)
					if os.path.exists(old_backlink_filename):
						os.unlink(old_backlink_filename)
					os.unlink(old_filename)

					ucr = ConfigRegistry()
					ucr.load()
					ucr_handlers = configHandlers()
					ucr_handlers.load()
					ucr_handlers.update()
					ucr_handlers.commit(ucr, ['/etc/ldap/slapd.conf'])

					self._todo_list.append(dn)
					self._do_reload = True

				finally:
					listener.unsetuid()


class UniventionDataExtension(UniventionLDAPExtension):
	target_container_name = 'data'
	udm_module_name = 'settings/data'
	active_flag_attribute = ''
	filesuffix = ''

	def is_local_active(self):
		return (0, None)

	def wait_for_activation(self, timeout=180):
		return True


class UniventionUDMExtension(six.with_metaclass(ABCMeta, UniventionLDAPExtension)):

	def wait_for_activation(self, timeout=180):
		if not UniventionLDAPExtension.wait_for_activation(self, timeout):
			return False

		timeout = 60
		print("Waiting for file %s:" % (self.filename,), end=' ')
		t0 = time.time()
		while not os.path.exists(self.filename):
			if time.time() - t0 > timeout:
				print("ERROR")
				print("ERROR: Timeout waiting for %s." % (self.filename,), file=sys.stderr)
				return False
			sys.stdout.write(".")
			sys.stdout.flush()
			time.sleep(3)
		print("OK")
		return True


class UniventionUDMModule(UniventionUDMExtension):
	target_container_name = "udm_module"
	udm_module_name = "settings/udm_module"
	active_flag_attribute = "univentionUDMModuleActive"
	filesuffix = ".py"

	def register(self, filename, options, udm_passthrough_options, target_filename=None):
		# Determine UDM module name
		saved_value = sys.dont_write_bytecode
		sys.dont_write_bytecode = True
		try:
			module_name = imp.load_source('dummy', filename).module
		except AttributeError:
			print("ERROR: python variable 'module' undefined in given file:", filename)
			sys.exit(1)
		finally:
			sys.dont_write_bytecode = saved_value

		UniventionUDMExtension.register(self, filename, options, udm_passthrough_options, target_filename=module_name + ".py")


class UniventionUDMSyntax(UniventionUDMExtension):
	target_container_name = "udm_syntax"
	udm_module_name = "settings/udm_syntax"
	active_flag_attribute = "univentionUDMSyntaxActive"
	filesuffix = ".py"


class UniventionUDMHook(UniventionUDMExtension):
	target_container_name = "udm_hook"
	udm_module_name = "settings/udm_hook"
	active_flag_attribute = "univentionUDMHookActive"
	filesuffix = ".py"


def option_validate_existing_filename(option, opt, value):
	if not os.path.exists(value):
		raise OptionValueError("%s: file does not exist: %s" % (opt, value))
	return value


def option_validate_ucs_version(option, opt, value):
	regex = re.compile("[-.0-9]+")
	if not regex.match(value):
		raise OptionValueError("%s: may only contain digit, dot and dash characters: %s" % (opt, value))
	return value


def option_validate_gnu_message_catalogfile(option, opt, value):
	if not os.path.exists(value):
		raise OptionValueError("%s: file does not exist: %s" % (opt, value))
	filename_parts = os.path.splitext(value)
	language = filename_parts[0]
	if language not in os.listdir('/usr/share/locale'):
		raise OptionValueError("%s: file basename is not a registered language: %s" % (opt, value))
	if not MIME_DESCRIPTION.file(value).startswith('GNU message catalog'):
		raise OptionValueError("%s: file is not a GNU message catalog: %s" % (opt, value))

	return value


class UCSOption(Option):
	TYPES = Option.TYPES + ("existing_filename", "ucs_version", )
	TYPE_CHECKER = copy(Option.TYPE_CHECKER)
	TYPE_CHECKER["existing_filename"] = option_validate_existing_filename
	TYPE_CHECKER["ucs_version"] = option_validate_ucs_version
	TYPE_CHECKER["gnu_message_catalogfile"] = option_validate_gnu_message_catalogfile


def option_callback_udm_passthrough_options(option, opt_str, value, parser, *args):
	if value.startswith('--'):
		raise OptionValueError("%s requires an argument" % (opt_str,))
	udm_passthrough_options = args[0]
	udm_passthrough_options.append(opt_str)
	udm_passthrough_options.append(value)
	setattr(parser.values, option.dest, value)


def check_data_module_options(option, opt_str, value, parser):
	if value.startswith('--'):
		raise OptionValueError("%s requires an argument" % (opt_str,))
	if not parser.values.data:
		raise OptionValueError("%s can only be used after --data" % (opt_str,))


def option_callback_set_data_module_options(option, opt_str, value, parser):
	check_data_module_options(option, opt_str, value, parser)
	setattr(parser.values, option.dest, value)


def option_callback_append_data_module_options(option, opt_str, value, parser):
	check_data_module_options(option, opt_str, value, parser)
	parser.values.ensure_value(option.dest, []).append(value)


def check_udm_module_options(option, opt_str, value, parser):
	if value.startswith('--'):
		raise OptionValueError("%s requires an argument" % (opt_str,))
	if not parser.values.udm_module:
		raise OptionValueError("%s can only be used after --udm_module" % (opt_str,))


def option_callback_set_udm_module_options(option, opt_str, value, parser):
	check_udm_module_options(option, opt_str, value, parser)
	setattr(parser.values, option.dest, value)


def option_callback_append_udm_module_options(option, opt_str, value, parser):
	check_udm_module_options(option, opt_str, value, parser)
	parser.values.ensure_value(option.dest, []).append(value)


def check_udm_syntax_options(option, opt_str, value, parser):
	if value.startswith('--'):
		raise OptionValueError("%s requires an argument" % (opt_str,))
	if not parser.values.udm_syntax:
		raise OptionValueError("%s can only be used after --udm_syntax" % (opt_str,))


def option_callback_append_udm_syntax_options(option, opt_str, value, parser):
	check_udm_syntax_options(option, opt_str, value, parser)
	parser.values.ensure_value(option.dest, []).append(value)


def check_udm_hook_options(option, opt_str, value, parser):
	if value.startswith('--'):
		raise OptionValueError("%s requires an argument" % (opt_str,))
	if not parser.values.udm_hook:
		raise OptionValueError("%s can only be used after --udm_hook" % (opt_str,))


def option_callback_append_udm_hook_options(option, opt_str, value, parser):
	check_udm_hook_options(option, opt_str, value, parser)
	parser.values.ensure_value(option.dest, []).append(value)


def ucs_registerLDAPExtension():
	functionname = inspect.stack()[0][3]
	parser = OptionParser(prog=functionname, option_class=UCSOption)

	parser.add_option(
		"--schema", dest="schemafile",
		action="append", type="existing_filename", default=[],
		help="Register LDAP schema", metavar="<LDAP schema file>")

	parser.add_option(
		"--acl", dest="aclfile",
		action="append", type="existing_filename", default=[],
		help="Register LDAP ACL", metavar="<UCR template for OpenLDAP ACL file>")

	parser.add_option(
		"--udm_module", dest="udm_module",
		action="append", type="existing_filename", default=[],
		help="UDM module", metavar="<filename>")

	parser.add_option(
		"--udm_syntax", dest="udm_syntax",
		action="append", type="existing_filename", default=[],
		help="UDM syntax", metavar="<filename>")

	parser.add_option(
		"--udm_hook", dest="udm_hook",
		action="append", type="existing_filename", default=[],
		help="UDM hook", metavar="<filename>")

	parser.add_option(
		"--data", dest="data",
		action="append", type="existing_filename", default=[],
		help="Data object", metavar="<filename>")

	parser.add_option(
		"--packagename", dest="packagename",
		help="Package name")
	parser.add_option(
		"--packageversion", dest="packageversion",
		help="Package version")

	parser.add_option(
		"--ucsversionstart", dest="ucsversionstart",
		action="store", type="ucs_version",
		help="Start activation with UCS version", metavar="<UCS Version>")
	parser.add_option(
		"--ucsversionend", dest="ucsversionend",
		action="store", type="ucs_version",
		help="End activation with UCS version", metavar="<UCS Version>")

	parser.add_option(
		"--name", dest="objectname",
		help="Default LDAP object name")

	data_module_options = OptionGroup(parser, "Data object specific options")
	data_module_options.add_option(
		"--data_type", dest="data_type",
		type="string",
		action="callback", callback=option_callback_set_data_module_options,
		help="type of data object", metavar="<Data object type>")
	data_module_options.add_option(
		"--data_meta", dest="data_meta", default=[],
		type="string",
		action="callback", callback=option_callback_append_data_module_options,
		help="meta data for data object", metavar="<string>")
	parser.add_option_group(data_module_options)

	udm_module_options = OptionGroup(parser, "UDM module specific options")
	udm_module_options.add_option(
		"--messagecatalog", dest="udm_module_messagecatalog",
		type="existing_filename", default=[],
		action="callback", callback=option_callback_append_udm_module_options,
		help="Gettext mo file", metavar="<GNU message catalog file>")
	udm_module_options.add_option(
		"--udm_module_messagecatalog", dest="udm_module_messagecatalog",
		type="existing_filename", default=[],
		action="callback", callback=option_callback_append_udm_module_options,
		help="Gettext mo file", metavar="<GNU message catalog file>")
	udm_module_options.add_option(
		"--umcmessagecatalog", dest="umcmessagecatalog",
		type="existing_filename", default=[],
		action="callback", callback=option_callback_append_udm_module_options,
		help="Gettext mo file", metavar="<GNU message catalog file>")
	udm_module_options.add_option(
		"--umcregistration", dest="umcregistration",
		type="existing_filename",
		action="callback", callback=option_callback_set_udm_module_options,
		help="UMC registration xml file", metavar="<XML file>")
	udm_module_options.add_option(
		"--icon", dest="icon",
		type="existing_filename", default=[],
		action="callback", callback=option_callback_append_udm_module_options,
		help="UDM module icon", metavar="<Icon file>")
	parser.add_option_group(udm_module_options)

	udm_module_options = OptionGroup(parser, "UDM syntax specific options")
	udm_module_options.add_option(
		"--udm_syntax_messagecatalog", dest="udm_syntax_messagecatalog",
		type="existing_filename", default=[],
		action="callback", callback=option_callback_append_udm_syntax_options,
		help="Gettext mo file", metavar="<GNU message catalog file>")
	parser.add_option_group(udm_module_options)

	udm_module_options = OptionGroup(parser, "UDM hook specific options")
	udm_module_options.add_option(
		"--udm_hook_messagecatalog", dest="udm_hook_messagecatalog",
		type="existing_filename", default=[],
		action="callback", callback=option_callback_append_udm_hook_options,
		help="Gettext mo file", metavar="<GNU message catalog file>")
	parser.add_option_group(udm_module_options)

	# parser.add_option("-v", "--verbose", action="count")

	udm_passthrough_options = []
	auth_options = OptionGroup(parser, "Authentication Options", "These options are usually passed e.g. from a calling joinscript")
	auth_options.add_option(
		"--binddn", dest="binddn", type="string",
		action="callback", callback=option_callback_udm_passthrough_options, callback_args=(udm_passthrough_options,),
		help="LDAP binddn", metavar="<LDAP DN>")
	auth_options.add_option(
		"--bindpwd", dest="bindpwd", type="string",
		action="callback", callback=option_callback_udm_passthrough_options, callback_args=(udm_passthrough_options,),
		help="LDAP bindpwd", metavar="<LDAP bindpwd>")
	auth_options.add_option(
		"--bindpwdfile", dest="bindpwdfile",
		action="callback", callback=option_callback_udm_passthrough_options, callback_args=(udm_passthrough_options,),
		type="existing_filename",
		help="File containing LDAP bindpwd", metavar="<filename>")
	parser.add_option_group(auth_options)

	opts, args = parser.parse_args()
	if len(opts.udm_module) > 1:
		parser.error('--udm_module option can be given once only.')
	if not opts.packagename:
		parser.error('--packagename option is required.')
	if not opts.packageversion:
		parser.error('--packageversion option is required.')
	if opts.data and not opts.data_type:
		parser.error('--data_type option is required if --data is used.')

	if not (opts.schemafile or opts.aclfile or opts.udm_syntax or opts.udm_hook or opts.udm_module or opts.data):
		parser.print_help()
		sys.exit(2)

	ucr = ConfigRegistry()
	ucr.load()

	objects = []
	if opts.schemafile:
		if UniventionLDAPSchema.create_base_container(ucr, udm_passthrough_options) != 0:
			sys.exit(1)

		for schemafile in opts.schemafile:
			univentionLDAPSchema = UniventionLDAPSchema(ucr)
			univentionLDAPSchema.register(schemafile, opts, udm_passthrough_options)
			objects.append(univentionLDAPSchema)

	if opts.aclfile:
		if UniventionLDAPACL.create_base_container(ucr, udm_passthrough_options) != 0:
			sys.exit(1)

		for aclfile in opts.aclfile:
			univentionLDAPACL = UniventionLDAPACL(ucr)
			univentionLDAPACL.register(aclfile, opts, udm_passthrough_options)
			objects.append(univentionLDAPACL)

	if opts.udm_syntax:
		if UniventionUDMSyntax.create_base_container(ucr, udm_passthrough_options) != 0:
			sys.exit(1)

		for udm_syntax in opts.udm_syntax:
			univentionUDMSyntax = UniventionUDMSyntax(ucr)
			univentionUDMSyntax.register(udm_syntax, opts, udm_passthrough_options)
			objects.append(univentionUDMSyntax)

	if opts.udm_hook:
		if UniventionUDMHook.create_base_container(ucr, udm_passthrough_options) != 0:
			sys.exit(1)

		for udm_hook in opts.udm_hook:
			univentionUDMHook = UniventionUDMHook(ucr)
			univentionUDMHook.register(udm_hook, opts, udm_passthrough_options)
			objects.append(univentionUDMHook)

	if opts.udm_module:
		if UniventionUDMModule.create_base_container(ucr, udm_passthrough_options) != 0:
			sys.exit(1)

		for udm_module in opts.udm_module:
			univentionUDMModule = UniventionUDMModule(ucr)
			univentionUDMModule.register(udm_module, opts, udm_passthrough_options)
			objects.append(univentionUDMModule)

	if opts.data:
		if UniventionDataExtension.create_base_container(ucr, udm_passthrough_options) != 0:
			sys.exit(1)

		for data in opts.data:
			univentionDataExtension = UniventionDataExtension(ucr)
			univentionDataExtension.register(data, opts, udm_passthrough_options)
			objects.append(univentionDataExtension)

	for obj in objects:
		if not obj.wait_for_activation():
			print("%s: registraton of %s failed." % (functionname, obj.filename))
			sys.exit(1)

	if opts.udm_module:
		print("Terminating running univention-cli-server processes.")
		p = subprocess.Popen(['pkill', '-f', 'univention-cli-server'], close_fds=True)
		p.wait()


def ucs_unregisterLDAPExtension():
	functionname = inspect.stack()[0][3]
	parser = OptionParser(prog=functionname, option_class=UCSOption)

	parser.add_option(
		"--schema", dest="schemaobject",
		action="append", type="string",
		help="LDAP schema", metavar="<schema name>")

	parser.add_option(
		"--acl", dest="aclobject",
		action="append", type="string",
		help="LDAP ACL", metavar="<ACL name>")

	parser.add_option(
		"--udm_module", dest="udm_module",
		action="append", type="string",
		help="UDM module", metavar="<module name>")

	parser.add_option(
		"--udm_syntax", dest="udm_syntax",
		action="append", type="string",
		help="UDM syntax", metavar="<syntax name>")

	parser.add_option(
		"--udm_hook", dest="udm_hook",
		action="append", type="string",
		help="UDM hook", metavar="<hook name>")

	parser.add_option(
		"--data", dest="data",
		action="append", type="string",
		help="Data object", metavar="<path to data object>")

	# parser.add_option("-v", "--verbose", action="count")

	udm_passthrough_options = []
	auth_options = OptionGroup(parser, "Authentication Options", "These options are usually passed e.g. from a calling joinscript")
	auth_options.add_option(
		"--binddn", dest="binddn", type="string",
		action="callback", callback=option_callback_udm_passthrough_options, callback_args=(udm_passthrough_options,),
		help="LDAP binddn", metavar="<LDAP DN>")
	auth_options.add_option(
		"--bindpwd", dest="bindpwd", type="string",
		action="callback", callback=option_callback_udm_passthrough_options, callback_args=(udm_passthrough_options,),
		help="LDAP bindpwd", metavar="<LDAP bindpwd>")
	auth_options.add_option(
		"--bindpwdfile", dest="bindpwdfile",
		action="callback", callback=option_callback_udm_passthrough_options, callback_args=(udm_passthrough_options,),
		type="existing_filename",
		help="File containing LDAP bindpwd", metavar="<filename>")
	parser.add_option_group(auth_options)
	opts, args = parser.parse_args()

	ucr = ConfigRegistry()
	ucr.load()

	if opts.data:
		for data in opts.data:
			univentionDataExtension = UniventionDataExtension(ucr)
			univentionDataExtension.unregister(data, opts, udm_passthrough_options)

	if opts.udm_module:
		for udm_module in opts.udm_module:
			univentionUDMModule = UniventionUDMModule(ucr)
			univentionUDMModule.unregister(udm_module, opts, udm_passthrough_options)

	if opts.udm_hook:
		for udm_hook in opts.udm_hook:
			univentionUDMHook = UniventionUDMHook(ucr)
			univentionUDMHook.unregister(udm_hook, opts, udm_passthrough_options)

	if opts.udm_syntax:
		for udm_syntax in opts.udm_syntax:
			univentionUDMSyntax = UniventionUDMSyntax(ucr)
			univentionUDMSyntax.unregister(udm_syntax, opts, udm_passthrough_options)

	if opts.aclobject:
		for aclobject in opts.aclobject:
			univentionLDAPACL = UniventionLDAPACL(ucr)
			univentionLDAPACL.unregister(aclobject, opts, udm_passthrough_options)

	if opts.schemaobject:
		for schemaobject in opts.schemaobject:
			univentionLDAPSchema = UniventionLDAPSchema(ucr)
			univentionLDAPSchema.unregister(schemaobject, opts, udm_passthrough_options)


if __name__ == '__main__':
	commands = {'ucs_unregisterLDAPExtension': ucs_unregisterLDAPExtension, 'ucs_registerLDAPExtension': ucs_registerLDAPExtension}
	if len(sys.argv) > 1 and sys.argv[1] in commands:
		commands[sys.argv.pop(1)]()
