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
	'Category': _('Services for Windows'),
	'CategoryShow': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
	'Description': _("Several Windows related services"),
	'Packages':
			[
				{
					'Name': _('Samba 4'),
					'Packages': ['univention-samba4'],
					'Edition': [ 'ucs' ],
					'Active': [ 'domaincontroller_slave', 'memberserver' ],
					'Possible': [ 'domaincontroller_slave', 'memberserver' ],
					'Description': _("Samba 4 Services"),
				},
				{
					'Name': _('Samba 4'), # DC Master and DC Backups need the s4 connector for UCS 3,0 MS1 and MS2
					'Packages': ['univention-s4-connector', 'univention-samba4'],
					'Edition': [ 'ucs' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup'],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup'],
					'Description': _("Samba 4 Services"),
				},
				{
					'Name': _('Samba 3'),
					'Packages': ['univention-samba', 'samba'],
					'Edition': [ 'ucs' ],
					'Active': [],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Description': _("Samba Services"),
				},
				{
					'Name': _('Samba 3 PDC on Non-DC Master'),
					'Packages': ['univention-samba-slave-pdc'],
					'Edition': [ 'ucs' ],
					'Active': [],
					'Possible': ['domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Description': _("Samba domain controller as a slave to another master domain controller"),
				},
				{
					'Name': _('Winbind for Samba 3'),
					'Packages': ['winbind'],
					'Edition': [ 'ucs' ],
					'Active': [ 'memberserver' ],
					'Possible': ['all'],
					'Description': _("Winbind Service"),
				},
				{
					'Name': _('Univention AD Connector'),
					'Packages': ['univention-ad-connector'],
					'EditionDisable': [ 'oxae' ],
					'Active': [ ],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup'],
					'Description': _('Sync users and groups with Active Directory'),
				},
			],
},
{
	'Category': _('Mail/Groupware'),
	'CategoryShow': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave' ],
	'Description': _('Several mail/groupware related services'),
	'Packages':
			[
				{
					'Name': _('Standard mail services'),
					'Packages': ['univention-mail-postfix', 'univention-mail-cyrus'],
					'Edition': [ 'ucs' ],
					'Active': [''], 
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver', 'Basis'],
					'Description': _('Standard mail services with postfix and cyrus (SMTP/POP/IMAP)'),
				},
			],
},
{
	'Category': _('Network management'),
	'CategoryShow': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
	'Description': _("Several IP related services"),
	'Packages':
			[
				{
					'Name': _('DNS'),
					'Packages': ['univention-bind', 'univention-bind-proxy', 'bind9'],
					'Edition': [ 'ucs' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave'],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave'],
					'Description': _("DNS Server and Proxy"),
				},
				{
					'Name': _('DHCP'),
					'Packages': ['univention-dhcp', 'dhcp3-server'],
					'Edition': [ 'ucs' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave'],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Description': _("DHCP Server"),
				},
				{
					'Name': _('Squid proxy server'),
					'Packages': ['univention-squid', 'squid'],
					'Edition': [ 'ucs' ],
					'Active': [ ],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Description': _('Web Proxy Services'),
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
					'Name': _('Univention AD Connector'),
					'Packages': ['univention-ad-connector'],
					'Edition': [ 'oxae' ],
					'Active': [ ],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup'],
					'Description': _('Sync users and groups with Active Directory'),
				},
				{
					'Name': _('Bacula (Backup)'),
					'Packages': ['univention-bacula'],
					'Edition': [ 'oxae' ],
					'Active': [],
					'Possible': ['all'],
					'Description': _('Network based Backup Software'),
				},
				{
					'Name': _('Open-Xchange'),
					'Packages': ['univention-ox', 'univention-ox-directory-integration', 'univention-oxae'],
					'Edition': [ 'oxae' ],
					'Active': ['domaincontroller_master'],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver', 'Basis'],
					'Description': _('Open-Xchange Groupware Server'),
				},
				{
					'Name': _('Samba'),
					'Packages': ['univention-samba', 'samba', 'cups', 'cups-bsd', 'cups-client', 'cups-driver-gutenprint', 'foomatic-db-gutenprint', 'foomatic-db-hpijs', 'foomatic-filters-ppds'],
					'Edition': [ 'oxae' ],
					'Active': ['domaincontroller_master'],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver', 'basesystem'],
					'Description': _("Samba Services"),
				},
				{
					'Name': _('Terminal server'),
					'Packages': ['univention-application-server'],
					'Edition': [ 'ucs' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup'],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Description': _('X-Window-System Client for Terminal Services'),
				},
				{
					'Name': _('Print server'),
					'Packages': ['univention-printserver', 'cups'],
					'Edition': [ 'ucs' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Possible': ['all'],
					'Description': _('Print server based on cups'),
				},
				{
					'Name': _('Print quota'),
					'Packages': ['univention-printquota', 'pykota', 'univention-printquotadb'],
					'Edition': [ 'ucs' ],
					'Active': [],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Description': _('Print quota support based on pykota'),
				},
				{
					'Name': _('Nagios server'),
					'Packages': ['univention-nagios-server'],
					'Edition': [ 'ucs' ],
					'Active': [ 'domaincontroller_master' ],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Description': _('Host, service and network monitoring program (server software)'),
				},
				{
					'Name': _('Nagios client'),
					'Packages': ['univention-nagios-client'],
					'Edition': [ 'ucs' ],
					'Active': [ 'domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver' ],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver' ],
					'Description': _('Host, service and network monitoring program (client software)'),
				},
				{
					'Name': _('OpenSSH server'),
					'Packages': ['openssh-server'],
					'Active': [ 'all' ],
					'Possible': [ 'all' ],
					'Description': _("Secure shell server, an rshd replacement"),
				},
				{
					'Name': _('FreeNX server'),
					'Packages': ['freenx'],
					'Edition': [ 'ucs' ],
					'Active': [ ],
					'Possible': ['all'],
					'Description': _('FreeNX application/thin-client server'),
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
					'Name': _('Virtual Machine Manager (UVMM)'),
					'Packages': ['univention-virtual-machine-manager-daemon', 'univention-virtual-machine-manager-schema'],
					'Edition': [ 'ucs' ],
					'Active': [ ],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave'],
					'Description': _('UMC module for managing virtualization servers and virtual instances'),
				},
				{
					'Name': _('Xen virtualization server'),
					'Packages': ['univention-virtual-machine-manager-node-xen'],
					'Edition': [ 'ucs' ],
					'Active': [ ],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver', 'basesystem'],
					'Description': _('Sets up a virtualization server based on Xen'),
				},
				{
					'Name': _('KVM virtualization server'),
					'Packages': ['univention-virtual-machine-manager-node-kvm'],
					'Edition': [ 'ucs' ],
					'Active': [ ],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver', 'basesystem'],
					'Description': _('Sets up a virtualization server based on KVM'),
				},
			],
},
{
	'Category': _('Administrative tools'),
	'CategoryShow': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
	'Description': _('Administrative tools'),
	'Packages':
			[
				{
					'Name': _('Univention Directory Manager'),
					'Packages': ['univention-management-console-module-udm', 'python-univention-license'],
					'Active': ['domaincontroller_master', 'domaincontroller_backup'],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup'],
					'Description': _('Univention Director Manager Web Frontend'),
				},
				{
					'Name': _('Univention Management Console'),
					'Packages': ['univention-management-console'],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver', 'mobile_client', 'managed_client'],
					'Possible': ['all'],
					'Description': _('Configuration Frontend for Servers and Clients'),
				},
				{
					'Name': _('Univention Software Monitor'),
					'Packages': ['univention-pkgdb'],
					'Edition': [ 'ucs' ],
					'Active': [''],
					'Possible': ['all'],
					'Description': _('Univention packagestatus database'),
				},
				{
					'Name': _('UCS Net Installer'),
					'Packages': ['univention-net-installer'],
					'Edition': [ 'ucs' ],
					'Active': [],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Description': _('Install UCS over the network'),
				},
			],
},
{
	'Category': _('Backup'),
	'CategoryShow': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
	'Description': _('Backup Tools'),
	'Packages':
			[
				{
					'Name': _('Bacula (Backup)'),
					'Packages': ['univention-bacula'],
					'Edition': [ 'ucs' ],
					'Active': [],
					'Possible': ['all'],
					'Description': _('Network based Backup Software'),
				},
				{
					'Name': _('Remote backup'),
					'Packages': ['univention-remote-backup'],
					'Edition': [ 'ucs' ],
					'Active': [],
					'Possible': ['all'],
					'Description': _('Backup Software based on rsync'),
				},
			],
},
{
	'Category': _('Desktop Environment'),
	'CategoryShow': ['all'],
	'Description': _('Desktop Environment packages'),
	'Packages':
			[
				{
					'Name': _('Graphical user interface'),
					'Packages': ['univention-kde'],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver', 'mobile_client', 'managed_client'],
					'Possible': ['all'],
					'Description': _('Core Packages for a Graphical Desktop Environment'),
				},
			],
},
{
	'Category': _('Tools'),
	'CategoryShow': ['all'],
	'Description': _("Extra Tools"),
	'Packages':
			[
				{
					'Name': _('Java'),
					'Packages': ['univention-java'],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver', 'mobile_client', 'managed_client'],
					'Possible': ['all'],
					'Description': _('Java Virtual Machine'),
				},
				{
					'Name': _('Commandline tools'),
					'Packages': ['vim', 'emacs23', 'less', 'elinks', 'wget', 'nmap', 'zip', 'unzip', 'eject'],
					'Active': ['all'],
					'Possible': [ 'all' ],
					'Description': _('Various commandline tools, like vim, less, nmap, ...'),
				},
			]

},
]
