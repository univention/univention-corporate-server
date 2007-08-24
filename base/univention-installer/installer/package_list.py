#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Installer
#  definitions of package lists
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
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
	'Description': _("Windows Components"),
	'Packages':
			[
				{
					'Name': _('Samba'),
					'Packages': ['univention-samba', 'samba'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver', 'basesystem'],
					'Description': _("Samba Services"),
				},
				{
					'Name': _('Windows Installer 4'),
					'Packages': ['univention-windows-installer'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave' ],
					'Description': _("Automatic Installation for Windows Clients"),
				},
				{
					'Name': _('DC Slave as Samba PDC'),
					'Packages': ['univention-samba-slave-pdc'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [],
					'Possible': ['domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Description': _("Samba as PDC on a DC Slave"),
				},
				{
					'Name': _('Winbind'),
					'Packages': ['winbind'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [ 'memberserver' ],
					'Possible': ['all'],
					'Description': _("Winbind Service"),
				},
			],
},
{
	'Category': _('Mail/Groupware'),
	'CategoryShow': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave' ],
	'Description': _('Mail/Groupware Component'),
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
					'Name': _('UGS Server'),
					'Packages': ['univention-kolab2', 'univention-kolab2-framework', 'univention-mail-postfix-kolab2', 'univention-mail-cyrus-kolab2'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Edition': [ 'ugs' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave' ],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave'],
					'Description': _('Groupware based on Kolab2'),
				},
				{
					'Name': _('UGS Webclient'),
					'Packages': ['univention-groupware-webclient'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [], 
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave'],
					'Description': _('Horde Webclient for UGS'),
				},
				{
					'Name': _('Mail Services (smtp/pop/imap)'),
					'Packages': ['univention-mail-postfix', 'univention-mail-cyrus'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [''], 
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver', 'Basis'],
					'Description': _('Standard Mail Services'),
				},
			],
},
{
	'Category': _('IP Management'),
	'CategoryShow': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
	'Description': _("Several IP Components"),
	'Packages':
			[
				{
					'Name': _('DNS'),
					'Packages': ['univention-bind', 'univention-bind-proxy', 'bind9'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave'],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave'],
					'Description': _("DNS Server and Proxy"),
				},
				{
					'Name': _('DHCP'),
					'Packages': ['univention-dhcp', 'dhcp3-server'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave'],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Description': _("DHCP Server"),
				},

			],
},
{
	'Category': _('Services'),
	'CategoryShow': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
	'Description': _("Additional Services"),
	'Packages':
			[
				{
					'Name': _('Terminalserver'),
					'Packages': ['univention-application-server'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup'],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Description': _('X-Window-System Client for Terminal Services'),
				},
				{
					'Name': _('Thinclient Environment'),
					'Packages': ['univention-thin-client'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup'],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Description': _('ThinClient Interface'),
				},
				{
					'Name': _('Print Server'),
					'Packages': ['univention-printserver', 'cupsys'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Possible': ['all'],
					'Description': _('Print Server'),
				},
				{
					'Name': _('Print Quota'),
					'Packages': ['univention-printquota', 'pykota', 'univention-printquotadb'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Possible': ['all'],
					'Description': _('Print Quota Support'),
				},
				{
					'Name': _('Nagios Server'),
					'Packages': ['univention-nagios-server'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [ 'domaincontroller_master' ],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Description': _('Host, service and network monitoring program '),
				},
				{
					'Name': _('Nagios Client'),
					'Packages': ['univention-nagios-client'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [ 'domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver' ],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver' ],
					'Description': _('Host, service and network monitoring program '),
				},
				{
					'Name': _('Univention AD Connector'),
					'Packages': ['univention-ad-connector'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [ ],
					'Possible': ['domaincontroller_master', 'domaincontroller_backup'],
					'Description': _('Sync users and groups with Active Directory'),
				},
				{
					'Name': _('Fax Server'),
					'Packages': ['univention-fax-server'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [ ],
					'Possible': ['all'],
					'Description': _('Fax Server'),
				},
				{
					'Name': _('Squid Proxyserver'),
					'Packages': ['univention-squid', 'squid'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [ ],
					'Possible': ['all'],
					'Description': _('Web Proxy Services'),
				},
				{
					'Name': _('OpenSSH Server'),
					'Packages': ['openssh-server'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [ 'all' ],
					'Possible': [ 'all' ],
					'Description': _("Secure shell server, an rshd replacemen"),
				},
				{
					'Name': _('FreeNX Server'),
					'Packages': ['freenx'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [ ],
					'Possible': ['all'],
					'Description': _('FreeNX Server'),
				},
				{
					'Name': _('VNC Server'),
					'Packages': ['tightvncserver', 'univention-fonts'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [  ],
					'Possible': [ 'all' ],
					'Description': _("Server for remote desktop access"),
				},
				{
					'Name': _('Network Installer'),
					'Packages': ['univention-net-installer'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup'],
					'Possible': ['all'],
					'Description': _('Install UCS over the network'),
				},
			],
},
{
	'Category': _('Administration'),
	'CategoryShow': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
	'Description': _('Administration Tools'),
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
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['domaincontroller_master'],
					'Possible': ['all'],
					'Description': _('Univention packagestatus database'),
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
					'Name': _('Unidump'),
					'Packages': ['unidump'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [],
					'Possible': ['all'],
					'Description': _('Tape Backup Software'),
				},
				{
					'Name': _('Remote Backup'),
					'Packages': ['univention-remote-backup'],
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
					'Name': _('Graphical User Interface'),
					'Packages': ['univention-x-core', 'univention-gdm', 'univention-gdm-sessions'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver', 'mobile_client', 'managed_client'],
					'Possible': ['all'],
					'Description': _('Core Packages for a Graphical Desktop Environment'),
				},
				{
					'Name': _('KDE Desktop'),
					'Packages': ['univention-kde', 'ispell', 'ingerman'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'mobile_client', 'managed_client'],
					'Possible': ['all'],
					'Description': _('KDE - K Desktop Environment'),
				},
				{
					'Name': _('OpenOffice.org'),
					'Packages': ['univention-ooffice2', 'hunspell-de-de'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['mobile_client', 'managed_client'],
					'Possible': ['all'],
					'Description': _('OpenOffice.org Office Suite'),
				},
				{
					'Name': _('Mozilla Firefox'),
					'Packages': ['univention-mozilla-firefox'],
					'Architecture': [ 'x86' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'mobile_client', 'managed_client'],
					'Possible': ['all'],
					'Description': _('Firefox Webbrowser'),
				},
				{
					'Name': "  %s" % _('Java Plugin/Runtime'),
					'Packages': ['univention-java'],
					'Architecture': [ 'x86' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'mobile_client', 'managed_client'],
					'Possible': ['all'],
					'Description': _('Java Virtual Machine'),
				},
				{
					'Name': "  %s" %_('Flash Plugin'),
					'Packages': ['univention-flashplugin'],
					'Architecture': [ 'x86' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'mobile_client', 'managed_client'],
					'Possible': ['all'],
					'Description': _('Flashplugin for webbrowsers'),
				},
				{
					'Name': "  %s" %_('Mplayer Plugin'),
					'Packages': ['mozilla-mplayer'],
					'Architecture': [ 'x86' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'mobile_client', 'managed_client'],
					'Possible': ['all'],
					'Description': _('Mplayer for webbrowsers'),
				},
				{
					'Name': _('Gimp'),
					'Packages': ['gimp'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['mobile_client', 'managed_client'],
					'Possible': ['all'],
					'Description': _('Gimp'),
				},
				{
					'Name': _('Acrobat Reader'),
					'Packages': ['acroread-de'],
					'Architecture': [ 'x86' ],
					'Active': ['mobile_client', 'managed_client'],
					'Possible': ['all'],
					'Description': _('PDF Viewer'),
				},
				{
					'Name': _('Additional KDE Applications'),
					'Packages': ['k3b', 'k3b-i18n', 'cdrdao', 'kdeartwork-misc', 'kdeartwork-emoticons', 'kdeartwork-style', 'kdeartwork-theme-icon', 'kscreensaver', 'kdewallpapers', 'kdeartwork-theme-window', 'kamera', 'kfax', 'kpdf', 'kview', 'kuickshow', 'ksnapshot', 'ark', 'kcalc', 'kgpg', 'klaptopdaemon', 'kwalletmanager', 'kdepim' ],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'mobile_client', 'managed_client'],
					'Possible': ['all'],
					'Description': _('More KDE applications, like k3b, kdegraphics, kdeadmin, kdeartwork, kdetoys or kdeutils'),
				},
				{
					'Name': _('Desktop Search (kerry/beagle)'),
					'Packages': ['kerry' ],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['mobile_client', 'managed_client'],
					'Possible': ['all'],
					'Description': _('Desktop Search with kerry and beagle'),
				},
				{
					'Name': _('Multimedia Applications'),
					'Packages': ['amarok', 'kaffeine', 'kmplayer', 'kdemultimedia', 'mplayer'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'mobile_client', 'managed_client'],
					'Possible': ['all'],
					'Description': _('Multimedia applications, like amarok, kmplayer or mplayer'),
				},
				{
					'Name': _('Fax Client'),
					'Packages': ['univention-fax-client'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [],
					'Possible': ['all'],
					'Description': _('Fax Client'),
				},
				{
					'Name': _('Evolution'),
					'Packages': ['evolution'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [''],
					'Possible': ['all'],
					'Description': _('The GNOME Mailer'),
				},
				{
					'Name': _('VNC Viewer'),
					'Packages': ['xtightvncviewer'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [ 'all' ],
					'Possible': [ 'all' ],
					'Description': _("Client for remote desktop Access"),
				},
				{
					'Name': _('Microsoft Fonts'),
					'Packages': ['msttcorefonts'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [ ],
					'Possible': [ 'all' ],
					'Description': _("Microsoft Fonts"),
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
					'Name': _('OpenSSH client'),
					'Packages': ['openssh-client'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [ 'all' ],
					'Possible': [ 'all' ],
					'Description': _("Secure shell client, an rlogin/rsh/rcp replacement"),
				},
				{
					'Name': _('dhcp client'),
					'Packages': ['dhcp3-client'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['mobile_client', 'managed_client'],
					'Possible': [ 'all' ],
					'Description': _("Dynamic IP configuration"),
				},
				{
					'Name': _('vim'),
					'Packages': ['vim'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [ 'all' ],
					'Possible': [ 'all' ],
					'Description': _("Vi IMproved - enhanced vi editor"),
				},
				{
					'Name': _('emacs'),
					'Packages': ['emacs21'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [ '' ],
					'Possible': [ 'all' ],
					'Description': _("The GNU Emacs editor"),
				},
				{
					'Name': _('less'),
					'Packages': ['less'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['all'],
					'Possible': ['all'],
					'Description': _('Pager program similar to more'),
				},
				{
					'Name': _('elinks'),
					'Packages': ['elinks'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': [],
					'Possible': ['all'],
					'Description': _('Advanced text-mode WWW browser'),
				},
				{
					'Name': _('wget'),
					'Packages': ['wget'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['all'],
					'Possible': ['all'],
					'Description': _('Retrieves files from the web'),
				},
				{
					'Name': _('nmap'),
					'Packages': ['nmap'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'],
					'Possible': ['all'],
					'Description': _('The Network Mapper'),
				},
				{
					'Name': _('zip/unzip'),
					'Packages': ['zip', 'unzip'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['all'],
					'Possible': ['all'],
					'Description': _('The Network Mapper'),
				},
				{
					'Name': _('eject'),
					'Packages': ['eject'],
					'Architecture': [ 'x86', 'powerpc' ],
					'Active': ['all'],
					'Possible': ['all'],
					'Description': _('ejects CDs and operates CD-Changers under Linux'),
				},
				{
					'Name': _('Java'),
					'Packages': ['univention-java'],
					'Architecture': [ 'x86' ],
					'Active': ['domaincontroller_master', 'domaincontroller_backup', 'mobile_client', 'managed_client'],
					'Possible': ['all'],
					'Description': _('Java Virtual Machine'),
				},
			]

},
]
