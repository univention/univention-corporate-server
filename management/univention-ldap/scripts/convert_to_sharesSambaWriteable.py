#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention LDAP
#  set the new attribute sambaWriteable to the same value as writeable
#  to get the same system-behavior
#
# Copyright 2004-2019 Univention GmbH
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

import sys
import re
import codecs

import univention.admin.uldap
import univention.admin.modules
import univention.admin.objects
from univention.config_registry import ConfigRegistry


baseConfig = ConfigRegistry()
baseConfig.load()

baseDN = baseConfig['ldap/base']
position = univention.admin.uldap.position(baseDN)

secretFile = open('/etc/ldap.secret', 'r')
pwdLine = secretFile.readline()
pwd = re.sub('\n', '', pwdLine)
tls = 2

try:
	lo = univention.admin.uldap.access(host=baseConfig['ldap/master'], base=baseDN, binddn='cn=admin,' + baseDN, bindpw=pwd, start_tls=tls)
except Exception as e:
	univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'authentication error: %s' % str(e))
	print 'authentication error: %s' % str(e)
	sys.exit(1)


module = univention.admin.modules.get('shares/share')
univention.admin.modules.init(lo, position, module)

for object in univention.admin.modules.lookup(module, None, lo, scope='sub'):
	object.open()
	print 'work on DN:', codecs.latin_1_encode(univention.admin.objects.dn(object))[0]

	if object['writeable'] and object['sambaWriteable']:
		object['sambaWriteable'] = object['writeable']
		dn = object.modify()
		lo.modify(dn, [])

	else:
		print "WARNING: Object is missing attributes writeable and/or sambaWriteable ! Did you already update univention-ldap ?"
