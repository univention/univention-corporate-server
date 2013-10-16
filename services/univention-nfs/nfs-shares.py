# -*- coding: utf-8 -*-
#
# Univention NFS
#  listener module: update configuration of local NFS shares
#
# Copyright 2004-2013 Univention GmbH
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

__package__='' 	# workaround for PEP 366
import listener
import os
import re
import univention.debug
import univention.lib.listenerSharePath
import cPickle
from univention.config_registry.interfaces import Interfaces

hostname=listener.baseConfig['hostname']
domainname=listener.baseConfig['domainname']
interfaces = Interfaces(listener.configRegistry)
ip = interfaces.get_default_ip_address().ip

name='nfs-shares'
description='Create configuration for NFS shares'
filter='(&(objectClass=univentionShare)(|(univentionShareHost=%s.%s)(univentionShareHost=%s)))' % (hostname, domainname, ip)
modrdn='1'

__exports = '/etc/exports'
__comment_pattern = re.compile('^"*/.*#[ \t]*LDAP:[ \t]*(.*)')

tmpFile = os.path.join("/var", "cache", "univention-directory-listener", name + ".oldObject")

def handler(dn, new, old, command):

	# create tmp dir
	tmpDir = os.path.dirname(tmpFile)
	listener.setuid(0)
	try:
		if not os.path.exists(tmpDir):
			os.makedirs(tmpDir)
	except Exception, e:
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
	oldDn = ""
	listener.setuid(0)
	try:
		# object was renamed -> save old object
		if command == "r" and old:
			f = open(tmpFile, "w+")
			os.chmod(tmpFile, 0600)
			cPickle.dump({"dn":dn, "old":old}, f)
			f.close()
		elif command == "a" and not old:
			if os.path.isfile(tmpFile):
				f = open(tmpFile, "r")
				p = cPickle.load(f)
				f.close()
				oldObject = p.get("old", {})
				oldDn = p.get("dn", {})
				os.remove(tmpFile)
	except Exception, e:
		if os.path.isfile(tmpFile):
			os.remove(tmpFile)
		univention.debug.debug(
			univention.debug.LISTENER, univention.debug.ERROR,
			"%s: could not read/write tmp file %s (%s)" % (name, tmpFile, str(e)))
	finally:
		listener.unsetuid()

	global __exports, __comment_pattern
	# update exports file
	fp = open(__exports)
	new_lines = []
	for line in fp.readlines():
		line=line[0:-1]
		s = __comment_pattern.findall(line)
		if not s or s[0] != dn:
			new_lines.append(line)
	fp.close()
	if new and new.has_key('objectClass') and 'univentionShareNFS' in new['objectClass']:
		path = new['univentionSharePath'][0]
		options = ''
		if new.get('univentionShareNFSSync', [''])[0] == 'async':
			sync_mode='async'
		else:
			sync_mode='sync'

		if new.get('univentionShareWriteable', [''])[0] == 'yes':
			read_write='rw'
		else:
			read_write='ro'

		if new.get('univentionShareNFSRootSquash', [''])[0] == 'yes':
			root_squash='root_squash'
		else:
			root_squash='no_root_squash'

		if new.get('univentionShareNFSSubTree', [''])[0] == 'yes':
			subtree='subtree_check'
		else:
			subtree='no_subtree_check'

		custom_settings = ""
		if new.has_key('univentionShareNFSCustomSetting'):
			for custom_setting in new['univentionShareNFSCustomSetting']:
				custom_settings += ",%s" % custom_setting

		if new.has_key( 'univentionShareNFSAllowed' ):
			permitted = new['univentionShareNFSAllowed']
		else:
			permitted=['*']

		for p in permitted:
			options += ' %s(%s,%s,%s,%s%s)' % (p, read_write, root_squash, sync_mode, subtree, custom_settings)

		new_lines.append('"%s" %s # LDAP:%s' % (path, options, dn))

		listener.setuid(0)
		try:
			fp = open(__exports, 'w')
			fp.write('\n'.join(new_lines)+'\n')
			fp.close()

			# object was renamed
			if not old and oldObject and command == "a":
				old = oldObject
			ret = univention.lib.listenerSharePath.createOrRename(old, new, listener.configRegistry)
			if ret:
				univention.debug.debug(
					univention.debug.LISTENER, univention.debug.ERROR,
					"%s: rename/create of sharePath for %s failed (%s)" % (name, dn, ret))

		finally:
			listener.unsetuid()
	else:
		listener.setuid(0)
		try:
			fp = open(__exports, 'w')
			fp.write('\n'.join(new_lines)+'\n')
			fp.close()

		finally:
			listener.unsetuid()

def clean():
	global __exports, __comment_pattern
	# clear exports file
	fp = open(__exports)
	new_lines = []
	for line in fp.readlines():
		line=line[0:-1]
		s = __comment_pattern.findall(line)
		if not s:
			new_lines.append(line)
	fp.close()

	listener.setuid(0)
	try:
		fp = open(__exports, 'w')
		fp.write('\n'.join(new_lines)+'\n')
		fp.close()
	finally:
		listener.unsetuid()


def postrun():
	if listener.baseConfig.has_key('nfsserver/ha/master') and listener.baseConfig['nfsserver/ha/master']:
		initscript='/etc/heartbeat/resource.d/nfs-kernel-server'
	else:
		initscript='/etc/init.d/nfs-kernel-server'
	listener.run(initscript, ['nfs-kernel-server', 'start'], uid=0)
	listener.run(initscript, ['nfs-kernel-server', 'reload'], uid=0)
