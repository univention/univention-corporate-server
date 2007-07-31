# -*- coding: utf-8 -*-
#
# Univention Samba
#  listener module: manages samba share configuration
#
# Copyright (C) 2001, 2002, 2003, 2004, 2005, 2006, 2007 Univention GmbH
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
import os, string
import univention.debug

if listener.baseConfig.has_key('samba/ha/master') and listener.baseConfig['samba/ha/master']:
	hostname=listener.baseConfig['samba/ha/master']
else:
	hostname=listener.baseConfig['hostname']
domainname=listener.baseConfig['domainname']
ip=listener.baseConfig['interfaces/eth0/address']

name='samba-shares'
description='Create configuration for Samba shares'
filter='(&(objectClass=univentionShare)(objectClass=univentionShareSamba)(|(univentionShareHost=%s.%s)(univentionShareHost=%s)))' % (hostname, domainname, ip)
atributes=[]

def handler(dn, new, old):

	if old:
		filename = '/etc/samba/shares.conf.d/%s' % old['univentionShareSambaName'][0]
		listener.setuid(0)
		try:
			if os.path.exists(filename):
				os.unlink(filename)
		finally:
			listener.unsetuid()

	if new:

		filename = '/etc/samba/shares.conf.d/%s' % new['univentionShareSambaName'][0]
		listener.setuid(0)
		try:
			fp = open(filename, 'w')

			print >>fp, '[%s]' % new['univentionShareSambaName'][0]
			if new['univentionShareSambaName'][0] != 'homes':
				print >>fp, 'path = %s' % new['univentionSharePath'][0]
			mapping=[
				('description', 'comment'),
				('univentionShareSambaMSDFS', 'msdfs root'),
				('univentionShareSambaWriteable', 'writeable'),
				('univentionShareSambaBrowseable', 'browseable'),
				('univentionShareSambaPublic', 'public'),
				('univentionShareSambaCreateMode', 'create mode'),
				('univentionShareSambaDirectoryMode', 'directory mode'),
				('univentionShareSambaForceCreateMode', 'force create mode'),
				('univentionShareSambaForceDirectoryMode', 'force directory mode'),
				('univentionShareSambaSecurityMode', 'security mask'),
				('univentionShareSambaDirectorySecurityMode', 'directory security mask'),
				('univentionShareSambaForceSecurityMode', 'force security mode'),
				('univentionShareSambaForceDirectorySecurityMode', 'force directory security mode'),
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
			for attr, var in mapping:
				if not new.has_key(attr):
					continue
				if attr == 'univentionShareSambaDirectoryMode' and new['univentionSharePath'] == '/tmp':
					continue
				if attr in ( 'univentionShareSambaHostsAllow', 'univentionShareSambaHostsDeny' ) :
					print >>fp, '%s = %s' % ( var, ', '.join( new[ attr ] ) )
				else:
					print >>fp, '%s = %s' % (var, new[attr][0])
			# try to create directory to share
			if new['univentionShareSambaName'][0] != 'homes':
				directory = os.path.join('/', new['univentionSharePath'][0])
				if not os.access(directory,os.F_OK):
					os.makedirs(directory,int('0755',0))
				uid = 0
				gid = 0
				mode = '0755'

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

				if new['univentionSharePath'][0] == '/tmp':
					univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN,
								"Custom permissions for share `%s' not allowed, overriding." % new['univentionSharePath'][0])
				else:
					try:
						os.chmod(directory,int(mode,0))
						os.chown(directory,uid,gid)
					except:
						pass
		finally:
			listener.unsetuid()

def initialize():
	if not os.path.exists('/etc/samba/shares.conf.d'):
		listener.setuid(0)
		try:
			os.mkdir('/etc/samba/shares.conf.d')
		finally:
			listener.unsetuid()

def clean():
	listener.setuid(0)
	try:
		if os.path.exists('/etc/samba/shares.conf.d'):
			for f in os.listdir('/etc/samba/shares.conf.d'):
				os.unlink(os.path.join('/etc/samba/shares.conf.d', f))
			if os.path.exists('/etc/samba/shares.conf'):
				os.unlink('/etc/samba/shares.conf')
			os.rmdir('/etc/samba/shares.conf.d')
	finally:
		listener.unsetuid()

def postrun():
	listener.setuid(0)
	try:
		fp = open('/etc/samba/shares.conf', 'w')
		print >>fp, '# Warning: This file is auto-generated and will be overwritten by \n#          univention-directory-listener module. \n#          Please edit the following file instead: \n#          /etc/samba/local.conf \n  \n# Warnung: Diese Datei wurde automatisch generiert und wird durch ein \n#          univention-directory-listener Modul überschrieben werden. \n#          Ergänzungen können an folgende Datei vorgenommen werden: \n# \n#          /etc/samba/local.conf \n#'

		for f in os.listdir('/etc/samba/shares.conf.d'):
			print >>fp, 'include = %s' % os.path.join('/etc/samba/shares.conf.d', f)
		fp.close()
		if listener.baseConfig.has_key('samba/ha/master') and listener.baseConfig['samba/ha/master']:
			initscript='/etc/heartbeat/resource.d/samba'
		else:
			initscript='/etc/init.d/samba'
		os.spawnv(os.P_WAIT, initscript, ['samba', 'reload'])
	finally:
		listener.unsetuid()
