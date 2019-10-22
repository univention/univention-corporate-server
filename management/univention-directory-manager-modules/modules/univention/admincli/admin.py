#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  command line frontend to univention-directory-manager (module)
#
# Copyright 2004-2019 Univention GmbH
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


from __future__ import print_function
import getopt
import re
import string
import base64
import os
import subprocess
import traceback

import ldap

import univention.debug as ud

import univention.admin.uexceptions
import univention.admin.uldap
import univention.admin.modules
import univention.admin.objects
from univention.admin.layout import Group
from univention.admin.syntax import ldapFilter
import univention.config_registry
import univention.admin.ipaddress

univention.admin.modules.update()

# usage information


def usage():
	out = []
	out.append('univention-directory-manager: command line interface for managing UCS')
	out.append('copyright (c) 2001-@%@copyright_lastyear@%@ Univention GmbH, Germany')
	out.append('')
	out.append('Syntax:')
	out.append('  univention-directory-manager module action [options]')
	out.append('  univention-directory-manager [--help] [--version]')
	out.append('')
	out.append('actions:')
	out.append('  %-32s %s' % ('create:', 'Create a new object'))
	out.append('  %-32s %s' % ('modify:', 'Modify an existing object'))
	out.append('  %-32s %s' % ('remove:', 'Remove an existing object'))
	out.append('  %-32s %s' % ('list:', 'List objects'))
	out.append('  %-32s %s' % ('move:', 'Move object in directory tree'))
	out.append('')
	out.append('  %-32s %s' % ('-h | --help | -?:', 'print this usage message'))
	out.append('  %-32s %s' % ('--version:', 'print version information'))
	out.append('')
	out.append('general options:')
	out.append('  --%-30s %s' % ('binddn', 'bind DN'))
	out.append('  --%-30s %s' % ('bindpwd', 'bind password'))
	out.append('  --%-30s %s' % ('bindpwdfile', 'file containing bind password'))
	out.append('  --%-30s %s' % ('logfile', 'path and name of the logfile to be used'))
	out.append('  --%-30s %s' % ('tls', '0 (no); 1 (try); 2 (must)'))
	out.append('')
	out.append('create options:')
	out.append('  --%-30s %s' % ('position', 'Set position in tree'))
	out.append('  --%-30s %s' % ('set', 'Set variable to value, e.g. foo=bar'))
	out.append('  --%-30s %s' % ('superordinate', 'Use superordinate module'))
	out.append('  --%-30s %s' % ('option', 'Use only given module options'))
	out.append('  --%-30s %s' % ('append-option', 'Append the module option'))
	out.append('  --%-30s %s' % ('remove-option', 'Remove the module option'))
	out.append('  --%-30s %s' % ('policy-reference', 'Reference to policy given by DN'))
	out.append('  --%-30s   ' % ('ignore_exists'))
	out.append('')
	out.append('modify options:')
	out.append('  --%-30s %s' % ('dn', 'Edit object with DN'))
	out.append('  --%-30s %s' % ('set', 'Set variable to value, e.g. foo=bar'))
	out.append('  --%-30s %s' % ('append', 'Append value to variable, e.g. foo=bar'))
	out.append('  --%-30s %s' % ('remove', 'Remove value from variable, e.g. foo=bar'))
	out.append('  --%-30s %s' % ('option', 'Use only given module options'))
	out.append('  --%-30s %s' % ('append-option', 'Append the module option'))
	out.append('  --%-30s %s' % ('remove-option', 'Remove the module option'))
	out.append('  --%-30s %s' % ('policy-reference', 'Reference to policy given by DN'))
	out.append('  --%-30s %s' % ('policy-dereference', 'Remove reference to policy given by DN'))
	out.append('')
	out.append('remove options:')
	out.append('  --%-30s %s' % ('dn', 'Remove object with DN'))
	out.append('  --%-30s %s' % ('superordinate', 'Use superordinate module'))
	out.append('  --%-30s %s' % ('filter', 'Lookup filter e.g. foo=bar'))
	out.append('  --%-30s %s' % ('remove_referring', 'remove referring objects'))
	out.append('  --%-30s   ' % ('ignore_not_exists'))
	out.append('')
	out.append('list options:')
	out.append('  --%-30s %s' % ('filter', 'Lookup filter e.g. foo=bar'))
	out.append('  --%-30s %s' % ('position', 'Search underneath of position in tree'))
	out.append('  --%-30s %s' % ('policies', 'List policy-based settings:'))
	out.append('    %-30s %s' % ('', '0:short, 1:long (with policy-DN)'))
	out.append('')
	out.append('move options:')
	out.append('  --%-30s %s' % ('dn', 'Move object with DN'))
	out.append('  --%-30s %s' % ('position', 'Move to position in tree'))
	out.append('')
	out.append('Description:')
	out.append('  univention-directory-manager is a tool to handle the configuration for UCS')
	out.append('  on command line level.')
	out.append('  Use "univention-directory-manager modules" for a list of available modules.')
	out.append('')
	return out


def version():
	o = []
	o.append('univention-directory-manager @%@package_version@%@')
	return o


def _print_property(module, action, name, output):
	property = module.property_descriptions.get(name)
	if property is None:
		output.append('E: unknown property %s of module %s' % (name, univention.admin.modules.name(module)))
		return

	required = {
		'create': False,
		'modify': False,
		'remove': False,
		'editable': True,
	}

	if property.required:
		required['create'] = True
	if property.identifies:
		required['modify'] = True
		required['remove'] = True
	if not property.editable:
		required['modify'] = False
		required['remove'] = False
		required['editable'] = False

	flags = ''
	if action in required and required[action]:
		flags = '*'
	elif action not in required:
		if required['create']:
			flags += 'c'
		if required['modify']:
			flags += 'm'
		if required['remove']:
			flags += 'r'
		if not required['editable']:
			flags += 'e'
	if property.options:
		if flags:
			flags += ','
		flags += ','.join(property.options)
	if property.multivalue:
		if flags:
			flags += ','
		flags += '[]'
	if flags:
		flags = '(' + flags + ')'

	output.append('		%-40s %s' % (name + ' ' + flags, property.short_description))


def module_usage(information, action=''):
	out = []
	for module, l in information.items():
		properties, options = l

		if options:
			out.append('')
			out.append('%s options:' % module.module)
			for name, option in options.items():
				out.append('  %-32s %s' % (name, option.short_description))

		out.append('')
		out.append('%s variables:' % module.module)

		if not hasattr(module, "layout"):
			continue
		for moduletab in module.layout:
			out.append('  %s:' % (moduletab.label))

			for row in moduletab.layout:
				if isinstance(row, Group):
					out.append('	%s' % row.label)
					for row in row.layout:
						if isinstance(row, basestring):
							_print_property(module, action, row, out)
							continue
						for item in row:
							_print_property(module, action, item, out)
				else:
					if isinstance(row, basestring):
						_print_property(module, action, row, out)
						continue
					for item in row:
						_print_property(module, action, item, out)

	return out


def module_information(module, identifies_only=0):
	information = {module: [{}, {}]}
	for superordinate in univention.admin.modules.superordinates(module):
		information.update(module_information(superordinate, identifies_only=1))

	if not identifies_only:
		for name, property in module.property_descriptions.items():
			information[module][0][name] = property
		if hasattr(module, 'options'):
			for name, option in module.options.items():
				information[module][1][name] = option

	return information


def _2utf8(text):
	try:
		return text.encode('utf-8')
	except:
		return text.decode('iso-8859-1')


def object_input(module, object, input, append=None, remove=None):
	out = []
	if append:
		for key, value in append.items():
			if key in object and not object.has_property(key):
				opts = module.property_descriptions[key].options
				if len(opts) == 1:
					object.options.extend(opts)
					out.append('WARNING: %s was set without --append-option. Automatically appending %s.' % (key, ', '.join(opts)))
			if module.property_descriptions[key].syntax.name == 'file':
				if os.path.exists(value):
					fh = open(value, 'r')
					content = ''
					for line in fh.readlines():
						content += line
					object[key] = content
					fh.close()
				else:
					out.append('WARNING: file not found: %s' % value)

			elif univention.admin.syntax.is_syntax(module.property_descriptions[key].syntax, univention.admin.syntax.complex):
				for i in range(0, len(value)):
					test_val = value[i].split('"')
					if test_val[0] and test_val[0] == value[i]:
						val = value[i].split(' ')
					else:
						val = []
						for j in test_val:
							if j and j.rstrip().lstrip():
								val.append(j.rstrip().lstrip())

					if not object.has_property(key):
						object[key] = []
					if val in object[key]:
						out.append('WARNING: cannot append %s to %s, value exists' % (val, key))
					elif object[key] == [''] or object[key] == []:
						object[key] = [val]
					else:
						object[key].append(val)
			else:
				for val in value:
					if val in object[key]:
						out.append('WARNING: cannot append %s to %s, value exists' % (val, key))
					elif object[key] == [''] or object[key] == []:
						object[key] = [val]
					else:
						try:
							tmp = list(object[key])
							tmp.append(val)
							object[key] = list(tmp)
						except univention.admin.uexceptions.valueInvalidSyntax as errmsg:
							out.append('E: Invalid Syntax: %s' % str(errmsg))
	if remove:
		for key, value in remove.items():
			if univention.admin.syntax.is_syntax(module.property_descriptions[key].syntax, univention.admin.syntax.complex):
				if value:
					for i in range(0, len(value)):
						test_val = value[i].split('"')
						if test_val[0] and test_val[0] == value[i]:
							val = value[i].split(' ')
						else:
							val = []
							out.append('test_val=%s' % test_val)
							for j in test_val:
								if j and j.rstrip().lstrip():
									val.append(j.rstrip().lstrip())

							for j in range(0, len(val)):
								val[j] = '"%s"' % val[j]

						if val and val in object[key]:
							object[key].remove(val)
						else:
							out.append("WARNING: cannot remove %s from %s, value does not exist" % (val, key))
				else:
					object[key] = []

			else:
				current_values = [object[key]] if isinstance(object[key], basestring) else list(object[key])
				if value is None:
					current_values = []
				else:
					vallist = [value] if isinstance(value, basestring) else value

					for val in vallist:
						if val in current_values:
							current_values.remove(val)
						else:
							out.append("WARNING: cannot remove %s from %s, value does not exist" % (val, key))
				if not module.property_descriptions[key].multivalue:
					try:
						current_values = current_values[0]
					except IndexError:
						current_values = None
				object[key] = current_values
	if input:
		for key, value in input.items():
			if key in object and not object.has_property(key):
				opts = module.property_descriptions[key].options
				if len(opts) == 1:
					object.options.extend(opts)
					out.append('WARNING: %s was set without --append-option. Automatically appending %s.' % (key, ', '.join(opts)))
			if module.property_descriptions[key].syntax.name == 'binaryfile':
				if value == '':
					object[key] = value
				elif os.path.exists(value):
					fh = open(value, 'r')
					content = fh.read()
					if "----BEGIN CERTIFICATE-----" in content:
						content = content.replace('----BEGIN CERTIFICATE-----', '')
						content = content.replace('----END CERTIFICATE-----', '')
						object[key] = base64.decodestring(content)
					else:
						object[key] = content
					fh.close()
				else:
					out.append('WARNING: file not found: %s' % value)

			elif univention.admin.syntax.is_syntax(module.property_descriptions[key].syntax, univention.admin.syntax.complex):
				if isinstance(value, list):
					for i in range(0, len(value)):
						test_val = value[i].split('"')
						if test_val[0] and test_val[0] == value[i]:
							val = value[i].split(' ')
						else:
							val = []
							for j in test_val:
								if j and j.rstrip().lstrip():
									val.append(j.rstrip().lstrip())
				else:
					val = value.split(' ')
				if module.property_descriptions[key].multivalue:
					object[key] = [val]
				else:
					object[key] = val
			else:
				try:
					object[key] = value
				except univention.admin.uexceptions.ipOverridesNetwork as e:
					out.append('WARNING: %s' % e.message)
				except univention.admin.uexceptions.valueMayNotChange as e:
					raise univention.admin.uexceptions.valueMayNotChange("%s: %s" % (e.message, key))
	return out


def list_available_modules(o=[]):

	o.append("Available Modules are:")
	avail_modules = []
	for mod in univention.admin.modules.modules.keys():
		avail_modules.append(mod)
	avail_modules.sort()
	for mod in avail_modules:
		o.append("  %s" % mod)
	return o


def doit(arglist):
	out = []
	try:
		out = _doit(arglist)
	except ldap.SERVER_DOWN:
		return out + ["E: The LDAP Server is currently not available.", "OPERATION FAILED"]
	except univention.admin.uexceptions.base as e:
		ud.debug(ud.ADMIN, ud.WARN, traceback.format_exc())

		# collect error information
		msg = []
		if getattr(e, 'message', None):
			msg.append(e.message)
		if getattr(e, 'args', None):
			# avoid duplicate messages
			if not len(msg) or len(e.args) > 1 or e.args[0] != msg[0]:
				msg.extend(e.args)

		# strip elements and make sure that a ':' is printed iff further information follows
		msg = [i.strip() for i in msg]
		if len(msg) == 1:
			msg[0] = '%s.' % msg[0].strip(':.')
		elif len(msg) > 1:
			msg[0] = '%s:' % msg[0].strip(':.')

		# append to the output
		out.append(' '.join(msg))
		return out + ["OPERATION FAILED"]
	return out


def _doit(arglist):

	out = []
	# parse module and action
	if len(arglist) < 2:
		return usage() + ["OPERATION FAILED"]

	module_name = arglist[1]
	if module_name in ['-h', '--help', '-?']:
		return usage()

	if module_name == '--version':
		return version()

	if module_name == 'modules':
		return list_available_modules()

	remove_referring = 0
	recursive = 1
	# parse options
	longopts = ['position=', 'dn=', 'set=', 'append=', 'remove=', 'superordinate=', 'option=', 'append-option=', 'remove-option=', 'filter=', 'tls=', 'ignore_exists', 'ignore_not_exists', 'logfile=', 'policies=', 'binddn=', 'bindpwd=', 'bindpwdfile=', 'policy-reference=', 'policy-dereference=', 'remove_referring', 'recursive']
	try:
		opts, args = getopt.getopt(arglist[3:], '', longopts)
	except getopt.error as msg:
		out.append(str(msg))
		return out + ["OPERATION FAILED"]

	if not args == [] and isinstance(args, list):
		msg = "WARNING: the following arguments are ignored:"
		for argument in args:
			msg = '%s "%s"' % (msg, argument)
		out.append(msg)

	position_dn = ''
	dn = ''
	binddn = None
	bindpwd = None
	list_policies = False
	policies_with_DN = False
	policyOptions = []
	logfile = '/var/log/univention/directory-manager-cmd.log'
	tls = 2
	ignore_exists = 0
	ignore_not_exists = False
	superordinate_dn = ''
	parsed_append_options = []
	parsed_remove_options = []
	parsed_options = []
	filter = ''
	input = {}
	append = {}
	remove = {}
	policy_reference = []
	policy_dereference = []
	for opt, val in opts:
		if opt == '--position':
			position_dn = _2utf8(val)
		elif opt == '--logfile':
			logfile = val
		elif opt == '--policies':
			list_policies = True
			if val == "1":
				policies_with_DN = True
			else:
				policyOptions = ['-s']
		elif opt == '--binddn':
			binddn = val
		elif opt == '--bindpwd':
			bindpwd = val
		elif opt == '--bindpwdfile':
			try:
				with open(val) as fp:
					bindpwd = fp.read().strip()
			except IOError as e:
				out.append('E: could not read bindpwd from file (%s)' % str(e))
				return out + ['OPERATION FAILED']
		elif opt == '--dn':
			dn = _2utf8(val)
		elif opt == '--tls':
			tls = val
		elif opt == '--ignore_exists':
			ignore_exists = 1
		elif opt == '--ignore_not_exists':
			ignore_not_exists = True
		elif opt == '--superordinate':
			superordinate_dn = val
		elif opt == '--option':
			parsed_options.append(val)
		elif opt == '--append-option':
			parsed_append_options.append(val)
		elif opt == '--remove-option':
			parsed_remove_options.append(val)
		elif opt == '--filter':
			ldapFilter.parse(val)
			filter = val
		elif opt == '--policy-reference':
			policy_reference.append(val)
		elif opt == '--policy-dereference':
			policy_dereference.append(val)

	if logfile:
		ud.init(logfile, 1, 0)
	else:
		out.append("WARNING: no logfile specified")

	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()

	co = None
	baseDN = configRegistry['ldap/base']

	if configRegistry.get('directory/manager/cmd/debug/level'):
		debug_level = configRegistry['directory/manager/cmd/debug/level']
	else:
		debug_level = 0

	ud.set_level(ud.LDAP, int(debug_level))
	ud.set_level(ud.ADMIN, int(debug_level))

	if binddn and bindpwd:
		ud.debug(ud.ADMIN, ud.INFO, "using %s account" % binddn)
		try:
			lo = univention.admin.uldap.access(host=configRegistry['ldap/master'], port=int(configRegistry.get('ldap/master/port', '7389')), base=baseDN, binddn=binddn, start_tls=tls, bindpw=bindpwd)
		except Exception as e:
			ud.debug(ud.ADMIN, ud.WARN, 'authentication error: %s' % str(e))
			out.append('authentication error: %s' % str(e))
			return out + ["OPERATION FAILED"]
		policyOptions.extend(['-D', binddn, '-w', bindpwd])  # FIXME not so nice

	else:
		if os.path.exists('/etc/ldap.secret'):
			ud.debug(ud.ADMIN, ud.INFO, "using cn=admin,%s account" % baseDN)
			secretFileName = '/etc/ldap.secret'
			binddn = 'cn=admin,' + baseDN
			policyOptions.extend(['-D', binddn, '-y', secretFileName])
		elif os.path.exists('/etc/machine.secret'):
			ud.debug(ud.ADMIN, ud.INFO, "using %s account" % configRegistry['ldap/hostdn'])
			secretFileName = '/etc/machine.secret'
			binddn = configRegistry['ldap/hostdn']
			policyOptions.extend(['-D', binddn, '-y', secretFileName])

		try:
			secretFile = open(secretFileName, 'r')
		except IOError:
			out.append('E: Permission denied, try --binddn and --bindpwd')
			return out + ["OPERATION FAILED"]
		pwdLine = secretFile.readline()
		pwd = re.sub('\n', '', pwdLine)

		try:
			lo = univention.admin.uldap.access(host=configRegistry['ldap/master'], port=int(configRegistry.get('ldap/master/port', '7389')), base=baseDN, binddn=binddn, bindpw=pwd, start_tls=tls)
		except Exception as e:
			ud.debug(ud.ADMIN, ud.WARN, 'authentication error: %s' % str(e))
			out.append('authentication error: %s' % str(e))
			return out + ["OPERATION FAILED"]

	if not position_dn and superordinate_dn:
		position_dn = superordinate_dn
	elif not position_dn:
		position_dn = baseDN

	try:
		position = univention.admin.uldap.position(baseDN)
		position.setDn(position_dn)
	except univention.admin.uexceptions.noObject:
		out.append('E: Invalid position')
		return out + ["OPERATION FAILED"]

	try:
		module = univention.admin.modules.get(module_name)
	except:
		out.append("failed to get module %s." % module_name)
		out.append("")
		return list_available_modules(out) + ["OPERATION FAILED"]

	if not module:
		out.append("unknown module %s." % module_name)
		out.append("")
		return list_available_modules(out) + ["OPERATION FAILED"]

	# initialise modules
	if module_name == 'settings/usertemplate':
		univention.admin.modules.init(lo, position, univention.admin.modules.get('users/user'))
	univention.admin.modules.init(lo, position, module)

	information = module_information(module)

	superordinate = None
	if superordinate_dn and univention.admin.modules.superordinate(module):
		# the superordinate itself also has a superordinate, get it!
		superordinate = univention.admin.objects.get_superordinate(module, None, lo, superordinate_dn)
		if superordinate is None:
			out.append('E: %s is not a superordinate for %s.' % (superordinate_dn, univention.admin.modules.name(module)))
			return out + ["OPERATION FAILED"]

	if len(arglist) == 2:
		out = usage() + module_usage(information)
		return out + ["OPERATION FAILED"]

	action = arglist[2]

	if len(arglist) == 3 and action != 'list':
		out = usage() + module_usage(information, action)
		return out + ["OPERATION FAILED"]

	for opt, val in opts:
		if opt == '--set':
			pos = val.find('=')
			name = val[:pos]
			value = _2utf8(val[pos + 1:])

			was_set = 0
			for mod, (properties, options) in information.items():
				if name in properties:
					if properties[name].multivalue:
						if name not in input:
							input[name] = []
							was_set = 1
						if value:
							input[name].append(value)
							was_set = 1
					else:
						input[name] = value
						was_set = 1

			if not was_set:
				out.append("WARNING: No attribute with name '%s' in this module, value not set." % name)
		elif opt == '--append':
			pos = val.find('=')
			name = val[:pos]
			value = _2utf8(val[pos + 1:])
			was_set = 0
			for mod, (properties, options) in information.items():
				if name in properties:
					if properties[name].multivalue:
						if name not in append:
							append[name] = []
						if value:
							append[name].append(value)
							was_set = 1
					else:
						append[name] = value
						was_set = 1
			if not was_set:
				out.append("WARNING: No attribute with name %s in this module, value not appended." % name)

		elif opt == '--remove':
			pos = val.find('=')
			if pos == -1:
				name = val
				value = None
			else:
				name = val[:pos]
				value = _2utf8(val[pos + 1:])
			was_set = False
			for mod, (properties, options) in information.items():
				if name in properties:
					was_set = True
					if properties[name].multivalue:
						if value is None:
							remove[name] = value
						elif value:
							remove.setdefault(name, [])
							if remove[name] is not None:
								remove[name].append(value)
					else:
						remove[name] = value
			if not was_set:
				out.append("WARNING: No attribute with name %s in this module, value not removed." % name)
		elif opt == '--remove_referring':
			remove_referring = 1
		elif opt == '--recursive':
			recursive = 1

	#+++# ACTION CREATE #+++#
	if action == 'create' or action == 'new':
			if hasattr(module, 'operations') and module.operations:
				if 'add' not in module.operations:
					out.append('Create %s not allowed' % module_name)
					return out + ["OPERATION FAILED"]
			try:
				object = module.object(co, lo, position=position, superordinate=superordinate)
			except univention.admin.uexceptions.insufficientInformation as exc:
				out.append('E: Insufficient information: %s' % (exc,))
				return out + ["OPERATION FAILED"]

			if parsed_options:
				object.options = parsed_options
			for option in parsed_append_options:
				object.options.append(option)
			for option in parsed_remove_options:
				try:
					object.option.remove(option)
				except ValueError:
					pass

			object.open()
			exists = 0
			try:
				out.extend(object_input(module, object, input, append=append))
			except univention.admin.uexceptions.nextFreeIp:
				if not ignore_exists:
					out.append('E: No free IP address found')
					return out + ['OPERATION FAILED']
			except univention.admin.uexceptions.valueInvalidSyntax as err:
				out.append('E: Invalid Syntax: %s' % err)
				return out + ["OPERATION FAILED"]

			default_containers = object.get_default_containers(lo)
			if default_containers and position.isBase() and not any(lo.compare_dn(default_container, position.getDn()) for default_container in default_containers):
				out.append('WARNING: The object is not going to be created underneath of its default containers.')

			object.policy_reference(*policy_reference)

			exists = 0
			exists_msg = None
			created = False
			try:
				dn = object.create()
				created = True
			except univention.admin.uexceptions.objectExists as exc:
				exists_msg = '%s' % (exc,)
				dn = exc.args[0]
				if not ignore_exists:
					out.append('E: Object exists: %s' % exists_msg)
					return out + ["OPERATION FAILED"]
				else:
					exists = 1
			except univention.admin.uexceptions.uidAlreadyUsed as user:
				exists_msg = '(uid) %s' % user
				if not ignore_exists:
					out.append('E: Object exists: %s' % exists_msg)
					return out + ["OPERATION FAILED"]
				else:
					exists = 1
			except univention.admin.uexceptions.groupNameAlreadyUsed as group:
				exists_msg = '(group) %s' % group
				if not ignore_exists:
					out.append('E: Object exists: %s' % exists_msg)
					return out + ["OPERATION FAILED"]
				else:
					exists = 1
			except univention.admin.uexceptions.dhcpServerAlreadyUsed as name:
				exists_msg = '(dhcpserver) %s' % name
				if not ignore_exists:
					out.append('E: Object exists: %s' % exists_msg)
					return out + ["OPERATION FAILED"]
				else:
					exists = 1
			except univention.admin.uexceptions.macAlreadyUsed as mac:
				exists_msg = '(mac) %s' % mac
				if not ignore_exists:
					out.append('E: Object exists: %s' % exists_msg)
					return out + ["OPERATION FAILED"]
				else:
					exists = 1
			except univention.admin.uexceptions.noLock as e:
				exists_msg = '(nolock) %s' % (e,)
				if not ignore_exists:
					out.append('E: Object exists: %s' % exists_msg)
					return out + ["OPERATION FAILED"]
				else:
					exists = 1
			except univention.admin.uexceptions.invalidDhcpEntry:
				out.append('E: The DHCP entry for this host should contain the zone dn, the ip address and the mac address.')
				return out + ["OPERATION FAILED"]
			except univention.admin.uexceptions.invalidOptions as e:
				out.append('E: invalid Options: %s' % e)
				if not ignore_exists:
					return out + ["OPERATION FAILED"]
			except univention.admin.uexceptions.insufficientInformation as exc:
				out.append('E: Insufficient information: %s' % (exc,))
				return out + ["OPERATION FAILED"]
			except univention.admin.uexceptions.noObject as e:
				out.append('E: object not found: %s' % e)
				return out + ["OPERATION FAILED"]
			except univention.admin.uexceptions.circularGroupDependency as e:
				out.append('E: circular group dependency detected: %s' % e)
				return out + ["OPERATION FAILED"]
			except univention.admin.uexceptions.invalidChild as e:
				out.append('E: %s' % e)
				return out + ["OPERATION FAILED"]

			if exists == 1:
				if exists_msg:
					out.append('Object exists: %s' % exists_msg)
				else:
					out.append('Object exists')
			elif created:
				out.append('Object created: %s' % _2utf8(dn))

	#+++# ACTION MODIFY #+++#
	elif action == 'modify' or action == 'edit' or action == 'move':
		if not dn:
			out.append('E: DN is missing')
			return out + ["OPERATION FAILED"]

		object_modified = 0

		if hasattr(module, 'operations') and module.operations:
			if 'edit' not in module.operations:
				out.append('Modify %s not allowed' % module_name)
				return out + ["OPERATION FAILED"]

		try:
			object = univention.admin.objects.get(module, co, lo, position='', dn=dn)
		except univention.admin.uexceptions.noObject:
			out.append('E: object not found')
			return out + ["OPERATION FAILED"]

		object.open()

		if action == 'move':
			if hasattr(module, 'operations') and module.operations:
				if 'move' not in module.operations:
					out.append('Move %s not allowed' % module_name)
					return out + ["OPERATION FAILED"]
			if not position_dn:
				out.append("need new position for moving object")
			else:
				try:  # check if destination exists
					lo.get(position_dn, required=True)
				except (univention.admin.uexceptions.noObject, ldap.INVALID_DN_SYNTAX):
					out.append("position does not exists: %s" % position_dn)
					return out + ["OPERATION FAILED"]
				rdn = ldap.dn.dn2str([ldap.dn.str2dn(dn)[0]])
				newdn = "%s,%s" % (rdn, position_dn)
				try:
					object.move(newdn)
					object_modified += 1
				except univention.admin.uexceptions.noObject:
					out.append('E: object not found')
					return out + ["OPERATION FAILED"]
				except univention.admin.uexceptions.ldapError as msg:
					out.append("ldap Error: %s" % msg)
					return out + ["OPERATION FAILED"]
				except univention.admin.uexceptions.nextFreeIp:
					out.append('E: No free IP address found')
					return out + ['OPERATION FAILED']
				except univention.admin.uexceptions.valueInvalidSyntax as err:
					out.append('E: Invalid Syntax: %s' % err)
					return out + ["OPERATION FAILED"]
				except univention.admin.uexceptions.invalidOperation as msg:
					out.append(str(msg))
					return out + ["OPERATION FAILED"]

		else:  # modify

			if (len(input) + len(append) + len(remove) + len(parsed_append_options) + len(parsed_remove_options) + len(parsed_options) + len(policy_reference) + len(policy_dereference)) > 0:
				if parsed_options:
					object.options = parsed_options
				for option in parsed_append_options:
					object.options.append(option)
				for option in parsed_remove_options[:]:
					try:
						object.options.remove(option)
					except ValueError:
						parsed_remove_options.remove(option)
						out.append('WARNING: option %r is not set. Ignoring.' % (option,))

				try:
					out.extend(object_input(module, object, input, append, remove))
				except univention.admin.uexceptions.valueMayNotChange as e:
					out.append(unicode(e[0]))
					return out + ["OPERATION FAILED"]

				object.policy_reference(*policy_reference)
				object.policy_dereference(*policy_dereference)

				if object.hasChanged(input.keys()) or object.hasChanged(append.keys()) or object.hasChanged(remove.keys()) or parsed_append_options or parsed_remove_options or parsed_options or object.policiesChanged():
					try:
						dn = object.modify()
						object_modified += 1
					except univention.admin.uexceptions.noObject:
						out.append('E: object not found')
						return out + ["OPERATION FAILED"]
					except univention.admin.uexceptions.invalidDhcpEntry:
						out.append('E: The DHCP entry for this host should contain the zone dn, the ip address and the mac address.')
						return out + ["OPERATION FAILED"]
					except univention.admin.uexceptions.circularGroupDependency as e:
						out.append('E: circular group dependency detected: %s' % e)
						return out + ["OPERATION FAILED"]
					except univention.admin.uexceptions.valueInvalidSyntax as e:
						out.append('E: Invalid Syntax: %s' % e)
						return out + ["OPERATION FAILED"]

		if object_modified > 0:
			out.append('Object modified: %s' % _2utf8(dn))
		else:
			out.append('No modification: %s' % _2utf8(dn))

	elif action == 'remove' or action == 'delete':

		if hasattr(module, 'operations') and module.operations:
			if 'remove' not in module.operations:
				out.append('Remove %s not allowed' % module_name)
				return out + ["OPERATION FAILED"]

		try:
			if dn and filter:
				object = univention.admin.modules.lookup(module, co, lo, scope='sub', superordinate=superordinate, base=dn, filter=filter, required=True, unique=True)[0]
			elif dn:
				object = univention.admin.modules.lookup(module, co, lo, scope='base', superordinate=superordinate, base=dn, filter=filter, required=True, unique=True)[0]
			elif filter:
				object = univention.admin.modules.lookup(module, co, lo, scope='sub', superordinate=superordinate, base=position.getDn(), filter=filter, required=True, unique=True)[0]
			else:
				out.append('E: dn or filter needed')
				return out + ["OPERATION FAILED"]
		except (univention.admin.uexceptions.noObject, IndexError):
			if ignore_not_exists:
				out.append('Object not found: %s' % _2utf8(dn or filter))
				return out
			out.append('E: object not found')
			return out + ["OPERATION FAILED"]

		object.open()

		if remove_referring and univention.admin.objects.wantsCleanup(object):
			univention.admin.objects.performCleanup(object)

		if recursive:
			try:
				object.remove(recursive)
			except univention.admin.uexceptions.ldapError as msg:
				out.append(str(msg))
				return out + ["OPERATION FAILED"]
		else:
			try:
				object.remove()
			except univention.admin.uexceptions.primaryGroupUsed:
				out.append('E: object in use')
				return out + ["OPERATION FAILED"]
		out.append('Object removed: %s' % _2utf8(dn or object.dn))

	elif action == 'list' or action == 'lookup':

		if hasattr(module, 'operations') and module.operations:
			if 'search' not in module.operations:
				out.append('Search %s not allowed' % module_name)
				return out + ["OPERATION FAILED"]

		out.append(_2utf8(filter))

		try:
			for object in univention.admin.modules.lookup(module, co, lo, scope='sub', superordinate=superordinate, base=position.getDn(), filter=filter):
				out.append('DN: %s' % _2utf8(univention.admin.objects.dn(object)))

				if (hasattr(module, 'virtual') and not module.virtual) or not hasattr(module, 'virtual'):
					object.open()
					for key, value in sorted(object.items()):
						if key == 'sambaLogonHours':
							# returns a list, which breaks things here
							# better show the bit string. See Bug #33703
							value = module.mapping.mapValue(key, value)
						s = module.property_descriptions[key].syntax
						if module.property_descriptions[key].multivalue:
							for v in value:
								if s.tostring(v):
									out.append('  %s: %s' % (_2utf8(key), _2utf8(s.tostring(v))))
								else:
									out.append('  %s: %s' % (_2utf8(key), None))
						else:
							if s.tostring(value):
								if module.module == 'settings/portal' and key == 'content':
									out.append('  %s:\n  %s' % (_2utf8(key), _2utf8(s.tostring(value).replace('\n', '\n  '))))
								else:
									out.append('  %s: %s' % (_2utf8(key), _2utf8(s.tostring(value))))
							else:
								out.append('  %s: %s' % (_2utf8(key), None))

					if 'univentionPolicyReference' in lo.get(univention.admin.objects.dn(object), ['objectClass'])['objectClass']:
						references = lo.get(_2utf8(univention.admin.objects.dn(object)), ['univentionPolicyReference'])
						if references:
							for el in references['univentionPolicyReference']:
								out.append('  %s: %s' % ('univentionPolicyReference', _2utf8(s.tostring(el))))

				if list_policies:
					utf8_objectdn = _2utf8(univention.admin.objects.dn(object))
					p1 = subprocess.Popen(['univention_policy_result'] + policyOptions + [utf8_objectdn], stdout=subprocess.PIPE)
					policyResults = p1.communicate()[0].split('\n')

					out.append("  Policy-based Settings:")
					policy = ''
					attribute = ''
					value = []
					client = {}
					for line in policyResults:
						line = line.strip()
						if not line or line.startswith("DN: ") or line.startswith("POLICY "):
							continue
						out.append("    %s" % line)

						if not policies_with_DN:
							ckey, cval = line.split('=', 1)
							client.setdefault(ckey, []).append(cval)
							continue

						ckey, cval = line.split(': ', 1)
						if ckey == 'Policy':
							if policy:
								client[attribute] = [policy, value]
								value = []
							policy = cval
						elif ckey == 'Attribute':
							attribute = cval
						elif ckey == 'Value':
							value.append(cval)

					if policies_with_DN:
						client[attribute] = [policy, value]
						value = []

					out.append('')

					if module_name == 'dhcp/host':
						subnet_module = univention.admin.modules.get('dhcp/subnet')
						# TODO: sharedsubnet_module = univention.admin.modules.get('dhcp/sharedsubnet')
						ips = object['fixedaddress']
						for ip in ips:
							for subnet in univention.admin.modules.lookup(subnet_module, co, lo, scope='sub', superordinate=superordinate, base=superordinate_dn, filter=''):
								if univention.admin.ipaddress.ip_is_in_network(subnet['subnet'], subnet['subnetmask'], ip):
									utf8_subnet_dn = _2utf8(subnet.dn)
									p1 = subprocess.Popen(['univention_policy_result'] + policyOptions + [utf8_subnet_dn], stdout=subprocess.PIPE)
									policyResults = p1.communicate()[0].split('\n')
									out.append("  Subnet-based Settings:")
									ddict = {}
									policy = ''
									value = []
									for line in policyResults:
										if not (line.strip() == "" or line.strip()[:4] == "DN: " or line.strip()[:7] == "POLICY "):
											out.append("    %s" % line.strip())
											if policies_with_DN:
												subsplit = string.split(line.strip(), ': ')
												if subsplit[0] == 'Policy':
													if policy:
														ddict[attribute] = [policy, value]
														value = []
													policy = subsplit[1]
												elif subsplit[0] == 'Attribute':
													attribute = subsplit[1]
												elif subsplit[0] == 'Value':
													value.append(subsplit[1])
											else:
												subsplit = string.split(line.strip(), '=')
												if subsplit[0] not in ddict:
													ddict[subsplit[0]] = []
												ddict[subsplit[0]].append(subsplit[1])

									out.append('')

									if policies_with_DN:
										ddict[attribute] = [policy, value]
										value = []

									out.append("  Merged Settings:")

									for key in ddict.keys():
										if key not in client:
											client[key] = ddict[key]

									if policies_with_DN:
										for key in client.keys():
											out.append("    Policy: " + client[key][0])
											out.append("    Attribute: " + key)
											for i in range(0, len(client[key][1])):
												out.append("    Value: " + client[key][1][i])
									else:
										for key in client.keys():
											for i in range(0, len(client[key])):
												out.append("    %s=%s" % (key, client[key][i]))
									out.append('')

				out.append('')
		except univention.admin.uexceptions.ldapError as errmsg:
			out.append('%s' % str(errmsg))
			return out + ["OPERATION FAILED"]
		except univention.admin.uexceptions.valueInvalidSyntax as errmsg:
			out.append('%s' % str(errmsg.message))
			return out + ["OPERATION FAILED"]
	else:
		out.append("Unknown or no action defined")
		out.append('')
		usage()
		return out + ["OPERATION FAILED"]

	return out  # nearly the only successful return


if __name__ == '__main__':
	import sys
	print('\n'.join(doit(sys.argv)))
