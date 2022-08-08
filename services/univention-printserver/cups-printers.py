# -*- coding: utf-8 -*-
#
# Univention Print Server
#  listener module: management of CUPS printers
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
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
import time
import pipes
import subprocess
import univention.debug as ud
import univention.config_registry
# for the ucr commit below in postrun we need ucr configHandlers
from univention.config_registry import configHandlers
from univention.config_registry.interfaces import Interfaces
from ldap.dn import str2dn

ucr_handlers = configHandlers()
ucr_handlers.load()
interfaces = Interfaces(listener.configRegistry)

hostname = listener.configRegistry['hostname']
domainname = listener.configRegistry['domainname']
ip = str(interfaces.get_default_ip_address().ip)
ldap_base = listener.configRegistry['ldap/base']

name = 'cups-printers'
description = 'Manage CUPS printer configuration'
filter = '(|(objectClass=univentionPrinter)(objectClass=univentionPrinterGroup))'
attributes = ['univentionPrinterSpoolHost', 'univentionPrinterModel', 'univentionPrinterURI', 'univentionPrinterLocation', 'description', 'univentionPrinterSambaName', 'univentionPrinterGroupMember', 'univentionPrinterACLUsers', 'univentionPrinterACLGroups', 'univentionPrinterACLtype']

EMPTY = (b'',)
reload_samba_in_postrun = None


def _rdn(_dn):
	# type: (str) -> str
	return str2dn(_dn)[0][0][1]


def _validate_smb_share_name(name):
	# type: (str) -> bool
	if len(name) > 80:
		return False
	illegal_chars = set('\\/[]:|<>+=;,*?"' + ''.join(map(chr, range(0x1F + 1))))
	if set(str(name)) & illegal_chars:
		return False
	return True


class BasedirLimit(Exception):
	pass


def _escape_filename(name):
	# type: (str) -> str
	name = name.replace('/', '').replace('\x00', '')
	if name in ('.', '..', ''):
		ud.debug(ud.LISTENER, ud.ERROR, "Invalid filename: %r" % (name,))
		raise BasedirLimit('Invalid filename: %s' % (name,))
	return name


def _join_basedir_filename(basedir, filename):
	# type: (str, str) -> str
	_filename = os.path.join(basedir, _escape_filename(filename))
	if not os.path.abspath(_filename).startswith(basedir):
		ud.debug(ud.LISTENER, ud.ERROR, "Basedir manipulation: %r" % (filename,))
		raise BasedirLimit('Invalid filename: %s' % (filename,))
	return _filename


def lpadmin(args):
	# type: (list) -> None
	quoted_args = [pipes.quote(x) for x in args]

	# Show this info message by default
	ud.debug(ud.LISTENER, ud.WARN, "cups-printers: info: univention-lpadmin %s" % ' '.join(quoted_args))

	rc = listener.run('/usr/sbin/univention-lpadmin', ['univention-lpadmin'] + args, uid=0)
	if rc != 0:
		ud.debug(ud.LISTENER, ud.ERROR, "cups-printers: Failed to execute the univention-lpadmin command. Please check the cups state.")
		filename = os.path.join('/var/cache/univention-printserver/', '%f.sh' % time.time())
		with open(filename, 'w+') as fd:
			os.chmod(filename, 0o755)
			fd.write('#!/bin/sh\n')
			fd.write('/usr/sbin/univention-lpadmin %s\n' % (' '.join(quoted_args),))


def filter_match(object):
	# type: (dict) -> bool
	fqdn = ('%s.%s' % (hostname, domainname)).lower()
	for host in object.get('univentionPrinterSpoolHost', ()):
		if host.decode('ASCII').lower() in (ip.lower(), fqdn):
			return True
	return False


def get_testparm_var(smbconf, sectionname, varname):
	# type: (str, str, str) -> str
	if not os.path.exists("/usr/bin/testparm"):
		return

	cmd = ["/usr/bin/testparm", "-s", "-l", "--section-name=%s" % sectionname, "--parameter-name=%s" % varname, smbconf]
	p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
	(out, err) = p1.communicate()
	return out.decode('UTF-8').strip()


def testparm_is_true(smbconf, sectionname, varname):
	# type: (str, str, str) -> bool
	testpram_output = get_testparm_var(smbconf, sectionname, varname)
	return testpram_output.lower() in ('yes', 'true', '1', 'on')


def handler(dn, new, old):
	# type: (str, dict, dict) -> None
	change_affects_this_host = False
	need_to_reload_samba = False
	need_to_reload_cups = False
	printer_is_group = False
	samba_force_printername = listener.configRegistry.is_true('samba/force_printername', True)
	global reload_samba_in_postrun
	reload_samba_in_postrun = True

	changes = []

	if old:
		if filter_match(old):
			if old.get('univentionPrinterSambaName'):
				old_sharename = old['univentionPrinterSambaName'][0].decode('UTF-8')
			else:
				old_sharename = old['cn'][0].decode('UTF-8')
			old_filename = _join_basedir_filename('/etc/samba/printers.conf.d/', old_sharename)
			samba_force_printername = testparm_is_true(old_filename, old_sharename, 'force printername')

		if b'univentionPrinterGroup' in old.get('objectClass', ()):
			printer_is_group = True

	if new:
		if b'univentionPrinterGroup' in new.get('objectClass', ()):
			printer_is_group = True

	modified_uri = ''
	for n in new.keys():
		if new.get(n, []) != old.get(n, []):
			changes.append(n)
		if n == 'univentionPrinterURI':
			modified_uri = new['univentionPrinterURI'][0].decode('ASCII')
	for o in old.keys():
		if o not in changes and new.get(o, []) != old.get(o, []):
			changes.append(o)
		if o == 'univentionPrinterURI' and not modified_uri:
			modified_uri = old['univentionPrinterURI'][0].decode('ASCII')

	options = {
		'univentionPrinterURI': '-v',
		'univentionPrinterLocation': '-L',
		'description': '-D',
		'univentionPrinterModel': '-m'
	}

	if (filter_match(new) or filter_match(old)):
		change_affects_this_host = True
		reload_samba_in_postrun = True  # default, if it isn't done earlier

	if filter_match(old):
		if 'cn' in changes or not filter_match(new):
			# Deletions done via UCR-Variables
			printer_name = old['cn'][0].decode('UTF-8')
			listener.configRegistry.load()
			printer_list = listener.configRegistry.get('cups/restrictedprinters', '').split()
			printer_is_restricted = printer_name in printer_list
			if printer_is_restricted and not listener.configRegistry.is_false('cups/automaticrestrict', False):
				printer_list.remove(printer_name)
				keyval = 'cups/restrictedprinters=%s' % ' '.join(printer_list)
				listener.setuid(0)
				try:
					univention.config_registry.handler_set([keyval])
				finally:
					listener.unsetuid()

			# Deletions done via lpadmin
			lpadmin(['-x', old['cn'][0].decode('UTF-8')])
			need_to_reload_samba = True

		# Deletions done via editing the Samba config
		if old.get('univentionPrinterSambaName'):
			filename = _join_basedir_filename('/etc/samba/printers.conf.d/', old['univentionPrinterSambaName'][0].decode('UTF-8'))
			listener.setuid(0)
			try:
				if os.path.exists(filename):
					os.unlink(filename)
			finally:
				listener.unsetuid()

		filename = _join_basedir_filename('/etc/samba/printers.conf.d/', old['cn'][0].decode('UTF-8'))
		listener.setuid(0)
		try:
			if os.path.exists(filename):
				os.unlink(filename)
		finally:
			listener.unsetuid()

	if filter_match(new):
		# Modifications done via UCR-Variables
		printer_name = new['cn'][0].decode('UTF-8')
		listener.configRegistry.load()
		printer_list = listener.configRegistry.get('cups/restrictedprinters', '').split()
		printer_is_restricted = printer_name in printer_list
		restrict_printer = (new.get('univentionPrinterACLUsers', []) or new.get('univentionPrinterACLGroups', [])) and new['univentionPrinterACLtype'][0] != b'allow all'

		update_restricted_printers = False
		if printer_is_restricted and not restrict_printer:
			printer_list.remove(printer_name)
			update_restricted_printers = True
		elif not printer_is_restricted and restrict_printer:
			printer_list.append(printer_name)
			update_restricted_printers = True

		if update_restricted_printers and not listener.configRegistry.is_false('cups/automaticrestrict', False):
			keyval = 'cups/restrictedprinters=%s' % ' '.join(printer_list)
			listener.setuid(0)
			try:
				univention.config_registry.handler_set([keyval])
			finally:
				listener.unsetuid()
			need_to_reload_cups = True

		# Modifications done via lpadmin
		args = []  # lpadmin args

		# description = new.get('univentionPrinterSambaName', [b''])[0].decode('UTF-8')

		if new.get('univentionPrinterACLtype'):
			if new['univentionPrinterACLtype'][0] == b'allow all':
				args += ['-u', 'allow:all', '-o', 'auth-info-required=none']
			elif new.get('univentionPrinterACLUsers') or new.get('univentionPrinterACLGroups'):
				args.append('-u')
				argument = "%s:" % new['univentionPrinterACLtype'][0].decode('ASCII')
				for userDn in new.get('univentionPrinterACLUsers', ()):
					argument += '%s,' % (_rdn(userDn.decode('UTF-8')),)
				for groupDn in new.get('univentionPrinterACLGroups', ()):
					argument += '@%s,' % (_rdn(groupDn.decode('UTF-8')),)
				args.append(argument.rstrip(','))
		else:
			args += ['-o', 'auth-info-required=none']

		# Add/Modify Printergroup
		if printer_is_group:
			#add = []
			#if old:  # Diff old <==> new
			#	rem = old['univentionPrinterGroupMember']
			#	for el in new['univentionPrinterGroupMember']:
			#		if el not in old['univentionPrinterGroupMember']:
			#			add.append(el)
			#		else:
			#			rem.remove(el)

			#else:  # Create new group
			#	add = new['univentionPrinterGroupMember']

			lpadmin(args)
		# Add/Modify Printer
		else:
			args.append('-p')
			args.append(new['cn'][0].decode('UTF-8'))
			for a in changes:
				if a == 'univentionPrinterURI':
					continue

				if a == 'univentionPrinterSpoolHost' and 'univentionPrinterModel' not in changes:
					model = new.get('univentionPrinterModel', EMPTY)[0].decode('ASCII')
					if model in ['None', 'smb']:
						model = 'raw'
					args += [options['univentionPrinterModel'], model]

				if a not in options:
					continue

				if a == 'univentionPrinterModel':
					model = new.get(a, EMPTY)[0].decode('ASCII')
					if model in ['None', 'smb']:
						model = 'raw'
					args += [options[a], model]
				else:
					args += [options[a], new.get(a, EMPTY)[0].decode('UTF-8')]

			args += [options['univentionPrinterURI'], modified_uri]
			args += ['-E']

			# insert printer
			lpadmin(args)
			need_to_reload_samba = True

			# Modifications done via editing Samba config
			printername = new['cn'][0].decode('UTF-8')
			cups_printername = new['cn'][0].decode('UTF-8')
			if new.get('univentionPrinterSambaName'):
				printername = new['univentionPrinterSambaName'][0].decode('UTF-8')

			filename = _join_basedir_filename('/etc/samba/printers.conf.d/', printername)

			if not _validate_smb_share_name(printername):
				ud.debug(ud.LISTENER, ud.ERROR, "Invalid printer share name: %r. Ignoring!" % (printername,))
				return

			def _quote(arg):
				if ' ' in arg:
					arg = '"%s"' % (arg.replace('"', '\\"'),)
				return arg.replace('\n', '')

			user_and_groups = [_quote(_rdn(_dn.decode('UTF-8'))) for _dn in new.get('univentionPrinterACLUsers', ())]
			user_and_groups.extend(_quote("@" + _rdn(_dn.decode('UTF-8'))) for _dn in new.get('univentionPrinterACLGroups', ()))
			perm = ' '.join(user_and_groups)

			# samba permissions
			listener.setuid(0)
			try:
				with open(filename, 'w') as fp:
					fp.write('[%s]\n' % (printername,))
					fp.write('printer name = %s\n' % (cups_printername,))
					fp.write('path = /tmp\n')
					fp.write('guest ok = yes\n')
					fp.write('printable = yes\n')
					if samba_force_printername:
						fp.write('force printername = yes\n')
					if perm:
						if new['univentionPrinterACLtype'][0] == b'allow':
							fp.write('valid users = %s\n' % perm)
						if new['univentionPrinterACLtype'][0] == b'deny':
							fp.write('invalid users = %s\n' % perm)

				os.chmod(filename, 0o755)
				os.chown(filename, 0, 0)
			finally:
				listener.unsetuid()

	if change_affects_this_host:
		listener.setuid(0)
		try:
			with open('/etc/samba/printers.conf.temp', 'w') as fp:
				for f in os.listdir('/etc/samba/printers.conf.d'):
					fp.write('include = %s\n' % os.path.join('/etc/samba/printers.conf.d', f))
			os.rename('/etc/samba/printers.conf.temp', '/etc/samba/printers.conf')

		finally:
			listener.unsetuid()

		reload_printer_restrictions()

		if need_to_reload_cups:
			reload_cups_daemon()

		if need_to_reload_samba:
			reload_smbd()
			time.sleep(3)
			reload_smbd()


def reload_cups_daemon():
	# type: () -> None
	script = '/etc/init.d/cups'
	daemon = 'cups'
	if os.path.exists(script):
		ud.debug(ud.LISTENER, ud.PROCESS, "cups-printers: cups reload")
		listener.run(script, [daemon, 'reload'], uid=0)
	else:
		ud.debug(ud.LISTENER, ud.PROCESS, "cups-printers: no %s to init script found")


def reload_printer_restrictions():
	# type: () -> None
	listener.setuid(0)
	try:
		subprocess.call(['python3', '-m', 'univention.lib.share_restrictions'])
	finally:
		listener.unsetuid()


def reload_smbd():
	# type: () -> None
	global reload_samba_in_postrun
	listener.setuid(0)
	try:
		ucr_handlers.commit(listener.configRegistry, ['/etc/samba/smb.conf'])
		if os.path.exists('/etc/init.d/samba'):
			subprocess.call(('/etc/init.d/samba', 'reload'))
		elif os.path.exists('/usr/bin/pkill'):
			ud.debug(ud.LISTENER, ud.WARN, "cups-printers: pkill -HUP smbd")
			subprocess.call(('/usr/bin/pkill', '-HUP', 'smbd'))
		else:
			ud.debug(ud.LISTENER, ud.ERROR, "cups-printers: Cannot reload smbd: Both /etc/init.d/samba and pkill are missing")
	finally:
		listener.unsetuid()
	reload_samba_in_postrun = False  # flag that this has been done.


def initialize():
	# type: () -> None
	if not os.path.exists('/etc/samba/printers.conf.d'):
		listener.setuid(0)
		try:
			os.mkdir('/etc/samba/printers.conf.d')
			os.chmod('/etc/samba/printers.conf.d', 0o755)
		finally:
			listener.unsetuid()


def clean():
	# type: () -> None
	global ucr_handlers
	listener.setuid(0)
	try:
		for f in os.listdir('/etc/samba/printers.conf.d'):
			if os.path.exists(os.path.join('/etc/samba/printers.conf.d', f)):
				os.unlink(os.path.join('/etc/samba/printers.conf.d', f))
		if os.path.exists('/etc/samba/printers.conf'):
			os.unlink('/etc/samba/printers.conf')
			ucr_handlers.commit(listener.configRegistry, ['/etc/samba/smb.conf'])
		os.rmdir('/etc/samba/printers.conf.d')
	finally:
		listener.unsetuid()


def postrun():
	# type: () -> None
	global reload_samba_in_postrun
	if reload_samba_in_postrun:
		reload_smbd()
