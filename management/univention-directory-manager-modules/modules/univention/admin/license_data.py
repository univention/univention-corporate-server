# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  mapping defining restricution for admin module
#
# Copyright (C) 2004-2009 Univention GmbH
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

UCS = 'UCS'
UGS = 'UGS'
OXAE = 'OXAE'

class Attributes:
	def __init__( self, required_license = None, options = {} ):
		self.required_license = required_license
		self._options = options

	def options( self, license_type ):
		if not self._options: return ()
		if not isinstance( license_type, list ):
			license_type = list( license_type )
		license_type.sort()
		
		for key in self._options.keys():
			skey = list( key )
			skey.sort()
			if license_type == skey:
				return self._options[ key ]

		return ()

	def valid( self, license_type ):
		if not isinstance( license_type, list ):
			license_type = list( license_type )

		if not self.required_license:
			return True

		if isinstance ( self.required_license, list ):
			for rl in self.required_license:
				if rl in license_type:
					return True
			return False
		else:
			return self.required_license in license_type

def moreGroupware(license):
	return False, (license.compare(license.licenses[license.ACCOUNT],
				       license.licenses[license.GROUPWARE]) != 1)

modules = {
	'computers/managedclient': Attributes( UCS ),
	'computers/computer': Attributes( [ UCS, UGS ]),
	'computers/domaincontroller_backup': Attributes(  [ UCS, UGS ], options =
				{
					( UCS, ) : ( ( 'nagios', (False, False) ), ),
					( UGS, ) : ( ( 'nagios', (True, False) ), ),
					( UCS, UGS ) : ( ( 'nagios', (False, False) ), ),
				} ),
	'computers/domaincontroller_master': Attributes( [ UCS, UGS ],options =
				{
					( UCS, ) : ( ( 'nagios', (False, False) ), ),
					( UGS, ) : ( ( 'nagios', (True, False) ), ),
					( UCS, UGS ) : ( ( 'nagios', (False, False) ), ),
				} ),
	'computers/domaincontroller_slave': Attributes( [ UCS, UGS ],options =
				{
					( UCS, ) : ( ( 'nagios', (False, False) ), ),
					( UGS, ) : ( ( 'nagios', (True, False) ), ),
					( UCS, UGS ) : ( ( 'nagios', (False, False) ), ),
				} ),
	'computers/ipmanagedclient': Attributes( UCS ),
	'computers/macos': Attributes( UCS ),
	'computers/memberserver': Attributes( UCS ),
	'computers/mobileclient': Attributes( UCS ),
	'computers/thinclient': Attributes( UCS ),
	'computers/trustaccount': Attributes( UCS ),
	'computers/windows': Attributes( UCS ),
	'container/cn': Attributes(),
	'container/dc': Attributes(),
	'container/ou': Attributes(),
	'dhcp/dhcp': Attributes( UCS ),
	'dhcp/host': Attributes( UCS ),
	'dhcp/pool': Attributes( UCS ),
	'dhcp/server': Attributes( UCS ),
	'dhcp/service': Attributes( UCS ),
	'dhcp/shared': Attributes( UCS ),
	'dhcp/sharedsubnet': Attributes( UCS ),
	'dhcp/subnet': Attributes( UCS ),
	'dns/alias': Attributes([ UCS, UGS ]),
	'dns/dns': Attributes([ UCS, UGS ]),
	'dns/forward_zone': Attributes([ UCS, UGS ]),
	'dns/host_record': Attributes([ UCS, UGS ]),
	'dns/ptr_record': Attributes([ UCS, UGS ]),
	'dns/reverse_zone': Attributes([ UCS, UGS ]),
	'dns/srv_record': Attributes([ UCS, UGS ]),
	'dns/zone_mx_record': Attributes([ UCS, UGS ]),
	'dns/zone_txt_record': Attributes([ UCS, UGS ]),
	'groups/group': Attributes(),
	'mail/domain': Attributes( UGS ),
	'mail/folder': Attributes( UGS ),
	'mail/lists': Attributes( UGS ),
	'mail/mail': Attributes( UGS ),
	'networks/network': Attributes( UCS ),
	'nagios/nagios': Attributes( UCS ),
	'nagios/service': Attributes( UCS ),
	'nagios/timeperiod': Attributes( UCS ),
	'policies/admin_container': Attributes([ UCS, UGS ]),
	'policies/admin_user': Attributes([ UCS, UGS ]),
	'policies/autostart': Attributes( UCS ),
	'policies/clientdevices': Attributes( UCS ),
	'policies/clientpackages': Attributes( UCS ),
	'policies/console_access': Attributes([ UCS, UGS ]),
	'policies/desktop': Attributes( UCS ),
	'policies/dhcp_boot': Attributes( UCS ),
	'policies/dhcp_dns': Attributes( UCS ),
	'policies/dhcp_dnsupdate': Attributes( UCS ),
	'policies/dhcp_leasetime': Attributes( UCS ),
	'policies/dhcp_netbios': Attributes( UCS ),
	'policies/dhcp_routing': Attributes( UCS ),
	'policies/dhcp_scope': Attributes( UCS ),
	'policies/dhcp_statements': Attributes( UCS ),
	'policies/ldapserver': Attributes( UCS ),
	'policies/mailquota': Attributes(),
	'policies/maintenance': Attributes( UCS ),
	'policies/managedclientpackages': Attributes([ UCS]),
	'policies/masterpackages': Attributes( UCS ),
	'policies/memberpackages': Attributes( UCS ),
	'policies/mobileclientpackages': Attributes( UCS ),
	'policies/nfsmounts': Attributes([ UCS, UGS ]),
	'policies/policy': Attributes(),
	'policies/print_quota': Attributes( UCS ),
	'policies/printserver': Attributes( UCS ),
	'policies/pwhistory': Attributes( ),
	'policies/registry': Attributes([ UCS, UGS ]),
	'policies/release': Attributes( UCS ),
	'policies/repositoryserver': Attributes( UCS ),
	'policies/repositorysync': Attributes( UCS ),
	'policies/share_userquota': Attributes( UCS ),
	'policies/slavepackages': Attributes( UCS ),
	'policies/sound': Attributes( UCS ),
	'policies/thinclient': Attributes( UCS ),
	'policies/windowsinstallation': Attributes( UCS ),
	'policies/xfree': Attributes( UCS ),
	'settings/admin': Attributes(),
	'settings/cn': Attributes(),
	'settings/customattribute': Attributes(),
	'settings/default': Attributes( [ UCS, UGS ]),
	'settings/directory': Attributes(),
	'settings/license': Attributes(),
	'settings/lock': Attributes(),
	'settings/packages': Attributes( UCS ),
	'settings/printermodel': Attributes( UCS ),
	'settings/printeruri': Attributes( UCS ),
	'settings/prohibited_username': Attributes(),
	'settings/sambaconfig': Attributes( UCS ),
	'settings/sambadomain': Attributes( UCS ),
	'settings/service': Attributes(),
	'settings/settings': Attributes(),
	'settings/user': Attributes(),
	'settings/usertemplate': Attributes(),
	'settings/xconfig_choices': Attributes([ UCS, UGS ]),
	'shares/print': Attributes( UCS ),
	'shares/printer': Attributes( UCS ),
	'shares/printergroup': Attributes( UCS ),
	'shares/share': Attributes( [UCS, OXAE] ),
	'users/passwd': Attributes(),
	'users/user': Attributes( options =
				{
					( UCS, ) : ( ( 'mail', True ), ( 'groupware', False ) ),
					( UGS, ) : ( ( 'mail', True ), ( 'groupware', True ) ),
					( UCS, UGS ) : ( ( 'mail', True ), ( 'groupware', moreGroupware ) ),
				} )
}
