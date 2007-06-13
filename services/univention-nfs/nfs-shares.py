# -*- coding: utf-8 -*-
#
# Univention NFS
#  listener module: update configuration of local NFS shares
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

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
			if path == '/tmp':
				univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN,
						       "Custom permissions for share `%s' not allowed, overriding." % path)
			else:
				try:
					os.chmod(path,int(mode,0))
					os.chown(path,uid,gid)
				except:
					pass

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
