# -*- coding: utf-8 -*-
#
# Univention Print Server
#  listener module: management of CUPS printers
#
# Copyright 2004-2012 Univention GmbH
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
import os, string, time
import univention.debug
## for the ucr commit below in postrun we need ucr configHandlers
from univention.config_registry import configHandlers
ucr_handlers = configHandlers()
ucr_handlers.load()

hostname=listener.baseConfig['hostname']
domainname=listener.baseConfig['domainname']
ip=listener.baseConfig['interfaces/eth0/address']
ldap_base=listener.baseConfig['ldap/base']

name='cups-printers'
description='Manage CUPS printer configuration'
filter='(|(objectClass=univentionPrinter)(objectClass=univentionPrinterGroup))'
attributes=['univentionPrinterSpoolHost', 'univentionPrinterModel', 'univentionPrinterURI', 'univentionPrinterLocation', 'description', 'univentionPrinterSambaName','univentionPrinterPricePerPage','univentionPrinterPricePerJob','univentionPrinterQuotaSupport','univentionPrinterGroupMember', 'univentionPrinterACLUsers', 'univentionPrinterACLGroups', 'univentionPrinterACLtype',]

def lpadmin(args):

	args = map(lambda x: '%s' % x.replace('"', '').strip(), args)
	args = map(lambda x: '%s' % x.replace("'", '').strip(), args)

	# Show this info message by default
	univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, "cups-printers: info: univention-lpadmin %s" % string.join(args, ' '))

	rc = listener.run('/usr/sbin/univention-lpadmin', ['univention-lpadmin']+args, uid=0)
	if rc != 0:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, "cups-printers: Failed to execute the univention-lpadmin command. Please check the cups state.")
		filename=os.path.join('/var/cache/univention-printserver/','%f.sh' % time.time())
		f=open(filename, 'w+')
		os.chmod(filename, 0755)
		print >>f, '#!/bin/sh'
		print >>f, '/usr/sbin/univention-lpadmin ' + ' '.join(map(lambda x: "'%s'" % x, args))
		f.close()

def pkprinters(args):
	listener.setuid(0)
	try:
		if os.path.exists("/usr/sbin/pkprinters"):
			univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "cups-printers: pkprinters args=%s" % args)
			os.system("/usr/sbin/pkprinters %s" % string.join(args, ' '))
		elif os.path.exists("/usr/bin/pkprinters"):
			univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "cups-printers: pkprinters args=%s" % args)
			os.system("/usr/bin/pkprinters %s" % string.join(args, ' '))
		else:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "cups-printers: pkprinters binary not found")
	finally:
		listener.unsetuid()

def filter_match(object):
	if object.has_key('univentionPrinterSpoolHost'):
		for i in range(0,len(object['univentionPrinterSpoolHost'])):
			if object['univentionPrinterSpoolHost'][i] == ip:
				return 1
			elif object['univentionPrinterSpoolHost'][i] == '%s.%s' % (hostname, domainname):
				return 1
	return 0

def handler(dn, new, old):
	need_to_reload_samba = 0
	need_to_reload_cups = 0
	printer_is_group = 0
	quota_support = 0

	changes=[]

	if old:
		if old.has_key('objectClass'):
			if old['objectClass'][1] == 'univentionPrinterGroup':
				printer_is_group=1
		if old.has_key('univentionPrinterQuotaSupport') and (old['univentionPrinterQuotaSupport'][0] == "1"):
			quota_support = 1
	if new:
		if new.has_key('objectClass'):
			if new['objectClass'][1]== 'univentionPrinterGroup':
				printer_is_group=1
		if new.has_key('univentionPrinterQuotaSupport') and (new['univentionPrinterQuotaSupport'][0] == "1"):
			quota_support = 1
		else:
			quota_support = 0
	modified_uri=''
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

	options={
		'univentionPrinterURI': '-v',
		'univentionPrinterLocation': '-L',
		'description': '-D',
		'univentionPrinterModel': '-m'
	}

	if filter_match(old):
		if 'cn' in changes or not filter_match(new):
			#Deletions done via UCR-Variables
			printer_name = old['cn'][0]
			listener.baseConfig.load()
			printer_list = listener.baseConfig.get('cups/restrictedprinters', '').split()
			printer_is_restricted = printer_name in printer_list
			if printer_is_restricted and not listener.baseConfig.get('cups/automaticrestrict', "true") in ['false','no']:
				printer_list.remove (printer_name)
				keyval = 'cups/restrictedprinters=%s' % string.join(printer_list, ' ')
				listener.setuid (0)
				try:
					univention.config_registry.handler_set( [ keyval.encode() ] )
				finally:
					listener.unsetuid ()

			#Deletions done via lpadmin
			lpadmin(['-x', old['cn'][0]])
			if old.has_key('univentionPrinterQuotaSupport') and old['univentionPrinterQuotaSupport'][0] == "1":
				if printer_is_group:
					for member in old['univentionPrinterGroupMember']:
						pkprinters(['--groups', old['cn'][0], '--remove', member])
				pkprinters(['--delete', old['cn'][0]])
			need_to_reload_samba = 1

		#Deletions done via editing the Samba config
		if old.has_key('univentionPrinterSambaName') and old['univentionPrinterSambaName']:
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

		if update_restricted_printers and not listener.baseConfig.get('cups/automaticrestrict', "true") in ['false','no']:
			keyval = 'cups/restrictedprinters=%s' % string.join (printer_list, ' ')
			listener.setuid (0)
			try:
				univention.config_registry.handler_set( [ keyval.encode() ] )
			finally:
				listener.unsetuid ()
			need_to_reload_cups=1

		#Modifications done via lpadmin
		description=""
		page_price=0
		job_price=0
		aclUsers = []
		aclGroups = []
		
		args = [] # lpadmin args

		if new.has_key('univentionPrinterSambaName'):
			description=new['univentionPrinterSambaName'][0]
		if new.has_key('univentionPrinterPricePerPage'):
			page_price=new['univentionPrinterPricePerPage'][0]
		if new.has_key('univentionPrinterPricePerJob'):
			job_price=new['univentionPrinterPricePerJob'][0]

		if new.has_key('univentionPrinterACLtype'):
			if new['univentionPrinterACLtype'][0] == 'allow all':
				args+=['-u', 'allow:all', '-o', 'auth-info-required=none']
			elif (new.has_key('univentionPrinterACLUsers') and len(new['univentionPrinterACLUsers']) > 0) or (new.has_key('univentionPrinterACLGroups') and len(new['univentionPrinterACLGroups']) > 0):
				args.append('-u')
				argument = "%s:" % new['univentionPrinterACLtype'][0]
				if new.has_key('univentionPrinterACLUsers'):
					for userDn in new['univentionPrinterACLUsers']:
						argument += '%s,' % userDn[userDn.find('=')+1:userDn.find(',')]
				if new.has_key('univentionPrinterACLGroups'):
					for groupDn in new['univentionPrinterACLGroups']:
						argument += '@%s,' % groupDn[groupDn.find('=')+1:groupDn.find(',')]
				args.append(argument[:-1])
		else:
			args+=['-o', 'auth-info-required=none']

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
				add=new['univentionPrinterGroupMember']

			if new.has_key('univentionPrinterQuotaSupport') and new['univentionPrinterQuotaSupport'][0] == "1":
				pkprinters(["--add","-D","%s"%description,"--charge","%s,%s"%(page_price,job_price), new['cn'][0]])
				for member in new['univentionPrinterGroupMember']:
					pkprinters([ "--groups",new['cn'][0],member])
			elif new.has_key('univentionPrinterQuotaSupport') and new['univentionPrinterQuotaSupport'][0] == "0" and old:
				for member in old['univentionPrinterGroupMember']:
					pkprinters(['--groups', old['cn'][0], '--remove', member])

			for add_member in add: # Add Members
				args+=['-p', add_member, '-c', new['cn'][0]]
				if new.has_key('univentionPrinterQuotaSupport') and new['univentionPrinterQuotaSupport'][0] == "1":
					pkprinters([ "--groups",new['cn'][0],add_member])
			if old: # Remove Members
				for rem_member in rem:
					args+=['-p', rem_member, '-r', new['cn'][0]]
					pkprinters([ "--groups",new['cn'][0],"--remove",rem_member])

			lpadmin(args)
		# Add/Modify Printer
		else:

			args.append('-p')
			args.append(new['cn'][0])
			for a in changes:
				if a == 'univentionPrinterQuotaSupport':
					if new.has_key('univentionPrinterQuotaSupport'):
						if new['univentionPrinterQuotaSupport'][0]=='1':
							pkprinters(["--add","-D","\"%s\""%description,"--charge","%s,%s"%(page_price,job_price), new['cn'][0]])
						else:
							pkprinters(['--delete', new['cn'][0]])

				if a == 'univentionPrinterURI':
					continue

				if a == 'univentionPrinterSpoolHost' and not 'univentionPrinterModel' in changes:
					if new.get('univentionPrinterModel', [''])[0] == 'None':
						continue

					if new.get('univentionPrinterModel', [''])[0] == 'smb':
						continue

					args+=[options['univentionPrinterModel'], new.get('univentionPrinterModel', [''])[0]]

				if not options.has_key(a):
					continue

				if a == 'univentionPrinterModel':
					if new.get(a, [''])[0] == 'None':
						continue

					if new.get(a, [''])[0] == 'smb':
						continue

					args+=[options[a], new.get(a, [''])[0]]

				else:
					args+=[options[a], '%s' % new.get(a, [''])[0]]

			args+=[options['univentionPrinterURI'], modified_uri]

			args+=['-E']

			# insert printer
			lpadmin(args)
			need_to_reload_samba = 1

			#Modifications done via editing Samba config
			printername = new['cn'][0]
			if new.has_key('univentionPrinterSambaName') and new['univentionPrinterSambaName']:
				printername = new['univentionPrinterSambaName'][0]

			filename = '/etc/samba/printers.conf.d/%s' % printername
			listener.setuid(0)

			if (new.has_key('univentionPrinterSambaName') and new['univentionPrinterSambaName']) or \
			(new.has_key('univentionPrinterACLtype') and new['univentionPrinterACLtype'][0] == "allow") or \
			(new.has_key('univentionPrinterACLtype') and new['univentionPrinterACLtype'][0] == "deny"):

				# samba permissions
				perm = ""
	
				# users
				if new.has_key('univentionPrinterACLUsers'):
					for dn in new['univentionPrinterACLUsers']:
						user = dn[dn.find('=')+1:dn.find(',')]
						if " " in user: user = "\"" + user + "\""
						perm = perm + " " + user
				# groups
				if new.has_key('univentionPrinterACLGroups'):
					for dn in new['univentionPrinterACLGroups']:
						group = "@" + dn[dn.find('=')+1:dn.find(',')]
						if " " in group : group = "\"" + group + "\""
						perm = perm + " " + group
	
				try:
					fp = open(filename, 'w')
	
					print >>fp, '[%s]' % printername
					print >>fp, 'printer name = %s' % new['cn'][0]
					print >>fp, 'path = /tmp'
					print >>fp, 'guest ok = yes'
					print >>fp, 'printable = yes'
					if perm:
						if new['univentionPrinterACLtype'][0] == 'allow':
							print >>fp, 'valid users = %s' % perm
						if new['univentionPrinterACLtype'][0] == 'deny':
							print >>fp, 'invalid users = %s' %perm
	
	
					uid = 0
					gid = 0
					mode = '0755'
	
					os.chmod(filename,int(mode,0))
					os.chown(filename,uid,gid)
				finally:
					listener.unsetuid()

		if need_to_reload_cups == 1:
			reload_daemon ('cups', 'cups-printers: ')

		if need_to_reload_samba == 1:
			reload_daemon ('samba', 'cups-printers: ')

def reload_daemon(daemon, prefix):
	script = os.path.join ('/etc/init.d', daemon)
	if os.path.exists(script):
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "%s %s reload" % (prefix, daemon) )
		listener.run(script, [daemon,'reload'], uid=0)
	else:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "%s no %s to reload found" % (prefix, daemon) )

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
	global ucr_handlers
	listener.setuid(0)
	try:
		run_ucs_commit = False
		if not os.path.exists('/etc/samba/shares.conf'):
			run_ucs_commit = True
		fp = open('/etc/samba/printers.conf', 'w')
		for f in os.listdir('/etc/samba/printers.conf.d'):
			print >>fp, 'include = %s' % os.path.join('/etc/samba/printers.conf.d', f)
		fp.close()
		if run_ucs_commit:
			ucr_handlers.commit(listener.configRegistry, ['/etc/samba/smb.conf'])
		if os.path.exists('/etc/init.d/samba4'):
			initscript='/etc/init.d/samba4'
			os.spawnv(os.P_WAIT, initscript, ['samba4', 'reload'])
		if os.path.exists('/etc/init.d/samba'):
			initscript='/etc/init.d/samba'
			os.spawnv(os.P_WAIT, initscript, ['samba', 'reload'])
	finally:
		listener.unsetuid()
