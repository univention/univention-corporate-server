#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Installer
#  definitions of package lists
#
# Copyright 2004-2011 Univention GmbH
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

from local import _

PackageList=[
{
	'Category': _('Desktop Environment'),
	'CategoryShow': ['all'],
	'Description': _('Desktop Environment packages'),
	'Packages':
			[
				{
					'Name': _('Desktop environemnt')
					'Packages': ['univention-kde'],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver', 'mobile_client', 'managed_client'],
					'Possible': ['all'],
					'Description': _('Core Packages for a Graphical Desktop Environment'),
				},
			],
},
{
	'Category': _('Services for Windows'),
	'CategoryShow': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
	'Description': _("Several Windows related services"),
	'Packages':
			[
				{
					'Name': _('Samba 4 server'),
					'Packages': ['univention-samba4'],
					'Edition': [ 'ucs' ],
					'Active': [ 'domaincontroller_slave', 'memberserver' ],
					'Possible': [ 'domaincontroller_slave', 'memberserver' ],
					'Description': _("Samba 4 Services"),
				},
				{
					'Name': _('Samba 4 server'), # DC Master and DC Backups need the s4 connector for UCS 3,0 MS1 and MS2
					'Packages': ['univention-s4-connector', 'univention-samba4'],
					'Edition': [ 'ucs' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup'],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup'],
					'Description': _("Samba 4 Services"),
				},
				{
					'Name': _('Samba 3 server'),
					'Packages': ['univention-samba', 'samba'],
					'Edition': [ 'ucs' ],
					'Active': [],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Description': _("Samba Services"),
				},
				{
					'Name': _('Active Directory Connector'),
					'Packages': ['univention-ad-connector'],
					'EditionDisable': [ 'oxae' ],
					'Active': [ ],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup'],
					'Description': _('Sync users and groups with Active Directory'),
				},
			],
},
{
	'Category': _('Virtualization'),
	'CategoryShow': ['all'],
	'Description': _('Univention virtualization'),
	'Packages':
			[
				{
					'Name': _('Management server for KVM or Xen'),
					'Packages': ['univention-virtual-machine-manager-daemon', 'univention-virtual-machine-manager-schema'],
					'Edition': [ 'ucs' ],
					'Active': [ ],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave'],
					'Description': _('UMC module for managing virtualization servers and virtual instances'),
				},
				{
					'Name': _('KVM virtualization server'),
					'Packages': ['univention-virtual-machine-manager-node-kvm'],
					'Edition': [ 'ucs' ],
					'Active': [ ],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver', 'basesystem'],
					'Description': _('Sets up a virtualization server based on KVM'),
				},
				{
					'Name': _('Xen virtualization server'),
					'Packages': ['univention-virtual-machine-manager-node-xen'],
					'Edition': [ 'ucs' ],
					'Active': [ ],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver', 'basesystem'],
					'Description': _('Sets up a virtualization server based on Xen'),
				},
			],
},
{
	'Category': _('System services'),
	'CategoryShow': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
	'Description': _("Additional Services"),
	'Packages':
			[
				{
					'Name': _('Mail server'),
					'Packages': ['univention-mail-postfix', 'univention-mail-cyrus'],
					'Edition': [ 'ucs' ],
					'Active': [''], 
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver', 'Basis'],
					'Description': _('Standard mail services with postfix and cyrus (SMTP/POP/IMAP)'),
				},
				{
					'Name': _('DHCP server'),
					'Packages': ['univention-dhcp'],
					'Edition': [ 'ucs' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave'],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Description': _("DHCP Server"),
				},
				{
					'Name': _('Print server (Cups)'),
					'Packages': ['univention-printserver', 'cups'],
					'Edition': [ 'ucs' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Possible': ['all'],
					'Description': _('Print server based on cups'),
				},
				{
					'Name': _('Web proxy server Squid)'),
					'Packages': ['univention-squid', 'squid'],
					'Edition': [ 'ucs' ],
					'Active': [ ],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Description': _('Web Proxy Services'),
				},
				{
					'Name': _('Bacula (Backup)'),
					'Packages': ['univention-bacula'],
					'Edition': [ 'ucs' ],
					'Active': [],
					'Possible': ['all'],
					'Description': _('Network based Backup Software'),
				},

			],
},
{
	'Category': _('Monitoring'),
	'CategoryShow': ['all'],
	'Description': _('Monitoring services'),
	'Packages':
			[
				{
					'Name': _('Network monitoring server (Nagios)'),
					'Packages': ['univention-nagios-server', 'univention-nagios-client'],
					'Edition': [ 'ucs' ],
					'Active': [ 'domaincontroller_master' ],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Description': _('Host, service and network monitoring program (server software)'),
				},
				{
					'Name': _('Software installation monitor'),
					'Packages': ['univention-pkgdb'],
					'Edition': [ 'ucs' ],
					'Active': [''],
					'Possible': ['all'],
					'Description': _('Univention packagestatus database'),
				},
			],
},
]
