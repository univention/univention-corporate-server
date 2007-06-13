#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention LDAP
#  set the new attribute sambaWriteable to the same value as writeable
#  to get the same system-behavior
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

import os, sys, getopt, types, re, codecs

import univention.admin.uldap
import univention.admin.modules
import univention.admin.objects
import univention_baseconfig

co=univention.admin.config.config()
baseConfig=univention_baseconfig.baseConfig()
baseConfig.load()

baseDN=baseConfig['ldap/base']
position=univention.admin.uldap.position(baseDN)

secretFile=open('/etc/ldap.secret','r')
pwdLine=secretFile.readline()
pwd=re.sub('\n','',pwdLine)
tls=2

try:
	lo=univention.admin.uldap.access(host=baseConfig['ldap/master'], base=baseDN, binddn='cn=admin,'+baseDN, bindpw=pwd, start_tls=tls)
except Exception, e:
	univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'authentication error: %s' % str(e))
	print 'authentication error: %s' % str(e)
	sys.exit(1)


module=univention.admin.modules.get('shares/share')
univention.admin.modules.init(lo,position,module)

for object in univention.admin.modules.lookup(module, None, lo, scope='sub'):
	object.open()
	print 'work on DN:', codecs.latin_1_encode(univention.admin.objects.dn(object))[0]

	if object['writeable'] and object['sambaWriteable']:
		object['sambaWriteable']=object['writeable']
		dn=object.modify()
		lo.modify(dn,[])

	else:
		print "WARNING: Object is missing attributes writeable and/or sambaWriteable ! Did you already update univention-ldap ?"
