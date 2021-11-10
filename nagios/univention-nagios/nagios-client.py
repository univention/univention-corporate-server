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

import os
import re
import stat

import univention.debug as ud

from listener import SetUID, configRegistry, run

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

		ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-CLIENT: updating plugin config')

		with SetUID(0):
			for fn in os.listdir(__pluginconfdir):
				with open(os.path.join(__pluginconfdir, fn), 'rb') as fp:
					content = fp.read().decode('UTF-8', 'replace')
				for cmddef in re.split(r'\s*define\s+command\s*\{', content):
					mcmdname = re.search(r'^\s+command_name\s+(.*?)\s*$', cmddef, re.MULTILINE)
					mcmdline = re.search(r'^\s+command_line\s+(.*?)\s*$', cmddef, re.MULTILINE)
					if mcmdname and mcmdline:
						__pluginconfig[mcmdname.group(1)] = mcmdline.group(1)
						ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-CLIENT: read configline for plugin %r ==> %r' % (mcmdname.group(1), mcmdline.group(1)))


def replaceArguments(cmdline, args):
	# type: (str, list) -> str
	for i in range(9):
		if i < len(args):
			cmdline = re.sub(r'\$ARG%d\$' % (i + 1), args[i], cmdline)
		else:
			cmdline = re.sub(r'\$ARG%d\$' % (i + 1), b'', cmdline)
	return cmdline


def writeConfig(fqdn, new):
	# type: (str, dict) -> None
	readPluginConfig()

	name = new['cn'][0].decode('UTF-8')
	cmdline = 'PluginNameNotFoundError'

	# if no univentionNagiosHostname is present or current host is no member then quit
	if fqdn.encode('UTF-8') not in new.get('univentionNagiosHostname', []):
		return

	nagios_check_command = new.get('univentionNagiosCheckCommand', [b''])[0].decode('UTF-8')
	cmdline = __pluginconfig.get(nagios_check_command, cmdline)
	if new.get('univentionNagiosCheckArgs', [b''])[0]:
		cmdline = replaceArguments(cmdline, new['univentionNagiosCheckArgs'][0].decode('UTF-8').split('!'))
	cmdline = re.sub(r'\$HOSTADDRESS\$', fqdn, cmdline)
	cmdline = re.sub(r'\$HOSTNAME\$', fqdn, cmdline)

	filename = os.path.join(__confdir, "%s.cfg" % name)
	with SetUID(0), open(filename, 'w') as fp:
		fp.write('# Warning: This file is auto-generated and might be overwritten.\n')
		fp.write('#          Please use univention-directory-manager instead.\n')
		fp.write('# Warnung: Diese Datei wurde automatisch generiert und wird\n')
		fp.write('#          automatisch ueberschrieben. Bitte benutzen Sie\n')
		fp.write('#          stattdessen den Univention Directory Manager.\n')
		fp.write('\n')
		fp.write('command[%s]=%s\n' % (name, cmdline))
	ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-CLIENT: service %s written' % name)


def removeConfig(name):
	# type: (str) -> None
	filename = os.path.join(__confdir, "%s.cfg" % name)
	with SetUID(0):
		if os.path.exists(filename):
			os.unlink(filename)


def handler(dn, new, old):
	# type: (str, dict, dict) -> None
	# ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-CLIENT: IN dn=%r' % (dn,))
	# ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-CLIENT: IN old=%r' % (old,))
	# ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-CLIENT: IN new=%r' % (new,))

	fqdn = '%(hostname)s.%(domainname)s' % configRegistry
	fqdn = fqdn.encode('UTF-8')

	if old and not new:
		ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-CLIENT: service %r deleted' % (old['cn'][0],))
		removeConfig(old['cn'][0].decode('UTF-8'))

	if old and \
		fqdn in old.get('univentionNagiosHostname', []) and \
		fqdn not in new.get('univentionNagiosHostname', []):
		# object changed and
		# local fqdn was in old object and
		# local fqdn is not in new object
		# ==> fqdn was deleted from list
		ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-CLIENT: host removed from service %s' % (old['cn'][0],))
		removeConfig(old['cn'][0].decode('UTF-8'))
	elif old and \
		old.get('univentionNagiosUseNRPE', [None])[0] == b'1' and \
		new.get('univentionNagiosUseNRPE', [None])[0] != b'1':
		# object changed and
		# local fqdn is in new object  (otherwise previous if-statement matches)
		# NRPE was enabled in old object
		# NRPE is disabled in new object
		# ==> remove config
		ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-CLIENT: nrpe disabled for service %r' % (old['cn'][0],))
		removeConfig(old['cn'][0].decode('UTF-8'))
	else:
		# otherwise:
		# - this host was configure in old and new object or
		# - this host is newly added to list or
		# - this object is new
		if 'univentionNagiosUseNRPE' in new and new['univentionNagiosUseNRPE'] and (new['univentionNagiosUseNRPE'][0] == b'1'):
			ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-CLIENT: writing service %r' % (new['cn'][0],))
			writeConfig(fqdn.decode('UTF-8'), new)


@SetUID(0)
def initialize():
	# type: () -> None
	dirname = '/etc/nagios/nrpe.univention.d'

	if not os.path.exists(dirname):
		os.mkdir(dirname)


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


@SetUID(0)
def clean():
	# type: () -> None
	dirname = '/etc/nagios/nrpe.univention.d'
	if os.path.exists(dirname):
		deleteTree(dirname)


def postrun():
	# type: () -> None
	global __initscript
	initscript = __initscript
	if configRegistry.is_true("nagios/client/autostart"):
		ud.debug(ud.LISTENER, ud.INFO, 'NRPED: Restarting server')
		run(initscript, ['nagios-nrpe-server', 'restart'], uid=0)
