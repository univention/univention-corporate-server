# -*- coding: utf-8 -*-
#
# Univention Print Server
#  listener module: management of CUPS printers
#
# Copyright 2004-2014 Univention GmbH
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

__package__='' 	# workaround for PEP 366
import listener
import os
import time
import subprocess
import univention.debug as ud
import univention.config_registry
## for the ucr commit below in postrun we need ucr configHandlers
from univention.config_registry import configHandlers
ucr_handlers = configHandlers()
ucr_handlers.load()
from univention.config_registry.interfaces import Interfaces
interfaces = Interfaces(listener.configRegistry)

hostname = listener.baseConfig['hostname']
domainname = listener.baseConfig['domainname']
ip = str(interfaces.get_default_ip_address().ip)
ldap_base = listener.baseConfig['ldap/base']

name='cups-printers'
description='Manage CUPS printer configuration'
filter='(|(objectClass=univentionPrinter)(objectClass=univentionPrinterGroup))'
attributes=['univentionPrinterSpoolHost', 'univentionPrinterModel', 'univentionPrinterURI', 'univentionPrinterLocation', 'description', 'univentionPrinterSambaName','univentionPrinterPricePerPage','univentionPrinterPricePerJob','univentionPrinterQuotaSupport','univentionPrinterGroupMember', 'univentionPrinterACLUsers', 'univentionPrinterACLGroups', 'univentionPrinterACLtype', 'univentionPrinterUseClientDriver',]

EMPTY = ('',)

def lpadmin(args):

	args = map(lambda x: '%s' % x.replace('"', '').strip(), args)
	args = map(lambda x: '%s' % x.replace("'", '').strip(), args)

	# Show this info message by default
	ud.debug(ud.LISTENER, ud.WARN, "cups-printers: info: univention-lpadmin %s" % ' '.join(args))

	rc = listener.run('/usr/sbin/univention-lpadmin', ['univention-lpadmin']+args, uid=0)
	if rc != 0:
		ud.debug(ud.LISTENER, ud.ERROR, "cups-printers: Failed to execute the univention-lpadmin command. Please check the cups state.")
		filename = os.path.join('/var/cache/univention-printserver/', '%f.sh' % time.time())
		f = open(filename, 'w+')
		os.chmod(filename, 0755)
		print >>f, '#!/bin/sh'
		print >>f, '/usr/sbin/univention-lpadmin ' + ' '.join(map(lambda x: "'%s'" % x, args))
		f.close()

def pkprinters(args):
	listener.setuid(0)
	try:
		if os.path.exists("/usr/sbin/pkprinters"):
			ud.debug(ud.LISTENER, ud.INFO, "cups-printers: pkprinters args=%s" % args)
			os.system("/usr/sbin/pkprinters %s" % ' '.join(args))
		elif os.path.exists("/usr/bin/pkprinters"):
			ud.debug(ud.LISTENER, ud.INFO, "cups-printers: pkprinters args=%s" % args)
			os.system("/usr/bin/pkprinters %s" % ' '.join(args))
		else:
			ud.debug(ud.LISTENER, ud.INFO, "cups-printers: pkprinters binary not found")
	finally:
		listener.unsetuid()

def filter_match(object):
	for host in object.get('univentionPrinterSpoolHost', ()):
		if host == ip:
			return True
		elif host == '%s.%s' % (hostname, domainname):
			return True
	return False

def handler(dn, new, old):
	change_affects_this_host = False
	need_to_reload_samba = False
	need_to_reload_cups = False
	printer_is_group = False
	quota_support = False
	global reload_samba_in_postrun
	reload_samba_in_postrun = True

	changes = []

	if old:
		if 'univentionPrinterGroup' in old.get('objectClass', ()):
			printer_is_group = True
		if old.get('univentionPrinterQuotaSupport', EMPTY)[0] == "1":
			quota_support = True
	if new:
		if 'univentionPrinterGroup' in new.get('objectClass', ()):
			printer_is_group = True
		if new.get('univentionPrinterQuotaSupport', EMPTY)[0] == "1":
			quota_support = True
		else:
			quota_support = False
	modified_uri = ''
	for n in new.keys():
		if new.get(n, []) != old.get(n, []):
			changes.append(n)
		if n == 'univentionPrinterURI':
			if quota_support:
				modified_uri = "cupspykota:%s" % new['univentionPrinterURI'][0]
			else:
				modified_uri = new['univentionPrinterURI'][0]
	for o in old.keys():
		if not o in changes and new.get(o, []) != old.get(o, []):
			changes.append(o)
		if o == 'univentionPrinterURI' and not modified_uri:
			if quota_support:
				modified_uri = "cupspykota:%s" % old['univentionPrinterURI'][0]
			else:
				modified_uri = old['univentionPrinterURI'][0]

	options = {
		'univentionPrinterURI': '-v',
		'univentionPrinterLocation': '-L',
		'description': '-D',
		'univentionPrinterModel': '-m'
	}

	if (filter_match(new) or filter_match(old)):
		change_affects_this_host = True
		reload_samba_in_postrun = True	## default, if it isn't done earlier


	if filter_match(old):
		if 'cn' in changes or not filter_match(new):
			#Deletions done via UCR-Variables
			printer_name = old['cn'][0]
			listener.baseConfig.load()
			printer_list = listener.baseConfig.get('cups/restrictedprinters', '').split()
			printer_is_restricted = printer_name in printer_list
			if printer_is_restricted and not listener.baseConfig.is_false('cups/automaticrestrict', False):
				printer_list.remove (printer_name)
				keyval = 'cups/restrictedprinters=%s' % ' '.join(printer_list)
				listener.setuid (0)
				try:
					univention.config_registry.handler_set( [ keyval.encode() ] )
				finally:
					listener.unsetuid ()

			#Deletions done via lpadmin
			lpadmin(['-x', old['cn'][0]])
			if old.get('univentionPrinterQuotaSupport', EMPTY)[0] == "1":
				if printer_is_group:
					for member in old['univentionPrinterGroupMember']:
						pkprinters(['--groups', old['cn'][0], '--remove', member])
				pkprinters(['--delete', old['cn'][0]])
			need_to_reload_samba = True

		#Deletions done via editing the Samba config
		if old.get('univentionPrinterSambaName'):
			filename = '/etc/samba/printers.conf.d/%s' % old['univentionPrinterSambaName'][0]
			listener.setuid(0)
			try:
				if os.path.exists(filename):
					os.unlink(filename)
			finally:
				listener.unsetuid()

		filename = '/etc/samba/printers.conf.d/%s' % old['cn'][0]
		listener.setuid(0)
		try:
			if os.path.exists(filename):
				os.unlink(filename)
		finally:
			listener.unsetuid()

	if filter_match(new):
		#Modifications done via UCR-Variables
		printer_name = new['cn'][0]
		listener.baseConfig.load()
		printer_list = listener.baseConfig.get('cups/restrictedprinters', '').split()
		printer_is_restricted = printer_name in printer_list
		restrict_printer = (new.get('univentionPrinterACLUsers', []) or new.get('univentionPrinterACLGroups', [])) and not (new['univentionPrinterACLtype'][0] == 'allow all')

		update_restricted_printers = False
		if printer_is_restricted and not restrict_printer:
			printer_list.remove (printer_name)
			update_restricted_printers = True
		elif not printer_is_restricted and restrict_printer:
			printer_list.append (printer_name)
			update_restricted_printers = True

		if update_restricted_printers and not listener.baseConfig.is_false('cups/automaticrestrict', False):
			keyval = 'cups/restrictedprinters=%s' % ' '.join(printer_list)
			listener.setuid (0)
			try:
				univention.config_registry.handler_set( [ keyval.encode() ] )
			finally:
				listener.unsetuid ()
			need_to_reload_cups = True

		#Modifications done via lpadmin
		description = ""
		page_price = 0
		job_price = 0
		aclUsers = []
		aclGroups = []

		args = [] # lpadmin args

		if new.get('univentionPrinterSambaName'):
			description = new['univentionPrinterSambaName'][0]
		if new.get('univentionPrinterPricePerPage'):
			page_price = new['univentionPrinterPricePerPage'][0]
		if new.get('univentionPrinterPricePerJob'):
			job_price = new['univentionPrinterPricePerJob'][0]

		if new.get('univentionPrinterACLtype'):
			if new['univentionPrinterACLtype'][0] == 'allow all':
				args += ['-u', 'allow:all', '-o', 'auth-info-required=none']
			elif new.get('univentionPrinterACLUsers') or new.get('univentionPrinterACLGroups'):
				args.append('-u')
				argument = "%s:" % new['univentionPrinterACLtype'][0]
				for userDn in new.get('univentionPrinterACLUsers', ()):
					argument += '%s,' % userDn[userDn.find('=')+1:userDn.find(',')]
				for groupDn in new.get('univentionPrinterACLGroups', ()):
					argument += '@%s,' % groupDn[groupDn.find('=')+1:groupDn.find(',')]
				args.append(argument[:-1])
		else:
			args += ['-o', 'auth-info-required=none']

		# Add/Modify Printergroup
		if printer_is_group:
			add = []
			if old: # Diff old <==> new
				rem = old['univentionPrinterGroupMember']
				for el in new['univentionPrinterGroupMember']:
					if el not in old['univentionPrinterGroupMember']:
						add.append(el)
					else:
						rem.remove(el)


			else: # Create new group
				add = new['univentionPrinterGroupMember']

			if new.get('univentionPrinterQuotaSupport', EMPTY)[0] == "1":
				pkprinters(["--add", "-D", '"%s"' % description, "--charge", "%s,%s" % (page_price, job_price), new['cn'][0]])
				for member in new['univentionPrinterGroupMember']:
					pkprinters([ "--groups", new['cn'][0],member])
			elif new.get('univentionPrinterQuotaSupport', EMPTY)[0] == "0" and old:
				for member in old['univentionPrinterGroupMember']:
					pkprinters(['--groups', old['cn'][0], '--remove', member])

			for add_member in add: # Add Members
				args += ['-p', add_member, '-c', new['cn'][0]]
				if new.get('univentionPrinterQuotaSupport', EMPTY)[0] == "1":
					pkprinters([ "--groups", new['cn'][0], add_member])
			if old: # Remove Members
				for rem_member in rem:
					args += ['-p', rem_member, '-r', new['cn'][0]]
					pkprinters(["--groups", new['cn'][0], "--remove", rem_member])

			lpadmin(args)
		# Add/Modify Printer
		else:

			args.append('-p')
			args.append(new['cn'][0])
			for a in changes:
				if a == 'univentionPrinterQuotaSupport':
					if new.get('univentionPrinterQuotaSupport'):
						if new['univentionPrinterQuotaSupport'][0] == '1':
							pkprinters(["--add", "-D", '"%s"' % description, "--charge", "%s,%s" % (page_price, job_price), new['cn'][0]])
						else:
							pkprinters(['--delete', new['cn'][0]])

				if a == 'univentionPrinterURI':
					continue

				if a == 'univentionPrinterSpoolHost' and not 'univentionPrinterModel' in changes:
					if new.get('univentionPrinterModel', EMPTY)[0] == 'None':
						continue

					if new.get('univentionPrinterModel', EMPTY)[0] == 'smb':
						continue

					args += [options['univentionPrinterModel'], new.get('univentionPrinterModel', EMPTY)[0]]

				if not a in options:
					continue

				if a == 'univentionPrinterModel':
					if new.get(a, EMPTY)[0] == 'None':
						continue

					if new.get(a, EMPTY)[0] == 'smb':
						continue

					args += [options[a], new.get(a, EMPTY)[0]]

				else:
					args += [options[a], '%s' % new.get(a, EMPTY)[0]]

			args += [options['univentionPrinterURI'], modified_uri]

			args += ['-E']

			# insert printer
			lpadmin(args)
			need_to_reload_samba = True

			#Modifications done via editing Samba config
			printername = new['cn'][0]
			if new.get('univentionPrinterSambaName'):
				printername = new['univentionPrinterSambaName'][0]

			filename = '/etc/samba/printers.conf.d/%s' % printername
			listener.setuid(0)

			# samba permissions
			perm = ""

			# users
			for dn in new.get('univentionPrinterACLUsers', ()):
				user = dn[dn.find('=')+1:dn.find(',')]
				if " " in user:
					user = "\"" + user + "\""
				perm = perm + " " + user
			# groups
			for dn in new.get('univentionPrinterACLGroups', ()):
				group = "@" + dn[dn.find('=')+1:dn.find(',')]
				if " " in group:
					group = "\"" + group + "\""
				perm = perm + " " + group

			try:
				fp = open(filename, 'w')

				print >>fp, '[%s]' % printername
				print >>fp, 'printer name = %s' % new['cn'][0]
				print >>fp, 'path = /tmp'
				print >>fp, 'guest ok = yes'
				print >>fp, 'printable = yes'
				if listener.baseConfig.is_true('samba/force_printername', True):
					print >>fp, 'force printername = yes'
				if perm:
					if new['univentionPrinterACLtype'][0] == 'allow':
						print >>fp, 'valid users = %s' % perm
					if new['univentionPrinterACLtype'][0] == 'deny':
						print >>fp, 'invalid users = %s' %perm

				if new.get('univentionPrinterUseClientDriver', [''])[0] == '1':
					print >>fp, 'use client driver = yes'

				uid = 0
				gid = 0
				mode = '0755'

				os.chmod(filename,int(mode,0))
				os.chown(filename,uid,gid)
			finally:
				listener.unsetuid()


	if change_affects_this_host:
		listener.setuid(0)
		try:
			fp = open('/etc/samba/printers.conf.temp', 'w')
			for f in os.listdir('/etc/samba/printers.conf.d'):
				print >>fp, 'include = %s' % os.path.join('/etc/samba/printers.conf.d', f)
			fp.close()
			os.rename('/etc/samba/printers.conf.temp', '/etc/samba/printers.conf')
			
		finally:
			listener.unsetuid()

		if need_to_reload_cups:
			reload_daemon ('cups', 'cups-printers: ')

		if need_to_reload_samba:
			reload_smbd()


def reload_daemon(daemon, prefix):
	script = os.path.join ('/etc/init.d', daemon)
	if os.path.exists(script):
		ud.debug(ud.LISTENER, ud.INFO, "%s %s reload" % (prefix, daemon) )
		listener.run(script, [daemon,'reload'], uid=0)
	else:
		ud.debug(ud.LISTENER, ud.INFO, "%s no %s to reload found" % (prefix, daemon) )

def reload_smbd():
	global reload_samba_in_postrun
	listener.setuid(0)
	try:
		ucr_handlers.commit(listener.configRegistry, ['/etc/samba/smb.conf'])
		if os.path.exists('/usr/bin/smbcontrol'):
			ud.debug(ud.LISTENER, ud.WARN, "cups-printers: smbcontrol smbd reload-config")
			subprocess.call(('/usr/bin/smbcontrol', 'smbd', 'reload-config')) 
			ud.debug(ud.LISTENER, ud.WARN, "cups-printers: smbcontrol smbd reload-printers")
			subprocess.call(('/usr/bin/smbcontrol', 'smbd', 'reload-printers')) 
		elif os.path.exists('/usr/bin/pkill'):
			ud.debug(ud.LISTENER, ud.WARN, "cups-printers: pkill -HUP smbd")
			subprocess.call(('/usr/bin/pkill', '-HUP', 'smbd')) 
		else:
			ud.debug(ud.LISTENER, ud.ERROR, "cups-printers: smbcontrol and pkill missing to reload smbd")
	finally:
		listener.unsetuid()
	reload_samba_in_postrun = False	## flag that this has been done.

def initialize():
	if not os.path.exists('/etc/samba/printers.conf.d'):
		listener.setuid(0)
		try:
			os.mkdir('/etc/samba/printers.conf.d')
		finally:
			listener.unsetuid()

def clean():
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
	if reload_samba_in_postrun:
		reload_smbd()
