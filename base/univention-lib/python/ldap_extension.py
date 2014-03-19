from optparse import OptionParser, OptionGroup, Option, OptionValueError
from copy import copy
import inspect
import os
import shutil
import re
import sys
import univention.debug as ud
from univention.config_registry import configHandlers, ConfigRegistry
from univention.admin import uldap as udm_uldap
from univention.admin import modules as udm_modules
from univention.admin import uexceptions as udm_errors
from univention.lib.ucs import UCS_Version
import subprocess
import bz2
import base64
import time
import tempfile
import datetime
import apt
from abc import ABCMeta, abstractproperty, abstractmethod
import imp
import listener
from univention.lib.umc_module import MIME_DESCRIPTION

class UniventionLDAPExtension(object):
	__metaclass__ = ABCMeta

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
		p = subprocess.Popen(cmd)
		p.wait()
		return p.returncode

	def is_local_active(self):
		object_dn = None

		cmd = ["univention-ldapsearch", "-xLLL", "-b", self.object_dn, "-s", "base", "(&(cn=%s)(%s=TRUE))" % (self.objectname, self.active_flag_attribute)]
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		(stdout, stderr) = p.communicate()
		if p.returncode:
			return (p.returncode, object_dn)
		regex = re.compile('^dn: (.*)$', re.M)
		m = regex.search(stdout)
		if m:
			object_dn = m.group(1)
		return (p.returncode, object_dn)

	def wait_for_activation(self, timeout=180):
		print "Waiting for activation of the extension object %s:" % (self.objectname,),
		t0 = time.time()
		while not self.is_local_active()[1]:
			if time.time() - t0 > timeout:
				print "ERROR"
				print >>sys.stderr, "ERROR: Master did not mark the extension object active within %s seconds." % (timeout,)
				return False
			sys.stdout.write(".")
			sys.stdout.flush()
			time.sleep(3)
		print "OK"
		return True

	def udm_find_object(self):
		cmd = ["univention-directory-manager", self.udm_module_name, "list"] + self.udm_passthrough_options + [
				"--filter", "name=%s" % self.objectname,
				]
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
		(stdout, stderr) = p.communicate()
		return (p.returncode, stdout)

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

	def register(self, filename, options, udm_passthrough_options, target_filename = None):
		self.filename = filename
		self.options = options
		self.udm_passthrough_options = udm_passthrough_options
		self.target_filename = target_filename or os.path.basename(filename)

		target_filename_parts = os.path.splitext(self.target_filename)
		if target_filename_parts[1] == self.filesuffix:
			self.objectname = target_filename_parts[0]
		else:
			self.objectname = self.target_filename

		try:
			with open(self.filename, 'r') as f:
				compressed_data = bz2.compress(f.read())
		except Exception as e:
			print >>sys.stderr, "Compression of file %s failed: %s" % (self.filename, e)
			sys.exit(1)

		new_data = base64.b64encode(compressed_data)

		active_change_udm_options = [
			"--set", "filename=%s" % self.target_filename,
			"--set", "data=%s" % new_data,
			"--set", "active=FALSE",
			]

		common_udm_options = [
			"--set", "package=%s" % (options.packagename,),
			"--set", "packageversion=%s" % (options.packageversion,),
			]

		if self.udm_module_name != "settings/ldapschema":
			if options.ucsversionstart:
				common_udm_options.extend(["--set", "ucsversionstart=%s" % (options.ucsversionstart,),])
			if options.ucsversionend:
				common_udm_options.extend(["--set", "ucsversionend=%s" % (options.ucsversionend,),])

		if self.udm_module_name == "settings/udm_module":
			for messagecatalog in options.messagecatalog:
				filename_parts = os.path.splitext(os.path.basename(messagecatalog))
				language = filename_parts[0]
				with open(messagecatalog, 'r') as f:
					common_udm_options.extend(["--append", "messagecatalog=%s %s" % (language, base64.b64encode(f.read()),),])
			if options.umcregistration:
				try:
					with open(options.umcregistration, 'r') as f:
						compressed_data = bz2.compress(f.read())
				except Exception as e:
					print >>sys.stderr, "Compression of file %s failed: %s" % (options.umcregistration, e)
					sys.exit(1)
				common_udm_options.extend(["--set", "umcregistration=%s" % (base64.b64encode(compressed_data),),])
			for icon in options.icon:
				with open(icon, 'r') as f:
					common_udm_options.extend(["--append", "icon=%s" % (base64.b64encode(f.read()),),])

		rc, self.object_dn, stdout = self.udm_find_object_dn()
		if not self.object_dn:

			cmd = ["univention-directory-manager", self.udm_module_name, "create"] + self.udm_passthrough_options + [
					"--set", "name=%s" % self.objectname,
					"--position", self.target_container_dn,
				] + common_udm_options + active_change_udm_options
			p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			(stdout, stderr) = p.communicate()
			print stdout
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
					print stdout
			else:	## check again, might be a race
				rc, self.object_dn, stdout = self.udm_find_object_dn()
				if not self.object_dn:
					print >>sys.stderr, "ERROR: Failed to create %s object." % (self.udm_module_name,)
					sys.exit(1)

		if self.object_dn: ## object exists already, modify it
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
					print >>sys.stderr, "WARNING: Registered package version %s is newer, refusing registration." % (registered_package_version,)
					sys.exit(4)
			else:
				print >>sys.stderr, "WARNING: Object %s was registered by package %s version %s, changing ownership." % (self.objectname, registered_package, registered_package_version,)

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
				print >>sys.stderr, "INFO: No change of core data of object %s." % (self.objectname,)
				active_change_udm_options = []

			cmd = ["univention-directory-manager", self.udm_module_name, "modify"] + self.udm_passthrough_options + [
					"--dn", self.object_dn,
				] + common_udm_options + active_change_udm_options
			p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			(stdout, stderr) = p.communicate()
			print stdout
			if p.returncode != 0:
				print >>sys.stderr, "ERROR: Modification of %s object failed." % (self.udm_module_name,)
				sys.exit(1)

			appidentifier = os.environ.get('UNIVENTION_APP_IDENTIFIER')
			if appidentifier:
				cmd = ["univention-directory-manager", self.udm_module_name, "modify"] + self.udm_passthrough_options + [
						"--append", "appidentifier=%s" % (appidentifier,),
						"--dn", self.object_dn,
					]
				p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
				(stdout, stderr) = p.communicate()
				print stdout

		if not self.object_dn:
			self.object_dn = new_object_dn


	def unregister(self, objectname, options, udm_passthrough_options):
		self.objectname = objectname
		self.options = options
		self.udm_passthrough_options = udm_passthrough_options

		rc, object_dn, stdout = self.udm_find_object_dn()
		if not object_dn:
			print >>sys.stderr, "ERROR: Object not found in UDM."
			return

		app_filter = ""
		regex = re.compile('^ *appidentifier: (.*)$', re.M)
		for appidentifier in regex.findall(stdout):
			if appidentifier != "None":
				app_filter = app_filter + "(cn=%s)" % appidentifier

		if app_filter:
			cmd = ["univention-ldapsearch", "-xLLL", "(&(objectClass=univentionApp)%s)", "cn" % (app_filter,)]
			p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			(stdout, stderr) = p.communicate()
			if p.returncode:
				print >>sys.stderr, "ERROR: LDAP search failed: %s" % (stdout,)
				sys.exit(1)
			if stdout:
				regex = re.compile('^cn: (.*)$', re.M)
				apps = ",".join(regex.findall(stdout))
				print >>sys.stderr, "INFO: The object %s is still registered by the following apps: %s" % (objectname, apps,)
				sys.exit(2)

		cmd = ["univention-directory-manager", self.udm_module_name, "delete"] + self.udm_passthrough_options + [
				"--dn", object_dn,
			]
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		(stdout, stderr) = p.communicate()
		print stdout

	def mark_active(self):
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
							udm_object['active']=True
							udm_object.modify()
						except udm_errors.noObject, e:
							ud.debug(ud.LISTENER, ud.ERROR, 'Error modifying %s: object not found.' % (object_dn,))
						except udm_errors.ldapError, e:
							ud.debug(ud.LISTENER, ud.ERROR, 'Error modifying %s: %s.' % (object_dn, e))
							raise
					self._todo_list = []

			except udm_errors.ldapError, e:
				ud.debug(ud.LISTENER, ud.ERROR, 'Error accessing UDM: %s' % (e,))


class UniventionLDAPExtensionWithListenerHandler(UniventionLDAPExtension):
	__metaclass__ = ABCMeta

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
		"""Handle LDAP schema extensions on Master and Backup"""
		if not listener.configRegistry.get('server/role') in ('domaincontroller_master', 'domaincontroller_backup'):
			return

		if new:
			new_version = new.get('univentionOwnedByPackageVersion', [None])[0]
			if not new_version:
				return

			new_pkgname = new.get('univentionOwnedByPackage', [None])[0]
			if not new_pkgname:
				return

			if old:	## check for trivial changes
				diff_keys = [ key for key in new.keys() if new.get(key) != old.get(key) and key not in ('entryCSN', 'modifyTimestamp', 'modifiersName')]
				if diff_keys == ['univentionLDAPSchemaActive'] and new.get('univentionLDAPSchemaActive') == 'TRUE':
					ud.debug(ud.LISTENER, ud.INFO, '%s: extension %s: activation status changed.' % (name, new['cn'][0]))
					return
				elif diff_keys == ['univentionAppIdentifier']:
					ud.debug(ud.LISTENER, ud.INFO, '%s: extension %s: App identifier changed.' % (name, new['cn'][0]))
					return
				ud.debug(ud.LISTENER, ud.INFO, '%s: extension %s: changed attributes: %s' % (name, new['cn'][0], diff_keys))

				if new_pkgname == old.get('univentionOwnedByPackage', [None])[0]:
					old_version = old.get('univentionOwnedByPackageVersion', ['0'])[0]
					rc = apt.apt_pkg.version_compare(new_version, old_version)
					if not rc > -1:
						ud.debug(ud.LISTENER, ud.WARN, '%s: New version is lower than version of old object (%s), skipping update.' % (name, old_version))
						return
			
			try:
				new_object_data = bz2.decompress(new.get('univentionLDAPSchemaData')[0])
			except TypeError:
				ud.debug(ud.LISTENER, ud.ERROR, '%s: Error uncompressing data of object %s.' % (name, dn))
				return

			new_filename = os.path.join(self.basedir, new.get('univentionLDAPSchemaFilename')[0])
			listener.setuid(0)
			try:
				backup_filename = None
				if old:
					old_filename = os.path.join(self.basedir, old.get('univentionLDAPSchemaFilename')[0])
					if os.path.exists(old_filename):
						backup_fd, backup_filename = tempfile.mkstemp()
						ud.debug(ud.LISTENER, ud.INFO, '%s: Moving old file %s to %s.' % (name, old_filename, backup_filename))
						try:
							shutil.move(old_filename, backup_filename)
						except IOError:
							ud.debug(ud.LISTENER, ud.WARN, '%s: Error renaming old file %s, removing it.' % (name, old_filename))
							os.unlink(old_filename)	## no choice
							backup_filename = None
							os.close(backup_fd)


				if not os.path.isdir(self.basedir):
					if os.path.exists(self.basedir):
						ud.debug(ud.LISTENER, ud.WARN, '%s: Directory name %s occupied, renaming blocking file.' % (name, self.basedir))
						shutil.move(self.basedir, "%s.bak" % self.basedir)
					ud.debug(ud.LISTENER, ud.INFO, '%s: Create directory %s.' % (name, self.basedir))
					os.makedirs(self.basedir, 0755)

				## Create new extension file
				try:
					ud.debug(ud.LISTENER, ud.INFO, '%s: Writing new extension file %s.' % (name, new_filename))
					with open(new_filename, 'w') as f:
						f.write(new_object_data)
				except IOError:
					ud.debug(ud.LISTENER, ud.ERROR, '%s: Error writing file %s.' % (name, new_filename))
					return

				ucr = ConfigRegistry()
				ucr.load()
				ucr_handlers = configHandlers()
				ucr_handlers.load()
				ucr_handlers.update()
				ucr_handlers.commit(ucr, ['/etc/ldap/slapd.conf'])

				## validate
				p = subprocess.Popen(['/usr/sbin/slapschema', ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
				stdout, stderr = p.communicate()
				if p.returncode != 0:
					ud.debug(ud.LISTENER, ud.ERROR, '%s: validation failed:\n%s.' % (name, stdout))
					## Revert changes
					ud.debug(ud.LISTENER, ud.ERROR, '%s: Removing new file %s.' % (name, new_filename))
					os.unlink(new_filename)
					if backup_filename:
						ud.debug(ud.LISTENER, ud.ERROR, '%s: Restoring previous file %s.' % (name, old_filename))
						try:
							shutil.move(backup_filename, old_filename)
							os.close(backup_fd)
						except IOError:
							ud.debug(ud.LISTENER, ud.ERROR, '%s: Error reverting to old file %s.' % (name, old_filename))
					## Commit and exit
					ucr_handlers.commit(ucr, ['/etc/ldap/slapd.conf'])
					return
				ud.debug(ud.LISTENER, ud.INFO, '%s: validation successful.' % (name,))

				## cleanup backup
				if backup_filename:
					ud.debug(ud.LISTENER, ud.INFO, '%s: Removing backup of old file %s.' % (name, backup_filename))
					os.unlink(backup_filename)
					os.close(backup_fd)

				self._todo_list.append(dn)
				self._do_reload = True

			finally:
				listener.unsetuid()
		elif old:
			old_filename = os.path.join(self.basedir, old.get('univentionLDAPSchemaFilename')[0])
			if os.path.exists(old_filename):
				listener.setuid(0)
				try:
					backup_fd, backup_filename = tempfile.mkstemp()
					ud.debug(ud.LISTENER, ud.INFO, '%s: Moving old file %s to %s.' % (name, old_filename, backup_filename))
					try:
						shutil.move(old_filename, backup_filename)
					except IOError:
						ud.debug(ud.LISTENER, ud.WARN, '%s: Error renaming old file %s, leaving it untouched.' % (name, old_filename))
						os.close(backup_fd)
						return

					ucr = ConfigRegistry()
					ucr.load()
					ucr_handlers = configHandlers()
					ucr_handlers.load()
					ucr_handlers.update()
					ucr_handlers.commit(ucr, ['/etc/ldap/slapd.conf'])

					p = subprocess.Popen(['/usr/sbin/slapschema', ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
					stdout, stderr = p.communicate()
					if p.returncode != 0:
						ud.debug(ud.LISTENER, ud.WARN, '%s: validation fails without %s:\n%s.' % (name, old_filename, stdout))
						ud.debug(ud.LISTENER, ud.WARN, '%s: Restoring %s.' % (name, old_filename))
						## Revert changes
						try:
							with open(backup_filename, 'r') as original:
								file_data = original.read()
							with open(old_filename, 'w') as target_file:
								target_file.write("### %s: Leftover of removed settings/ldapschema\n" % (datetime.datetime.now(), ) + file_data)
							os.unlink(backup_filename)
							os.close(backup_fd)
						except IOError:
							ud.debug(ud.LISTENER, ud.ERROR, '%s: Error reverting removal of %s.' % (name, old_filename))
						## Commit and exit
						ucr_handlers.commit(ucr, ['/etc/ldap/slapd.conf'])
						return

					ud.debug(ud.LISTENER, ud.INFO, '%s: validation successful, removing backup of old file %s.' % (name, backup_filename))
					os.unlink(backup_filename)
					os.close(backup_fd)

					self._do_reload = True
					if dn in self._todo_list:
						self._todo_list = [ x for x in self._todo_list if x != dn ]

				finally:
					listener.unsetuid()
		return



class UniventionLDAPACL(UniventionLDAPExtensionWithListenerHandler):
	target_container_name = "ldapacl"
	udm_module_name = "settings/ldapacl"
	active_flag_attribute = "univentionLDAPACLActive"
	filesuffix = ".acl"
	file_prefix = 'ldapacl_'

	def handler(self, dn, new, old, name=None):
		"""Handle LDAP ACL extensions on Master, Backup and Slave"""

		if not listener.configRegistry.get('ldap/server/type'):
			return

		## Check UCS version requirements first and skip new if they are not met.
		if new:
			univentionUCSVersionStart = new.get('univentionUCSVersionStart', [None])[0]
			univentionUCSVersionEnd = new.get('univentionUCSVersionEnd', [None])[0]
			current_UCS_version = "%s-%s" % ( listener.configRegistry.get('version/version'), listener.configRegistry.get('version/patchlevel') )
			if univentionUCSVersionStart and UCS_Version(current_UCS_version) < UCS_Version(univentionUCSVersionStart):
				ud.debug(ud.LISTENER, ud.INFO, '%s: extension %s requires at least UCR version %s.' % (name, new['cn'][0], univentionUCSVersionStart))
				new=None
			elif univentionUCSVersionEnd and UCS_Version(current_UCS_version) > UCS_Version(univentionUCSVersionEnd):
				ud.debug(ud.LISTENER, ud.INFO, '%s: extension %s specifies compatibility only up to and including UCR version %s.' % (name, new['cn'][0], univentionUCSVersionEnd))
				new=None

		if new:
			new_version = new.get('univentionOwnedByPackageVersion', [None])[0]
			if not new_version:
				return

			new_pkgname = new.get('univentionOwnedByPackage', [None])[0]
			if not new_pkgname:
				return

			if old:	## check for trivial changes
				diff_keys = [ key for key in new.keys() if new.get(key) != old.get(key) and key not in ('entryCSN', 'modifyTimestamp', 'modifiersName')]
				if diff_keys == ['univentionLDAPACLActive'] and new.get('univentionLDAPACLActive')[0] == 'TRUE':
					ud.debug(ud.LISTENER, ud.INFO, '%s: extension %s: activation status changed.' % (name, new['cn'][0]))
					return
				elif diff_keys == ['univentionAppIdentifier']:
					ud.debug(ud.LISTENER, ud.INFO, '%s: extension %s: App identifier changed.' % (name, new['cn'][0]))
					return
				ud.debug(ud.LISTENER, ud.INFO, '%s: extension %s: changed attributes: %s' % (name, new['cn'][0], diff_keys))

				if new_pkgname == old.get('univentionOwnedByPackage', [None])[0]:
					old_version = old.get('univentionOwnedByPackageVersion', ['0'])[0]
					rc = apt.apt_pkg.version_compare(new_version, old_version)
					if not rc > -1:
						ud.debug(ud.LISTENER, ud.WARN, '%s: New version is lower than version of old object (%s), skipping update.' % (name, old_version))
						return
			
			try:
				new_object_data = bz2.decompress(new.get('univentionLDAPACLData')[0])
			except TypeError:
				ud.debug(ud.LISTENER, ud.ERROR, '%s: Error uncompressing data of object %s.' % (name, dn))
				return

			new_basename = new.get('univentionLDAPACLFilename')[0]
			new_filename = os.path.join(self.ucr_slapd_conf_subfile_dir, new_basename)
			listener.setuid(0)
			try:
				backup_filename = None
				backup_ucrinfo_filename = None
				backup_backlink_filename = None
				if old:
					old_filename = os.path.join(self.ucr_slapd_conf_subfile_dir, old.get('univentionLDAPACLFilename')[0])
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

					## plus the old backlink file
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

					## and the old UCR registration
					old_ucrinfo_filename = os.path.join(self.ucr_info_basedir, "%s%s.info" % (self.file_prefix, old.get('univentionLDAPACLFilename')[0]))
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
					os.makedirs(self.ucr_slapd_conf_subfile_dir, 0755)

				## Create new extension file
				try:
					ud.debug(ud.LISTENER, ud.INFO, '%s: Writing new extension file %s.' % (name, new_filename))
					with open(new_filename, 'w') as f:
						f.write(new_object_data)
				except IOError:
					ud.debug(ud.LISTENER, ud.ERROR, '%s: Error writing file %s.' % (name, new_filename))
					return

				## plus backlink file
				try:
					new_backlink_filename = "%s.info" % new_filename
					ud.debug(ud.LISTENER, ud.INFO, '%s: Writing backlink file %s.' % (name, new_backlink_filename))
					with open(new_backlink_filename, 'w') as f:
						f.write("%s\n" % dn)
				except IOError:
					ud.debug(ud.LISTENER, ud.ERROR, '%s: Error writing backlink file %s.' % (name, new_backlink_filename))
					return

				## and UCR registration
				try:
					new_ucrinfo_filename = os.path.join(self.ucr_info_basedir, "%s%s.info" % (self.file_prefix, new.get('univentionLDAPACLFilename')[0]))
					ud.debug(ud.LISTENER, ud.INFO, '%s: Writing UCR info file %s.' % (name, new_ucrinfo_filename))
					with open(new_ucrinfo_filename, 'w') as f:
						f.write("Type: multifile\nMultifile: etc/ldap/slapd.conf\n\nType: subfile\nMultifile: etc/ldap/slapd.conf\nSubfile: etc/ldap/slapd.conf.d/%s\n" % new_basename)
				except IOError:
					ud.debug(ud.LISTENER, ud.ERROR, '%s: Error writing UCR info file %s.' % (name, new_ucrinfo_filename))
					return

				## Commit to slapd.conf
				ucr = ConfigRegistry()
				ucr.load()
				ucr_handlers = configHandlers()
				ucr_handlers.load()
				ucr_handlers.update()
				ucr_handlers.commit(ucr, ['/etc/ldap/slapd.conf'])

				## validate
				p = subprocess.Popen(['/usr/sbin/slaptest', '-u'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
				stdout, stderr = p.communicate()
				if p.returncode != 0:
					ud.debug(ud.LISTENER, ud.ERROR, '%s: slapd.conf validation failed:\n%s.' % (name, stdout))
					## Revert changes
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
					## plus backlink file
					if backup_backlink_filename:
						ud.debug(ud.LISTENER, ud.ERROR, '%s: Restoring previous backlink file %s.' % (name, old_backlink_filename))
						try:
							shutil.move(backup_backlink_filename, old_backlink_filename)
							os.close(backup_backlink_fd)
						except IOError:
							ud.debug(ud.LISTENER, ud.ERROR, '%s: Error reverting to old backlink file %s.' % (name, old_backlink_filename))
					## and the old UCR registration
					if backup_ucrinfo_filename:
						ud.debug(ud.LISTENER, ud.ERROR, '%s: Restoring previous UCR info file %s.' % (name, old_ucrinfo_filename))
						try:
							shutil.move(backup_ucrinfo_filename, old_ucrinfo_filename)
							os.close(backup_ucrinfo_fd)
						except IOError:
							ud.debug(ud.LISTENER, ud.ERROR, '%s: Error reverting to old UCR info file %s.' % (name, old_ucrinfo_filename))
					## Commit and exit
					ucr_handlers.commit(ucr, ['/etc/ldap/slapd.conf'])
					return
				ud.debug(ud.LISTENER, ud.INFO, '%s: validation successful.' % (name,))

				## cleanup backup
				if backup_filename:
					ud.debug(ud.LISTENER, ud.INFO, '%s: Removing backup of old file %s.' % (name, backup_filename))
					os.unlink(backup_filename)
					os.close(backup_fd)
				## plus backlink file
				if backup_backlink_filename:
					ud.debug(ud.LISTENER, ud.INFO, '%s: Removing backup of old backlink file %s.' % (name, backup_backlink_filename))
					os.unlink(backup_backlink_filename)
					os.close(backup_backlink_fd)
				## and the old UCR registration
				if backup_ucrinfo_filename:
					ud.debug(ud.LISTENER, ud.INFO, '%s: Removing backup of old UCR info file %s.' % (name, backup_ucrinfo_filename))
					os.unlink(backup_ucrinfo_filename)
					os.close(backup_ucrinfo_fd)

				self._todo_list.append(dn)
				self._do_reload = True

			finally:
				listener.unsetuid()
		elif old:
			old_filename = os.path.join(self.ucr_slapd_conf_subfile_dir, old.get('univentionLDAPACLFilename')[0])
			## plus backlink file
			old_backlink_filename = "%s.info" % old_filename
			## and the old UCR registration
			old_ucrinfo_filename = os.path.join(self.ucr_info_basedir, "%s%s.info" % (self.file_prefix, old.get('univentionLDAPACLFilename')[0]))
			if os.path.exists(old_filename):
				listener.setuid(0)
				try:
					ud.debug(ud.LISTENER, ud.INFO, '%s: Removing extension %s.' % (name, old['cn'][0]))
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

					self._do_reload = True
					if dn in self._todo_list:
						self._todo_list = [ x for x in self._todo_list if x != dn ]
						if not self._todo_list:
							self._do_reload = False

				finally:
					listener.unsetuid()


class UniventionUDMExtension(UniventionLDAPExtension):
	__metaclass__ = ABCMeta

	def wait_for_activation(self, timeout=180):
		if not UniventionLDAPExtension.wait_for_activation(self, timeout):
				return False

		timeout = 60
		print "Waiting for file %s:" % (self.filename,),
		t0 = time.time()
		while not os.path.exists(self.filename):
			if time.time() - t0 > timeout:
				print "ERROR"
				print >>sys.stderr, "ERROR: Timout waiting for %s." % (self.filename,)
				return False
			sys.stdout.write(".")
			sys.stdout.flush()
			time.sleep(3)
		print "OK"
		return True

class UniventionUDMModule(UniventionUDMExtension):
	target_container_name = "udm_module"
	udm_module_name = "settings/udm_module"
	active_flag_attribute = "univentionUDMModuleActive"
	filesuffix = ".py"

	def register(self, filename, options, udm_passthrough_options, target_filename = None):
		## Determine UDM module name
		saved_value = sys.dont_write_bytecode
		sys.dont_write_bytecode = True
		try:
			module_name=imp.load_source('dummy', filename).module
		except AttributeError:
			print "ERROR: python variable 'module' undefined in given file:", filename
			sys.exit(1)
		sys.dont_write_bytecode = saved_value

		UniventionUDMExtension.register(self, filename, options, udm_passthrough_options, target_filename = module_name + ".py")


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
	if not language in os.listdir('/usr/share/locale'):
		raise OptionValueError("%s: file basename is not a registered language: %s" % (opt, value))
	if not MIME_DESCRIPTION.file(value).startswith('GNU message catalog'):
		raise OptionValueError("%s: file is not a GNU message catalog: %s" % (opt, value))
	
	return value

class UCSOption (Option):
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

def ucs_registerLDAPExtension():
	functionname = inspect.stack()[0][3]
	parser = OptionParser(prog=functionname, option_class=UCSOption)

	parser.add_option("--schema", dest="schemafile",
			action="append", type="existing_filename", default=[],
			help="Register LDAP schema", metavar="<LDAP schema file>")

	parser.add_option("--acl", dest="aclfile",
			action="append", type="existing_filename", default=[],
			help="Register LDAP ACL", metavar="<UCR template for OpenLDAP ACL file>")

	parser.add_option("--udm_module", dest="udm_module",
			action="append", type="existing_filename", default=[],
			help="UDM module", metavar="<filename>")

	parser.add_option("--udm_syntax", dest="udm_syntax",
			action="append", type="existing_filename", default=[],
			help="UDM syntax", metavar="<filename>")

	parser.add_option("--udm_hook", dest="udm_hook",
			action="append", type="existing_filename", default=[],
			help="UDM hook", metavar="<filename>")

	parser.add_option("--packagename", dest="packagename",
			help="Package name")
	parser.add_option("--packageversion", dest="packageversion",
			help="Package version")

	parser.add_option("--ucsversionstart", dest="ucsversionstart",
			action="store", type="ucs_version",
			help="Start activation with UCS version", metavar="<UCS Version>")
	parser.add_option("--ucsversionend", dest="ucsversionend",
			action="store", type="ucs_version",
			help="End activation with UCS version", metavar="<UCS Version>")

	udm_module_options = OptionGroup(parser, "UDM module specific options")
	udm_module_options.add_option("--messagecatalog", dest="messagecatalog",
			type="existing_filename", default=[],
			action="callback", callback=option_callback_append_udm_module_options,
			help="Gettext mo file", metavar="<GNU message catalog file>")
	udm_module_options.add_option("--umcregistration", dest="umcregistration",
			type="existing_filename",
			action="callback", callback=option_callback_set_udm_module_options,
			help="UMC registration xml file", metavar="<XML file>")
	udm_module_options.add_option("--icon", dest="icon",
			type="existing_filename", default=[],
			action="callback", callback=option_callback_append_udm_module_options,
			help="UDM module icon", metavar="<Icon file>")
	parser.add_option_group(udm_module_options)


	# parser.add_option("-v", "--verbose", action="count")
	
	udm_passthrough_options = []
	auth_options = OptionGroup(parser, "Authentication Options",
			"These options are usually passed e.g. from a calling joinscript")
	auth_options.add_option("--binddn", dest="binddn", type="string",
			action="callback", callback=option_callback_udm_passthrough_options, callback_args=(udm_passthrough_options,),
			help="LDAP binddn", metavar="<LDAP DN>")
	auth_options.add_option("--bindpwd", dest="bindpwd", type="string",
			action="callback", callback=option_callback_udm_passthrough_options, callback_args=(udm_passthrough_options,),
			help="LDAP bindpwd", metavar="<LDAP bindpwd>")
	auth_options.add_option("--bindpwdfile", dest="bindpwdfile",
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

	if not (opts.schemafile or opts.aclfile or opts.udm_syntax or opts.udm_hook or opts.udm_module):
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

	for obj in objects:
		if not obj.wait_for_activation():
			print "%s: registraton of %s failed." % (functionname, obj.filename)
			sys.exit(1)

	if opts.udm_module:
		print "Terminating running univention-cli-server processes."
		p = subprocess.Popen(['pkill', '-f', 'univention-cli-server'], close_fds=True)
		p.wait()

def ucs_unregisterLDAPExtension():
	functionname = inspect.stack()[0][3]
	parser = OptionParser(prog=functionname, option_class=UCSOption)

	parser.add_option("--schema", dest="schemaobject",
			action="append", type="string",
			help="LDAP schema", metavar="<schema name>")

	parser.add_option("--acl", dest="aclobject",
			action="append", type="string",
			help="LDAP ACL", metavar="<ACL name>")

	parser.add_option("--udm_module", dest="udm_module",
			action="append", type="string",
			help="UDM module", metavar="<module name>")

	parser.add_option("--udm_syntax", dest="udm_syntax",
			action="append", type="string",
			help="UDM syntax", metavar="<syntax name>")

	parser.add_option("--udm_hook", dest="udm_hook",
			action="append", type="string",
			help="UDM hook", metavar="<hook name>")

	# parser.add_option("-v", "--verbose", action="count")
	
	udm_passthrough_options = []
	auth_options = OptionGroup(parser, "Authentication Options",
			"These options are usually passed e.g. from a calling joinscript")
	auth_options.add_option("--binddn", dest="binddn", type="string",
			action="callback", callback=option_callback_udm_passthrough_options, callback_args=(udm_passthrough_options,),
			help="LDAP binddn", metavar="<LDAP DN>")
	auth_options.add_option("--bindpwd", dest="bindpwd", type="string",
			action="callback", callback=option_callback_udm_passthrough_options, callback_args=(udm_passthrough_options,),
			help="LDAP bindpwd", metavar="<LDAP bindpwd>")
	auth_options.add_option("--bindpwdfile", dest="bindpwdfile",
			action="callback", callback=option_callback_udm_passthrough_options, callback_args=(udm_passthrough_options,),
			type="existing_filename",
			help="File containing LDAP bindpwd", metavar="<filename>")
	parser.add_option_group(auth_options)
	opts, args = parser.parse_args()

	ucr = ConfigRegistry()
	ucr.load()

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

