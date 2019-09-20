# -*- coding: utf-8 -*-
#
# Univention Samba
#  listener module: manages samba share configuration
#
# Copyright 2001-2019 Univention GmbH
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
import listener
import os
import univention.debug
import univention.lib.listenerSharePath
import cPickle
import urllib
# for the ucr commit below in postrun we need ucr configHandlers
from univention.config_registry import configHandlers, ConfigRegistry
from univention.config_registry.interfaces import Interfaces
ucr_handlers = configHandlers()
ucr_handlers.load()

domainname = listener.baseConfig['domainname']

name = 'samba-shares'
description = 'Create configuration for Samba shares'
filter = '(&(objectClass=univentionShare)(objectClass=univentionShareSamba))'  # filter fqdn/ip in handler
attributes = []
modrdn = '1'

tmpFile = '/var/cache/univention-directory-listener/samba-shares.oldObject'


def _validate_smb_share_name(name):
	if not name or len(name) > 80:
		return False
	illegal_chars = set('\\/[]:|<>+=;,*?"' + ''.join(map(chr, range(0x1F + 1))))
	if set(str(name)) & illegal_chars:
		return False
	return True


def handler(dn, new, old, command):
	configRegistry = ConfigRegistry()
	configRegistry.load()
	interfaces = Interfaces(configRegistry)

	# dymanic module object filter
	current_fqdn = "%s.%s" % (configRegistry['hostname'], domainname)
	current_ip = str(interfaces.get_default_ip_address().ip)

	new_univentionShareHost = new.get('univentionShareHost', [None])[0]
	if new and new_univentionShareHost not in (current_fqdn, current_ip):
		new = {}  # new object is not for this host

	old_univentionShareHost = old.get('univentionShareHost', [None])[0]
	if old and old_univentionShareHost not in (current_fqdn, current_ip):
		old = {}  # old object is not for this host

	if not (new or old):
		return

	# create tmp dir
	tmpDir = os.path.dirname(tmpFile)
	listener.setuid(0)
	try:
		if not os.path.exists(tmpDir):
			os.makedirs(tmpDir)
	except Exception as e:
		univention.debug.debug(
			univention.debug.LISTENER, univention.debug.ERROR,
			"%s: could not create tmp dir %s (%s)" % (name, tmpDir, str(e)))
		return
	finally:
		listener.unsetuid()

	# modrdn stuff
	# 'r'+'a' -> renamed
	# command='r' and "not new and old"
	# command='a' and "new and not old"

	# write old object to pickle file
	oldObject = {}
	listener.setuid(0)
	try:
		# object was renamed -> save old object
		if command == "r" and old:
			f = open(tmpFile, "w+")
			os.chmod(tmpFile, 0o600)
			cPickle.dump({"dn": dn, "old": old}, f)
			f.close()
		elif command == "a" and not old and os.path.isfile(tmpFile):
			f = open(tmpFile, "r")
			p = cPickle.load(f)
			f.close()
			oldObject = p.get("old", {})
			os.remove(tmpFile)
	except Exception as e:
		if os.path.isfile(tmpFile):
			os.remove(tmpFile)
		univention.debug.debug(
			univention.debug.LISTENER, univention.debug.ERROR,
			"%s: could not read/write tmp file %s (%s)" % (name, tmpFile, str(e)))
	finally:
		listener.unsetuid()

	if old:
		share_name = old.get('univentionShareSambaName', [''])[0]
		share_name_mapped = urllib.quote(share_name, safe='')
		filename = '/etc/samba/shares.conf.d/%s' % (share_name_mapped,)
		listener.setuid(0)
		try:
			if os.path.exists(filename):
				os.unlink(filename)
		finally:
			listener.unsetuid()

	def _quote(arg):
		if ' ' in arg or '"' in arg or '\\' in arg:
			arg = '"%s"' % (arg.replace('\\', '\\\\').replace('"', '\\"'),)
		return arg.replace('\n', '')

	def _simple_quote(arg):
		return arg.replace('\n', '')

	def _map_quote(args):
		return (_quote(arg) for arg in args)

	if new:
		share_name = new.get('univentionShareSambaName', [''])[0]
		if not _validate_smb_share_name(share_name):
			univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, "invalid samba share name: %r" % (share_name,))
			return
		share_name_mapped = urllib.quote(share_name, safe='')
		filename = '/etc/samba/shares.conf.d/%s' % (share_name_mapped,)

		# important!: createOrRename() checks if the share path is allowed. this must be done prior to writing any files.
		# try to create directory to share
		if share_name != 'homes':
			# object was renamed
			if not old and oldObject and command == "a":
				old = oldObject
			listener.setuid(0)
			try:
				ret = univention.lib.listenerSharePath.createOrRename(old, new, listener.configRegistry)
			finally:
				listener.unsetuid()
			if ret:
				univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, "%s: rename/create of sharePath for %s failed (%s)" % (name, dn, ret))
				return

		listener.setuid(0)
		try:
			fp = open(filename, 'w')

			print('[%s]' % (share_name,), file=fp)
			if share_name != 'homes':
				print('path = %s' % _quote(new['univentionSharePath'][0]), file=fp)
			mapping = [
				('description', 'comment'),
				('univentionShareSambaMSDFS', 'msdfs root'),
				('univentionShareSambaWriteable', 'writeable'),
				('univentionShareSambaBrowseable', 'browseable'),
				('univentionShareSambaPublic', 'public'),
				('univentionShareSambaDosFilemode', 'dos filemode'),
				('univentionShareSambaHideUnreadable', 'hide unreadable'),
				('univentionShareSambaCreateMode', 'create mode'),
				('univentionShareSambaDirectoryMode', 'directory mode'),
				('univentionShareSambaForceCreateMode', 'force create mode'),
				('univentionShareSambaForceDirectoryMode', 'force directory mode'),
				('univentionShareSambaLocking', 'locking'),
				('univentionShareSambaBlockingLocks', 'blocking locks'),
				('univentionShareSambaStrictLocking', 'strict locking'),
				('univentionShareSambaOplocks', 'oplocks'),
				('univentionShareSambaLevel2Oplocks', 'level2 oplocks'),
				('univentionShareSambaFakeOplocks', 'fake oplocks'),
				('univentionShareSambaBlockSize', 'block size'),
				('univentionShareSambaCscPolicy', 'csc policy'),
				('univentionShareSambaValidUsers', 'valid users'),
				('univentionShareSambaInvalidUsers', 'invalid users'),
				('univentionShareSambaForceUser', 'force user'),
				('univentionShareSambaForceGroup', 'force group'),
				('univentionShareSambaHideFiles', 'hide files'),
				('univentionShareSambaNtAclSupport', 'nt acl support'),
				('univentionShareSambaInheritAcls', 'inherit acls'),
				('univentionShareSambaPostexec', 'postexec'),
				('univentionShareSambaPreexec', 'preexec'),
				('univentionShareSambaWriteList', 'write list'),
				('univentionShareSambaVFSObjects', 'vfs objects'),
				('univentionShareSambaInheritOwner', 'inherit owner'),
				('univentionShareSambaInheritPermissions', 'inherit permissions'),
				('univentionShareSambaHostsAllow', 'hosts allow'),
				('univentionShareSambaHostsDeny', 'hosts deny'),
			]

			vfs_objects = []
			samba4_ntacl_backend = listener.configRegistry.get('samba4/ntacl/backend', 'native')
			if samba4_ntacl_backend == 'native':
				vfs_objects.append('acl_xattr')
				if listener.configRegistry.is_true('samba/vfs/acl_xattr/ignore_system_acls', False):
					print('acl_xattr:ignore system acls = yes')
			elif samba4_ntacl_backend == 'tdb':
				vfs_objects.append('acl_tdb')

			additional_vfs_objects = new.get('univentionShareSambaVFSObjects', [])
			if additional_vfs_objects:
				vfs_objects.extend(additional_vfs_objects)

			if vfs_objects:
				print('vfs objects = %s' % (' '.join(_map_quote(vfs_objects)), ), file=fp)

			for attr, var in mapping:
				if not new.get(attr):
					continue
				if attr == 'univentionShareSambaVFSObjects':
					continue
				if attr == 'univentionShareSambaDirectoryMode' and new['univentionSharePath'] in ('/tmp', '/tmp/'):
					continue
				if attr in ('univentionShareSambaHostsAllow', 'univentionShareSambaHostsDeny'):
					print('%s = %s' % (var, (', '.join(_map_quote(new[attr])))), file=fp)
				elif attr in ('univentionShareSambaValidUsers', 'univentionShareSambaInvalidUsers'):
					print('%s = %s' % (var, _simple_quote(new[attr][0])), file=fp)
				else:
					print('%s = %s' % (var, _quote(new[attr][0])), file=fp)

			for setting in new.get('univentionShareSambaCustomSetting', []):  # FIXME: vulnerable to injection of further paths and entries
				print(setting.replace('\n', ''), file=fp)

			# implicit settings

			# acl and inherit -> map acl inherit (Bug #47850)
			if '1' in new.get('univentionShareSambaNtAclSupport', []) and '1' in new.get('univentionShareSambaInheritAcls', []):
				print('map acl inherit = yes', file=fp)
		finally:
			listener.unsetuid()

	if (not (new and old)) or (new['univentionShareSambaName'][0] != old['univentionShareSambaName'][0]):
		global ucr_handlers
		listener.setuid(0)
		try:
			run_ucs_commit = False
			if not os.path.exists('/etc/samba/shares.conf'):
				run_ucs_commit = True
			fp = open('/etc/samba/shares.conf.temp', 'w')
			print('# Warning: This file is auto-generated and will be overwritten by \n#          univention-directory-listener module. \n#          Please edit the following file instead: \n#          /etc/samba/local.conf \n  \n# Warnung: Diese Datei wurde automatisch generiert und wird durch ein \n#          univention-directory-listener Module überschrieben werden. \n#          Ergänzungen können an folgender Datei vorgenommen werden: \n# \n#          /etc/samba/local.conf \n#', file=fp)

			for f in os.listdir('/etc/samba/shares.conf.d'):
				print('include = %s' % _quote(os.path.join('/etc/samba/shares.conf.d', f)), file=fp)
			fp.close()
			os.rename('/etc/samba/shares.conf.temp', '/etc/samba/shares.conf')
			if run_ucs_commit:
				ucr_handlers.commit(listener.configRegistry, ['/etc/samba/smb.conf'])
		finally:
			listener.unsetuid()


def initialize():
	if not os.path.exists('/etc/samba/shares.conf.d'):
		listener.setuid(0)
		try:
			os.mkdir('/etc/samba/shares.conf.d')
		finally:
			listener.unsetuid()


def prerun():
	if not os.path.exists('/etc/samba/shares.conf.d'):
		listener.setuid(0)
		try:
			os.mkdir('/etc/samba/shares.conf.d')
		finally:
			listener.unsetuid()


def clean():
	global ucr_handlers
	listener.setuid(0)
	try:
		if os.path.exists('/etc/samba/shares.conf.d'):
			for f in os.listdir('/etc/samba/shares.conf.d'):
				os.unlink(os.path.join('/etc/samba/shares.conf.d', f))
			if os.path.exists('/etc/samba/shares.conf'):
				os.unlink('/etc/samba/shares.conf')
				ucr_handlers.commit(listener.configRegistry, ['/etc/samba/smb.conf'])
			os.rmdir('/etc/samba/shares.conf.d')
	finally:
		listener.unsetuid()


def postrun():
	listener.setuid(0)
	try:
		initscript = '/etc/init.d/samba'
		os.spawnv(os.P_WAIT, initscript, ['samba', 'reload'])
	finally:
		listener.unsetuid()
