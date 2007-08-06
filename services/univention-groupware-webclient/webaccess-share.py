#
# Univention Groupware Webclient
#  create webaccess shares
#
# Copyright (C) 2007 Univention GmbH
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

name='webaccess-share'
description='create webaccess shares'
filter='(objectClass=univentionShare)'
attributes=[]

import listener, univention_baseconfig
import univention.debug

def get_next_id ():
	baseConfig = univention_baseconfig.baseConfig()
	baseConfig.load()

	max_id = 0
	for key in baseConfig.keys():
		if key.startswith('horde/webaccess/share/'):
			try:
				id = int(key.split('/')[3])
			except:
				id = 0
			if id > max_id:
				max_id = id
	
	return str(max_id+1)


def handler(dn, new, old):
	baseConfig = univention_baseconfig.baseConfig()
	baseConfig.load()

	
	remove_list = []
	add_list = []
	if old and old.has_key('objectClass') and 'univentionShareWebaccess' in old['objectClass']:
		for key in baseConfig.keys():
			if key.startswith('horde/webaccess/share/') and key.endswith('/ldapdn') and baseConfig[ key ] == dn:
				name = key.split('ldapdn')[0]
				for k in baseConfig.keys():
					if k.startswith(name):
						remove_list.append( k )
	if new and new.has_key('objectClass') and 'univentionShareWebaccess' in new['objectClass']:
		id = None
		for key in baseConfig.keys():
			if key.startswith('horde/webaccess/share/') and key.endswith('/ldapdn') and baseConfig[ key ] == dn:
				id = key.split('/')[3]
		if not id:
			id = get_next_id()

		add_list.append( 'horde/webaccess/share/%s/ldapdn=%s' % (id, dn) )
		if new.has_key( 'univentionShareHost' ):
			add_list.append( 'horde/webaccess/share/%s/hostspec=%s' % (id, new['univentionShareHost'][0].split('.')[0]) )
		if new.has_key( 'univentionShareSambaName' ):
			add_list.append( 'horde/webaccess/share/%s/share=%s' % (id, new['univentionShareSambaName'][0]) )
		if new.has_key( 'univentionShareWebaccessName' ):
			add_list.append( 'horde/webaccess/share/%s/name=%s' % (id, new['univentionShareWebaccessName'][0] ) )
		if new.has_key( 'univentionShareWebaccessIpaddress' ):
			add_list.append( 'horde/webaccess/share/%s/ipaddress=%s' % (id, new['univentionShareWebaccessIpaddress'][0] ) )

	listener.setuid(0)
	if len(remove_list) > 0:
		univention_baseconfig.handler_unset( remove_list )
	if len(add_list) > 0:
		univention_baseconfig.handler_set( add_list )
	listener.unsetuid()

