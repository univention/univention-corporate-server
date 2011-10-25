# -*- coding: utf-8 -*-
#
# Univention NFS
#  listener module: update configuration of local NFS shares
#
# Copyright 2004-2011 Univention GmbH
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
import os, re, string
import univention.debug

if listener.baseConfig.has_key('nfsserver/ha/master') and listener.baseConfig['nfsserver/ha/master']:
	hostname=listener.baseConfig['nfsserver/ha/master']
else:
	hostname=listener.baseConfig['hostname']
domainname=listener.baseConfig['domainname']
ip=listener.baseConfig['interfaces/eth0/address']

name='nfs-shares'
description='Create configuration for NFS shares'
filter='(&(objectClass=univentionShare)(|(univentionShareHost=%s.%s)(univentionShareHost=%s)))' % (hostname, domainname, ip)

__exports = '/etc/exports'
__comment_pattern = re.compile('^"*/.*#[ \t]*LDAP:[ \t]*(.*)')


def handler(dn, new, old):

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
	uid = 0
	gid = 0
	mode = '0755'
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

		if new.has_key( 'univentionShareNFSAllowed' ):
			permitted = new['univentionShareNFSAllowed']
		else:
			permitted=['*']

		for p in permitted:
			options += ' %s(%s,%s,%s,%s)' % (p, read_write, root_squash, sync_mode, subtree)

		new_lines.append('"%s" %s # LDAP:%s' % (path, options, dn))

		try:
			if new.has_key('univentionShareUid'):
				uid=int(new['univentionShareUid'][0])
		except:
			pass
		try:
			if new.has_key('univentionShareGid'):
				gid=int(new['univentionShareGid'][0])
		except:
			pass
		try:
			if new.has_key('univentionShareDirectoryMode'):
				mode=new['univentionShareDirectoryMode'][0]
		except:
			pass

		listener.setuid(0)
		try:
			fp = open(__exports, 'w')
			fp.write(string.join(new_lines, '\n')+'\n')
			fp.close()

			if not os.access(path,os.F_OK):
				os.makedirs(path,int('0755',0))

			# deny chmod for dirs in dirBlackList and files
			dirBlackList = ["sys", "proc", "dev", "tmp", "root"]
			path = new['univentionSharePath'][0]
			dirOnBlackList = False
			if os.path.islink(path):
				path = os.path.realpath(path)
			for dir in dirBlackList:
				if re.match("^/%s$|^/%s/" % (dir, dir), path):
					dirOnBlackList = True

			if os.path.isdir(path) and not dirOnBlackList:
				try:
					os.chmod(directory,int(mode,0))
					os.chown(directory,uid,gid)
				except:
					pass
			else:
				univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN,
					"'%s': Custom permissions for files not allowed, skip." % path)

		finally:
			listener.unsetuid()
	else:
		listener.setuid(0)
		try:
			fp = open(__exports, 'w')
			fp.write(string.join(new_lines, '\n')+'\n')
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
		fp.write(string.join(new_lines, '\n')+'\n')
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
