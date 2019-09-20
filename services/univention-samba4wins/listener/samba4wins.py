# -*- coding: utf-8 -*-
#
# Univention Samba4WINS
#  listener module: Samba4WINS configuration
#
# Copyright 2008-2019 Univention GmbH
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

__package__ = ''  # workaround for PEP 366
import listener
import univention.config_registry
import os
import subprocess
import univention.debug

name = 'samba4wins'
description = 'Samba4WINS configuration'
filter = "(objectClass=univentionSamba4WinsHost)"
attributes = ['univentionSamba4WinsNetbiosName', 'univentionSamba4WinsSecondaryIp']


def pipe(input, cmd1argv, uid=-1, wait=1):
	output = None
	if uid > -1:
		olduid = os.getuid()
		listener.setuid(uid)
	try:
		p1 = subprocess.Popen(cmd1argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
		if wait:
			output = p1.communicate(input)[0]
		else:
			output = p1.pid
	finally:
		if uid > -1:
			listener.setuid(olduid)
	return output


def initialize():
	pass


def handler(dn, new, old):
	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()
	listener.setuid(0)
	try:
		if dn == configRegistry['ldap/hostdn']:
			if new:
				samba4wins_dict = {}
				if new.get('univentionSamba4WinsNetbiosName'):
					samba4wins_dict['netbios/name'] = new['univentionSamba4WinsNetbiosName'][0]
				if new.get('univentionSamba4WinsSecondaryIp'):
					samba4wins_dict['address'] = new['univentionSamba4WinsSecondaryIp'][0]

				# determine network interface to use
				samba4wins_interface = None
				if configRegistry.get('samba4wins/interface'):
					samba4wins_interface = configRegistry['samba4wins/interface']
				else:
					if configRegistry.get('samba/interfaces'):
						for interface in configRegistry['samba/interfaces'].split():
							if interface.startswith('eth'):
								samba4wins_interface = interface
								samba4wins_dict['interface'] = interface
								break

				if samba4wins_interface and samba4wins_dict.get('netbios/name') and samba4wins_dict.get('address'):
					# determine netmask, network and broadcast from parent interface
					parentinterface = configRegistry['samba/interfaces']
					for rkey in ['netmask', 'network', 'broadcast']:
						samba4wins_dict[rkey] = configRegistry.get('samba4wins/%s' % rkey) or configRegistry.get('interfaces/%s/%s' % (parentinterface, rkey))

					# setup network interface
					ucrcmd = ['univention-config-registry', 'set']
					for rkey in ['address', 'netmask', 'network', 'broadcast']:
						ucrcmd.append('interfaces/%s/%s=%s' % (samba4wins_interface, rkey, samba4wins_dict[rkey]))
					listener.run('/usr/sbin/univention-config-registry', ucrcmd, uid=0)

					# activate samba4wins variables
					ucrcmd = ['univention-config-registry', 'set']
					for key in ['address', 'netbios/name']:
						ucrcmd.append('samba4wins/%s=%s' % (key, samba4wins_dict[key]))
					# and deactivate "wins support" in Samba3
					ucrcmd.append('windows/wins-support=no')
					ucrcmd.append('windows/wins-server=%s' % samba4wins_dict['address'])
					listener.run('/usr/sbin/univention-config-registry', ucrcmd, uid=0)

			elif old:
				# determine network interface
				samba4wins_interface = None
				if configRegistry.get('samba4wins/interface'):
					samba4wins_interface = configRegistry['samba4wins/interface']

				# reactivate "wins support" in Samba3 in case we are on a master
				if configRegistry.get('server/role') == 'domaincontroller_master':
					listener.run('/usr/sbin/univention-config-registry', ['univention-config-registry', 'set', 'wins/wins-support=yes'], uid=0)

				# deactivate samba4wins variables
				listener.run('/usr/sbin/univention-config-registry', ['univention-config-registry', 'unset', 'samba4wins/netbios/name', 'samba4wins/address'], uid=0)

				# unset network interface
				if samba4wins_interface:
					ucrcmd = ['univention-config-registry', 'unset']
					for rkey in ['address', 'netmask', 'network', 'broadcast']:
						ucrcmd.append('interfaces/%s/%s' % (samba4wins_interface, rkey))

					listener.run('/usr/sbin/univention-config-registry', ucrcmd, uid=0)

		else:  # not my dn, so a Samba4WINS "Partner" server changed
			if new:
				# modify samba4wins ldb
				samba4wins_dict = {}
				if new.get('univentionSamba4WinsNetbiosName'):
					samba4wins_dict['netbios/name'] = new['univentionSamba4WinsNetbiosName'][0]
				if new.get('univentionSamba4WinsSecondaryIp'):
					samba4wins_dict['address'] = new['univentionSamba4WinsSecondaryIp'][0]

				ldbadd = True
				if old:
					old_name = None
					old_ip = None
					if old.get('univentionSamba4WinsNetbiosName'):
						old_name = old['univentionSamba4WinsNetbiosName'][0]
					if old.get('univentionSamba4WinsSecondaryIp'):
						old_ip = old['univentionSamba4WinsSecondaryIp'][0]
					if old_name and old_ip:
						if samba4wins_dict.get('netbios/name') != old_name or samba4wins_dict.get('address') != old_ip:
							listener.run('/usr/bin/ldbdel', ['ldbdel', '-d0', '-H', '/var/lib/samba4wins/private/wins_config.ldb', 'CN=%s,CN=PARTNERS' % old_name], uid=0)
						# else:
						#	ldbadd=False
				if ldbadd and samba4wins_dict.get('netbios/name') and samba4wins_dict.get('address'):
					ldif = 'dn: CN=%(netbios/name)s,CN=PARTNERS\nobjectClass: wreplPartner\naddress: %(address)s\n' % samba4wins_dict
					pipe(ldif, ['/usr/bin/ldbadd', '-d0', '-H', '/var/lib/samba4wins/private/wins_config.ldb'], uid=0)

			elif old:
				if old.get('univentionSamba4WinsNetbiosName'):
					old_name = old['univentionSamba4WinsNetbiosName'][0]
					listener.run('/usr/bin/ldbdel', ['ldbdel', '-d0', '-H', '/var/lib/samba4wins/private/wins_config.ldb', 'CN=%s,CN=PARTNERS' % old_name], uid=0)

	finally:
		listener.unsetuid()


def postrun():
	listener.setuid(0)
	try:
		os.spawnv(os.P_WAIT, '/bin/sh', ['sh', '/etc/init.d/samba4wins', 'stop'])
		os.spawnv(os.P_WAIT, '/bin/sh', ['sh', '/etc/init.d/samba4wins', 'start'])
	finally:
		listener.unsetuid()
