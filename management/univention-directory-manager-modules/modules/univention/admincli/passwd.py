# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  passwd part for the command line interface
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

import os
import getopt
import univention.debug as ud
import univention.misc

import univention.config_registry
import univention.admin.uldap
import univention.admin.modules
import univention.admin.objects
import univention.admin.handlers.users.user


def doit(arglist):
	ud.init('/var/log/univention/directory-manager-cmd.log', 1, 1)
	out = []
	opts, args = getopt.getopt(arglist[1:], '', ['binddn=', 'pwdfile=', 'user=', 'pwd='])

	binddn = None
	pwdfile = None
	user = None
	pwd = None

	for opt, val in opts:
		if opt == '--binddn':
			binddn = val
		elif opt == '--pwdfile':
			pwdfile = val
		elif opt == '--user':
			user = val
		elif opt == '--pwd':
			pwd = val

	ud.set_level(ud.LDAP, ud.ALL)
	ud.set_level(ud.ADMIN, ud.ALL)

	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()

	baseDN = configRegistry['ldap/base']

	bindpw = open(pwdfile).read()
	if bindpw[-1] == '\n' or bindpw[-1] == '\r':
		bindpw = bindpw[0:-1]

	ud.debug(ud.ADMIN, ud.WARN, 'binddn: %s; bindpwd: *************' % (binddn))
	try:
		lo = univention.admin.uldap.access(host=configRegistry['ldap/master'], port=int(configRegistry.get('ldap/master/port', '7389')), base=baseDN, binddn=binddn, bindpw=bindpw, start_tls=2)
	except Exception as e:
		ud.debug(ud.ADMIN, ud.WARN, 'authentication error: %s' % str(e))
		out.append('authentication error: %s' % e)
		return out

	try:
		dn = lo.searchDn(filter=unicode('(&(uid=%s)(|(objectClass=posixAccount)(objectClass=sambaSamAccount)(objectClass=person)))' % user, 'utf8'), base=baseDN, unique=True)
		position = univention.admin.uldap.position(baseDN)

		module = univention.admin.modules.get('users/user')
		univention.admin.modules.init(lo, position, module)

		object = univention.admin.objects.get(module, None, lo, position=position, dn=dn[0])
		object.open()

		# hack, to prevent that attributes belonging to the samba option are changed; Bug #41530
		if 'samba' in object.options:
			object.options.remove('samba')
			object.old_options.remove('samba')
			object._ldap_object_classes = lambda ml: ml

		if 'samba/charset/unix' not in configRegistry:
			ud.debug(ud.ADMIN, ud.INFO, 'univention-passwd: no unix-charset given')
			object['password'] = unicode(pwd, 'utf8')
		elif configRegistry['samba/charset/unix'] in ['utf8', 'latin']:
			ud.debug(ud.ADMIN, ud.INFO, 'univention-passwd: known charset given: %s' % configRegistry['samba/charset/unix'])
			object['password'] = unicode(pwd, configRegistry['samba/charset/unix'])
		else:
			ud.debug(ud.ADMIN, ud.INFO, 'univention-passwd: unknown charset given, try fallback')
			object['password'] = unicode(pwd)

		ud.debug(ud.ADMIN, ud.INFO, 'univention-passwd: passwd set, modify object')
		dn = object.modify()

		out.append('password changed')
		ud.debug(ud.ADMIN, ud.INFO, 'univention-passwd: password changed')

	except univention.admin.uexceptions.pwalreadyused:
		out.append('passwd error: password already used')
		return out

	except Exception as e:
		ud.debug(ud.ADMIN, ud.WARN, 'passwd error: %s' % e)
		out.append('passwd error: %s' % e)
		return out

	try:
		# check for local ldap server connection
		if configRegistry.is_true('ldap/replication/preferredpassword'):
			if configRegistry.get('ldap/server/type') == 'slave':
				if os.path.exists('/etc/ldap/rootpw.conf'):
					bindpw = open('/etc/ldap/rootpw.conf').read()
					bindpw = bindpw.split(' ')[1].strip('\n\r"')
					lo = univention.admin.uldap.access(host='%s.%s' % (configRegistry['hostname'], configRegistry['domainname']), base=baseDN, binddn='cn=update,%s' % (baseDN), bindpw=bindpw, start_tls=2)
					dn = lo.searchDn(filter=unicode('(&(uid=%s)(|(objectClass=posixAccount)(objectClass=sambaSamAccount)(objectClass=person)))' % user, 'utf8'), base=baseDN, unique=True)
					position = univention.admin.uldap.position(baseDN)
					module = univention.admin.modules.get('users/user')
					univention.admin.modules.init(lo, position, module)

					object = univention.admin.objects.get(module, None, lo, position=position, dn=dn[0])
					object.open()

					if 'samba/charset/unix' not in configRegistry:
						ud.debug(ud.ADMIN, ud.INFO, 'univention-passwd: no unix-charset given')
						object['password'] = unicode(pwd, 'utf8')
					elif configRegistry['samba/charset/unix'] in ['utf8', 'latin']:
						ud.debug(ud.ADMIN, ud.INFO, 'univention-passwd: known charset given: %s' % configRegistry['samba/charset/unix'])
						object['password'] = unicode(pwd, configRegistry['samba/charset/unix'])
					else:
						ud.debug(ud.ADMIN, ud.INFO, 'univention-passwd: unknown charset given, try fallback')
						object['password'] = unicode(pwd)

					ud.debug(ud.ADMIN, ud.INFO, 'univention-passwd: passwd set, modify object')
					object['overridePWHistory'] = '1'
					object['overridePWLength'] = '1'
					dn = object.modify()

					ud.debug(ud.ADMIN, ud.INFO, 'univention-passwd: password changed')
	except Exception as e:
		ud.debug(ud.ADMIN, ud.WARN, 'passwd error: %s' % e)

	return out
