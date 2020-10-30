# -*- coding: utf-8 -*-
#
# Univention Nagios
#  listener module: update configuration of local Nagios server
#
# Copyright 2004-2020 Univention GmbH
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

from __future__ import absolute_import
import listener
import os
import re
import pipes
import stat
import univention.debug as ud
import subprocess

name = 'nagios-server'
description = 'Create configuration for Nagios server'
filter = '(|(objectClass=univentionNagiosServiceClass)(objectClass=univentionNagiosTimeperiodClass)(objectClass=univentionHost))'

__predefinedTimeperiod = 'Univention-Predefined-24x7'
__fallbackContact = 'root@localhost'
__initscript = '/etc/init.d/nagios'

#
# /etc/nagios/conf.univention.d/services/<SERVICENAME>,<HOSTFQDN>.cfg
# /etc/nagios/conf.univention.d/hosts/<HOSTFQDN>.cfg
# /etc/nagios/conf.univention.d/hostgrps/<GRPNAME>.cfg
# /etc/nagios/conf.univention.d/contacts/<EMAILADDR>.cfg
# /etc/nagios/conf.univention.d/contactgrps/<HOSTFQDN>.cfg
# /etc/nagios/conf.univention.d/timeperiods/<PERIODNAME>.cfg
#

__confdir = '/etc/nagios/conf.univention.d/'
__confsubdirs = ['services', 'hosts', 'hostextinfo', 'hostgrps', 'contacts', 'contactgrps', 'timeperiods']

__servicesdir = __confdir + 'services/'
__hostsdir = __confdir + 'hosts/'
__hostextinfodir = __confdir + 'hostextinfo/'
__hostgrpsdir = __confdir + 'hostgrps/'
__contactsdir = __confdir + 'contacts/'
__contactgrpsdir = __confdir + 'contactgrps/'
__timeperiodsdir = __confdir + 'timeperiods/'

__exthostinfo_mapping = {
	'unknown': {
		'icon_image': 'univention/unknown.gif',
		'vrml_image': 'univention/unknown.gif',
		'statusmap_image': 'univention/unknown.gd2'
	},
	'ipmanagedclient': {
		'icon_image': 'univention/ipmanagedclient.gif',
		'vrml_image': 'univention/ipmanagedclient.gif',
		'statusmap_image': 'univention/ipmanagedclient.gd2'
	},
	'client': {
		'icon_image': 'univention/client.gif',
		'vrml_image': 'univention/client.gif',
		'statusmap_image': 'univention/client.gd2'
	},
	'macos': {
		'icon_image': 'univention/macos.gif',
		'vrml_image': 'univention/macos.gif',
		'statusmap_image': 'univention/macos.gd2'
	},
	'windows': {
		'icon_image': 'univention/windows.gif',
		'vrml_image': 'univention/windows.gif',
		'statusmap_image': 'univention/windows.gd2'
	},
	'memberserver': {
		'icon_image': 'univention/memberserver.gif',
		'vrml_image': 'univention/memberserver.gif',
		'statusmap_image': 'univention/memberserver.gd2'
	},
	'domaincontroller_master': {
		'icon_image': 'univention/domaincontroller_master.gif',
		'vrml_image': 'univention/domaincontroller_master.gif',
		'statusmap_image': 'univention/domaincontroller_master.gd2'
	},
	'domaincontroller_backup': {
		'icon_image': 'univention/domaincontroller_backup.gif',
		'vrml_image': 'univention/domaincontroller_backup.gif',
		'statusmap_image': 'univention/domaincontroller_backup.gd2'
	},
	'domaincontroller_slave': {
		'icon_image': 'univention/domaincontroller_slave.gif',
		'vrml_image': 'univention/domaincontroller_slave.gif',
		'statusmap_image': 'univention/domaincontroller_slave.gd2'
	},
}


__reload = False


def writeTimeperiod(filename, name, alias, periods):
	listener.setuid(0)
	try:
		fp = open(filename, 'w')
		fp.write('# Warning: This file is auto-generated and might be overwritten.\n')
		fp.write('#          Please use univention-directory-manager instead.\n')
		fp.write('# Warnung: Diese Datei wurde automatisch generiert und wird\n')
		fp.write('#          automatisch ueberschrieben. Bitte benutzen Sie\n')
		fp.write('#          stattdessen den Univention Directory Manager.\n')
		fp.write('\n')
		fp.write('define timeperiod {\n')
		fp.write('    timeperiod_name   %s\n' % name)
		fp.write('    alias             %s\n' % alias)

		if periods[0]:
			fp.write('    monday            %s\n' % periods[0])
		if periods[1]:
			fp.write('    tuesday           %s\n' % periods[1])
		if periods[2]:
			fp.write('    wednesday         %s\n' % periods[2])
		if periods[3]:
			fp.write('    thursday          %s\n' % periods[3])
		if periods[4]:
			fp.write('    friday            %s\n' % periods[4])
		if periods[5]:
			fp.write('    saturday          %s\n' % periods[5])
		if periods[6]:
			fp.write('    sunday            %s\n' % periods[6])
		fp.write('}\n')
		fp.close()

		ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-SERVER: timeperiod %s written' % name)
	finally:
		listener.unsetuid()


def handleTimeperiod(dn, new, old):
	conffilename = __timeperiodsdir + '%s.cfg'

	if old:
		filename = conffilename % old['cn'][0].decode('UTF-8')
		listener.setuid(0)
		try:
			if os.path.exists(filename):
				os.unlink(filename)
		finally:
			listener.unsetuid()

	if new:
		cn = new['cn'][0].decode('UTF-8')
		filename = conffilename % (cn,)
		listener.setuid(0)

		periods = new['univentionNagiosTimeperiod'][0].decode('UTF-8').split('#')

		writeTimeperiod(filename, cn, new['description'][0].decode('UTF-8'), periods)


def createDefaultTimeperiod():
	filename = __timeperiodsdir + __predefinedTimeperiod + '.cfg'
	if not os.path.exists(filename):
		periods = ['00:00-24:00', '00:00-24:00', '00:00-24:00', '00:00-24:00', '00:00-24:00', '00:00-24:00', '00:00-24:00']
		writeTimeperiod(filename, __predefinedTimeperiod, __predefinedTimeperiod, periods)


def hostDeleted(new, old):
	"""Checks if a host was enabled for Nagios services and has now been disabled or deleted.
	Returns True if deleted/deactivated and False if not"""

	if not new:
		# host object has been deleted
		return True
	if old and old.get('univentionNagiosEnabled', [b'0'])[0] == b'1':
		# old host object had enabled nagios support

		if not new.get('univentionNagiosEnabled', [b'0'])[0] == b'1':
			# new host object is not enabled ==> delete nagios host config
			return True
		if not new.get('aRecord'):
			# new host object contains no aRecord ==> delete nagios host config
			return True

	# host object seems to be ok
	return False


def createContact(contact):
	listener.setuid(0)
	try:
		filename = '%s%s.cfg' % (__contactsdir, contact)
		fp = open(filename, 'w')
		fp.write('# Warning: This file is auto-generated and might be overwritten.\n')
		fp.write('#          Please use univention-admin instead.\n')
		fp.write('# Warnung: Diese Datei wurde automatisch generiert und wird\n')
		fp.write('#          automatisch ueberschrieben. Bitte benutzen Sie\n')
		fp.write('#          stattdessen den Univention Admin.\n')
		fp.write('\n')
		fp.write('define contact {\n')
		fp.write('    contact_name                   %s\n' % contact)
		fp.write('    alias                          Kontakt %s\n' % contact)
		fp.write('    host_notification_period       %s\n' % __predefinedTimeperiod)
		fp.write('    service_notification_period    %s\n' % __predefinedTimeperiod)
		fp.write('    host_notification_options      d,u,r,f\n')
		fp.write('    service_notification_options   w,u,c,r,f\n')
		fp.write('    host_notification_commands     notify-host-by-email\n')
		fp.write('    service_notification_commands  notify-service-by-email\n')
		fp.write('    email                          %s\n' % contact)
		fp.write('}\n')
		fp.close()

		ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-SERVER: contact %s written' % contact)
	finally:
		listener.unsetuid()


def removeContactIfUnused(contact):
	contact_filename = os.path.join(__contactsdir, "%s.cfg" % contact)
	if os.path.exists(contact_filename):
		listener.setuid(0)
		try:
			# check if email address is still in use
			result = os.system('grep -c "%s" %s* 2> /dev/null > /dev/null' % (pipes.quote(contact), __contactgrpsdir))
			if result == 1:
				ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-SERVER: removing contact %s' % contact_filename)
				os.unlink(contact_filename)
			else:
				ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-SERVER: contact %s is in use' % contact_filename)
		finally:
			listener.unsetuid()


def createContactGroup(grpname, contactlist):
	listener.setuid(0)
	try:
		filename = '%s%s.cfg' % (__contactgrpsdir, grpname)
		fp = open(filename, 'w')
		fp.write('# Warning: This file is auto-generated and might be overwritten.\n')
		fp.write('#          Please use univention-admin instead.\n')
		fp.write('# Warnung: Diese Datei wurde automatisch generiert und wird\n')
		fp.write('#          automatisch ueberschrieben. Bitte benutzen Sie\n')
		fp.write('#          stattdessen den Univention Admin.\n')
		fp.write('\n')
		fp.write('define contactgroup {\n')
		fp.write('    contactgroup_name    %s\n' % grpname)
		fp.write('    alias                Gruppe %s\n' % grpname)
		fp.write('    members              %s\n' % ', '.join(contactlist))
		fp.write('}\n')
		fp.close()

		ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-SERVER: contactgroup %s written: members=%s' % (grpname, contactlist))
		# create missing contacts
		for contact in contactlist:
			if not os.path.exists(os.path.join(__contactsdir, '%s.cfg' % contact)):
				createContact(contact)

		# create default timeperiod if missing
		createDefaultTimeperiod()

	finally:
		listener.unsetuid()


def updateContactGroup(fqdn, new, old):
	cg_old = old.get('univentionNagiosEmail', [__fallbackContact.encode('UTF-8')])
	cg_new = new.get('univentionNagiosEmail', [__fallbackContact.encode('UTF-8')])

	if hostDeleted(new, old):
		# host deleted --> remove contact group

		cg_filename = os.path.join(__contactgrpsdir, 'cg-%s.cfg' % fqdn)
		if os.path.exists(cg_filename):
			listener.setuid(0)
			try:
				os.unlink(cg_filename)
			finally:
				listener.unsetuid()

		ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-SERVER: removed contactgroup for host %s' % fqdn)

		# remove old contacts if unused
		for contact in cg_old:
			removeContactIfUnused(contact.decode('UTF-8'))
	else:
		# host has been updated
		createContactGroup('cg-%s' % fqdn, [x.decode('UTF-8') for x in cg_new])

		ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-SERVER: wrote contactgroup for host %s' % fqdn)

		# find deleted contacts
		for contact in cg_old:
			if contact not in cg_new:
				removeContactIfUnused(contact.decode('UTF-8'))


def readHostGroup(grpname):
	grp_filename = os.path.join(__hostgrpsdir, '%s.cfg' % grpname)

	listener.setuid(0)
	try:
		if not os.path.exists(grp_filename):
			return []
		with open(grp_filename, 'r') as fp:
			content = fp.read()
		res = re.search(r'\W+members\W+(.*?)\W*$', content, re.MULTILINE)
		if res:
			return res.group(1).split(', ')
		return []
	finally:
		listener.unsetuid()


def writeHostGroup(grpname, members):
	grp_filename = os.path.join(__hostgrpsdir, '%s.cfg' % grpname)

	listener.setuid(0)
	try:
		fp = open(grp_filename, 'w')
		fp.write('define hostgroup {\n')
		fp.write('    hostgroup_name     %s\n' % grpname)
		fp.write('    alias              Hostgroup %s\n' % grpname)
		fp.write('    members            %s\n' % ', '.join(members))
		fp.write('}')
		fp.close()
	finally:
		listener.unsetuid()


def deleteHostGroup(grpname):
	grp_filename = os.path.join(__hostgrpsdir, '%s.cfg' % grpname)

	listener.setuid(0)
	try:
		if os.path.exists(grp_filename):
			os.unlink(os.path.join(__servicesdir, grp_filename))
	finally:
		listener.unsetuid()


def removeFromHostGroup(grpname, fqdn):
	old_members = readHostGroup(grpname)
	if old_members:
		new_members = [item for item in old_members if item != fqdn]

		if new_members:
			writeHostGroup(grpname, new_members)
		else:
			deleteHostGroup(grpname)


def addToHostGroup(grpname, fqdn):
	members = readHostGroup(grpname)
	if fqdn not in members:
		members.append(fqdn)
	writeHostGroup(grpname, members)


def handleService(dn, new, old):
	if old:
		listener.setuid(0)
		try:
			for fn in os.listdir(__servicesdir):
				if fn.find("%s," % old['cn'][0].decode('UTF-8')) == 0:
					os.unlink(os.path.join(__servicesdir, fn))
		finally:
			listener.unsetuid()

	if new:
		listener.setuid(0)
		try:
			for host in new.get('univentionNagiosHostname', []):
					new_cn = new['cn'][0].decode('UTF-8')
					filename = os.path.join(__servicesdir, '%s,%s.cfg' % (new_cn, host.decode('UTF-8')))
					fp = open(filename, 'w')
					fp.write('# Warning: This file is auto-generated and might be overwritten.\n')
					fp.write('#          Please use univention-admin instead.\n')
					fp.write('# Warnung: Diese Datei wurde automatisch generiert und wird\n')
					fp.write('#          automatisch ueberschrieben. Bitte benutzen Sie\n')
					fp.write('#          stattdessen den Univention Admin.\n')
					fp.write('\n')
					fp.write('define service {\n')
					fp.write('    host_name               %s\n' % host.decode('UTF-8'))
					fp.write('    service_description     %s\n' % new_cn)

					if new.get('univentionNagiosUseNRPE', [b''])[0] == b'1':
						fp.write('    check_command           check_nrpe_1arg!%s\n' % new_cn)
					else:
						if new.get('univentionNagiosCheckArgs', [b''])[0]:
							fp.write('    check_command           %s!%s\n' % (new['univentionNagiosCheckCommand'][0].decode('UTF-8'), new['univentionNagiosCheckArgs'][0].decode('UTF-8')))
						else:
							fp.write('    check_command           %s\n' % new['univentionNagiosCheckCommand'][0].decode('UTF-8'))

					fp.write('    normal_check_interval   %s\n' % new['univentionNagiosNormalCheckInterval'][0].decode('UTF-8'))
					fp.write('    retry_check_interval    %s\n' % new['univentionNagiosRetryCheckInterval'][0].decode('UTF-8'))
					fp.write('    max_check_attempts      %s\n' % new['univentionNagiosMaxCheckAttempts'][0].decode('UTF-8'))
					fp.write('    check_period            %s\n' % new['univentionNagiosCheckPeriod'][0].decode('UTF-8'))
					fp.write('    notification_interval   %s\n' % new['univentionNagiosNotificationInterval'][0].decode('UTF-8'))
					fp.write('    notification_period     %s\n' % new['univentionNagiosNotificationPeriod'][0].decode('UTF-8'))
					fp.write('    notification_options    %s\n' % new['univentionNagiosNotificationOptions'][0].decode('UTF-8'))
					fp.write('    contact_groups          cg-%s\n' % host)
					fp.write('}\n')
					fp.close()

					cg_filename = os.path.join(__contactgrpsdir, 'cg-%s.cfg' % host)
					if not os.path.exists(cg_filename):
						ud.debug(ud.LISTENER, ud.ERROR, 'NAGIOS-SERVER: handleService: contactgrp for host %s does not exist - using fallback' % host)

						createContactGroup('cg-%s' % host, [__fallbackContact])
						listener.setuid(0)

		finally:
			listener.unsetuid()


def getUniventionComputerType(new):
	if not new or 'objectClass' not in new:
		return 'unknown'

	if new and 'objectClass' in new:
		if b'univentionClient' in new['objectClass']:
			if b'posixAccount' in new['objectClass'] or b'shadowAccount' in new['objectClass']:
				return 'client'
			else:
				return 'ipmanagedclient'
		elif b'univentionMacOSClient' in new['objectClass']:
			return 'macos'
		elif b'univentionWindows' in new['objectClass']:
			return 'windows'
		elif b'univentionWindows' in new['objectClass']:
			return 'windows'
		elif b'univentionMemberServer' in new['objectClass']:
			return 'memberserver'
		elif b'univentionDomainController' in new['objectClass']:
			if 'univentionServerRole' in new:
				for role in [b'master', b'backup', b'slave']:
					if role in new['univentionServerRole']:
						return 'domaincontroller_%s' % role.decode('UTF-8')
	return 'unknown'


def createHostExtInfo(fqdn, new):
	fn = os.path.join(__hostextinfodir, '%s.cfg' % fqdn)

	if new:
		hosttype = getUniventionComputerType(new)
		if hosttype not in __exthostinfo_mapping:
			ud.debug(ud.LISTENER, ud.ERROR, 'NAGIOS-SERVER: createHostExtInfo: unknown host type "%s" of %s' % (hosttype, fqdn))
			return

		listener.setuid(0)
		try:
			fp = open(fn, 'w')
			fp.write('# Warning: This file is auto-generated and might be overwritten.\n')
			fp.write('#          Please use univention-admin instead.\n')
			fp.write('# Warnung: Diese Datei wurde automatisch generiert und wird\n')
			fp.write('#          automatisch ueberschrieben. Bitte benutzen Sie\n')
			fp.write('#          stattdessen den Univention Admin.\n')
			fp.write('\n')
			fp.write('define hostextinfo {\n')
			fp.write('    host_name               %s\n' % fqdn)
			fp.write('    icon_image              %s\n' % __exthostinfo_mapping[hosttype]['icon_image'])
			fp.write('    vrml_image              %s\n' % __exthostinfo_mapping[hosttype]['vrml_image'])
			fp.write('    statusmap_image         %s\n' % __exthostinfo_mapping[hosttype]['statusmap_image'])
			fp.write('}\n')
			fp.close()

		finally:
			listener.unsetuid()

		ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-SERVER: extended info for host %s written' % fqdn)


def removeHostExtInfo(fqdn):
	fn = os.path.join(__hostextinfodir, '%s.cfg' % fqdn)
	if os.path.exists(fn):
		listener.setuid(0)
		try:
			os.unlink(fn)
		finally:
			listener.unsetuid()


def removeHost(fqdn):
	fn = os.path.join(__hostsdir, '%s.cfg' % fqdn)
	if os.path.exists(fn):
		listener.setuid(0)
		try:
			os.unlink(fn)
		finally:
			listener.unsetuid()


def handleHost(dn, new, old):
	# avoid additional ldap requests - building fqdn by combining "cn" and baseconfig variable "domainname"
	host = ''
	oldfqdn = 'unknown'
	newfqdn = 'unknown'

	olddomain = listener.configRegistry['domainname']
	if old and 'associatedDomain' in old and old['associatedDomain']:
		olddomain = old['associatedDomain'][0].decode('ASCII')
	if old:
		if 'cn' in old and old['cn']:
			host = old['cn'][0].decode('UTF-8')
			oldfqdn = host + '.' + olddomain
		else:
			ud.debug(ud.LISTENER, ud.ERROR, 'NAGIOS-SERVER: unable to determine old fqdn for %s' % str(dn))
			host = 'unknown'
			oldfqdn = host + '.unknown'
	old_host_filename = os.path.join(__hostsdir, '%s.cfg' % oldfqdn)

	newdomain = listener.configRegistry['domainname']
	if new and 'associatedDomain' in new and new['associatedDomain']:
		newdomain = new['associatedDomain'][0].decode('ASCII')
	if new:
		if 'cn' in new and new['cn']:
			host = new['cn'][0].decode('UTF-8')
			newfqdn = host + '.' + newdomain
		else:
			ud.debug(ud.LISTENER, ud.ERROR, 'NAGIOS-SERVER: unable to determine new fqdn for %s' % str(dn))
			host = 'unknown'
			newfqdn = host + '.unknown'
	new_host_filename = os.path.join(__hostsdir, '%s.cfg' % newfqdn)

	# determine grpname
	# default: AllHosts
	# if host object resides within ou or container then parts of ou/container's dn is used as groupname
	grpname = 'AllHosts'
	ldapbase = listener.configRegistry['ldap/base']
	result = re.search('^cn=%s(,.*?)?,%s$' % (host, ldapbase), dn)
	if result and result.group(1):
		grpname = re.sub(r',\w+=', '_', result.group(1))[1:]

	# fqdn changed ==> remove old entry and create new ones
	if oldfqdn != newfqdn and new and old:
		listener.setuid(0)
		try:
			if os.path.exists(old_host_filename):
				os.unlink(old_host_filename)
		finally:
			listener.unsetuid()
		ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-SERVER: fqdn changed: host %s deleted' % oldfqdn)

		# remove contact group and contacts
		updateContactGroup(oldfqdn, {}, old)

		# remove host from hostgroup
		removeFromHostGroup(grpname, oldfqdn)

		# remove ext host info
		removeHostExtInfo(oldfqdn)

	# check if host has been deleted or nagios support disabled
	if hostDeleted(new, old):
		listener.setuid(0)
		try:
			if os.path.exists(old_host_filename):
				os.unlink(old_host_filename)
		finally:
			listener.unsetuid()
		ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-SERVER: host %s deleted' % oldfqdn)

		# remove contact group and contacts
		updateContactGroup(oldfqdn, new, old)

		# remove host from hostgroup
		removeFromHostGroup(grpname, oldfqdn)

		removeHostExtInfo(oldfqdn)

		removeHost(oldfqdn)

	elif new:
		if not ('aRecord' in new and new['aRecord']):
			ud.debug(ud.LISTENER, ud.ERROR, 'NAGIOS-SERVER: missing aRecord (%s)' % dn)
			return

		listener.setuid(0)
		try:
			fp = open(new_host_filename, 'w')
			fp.write('# Warning: This file is auto-generated and might be overwritten.\n')
			fp.write('#          Please use univention-admin instead.\n')
			fp.write('# Warnung: Diese Datei wurde automatisch generiert und wird\n')
			fp.write('#          automatisch ueberschrieben. Bitte benutzen Sie\n')
			fp.write('#          stattdessen den Univention Admin.\n')
			fp.write('\n')
			fp.write('define host {\n')
			fp.write('    host_name               %s\n' % newfqdn)
			if 'description' in new and new['description']:
				fp.write('    alias                   %s (%s)\n' % (newfqdn, new['description'][0].decode('UTF-8')))
			else:
				fp.write('    alias                   %s\n' % newfqdn)
			fp.write('    address                 %s\n' % new['aRecord'][0].decode('ASCII'))
			if 'univentionNagiosParent' in new and new['univentionNagiosParent']:
				fp.write('    parents                 %s\n' % b', '.join(new['univentionNagiosParent']).decode('UTF-8'))

			if listener.configRegistry.is_true("nagios/server/hostcheck/enable", False):
				fp.write('    check_command           check-host-alive\n')

			fp.write('    max_check_attempts      10\n')
			fp.write('    contact_groups          cg-%s\n' % newfqdn)

			notification_interval = 0
			if "nagios/server/hostcheck/notificationinterval" in listener.configRegistry and listener.configRegistry["nagios/server/hostcheck/notificationinterval"]:
				notification_interval = listener.configRegistry["nagios/server/hostcheck/notificationinterval"]

			fp.write('    notification_interval   %s\n' % notification_interval)
			fp.write('    notification_period     %s\n' % __predefinedTimeperiod)
			fp.write('    notification_options    d,u,r\n')
			fp.write('}\n')
			fp.close()

		finally:
			listener.unsetuid()

		ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-SERVER: host %s written' % newfqdn)

		if oldfqdn == newfqdn:
			updateContactGroup(newfqdn, new, old)
		else:
			updateContactGroup(newfqdn, new, {})

		addToHostGroup(grpname, newfqdn)

		createHostExtInfo(newfqdn, new)


def handler(dn, new, old):
	global __reload

#	ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-SERVER: IN dn=%s' % str(dn))
#	ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-SERVER: IN old=%s' % str(old))
#	ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-SERVER: IN new=%s' % str(new))

	if b'univentionNagiosServiceClass' in old.get('objectClass', []) or b'univentionNagiosServiceClass' in new.get('objectClass', []):
		handleService(dn, new, old)
		__reload = True

	elif b'univentionNagiosHostClass' in old.get('objectClass', []) or b'univentionNagiosHostClass' in new.get('objectClass', []):
		# check if the nagios related attributes were changed
		for attr in ['aRecord', 'associatedDomain', 'uid', 'cn', 'description', 'univentionNagiosParent', 'univentionNagiosEnabled', 'univentionNagiosEmail']:
			if not (new.get(attr, None) == old.get(attr, None)):
				handleHost(dn, new, old)
				__reload = True
				break

	elif b'univentionNagiosTimeperiodClass' in old.get('objectClass', []) or b'univentionNagiosTimeperiodClass' in new.get('objectClass', []):
		handleTimeperiod(dn, new, old)
		__reload = True


def initialize():
	dirs = ['']
	dirs.extend(__confsubdirs)

	for dirname in dirs:
		dirname = os.path.join('/etc/nagios/conf.univention.d', dirname)
		ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-SERVER: creating dir: %s' % dirname)
		if not os.path.exists(dirname):
			listener.setuid(0)
			try:
				os.mkdir(dirname)
			finally:
				listener.unsetuid()


def deleteTree(dirname):
	if os.path.exists(dirname):
		for f in os.listdir(dirname):
			fn = os.path.join(dirname, f)
			mode = os.stat(fn)[stat.ST_MODE]
			if stat.S_ISDIR(mode):
				deleteTree(fn)
			else:
				os.unlink(fn)
		os.rmdir(dirname)


def clean():
	dirname = '/etc/nagios/conf.univention.d'
	if os.path.exists(dirname):
		listener.setuid(0)
		try:
			deleteTree(dirname)
		finally:
			listener.unsetuid()


def postrun():
	global __reload

	if __reload:
		initscript = __initscript
		# restart nagios if not running and nagios/server/autostart is set to yes/true/1
		# otherwise if nagios is running, ask nagios to reload config
		p = subprocess.Popen(('pidof', '/usr/sbin/nagios'), stdout=subprocess.PIPE)
		pidlist, stderr = p.communicate()
		listener.setuid(0)
		null = open(os.path.devnull, 'w')
		try:
			retcode = subprocess.call(('nagios', '-v', '/etc/nagios/nagios.cfg'), stdout=null, stderr=null)
		finally:
			null.close()
		listener.unsetuid()
		if not pidlist.strip():
			if retcode == 0:
				if listener.configRegistry.is_true("nagios/server/autostart", False):
					ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-SERVER: nagios not running - restarting server')

					listener.setuid(0)
					try:
						listener.run(initscript, ['nagios', 'restart'], uid=0)
					finally:
						listener.unsetuid()
			else:
				ud.debug(ud.LISTENER, ud.ERROR, 'NAGIOS-SERVER: nagios reported an error in configfile /etc/nagios/nagios.cfg. Please restart nagios manually: "%s restart".' % initscript)
				listener.unsetuid()

		else:
			if retcode == 0:
				ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-SERVER: reloading server')
				listener.setuid(0)
				try:
					listener.run(initscript, ['nagios', 'reload'], uid=0)
				finally:
					listener.unsetuid()
			else:
				ud.debug(ud.LISTENER, ud.ERROR, 'NAGIOS-SERVER: nagios reported an error in configfile /etc/nagios/nagios.cfg. Please restart nagios manually: "%s restart".' % initscript)
				listener.unsetuid()
		__reload = False
