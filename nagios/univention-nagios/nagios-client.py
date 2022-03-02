# -*- coding: utf-8 -*-
#
# Univention Nagios
#  listener module: update configuration of local Nagios client
#
# Copyright 2004-2022 Univention GmbH
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
import stat
import univention.debug

name = 'nagios-client'
description = 'Create configuration for Nagios nrpe server'
filter = '(objectClass=univentionNagiosServiceClass)'

__initscript = '/etc/init.d/nagios-nrpe-server'
__confdir = '/etc/nagios/nrpe.univention.d/'
__pluginconfdir = '/etc/nagios-plugins/config/'

__pluginconfdirstat = 0
__pluginconfig = {}


def readPluginConfig():
	# type: () -> None
	global __pluginconfdirstat

	if __pluginconfdirstat != os.stat(__pluginconfdir)[8]:
		# save modification time
		__pluginconfdirstat = os.stat(__pluginconfdir)[8]

		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'NAGIOS-CLIENT: updating plugin config')

		listener.setuid(0)
		try:
			for fn in os.listdir(__pluginconfdir):
				with open(os.path.join(__pluginconfdir, fn), 'rb') as fp:
					content = fp.read()
				for cmddef in re.split(r'\s*define\s+command\s*\{'.encode('ASCII'), content):
					mcmdname = re.search(r'^\s+command_name\s+(.*?)\s*$'.encode('ASCII'), cmddef, re.MULTILINE)
					mcmdline = re.search(r'^\s+command_line\s+(.*?)\s*$'.encode('ASCII'), cmddef, re.MULTILINE)
					if mcmdname and mcmdline:
						__pluginconfig[mcmdname.group(1)] = mcmdline.group(1)
						univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'NAGIOS-CLIENT: read configline for plugin %s ==> %s' % (mcmdname.group(1), mcmdline.group(1)))
		finally:
			listener.unsetuid()


def replaceArguments(cmdline, args):
	# type: (str, list) -> str
	for i in range(9):
		if i < len(args):
			cmdline = re.sub(r'\$ARG%d\$'.encode('ASCII') % (i + 1), args[i], cmdline)
		else:
			cmdline = re.sub(r'\$ARG%d\$'.encode('ASCII') % (i + 1), b'', cmdline)
	return cmdline


def writeConfig(fqdn, new):
	# type: (str, dict) -> None
	readPluginConfig()

	name = new['cn'][0].decode('UTF-8')
	cmdline = b'PluginNameNotFoundError'

	# if no univentionNagiosHostname is present or current host is no member then quit
	if 'univentionNagiosHostname' in new and new['univentionNagiosHostname']:
		if fqdn not in new['univentionNagiosHostname']:
			return
	else:
		return

	if 'univentionNagiosCheckCommand' in new and new['univentionNagiosCheckCommand'] and new['univentionNagiosCheckCommand'][0]:
		if new['univentionNagiosCheckCommand'][0] in __pluginconfig:
			cmdline = __pluginconfig[new['univentionNagiosCheckCommand'][0]]
	if 'univentionNagiosCheckArgs' in new and new['univentionNagiosCheckArgs'] and new['univentionNagiosCheckArgs'][0]:
		cmdline = replaceArguments(cmdline, new['univentionNagiosCheckArgs'][0].split(b'!'))
	cmdline = re.sub(r'\$HOSTADDRESS\$'.encode('ASCII'), fqdn, cmdline)
	cmdline = re.sub(r'\$HOSTNAME\$'.encode('ASCII'), fqdn, cmdline)

	listener.setuid(0)
	try:
		filename = os.path.join(__confdir, "%s.cfg" % name)
		fp = open(filename, 'w')
		fp.write('# Warning: This file is auto-generated and might be overwritten.\n')
		fp.write('#          Please use univention-directory-manager instead.\n')
		fp.write('# Warnung: Diese Datei wurde automatisch generiert und wird\n')
		fp.write('#          automatisch ueberschrieben. Bitte benutzen Sie\n')
		fp.write('#          stattdessen den Univention Directory Manager.\n')
		fp.write('\n')
		fp.write('command[%s]=%s\n' % (name, cmdline))
		fp.close()

		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'NAGIOS-CLIENT: service %s written' % name)
	finally:
		listener.unsetuid()


def removeConfig(name):
	# type: (str) -> None
	filename = os.path.join(__confdir, "%s.cfg" % name)
	listener.setuid(0)
	try:
		if os.path.exists(filename):
			os.unlink(filename)
	finally:
		listener.unsetuid()


def handler(dn, new, old):
	# type: (str, dict, dict) -> None
	# univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'NAGIOS-CLIENT: IN dn=%r' % (dn,))
	# univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'NAGIOS-CLIENT: IN old=%r' % (old,))
	# univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'NAGIOS-CLIENT: IN new=%r' % (new,))

	fqdn = '%s.%s' % (listener.configRegistry['hostname'], listener.configRegistry['domainname'])
	fqdn = fqdn.encode('UTF-8')

	if old and not new:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'NAGIOS-CLIENT: service %r deleted' % (old['cn'][0],))
		removeConfig(old['cn'][0].decode('UTF-8'))

	if old and \
		fqdn in old.get('univentionNagiosHostname', []) and \
		fqdn not in new.get('univentionNagiosHostname', []):
		# object changed and
		# local fqdn was in old object and
		# local fqdn is not in new object
		# ==> fqdn was deleted from list
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'NAGIOS-CLIENT: host removed from service %s' % (old['cn'][0],))
		removeConfig(old['cn'][0].decode('UTF-8'))
	elif old and \
		old.get('univentionNagiosUseNRPE', [None])[0] == b'1' and \
		new.get('univentionNagiosUseNRPE', [None])[0] != b'1':
		# object changed and
		# local fqdn is in new object  (otherwise previous if-statement matches)
		# NRPE was enabled in old object
		# NRPE is disabled in new object
		# ==> remove config
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'NAGIOS-CLIENT: nrpe disabled for service %r' % (old['cn'][0],))
		removeConfig(old['cn'][0].decode('UTF-8'))
	else:
		# otherwise:
		# - this host was configure in old and new object or
		# - this host is newly added to list or
		# - this object is new
		if 'univentionNagiosUseNRPE' in new and new['univentionNagiosUseNRPE'] and (new['univentionNagiosUseNRPE'][0] == b'1'):
			univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'NAGIOS-CLIENT: writing service %r' % (new['cn'][0],))
			writeConfig(fqdn, new)


def initialize():
	# type: () -> None
	dirname = '/etc/nagios/nrpe.univention.d'

	if not os.path.exists(dirname):
		listener.setuid(0)
		try:
			os.mkdir(dirname)
		finally:
			listener.unsetuid()


def deleteTree(dirname):
	# type: (str) -> None
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
	# type: () -> None
	dirname = '/etc/nagios/nrpe.univention.d'
	if os.path.exists(dirname):
		listener.setuid(0)
		try:
			deleteTree(dirname)
		finally:
			listener.unsetuid()


def postrun():
	# type: () -> None
	global __initscript
	initscript = __initscript
	if listener.configRegistry.is_true("nagios/client/autostart"):
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'NRPED: Restarting server')
		listener.setuid(0)
		try:
			listener.run(initscript, ['nagios-nrpe-server', 'restart'], uid=0)
		finally:
			listener.unsetuid()
