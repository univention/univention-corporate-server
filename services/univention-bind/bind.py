#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Bind
#  listener script
#
# Copyright (C) 2001, 2002, 2003, 2004, 2005, 2006 Univention GmbH
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA	 02110-1301	 USA

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
				f=open(os.path.join('/var/cache/univention-bind-proxy', new['zoneName'][0]), 'w')
				f.close()
	finally:
		listener.unsetuid()

def new_zone(baseConfig, zonename, dn):

	univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'DNS: Creating zone %s' % zonename)
	if not os.path.exists(named_conf_dir):
		os.mkdir(named_conf_dir)

	f=open(os.path.join(named_conf_dir, zonename), 'w')
	f.write('zone "%s" {\n' % zonename)
	f.write('\ttype master;\n')
	f.write('\tnotify yes;\n')
	f.write('\tdatabase "ldap ldap://%s/%s 172800";\n' % (baseConfig['ldap/server/ip'], dn))
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
	univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'DNS: Updating univention.conf')
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
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'DNS: Reloading BIND')
		for file in os.listdir('/var/cache/univention-bind-proxy'):
			if not os.path.exists(os.path.join('/var/cache/bind', file)):
				os.spawnv(os.P_WAIT, '/etc/init.d/univention-bind-proxy', ['univention-bind-proxy', 'restart'])
				os.spawnv(os.P_WAIT, '/etc/init.d/univention-bind', ['univention-bind', 'restart'])
			else:
				if os.path.exists('/usr/sbin/rndc'):
					os.spawnv(os.P_WAIT, '/usr/sbin/rndc', ['rndc', '-p 55555', 'reload', file])
					os.spawnv(os.P_WAIT, '/usr/sbin/rndc', ['rndc', '-p 953', 'reload', file])
			os.remove(os.path.join('/var/cache/univention-bind-proxy', file))

	finally:
		listener.unsetuid()
