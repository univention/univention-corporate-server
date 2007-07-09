# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  passwd part for the command line interface
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

import os, sys, getopt, codecs, string, re
import univention.debug
import univention.misc

import univention_baseconfig
import univention.admin.uldap
import univention.admin.config
import univention.admin.modules
import univention.admin.objects
import univention.admin.handlers.users.user

def doit(arglist):
	univention.debug.init('/var/log/univention/admin-cmd.log', 1, 1)
	out=[]
	opts, args=getopt.getopt(arglist[1:], '', ['binddn=', 'pwdfile=', 'user=', 'pwd='])
	
	binddn=None
	pwdfile=None
	user=None
	pwd=None
	
	for opt, val in opts:
		if opt == '--binddn':
			binddn=val
		elif opt == '--pwdfile':
			pwdfile=val
		elif opt == '--user':
			user=val
		elif opt == '--pwd':
			pwd=val
	
	univention.debug.set_level(univention.debug.LDAP, univention.debug.ALL)
	univention.debug.set_level(univention.debug.ADMIN, univention.debug.ALL)

	co=univention.admin.config.config()
	baseConfig=univention_baseconfig.baseConfig()
	baseConfig.load()

	baseDN=baseConfig['ldap/base']

	bindpw=open(pwdfile).read()
	if bindpw[-1] == '\n' or bindpw[-1] == '\r':
		bindpw=bindpw[0:-1]

	univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'binddn: %s; bindpwd: *************' % (binddn))
	try:
		lo=univention.admin.uldap.access(host=baseConfig['ldap/master'], base=baseDN, binddn=binddn, bindpw=bindpw, start_tls=2)
	except Exception, e:
		univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'authentication error: %s' % str(e))
		out.append('authentication error: %s' % e)
		return out	
		pass

	try:
		dn=lo.searchDn(filter=unicode('(&(uid=%s)(|(objectClass=posixAccount)(objectClass=sambaSamAccount)(objectClass=person)))' % user, 'utf8'), base=baseDN, unique=1)
		position=univention.admin.uldap.position(baseDN)

		module=univention.admin.modules.get('users/user')
		univention.admin.modules.init(lo,position,module)

		object=univention.admin.objects.get(module, co, lo, position=position, dn=dn[0])
		object.open()

		if 'samba' in object.options:
			object.options.remove('samba')

		if not baseConfig.has_key('samba/charset/unix'):
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'univention-passwd: no unix-charset given')
			object['password']=unicode(pwd, 'utf8')
		elif baseConfig['samba/charset/unix'] in ['utf8', 'latin']:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'univention-passwd: known charset given: %s'%baseConfig['samba/charset/unix'])
			object['password']=unicode(pwd, baseConfig['samba/charset/unix'])
		else:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'univention-passwd: unknown charset given, try fallback')
			object['password']=unicode(pwd)

		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'univention-passwd: passwd set, modify object')
		object['disabled']='0'
		dn=object.modify()

		out.append('password changed')
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'univention-passwd: password changed')

	except univention.admin.uexceptions.pwalreadyused:
		out.append('passwd error: password alreay used')
		return out

	except Exception, e:
		univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'passwd error: %s' % e)
		out.append('passwd error: %s' % e)
		return out

	try:
		# check for local ldap server connection
		if baseConfig.has_key('ldap/replication/preferredpassword') and baseConfig['ldap/replication/preferredpassword'].lower() in ['true' , 'yes']:
			if baseConfig.has_key('ldap/server/type') and baseConfig['ldap/server/type'] == 'slave':
				if os.path.exists('/etc/ldap/rootpw.conf'):
					bindpw=open('/etc/ldap/rootpw.conf').read()
					bindpw=bindpw.split(' ')[1].strip('\n\r"')
					lo=univention.admin.uldap.access(host='%s.%s' % (baseConfig['hostname'],baseConfig['domainname']), base=baseDN, binddn='cn=update,%s' % (baseDN), bindpw=bindpw, start_tls=2)
					dn=lo.searchDn(filter=unicode('(&(uid=%s)(|(objectClass=posixAccount)(objectClass=sambaSamAccount)(objectClass=person)))' % user, 'utf8'), base=baseDN, unique=1)
					position=univention.admin.uldap.position(baseDN)
					module=univention.admin.modules.get('users/user')
					univention.admin.modules.init(lo,position,module)

					object=univention.admin.objects.get(module, co, lo, position=position, dn=dn[0])
					object.open()

					if not baseConfig.has_key('samba/charset/unix'):
						univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'univention-passwd: no unix-charset given')
						object['password']=unicode(pwd, 'utf8')
					elif baseConfig['samba/charset/unix'] in ['utf8', 'latin']:
						univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'univention-passwd: known charset given: %s'%baseConfig['samba/charset/unix'])
						object['password']=unicode(pwd, baseConfig['samba/charset/unix'])
					else:
						univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'univention-passwd: unknown charset given, try fallback')
						object['password']=unicode(pwd)

					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'univention-passwd: passwd set, modify object')
					object['disabled']='0'
					object['overridePWHistory']='1'
					object['overridePWLength']='1'
					dn=object.modify()

					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'univention-passwd: password changed')
	except Exception, e:
		univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'passwd error: %s' % e)

	return out


