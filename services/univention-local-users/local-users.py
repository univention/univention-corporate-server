# -*- coding: utf-8 -*-
#
# Univention Local Users
#  listener module: replicates a selected group of LDAP users to
#  /etc/passwd
#
# Copyright 2003-2012 Univention GmbH
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
import os, time, ldap, univention.uldap, sys, string, grp

import univention_baseconfig
import univention.debug
baseConfig=univention_baseconfig.baseConfig()
baseConfig.load()
group_name=baseConfig['local-user-sync/group']
if not group_name:
	group_name='admin'

if baseConfig.has_key('local-user-sync/program') and baseConfig['local-user-sync/program']:
	external_program=baseConfig['local-user-sync/program']

use_passwd_file=1
if baseConfig.has_key('local-user-sync/passwd') and baseConfig['local-user-sync/passwd']:
	if baseConfig['local-user-sync/passwd'] in ["TRUE", "True", "true", "1", "YES", "Yes", "yes"]:
		use_passwd_file=1
	else:
		use_passwd_file=0
FIRST_LDAP_UID=1000
LAST_LDAP_UID=62999

name='local-users'
description='Replicate a selected set of users to the local flat files'
filter='(|(objectClass=posixAccount)(&(objectClass=posixGroup)(cn=%s)))' % group_name

__passwd_file = '/etc/passwd'
__shadow_file = '/etc/shadow'

def run_program(ent):
	os.setuid(0)
	univention.debug.debug(univention.debug.LISTENER, univention.debug.ALL, 'run %s with args %s' % (external_program, string.join(ent,':')))
	if os.path.exists(external_program):
		s="%s" % string.join(ent,':')
		p_out, p_in = os.popen2(external_program)
		p_out.write(s)
		p_out.close()
		p_in.close()
	else:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, 'Script %s does not exists' % external_program)

def passwd_lock_file(file):

	lock_file = file+'.lock'

	wait=20
	fd = -1
	while wait > 0 and fd < 0:
		try:
			fd = os.open(lock_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0600)
		except OSError, e:
			if e.errno != 17:
				raise OSError, e
			time.sleep(1)
			wait -= 1
			continue
	if fd < 0:
		raise 'unable to lock password file'

	os.write(fd, str(os.getpid()))
	os.close(fd)

def passwd_unlock_file(file):

	lock_file = file+'.lock'
	if os.path.exists(lock_file) and open(lock_file).read() == str(os.getpid()):
		os.unlink(lock_file)
	else:
		raise 'unable to unlock password file'

def passwd_getpwnam(nam):
	fp = open(__passwd_file)
	while 1:
		line = fp.readline()
		if not line:
			break
		line = line[0:-1]
		ent = line.split(':')
		if ent[0] == nam:
			return ent
	raise KeyError, 'not found'

def passwd_getpwent():
	fp = open(__passwd_file)
	ret = []
	while 1:
		line = fp.readline()
		if not line:
			continue
		line = line[0:-1]
		ret.append(line.split(':'))
	return ret

def passwd_setpwnam(nam, ent):

	listener.setuid(0)
	try:
		passwd_lock_file(__passwd_file)
		try:
			passwd_lock_file(__shadow_file)
		except Exception, e:
			passwd_unlock_file(__passwd_file)
			raise Exception, e

		try:
			old_passwd_fp = open(__passwd_file)
			old_shadow_fp = open(__shadow_file)
			new_passwd_fd = os.open(__passwd_file+'.edit', os.O_WRONLY | os.O_CREAT | os.O_EXCL, os.stat(__passwd_file)[0] & 07777)
			new_shadow_fd = os.open(__shadow_file+'.edit', os.O_WRONLY | os.O_CREAT | os.O_EXCL, os.stat(__shadow_file)[0] & 07777)
			backup_passwd_fd = os.open(__passwd_file+'-', os.O_WRONLY | os.O_CREAT, os.stat(__passwd_file)[0] & 07777)
			backup_shadow_fd = os.open(__shadow_file+'-', os.O_WRONLY | os.O_CREAT, os.stat(__shadow_file)[0] & 07777)

			# update /etc/passwd
			found = 0
			while 1:
				line = old_passwd_fp.readline()
				if not line:
					break
				os.write(backup_passwd_fd, line)
				name = line[0:line.find(':')]
				if name == nam:
					found = 1
					if ent:
						os.write(new_passwd_fd, '%s:x:%s:%s:%s:%s:%s\n' % (ent[0], ent[2], ent[3], ent[4], ent[5], ent[6]))
				else:
					os.write(new_passwd_fd, line)
			if not found and ent:
				os.write(new_passwd_fd, '%s:x:%s:%s:%s:%s:%s\n' % (ent[0], ent[2], ent[3], ent[4], ent[5], ent[6]))

			# update /etc/shadow
			found = 0
			while 1:
				line = old_shadow_fp.readline()
				if not line:
					break
				os.write(backup_shadow_fd, line)
				name = line[0:line.find(':')]
				if name == nam:
					found = 1
					if ent:
						os.write(new_shadow_fd, '%s:%s:12923:0:99999:7:::\n' % (ent[0], ent[1]))
				else:
					os.write(new_shadow_fd, line)
			if not found and ent:
				os.write(new_shadow_fd, '%s:%s:12923:0:99999:7:::\n' % (ent[0], ent[1]))

			os.close(new_passwd_fd)
			os.close(new_shadow_fd)
			os.rename(__passwd_file+'.edit', __passwd_file)
			os.rename(__shadow_file+'.edit', __shadow_file)
			os.close(backup_passwd_fd)
			os.close(backup_shadow_fd)

		finally:
			passwd_unlock_file(__passwd_file)
			passwd_unlock_file(__shadow_file)

	finally:
		listener.unsetuid()

def ldapent(attr):
	ent=[]
	ent.append(attr['uid'][0])
	xpw='x'
	if attr.has_key('userPassword'):
		for pw in attr['userPassword']:
			if pw.lower().startswith('{crypt}'):
				xpw = pw[7:]
				break
	ent.append(xpw)
	ent.append(attr['uidNumber'][0])
	ent.append(attr['gidNumber'][0])
	if attr.has_key('gecos'):
		ent.append(attr['gecos'][0])
	elif attr.has_key('cn'):
		ent.append(attr['cn'][0])
	else:
		ent.append('')
	ent.append(attr['homeDirectory'][0])
	ent.append(attr['loginShell'][0])
	if attr.has_key('sambaNTPassword'):
		ent.append(attr['sambaNTPassword'][0])
	else:
		ent.append("")
	if attr.has_key('sambaLMPassword'):
		ent.append(attr['sambaLMPassword'][0])
	else:
		ent.append("")
	return ent

def handler(dn, new, old):
	listener.setuid(0)
	bindpw=open('/etc/machine.secret').read()
	if bindpw[-1] == '\n':
		bindpw=bindpw[0:-1]

	try:
		lo = univention.uldap.access(host=listener.baseConfig['ldap/server/name'], base=listener.baseConfig['ldap/base'], binddn=baseConfig['ldap/hostdn'], bindpw=bindpw)
	except ldap.LDAPError, msg:
		lo = univention.uldap.access(host=listener.baseConfig['ldap/master'], base=listener.baseConfig['ldap/base'], binddn=baseConfig['ldap/hostdn'], bindpw=bindpw)


	# group
	if 'posixGroup' in new.get('objectClass', []) or 'posixGroup' in old.get('objectClass', []):

		new_members=new.get('uniqueMember', [])
		old_members=old.get('uniqueMember', [])
		add_members=[]
		remove_members=[]
		for m in new_members:
			if not m in old_members:
				add_members.append(m)
		for m in old_members:
			if not m in new_members:
				remove_members.append(m)

		for m in add_members:
			try:
				ent = ldapent(lo.get(m, required=1))
				if use_passwd_file:
					passwd_setpwnam(ent[0], ent)
				if external_program:
					run_program(ent)
			except ldap.NO_SUCH_OBJECT:
				univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, 'DN %s does not exist' % m)
		for m in remove_members:
			try:
				ent = ldapent(lo.get(m, required=1))
				if use_passwd_file:
					passwd_setpwnam(ent[0], None)
				if external_program:
					run_program([ent[0]])
			except ldap.NO_SUCH_OBJECT:
				univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, 'DN %s does not exist' % m)

	# account
	elif 'posixAccount' in new.get('objectClass', []) or 'posixAccount' in old.get('objectClass', []):

		ent=[]
		if new:
			name = new['uid'][0]
		else:
			name = old['uid'][0]

		# check if account exists locally; if not, we don't need to update it
		if use_passwd_file:
			found = 1
			try:
				passwd_getpwnam(name)
			except KeyError:
				found = 0
			if not found:
				return

			if new:
				ent = ldapent(new)
				passwd_setpwnam(ent[0], ent)
			else:
				passwd_setpwnam(name, None)
		if external_program:
			if not ent:
				ent = ldapent(new)
			if ent[0] in grp.getgrnam(group_name)[3]:
				run_program(ent)
