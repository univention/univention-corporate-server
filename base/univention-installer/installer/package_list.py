#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Installer
#  definitions of package lists
#
# Copyright (C) 2004-2010 Univention GmbH
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

from local import _

PackageList=[
{
	'Category': _('Services for Windows'),
	'CategoryShow': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
	'Description': _("Several Windows related services"),
	'Packages':
			[
				{
					'Name': _('Samba'),
					'Packages': ['univention-samba', 'samba'],
					'Edition': [ 'scalix', 'ugs' ],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver', 'basesystem'],
					'Description': _("Samba Services"),
				},
				{
					'Name': _('Windows Installer'),
					'Packages': ['univention-windows-installer'],
					'Edition': [ 'scalix', 'ugs' ],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave' ],
					'Description': _("Automatic Installation for Windows Clients"),
				},
				{
					'Name': _('Samba PDC on Non-DC Master'),
					'Packages': ['univention-samba-slave-pdc'],
					'Edition': [ 'scalix', 'ugs' ],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [],
					'Possible': ['domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Description': _("Samba domain controller as a slave to another master domain controller"),
				},
				{
					'Name': _('Winbind'),
					'Packages': ['winbind'],
					'Edition': [ 'scalix', 'ugs' ],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [ 'memberserver' ],
					'Possible': ['all'],
					'Description': _("Winbind Service"),
				},
				{
					'Name': _('Univention AD Connector'),
					'Packages': ['univention-ad-connector'],
					'Architecture': [ 'x86', 'powerpc' ],
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
					'Name': _('Scalix for UCS'),
					'Packages': ['univention-scalix', 'univention-scalix-amavis' ],
					'Edition': [ 'scalix' ],
					'Architecture': [ 'x86' ],
					'Active': ['domaincontroller_master' ],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver', 'basesystem'],
					'Description': _('The Scalix Groupware'),
				},
				{
					'Name': _('Kolab 2 for UCS'),
					'Packages': ['univention-kolab2', 'univention-kolab2-framework', 'univention-mail-postfix-kolab2', 'univention-mail-cyrus-kolab2', 'univention-kolab2-webclient'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Edition': [ 'ugs' ],
					'Active': ['domaincontroller_master' ],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave'],
					'Description': _('Groupware based on Kolab 2 (server and client)'),
				},
				{
					'Name': _('Standard mail services'),
					'Packages': ['univention-mail-postfix', 'univention-mail-cyrus'],
					'Edition': [ 'scalix', 'ugs' ],
					'Architecture': [ 'x86', 'powerpc' ],
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
					'Edition': [ 'scalix', 'ugs' ],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave'],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave'],
					'Description': _("DNS Server and Proxy"),
				},
				{
					'Name': _('DHCP'),
					'Packages': ['univention-dhcp', 'dhcp3-server'],
					'Edition': [ 'scalix', 'ugs' ],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave'],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Description': _("DHCP Server"),
				},
				{
					'Name': _('Squid proxy server'),
					'Packages': ['univention-squid', 'squid'],
					'Edition': [ 'scalix', 'ugs' ],
					'Architecture': [ 'x86', 'powerpc' ],
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
					'Architecture': [ 'x86', 'powerpc' ],
					'Edition': [ 'oxae' ],
					'Active': [ ],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup'],
					'Description': _('Sync users and groups with Active Directory'),
				},
				{
					'Name': _('Bacula (Backup)'),
					'Packages': ['univention-bacula'],
					'Edition': [ 'oxae' ],
					'Architecture': [ 'x86' ],
					'Active': [],
					'Possible': ['all'],
					'Description': _('Network based Backup Software'),
				},
				{
					'Name': _('Open-Xchange'),
					'Packages': ['univention-ox', 'univention-ox-directory-integration', 'univention-oxae'],
					'Edition': [ 'oxae' ],
					'Architecture': [ 'x86' ],
					'Active': ['domaincontroller_master'],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver', 'Basis'],
					'Description': _('Open-Xchange Groupware Server'),
				},
				{
					'Name': _('Samba'),
					'Packages': ['univention-samba', 'samba', 'cups', 'cups-bsd', 'cups-client', 'cups-driver-gutenprint', 'foomatic-db-gutenprint', 'foomatic-db-hpijs', 'foomatic-filters-ppds'],
					'Edition': [ 'oxae' ],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['domaincontroller_master'],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver', 'basesystem'],
					'Description': _("Samba Services"),
				},
				{
					'Name': _('Terminal server'),
					'Packages': ['univention-application-server'],
					'Edition': [ 'scalix', 'ugs' ],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup'],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Description': _('X-Window-System Client for Terminal Services'),
				},
				{
					'Name': _('Thin client environment'),
					'Packages': ['univention-thin-client'],
					'Edition': [ 'scalix', 'ugs' ],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave'],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Description': _('Thinclient Infrastructure'),
				},
				{
					'Name': _('Print server'),
					'Packages': ['univention-printserver', 'cups'],
					'Edition': [ 'scalix', 'ugs' ],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Possible': ['all'],
					'Description': _('Print server based on cups'),
				},
				{
					'Name': _('Print quota'),
					'Packages': ['univention-printquota', 'pykota', 'univention-printquotadb'],
					'Edition': [ 'scalix', 'ugs' ],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Description': _('Print quota support based on pykota'),
				},
				{
					'Name': _('Nagios server'),
					'Packages': ['univention-nagios-server'],
					'Edition': [ 'scalix', 'ugs' ],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [ 'domaincontroller_master' ],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Description': _('Host, service and network monitoring program (server software)'),
				},
				{
					'Name': _('Nagios client'),
					'Packages': ['univention-nagios-client'],
					'Edition': [ 'scalix', 'ugs' ],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [ 'domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver' ],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver' ],
					'Description': _('Host, service and network monitoring program (client software)'),
				},
				{
					'Name': _('Fax server'),
					'Packages': ['univention-fax-server', 'univention-fax-client'],
					'Edition': [ 'scalix', 'ugs' ],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [ ],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Description': _('Fax server and client based on hylafax'),
				},
				{
					'Name': _('OpenSSH server'),
					'Packages': ['openssh-server'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [ 'all' ],
					'Possible': [ 'all' ],
					'Description': _("Secure shell server, an rshd replacement"),
				},
				{
					'Name': _('FreeNX server'),
					'Packages': ['freenx'],
					'Edition': [ 'scalix', 'ugs' ],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [ ],
					'Possible': ['all'],
					'Description': _('FreeNX application/thin-client server'),
				},

			],
},
{
	'Category': _('Virtualization'),
	'CategoryShow': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
	'Description': _('Xen Virtualization'),
	'Packages':
			[
				{
					'Name': _('Xen hypervisor (2.6.18)'),
					'Packages': ['univention-kernel-image-2.6.18-xen', 'univention-xen'],
					'Architecture': [ 'x86' ],
					'Edition': [ 'scalix', 'ugs' ],
					'Active': [ ],
					'Possible': ['all'],
					'Description': _('Xen hypervisor environment to run virtualised hosts.'),
				},
				{
					'Name': _('Xen hypervisor (2.6.32)'),
					'Packages': ['univention-kernel-image-2.6.32-xen', 'univention-xen'],
					'Architecture': [ 'x86' ],
					'Edition': [ 'scalix', 'ugs' ],
					'Active': [ ],
					'Possible': ['all'],
					'Description': _('Xen hypervisor environment to run virtualised hosts.'),
				},
				{
					'Name': _('Xen kernel images (2.6.18)'),
					'Packages': ['univention-kernel-image-2.6.18-xen'],
					'Architecture': [ 'x86' ],
					'Active': [ ],
					'Possible': ['all'],
					'Description': _('Xen kernel images for Xen guests.'),
				},
				{
					'Name': _('Xen kernel images (2.6.32)'),
					'Packages': ['univention-kernel-image-2.6.32-xen'],
					'Architecture': [ 'x86' ],
					'Active': [ ],
					'Possible': ['all'],
					'Description': _('Xen kernel images for Xen guests.'),
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
					'Packages': ['univention-directory-manager', 'python-univention-license'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup'],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup'],
					'Description': _('Univention Director Manager Web Frontend'),
				},
				{
					'Name': _('Univention Management Console'),
					'Packages': ['univention-management-console'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver', 'mobile_client', 'managed_client'],
					'Possible': ['all'],
					'Description': _('Configuration Frontend for Servers and Clients'),
				},
				{
					'Name': _('Univention Software Monitor'),
					'Packages': ['univention-pkgdb'],
					'Edition': [ 'scalix', 'ugs' ],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['domaincontroller_master'],
					'Possible': ['all'],
					'Description': _('Univention packagestatus database'),
				},
				{
					'Name': _('UCS Net Installer'),
					'Packages': ['univention-net-installer'],
					'Edition': [ 'scalix', 'ugs' ],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup'],
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
					'Edition': [ 'scalix', 'ugs' ],
					'Architecture': [ 'x86' ],
					'Active': [],
					'Possible': ['all'],
					'Description': _('Network based Backup Software'),
				},
				{
					'Name': _('Unidump'),
					'Packages': ['unidump'],
					'Edition': [ 'scalix', 'ugs' ],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [],
					'Possible': ['all'],
					'Description': _('Tape Backup Software'),
				},
				{
					'Name': _('Remote backup (for Unidump)'),
					'Packages': ['univention-remote-backup'],
					'Edition': [ 'scalix', 'ugs' ],
					'Architecture': [ 'x86', 'powerpc' ],
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
					'Packages': ['univention-x-core', 'univention-gdm', 'univention-gdm-sessions'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver', 'mobile_client', 'managed_client'],
					'Possible': ['all'],
					'Description': _('Core Packages for a Graphical Desktop Environment'),
				},
				{
					'Name': _('KDE desktop'),
					'Packages': ['univention-kde', 'ispell', 'ingerman', 'gimp', 'acroread-de'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver', 'mobile_client', 'managed_client'],
					'Possible': ['all'],
					'Description': _('KDE - K Desktop Environment'),
				},
				{
					'Name': _('KDE add-ons'),
					'Packages': ['k3b', 'k3b-i18n', 'cdrdao', 'kdeartwork-misc', 'kdeartwork-emoticons', 'kdeartwork-style', 'kdeartwork-theme-icon', 'kscreensaver', 'kdewallpapers', 'kdeartwork-theme-window', 'kamera', 'kfax', 'kpdf', 'kview', 'kuickshow', 'ksnapshot', 'kgpg', 'kpowersave', 'kwalletmanager', 'kdepim', 'kompose', 'kerry', 'amarok', 'kaffeine', 'kmplayer', 'kdemultimedia', 'mplayer'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver', 'mobile_client', 'managed_client'],
					'Possible': ['all'],
					'Description': _('Additional KDE applications like k3b, kamera, ...'),
				},
				{
					'Name': _('OpenOffice.org'),
					'Packages': ['univention-ooffice2', 'myspell-de-de'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver', 'mobile_client', 'managed_client'],
					'Possible': ['all'],
					'Description': _('OpenOffice.org is a full-featured office productivity suite.'),
				},
				{
					'Name': _('Mozilla Firefox'),
					'Packages': ['univention-mozilla-firefox'],
					'Architecture': [ 'x86' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver', 'mobile_client', 'managed_client'],
					'Possible': ['all'],
					'Description': _('Firefox Webbrowser'),
				},
				{
					'Name': "  %s" % _('Java plugin/runtime'),
					'Packages': ['univention-java'],
					'Architecture': [ 'x86' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver', 'mobile_client', 'managed_client'],
					'Possible': ['all'],
					'Description': _('Java Virtual Machine'),
				},
				{
					'Name': "  %s" %_('Flash plugin installer'),
					'Packages': ['univention-flashplugin'],
					'Architecture': [ 'x86' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver', 'mobile_client', 'managed_client'],
					'Possible': ['all'],
					'Description': _('Flashplugin for webbrowsers'),
				},
				{
					'Name': "  %s" %_('Mplayer plugin'),
					'Packages': ['mozilla-mplayer'],
					'Architecture': [ 'x86' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver', 'mobile_client', 'managed_client'],
					'Possible': ['all'],
					'Description': _('Mplayer for webbrowsers'),
				},
				{
					'Name': _('Microsoft fonts installer'),
					'Packages': ['msttcorefonts'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [ ],
					'Possible': [ 'all' ],
					'Description': _("Microsoft True Type Core fonts"),
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
					'Architecture': [ 'x86' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver', 'mobile_client', 'managed_client'],
					'Possible': ['all'],
					'Description': _('Java Virtual Machine'),
				},
				{
					'Name': _('Commandline tools'),
					'Packages': ['vim', 'emacs22', 'less', 'elinks', 'wget', 'nmap', 'zip', 'unzip', 'eject'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['all'],
					'Possible': [ 'all' ],
					'Description': _('Various commandline tools, like vim, less, nmap, ...'),
				},
			]

},
]
