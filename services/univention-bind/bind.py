#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Bind
#  listener script
#
# Copyright 2001-2012 Univention GmbH
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
import univention_baseconfig
import os, grp
import univention.debug

name='bind'
description='Update BIND zones'
filter='(&(objectClass=dNSZone)(relativeDomainName=@)(zoneName=*))'
attributes=[]

named_conf_file   = "/etc/bind/univention.conf"
named_conf_dir    = "/etc/bind/univention.conf.d"
proxy_conf_file   = "/etc/bind/univention.conf.proxy"

def initialize():
	pass

def handler(dn, new, old):
	baseConfig = univention_baseconfig.baseConfig()
	baseConfig.load()
	listener.setuid(0)
	try:
		if (baseConfig.has_key('dns/ldap/base') and baseConfig['dns/ldap/base'] and dn.endswith(baseConfig['dns/ldap/base'])) or not (baseConfig.has_key('dns/ldap/base') and baseConfig['dns/ldap/base']):
			if new and not old:
				new_zone(baseConfig, new['zoneName'][0], dn)
			elif old and not new:
				remove_zone(old['zoneName'][0])
			if new.has_key('zoneName'):
				zonefile=os.path.join('/var/cache/univention-bind-proxy', new['zoneName'][0]) + ".zone"
				f=open(zonefile, 'w')
				f.close()
				os.chmod(zonefile, 0640)
	finally:
		listener.unsetuid()

def ldap_auth_string(baseConfig):

	account=baseConfig.get('bind/binddn', baseConfig.get('ldap/hostdn')).replace(',', '%2c')

	pwdfile=baseConfig.get('bind/bindpw', '/etc/machine.secret')
	pwd=open(pwdfile).readlines()


	return '????!bindname=%s,!x-bindpw=%s,x-tls' % (account, pwd[0])

def new_zone(baseConfig, zonename, dn):

	univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'DNS: Creating zone %s' % zonename)
	if not os.path.exists(named_conf_dir):
		os.mkdir(named_conf_dir)


	zonefile=os.path.join(named_conf_dir, zonename)
	f=open(zonefile, 'w').close()
	os.chmod(zonefile, 0640)

	f=open(zonefile, 'w+')

	f.write('zone "%s" {\n' % zonename)
	f.write('\ttype master;\n')
	f.write('\tnotify yes;\n')
	f.write('\tdatabase "ldap ldap://%s:%s/%s%s 172800";\n' % (baseConfig.get('bind/ldap/server/ip', '127.0.0.1'), baseConfig.get('ldap/server/port', '7389'), dn, ldap_auth_string(baseConfig)))
	f.write('};\n')
	f.close()

	f=open(os.path.join(named_conf_dir, zonename+'.proxy'), 'w')
	f.write('zone "%s" {\n' % zonename)
	f.write('\ttype slave;\n')
	f.write('\tfile "%s.zone";\n' % zonename)
	f.write('\tmasters port 7777 { 127.0.0.1; };\n')
	f.write('};\n')
	f.close()

def remove_zone(zonename):
	univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'DNS: Removing zone %s' % zonename)
	zfile=os.path.join(named_conf_dir, zonename)
	if os.path.exists(zfile):
		os.unlink(zfile)
	if os.path.exists(zfile+'.proxy'):
		os.unlink(zfile+'.proxy')

def clean():
	listener.setuid(0)
	try:
		if os.path.exists(named_conf_file):
			os.unlink(named_conf_file)
		open(named_conf_file, 'w').close()

		if os.path.isdir(named_conf_dir):
			for f in os.listdir(named_conf_dir):
				os.unlink(os.path.join(named_conf_dir, f))
			os.rmdir(named_conf_dir)
	finally:
		listener.unsetuid()

def postrun():
	baseConfig = univention_baseconfig.baseConfig()
	baseConfig.load()

	listener.setuid(0)
	try:
		fp = open(named_conf_file, 'w')
		if os.path.isdir(named_conf_dir):
			for f in os.listdir(named_conf_dir):
				if not f.endswith('.proxy'):
					fp.write('include "%s";\n' % os.path.join(named_conf_dir, f))
		fp.close()
		fp = open(proxy_conf_file, 'w')
		if os.path.isdir(named_conf_dir):
			for f in os.listdir(named_conf_dir):
				if f.endswith('.proxy'):
					fp.write('include "%s";\n' % os.path.join(named_conf_dir, f))
		fp.close()

		if baseConfig.get('dns/backend') in ['samba4', 'none']:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'DNS: Skip zone reload')
			listener.unsetuid()
			return

		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'DNS: Reloading BIND')
		restart=False
		for file in os.listdir('/var/cache/univention-bind-proxy'):
			if not os.path.exists(os.path.join('/var/cache/bind', file)):
				restart=True
			else:
				zone = file.replace(".zone", "")
				if os.path.exists('/usr/sbin/rndc'):
					os.spawnv(os.P_WAIT, '/usr/sbin/rndc', ['rndc', '-p 55555', 'reload', zone])
					os.spawnv(os.P_WAIT, '/usr/sbin/rndc', ['rndc', '-p 953', 'reload', zone])
			os.remove(os.path.join('/var/cache/univention-bind-proxy', file))
		if restart:
			os.spawnv(os.P_WAIT, '/etc/init.d/univention-bind-proxy', ['univention-bind-proxy', 'restart'])
			os.spawnv(os.P_WAIT, '/etc/init.d/univention-bind', ['univention-bind', 'restart'])

	finally:
		listener.unsetuid()
