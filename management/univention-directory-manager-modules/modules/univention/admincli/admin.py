#!/usr/bin/python3
# -*- coding: utf-8 -*-
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

"""
command line frontend to univention-directory-manager (module)
"""

from __future__ import print_function
import getopt
import base64
import os
import subprocess
import traceback
from ipaddress import IPv4Address, IPv4Network

import ldap
import six

import univention.debug as ud

import univention.admin.uexceptions
import univention.admin.uldap
import univention.admin.modules
import univention.admin.objects
from univention.admin.layout import Group
from univention.admin.syntax import ldapFilter
import univention.config_registry

univention.admin.modules.update()


class OperationFailed(Exception):

	def __init__(self, out=None, msg=None):
		self.out = out or []
		if msg:
			self.out.append(msg)


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
	out.append('  --%-30s   ' % ('ignore_not_exists'))
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
						if isinstance(row, six.string_types):
							_print_property(module, action, row, out)
							continue
						for item in row:
							_print_property(module, action, item, out)
				else:
					if isinstance(row, six.string_types):
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


def object_input(module, object, input, append=None, remove=None):
	out = []
	if append:
		for key, values in append.items():
			if key in object and not object.has_property(key):
				opts = module.property_descriptions[key].options
				if len(opts) == 1:
					object.options.extend(opts)
					out.append('WARNING: %s was set without --append-option. Automatically appending %s.' % (key, ', '.join(opts)))

			if module.property_descriptions[key].syntax.name == 'file':
				if os.path.exists(values):
					with open(values, 'r') as fh:
						object[key] = fh.read()
				else:
					out.append('WARNING: file not found: %s' % values)
			else:
				if univention.admin.syntax.is_syntax(module.property_descriptions[key].syntax, univention.admin.syntax.complex):
					values = _parse_complex_syntax_input(values if isinstance(values, list) else [values])
				current_values = list(object[key] or [])
				if current_values == ['']:
					current_values = []

				for val in values:
					if val in current_values:
						out.append('WARNING: cannot append %s to %s, value exists' % (val, key))
					else:
						current_values.append(val)

				if not module.property_descriptions[key].multivalue:
					out.append('WARNING: using --append on a single value property (%s) is not supported.' % (key,))
					try:
						current_values = current_values[-1]
					except IndexError:
						current_values = None

				try:
					object[key] = current_values
				except univention.admin.uexceptions.valueInvalidSyntax as errmsg:
					raise OperationFailed(out, 'E: Invalid Syntax: %s' % (errmsg,))

	if remove:
		for key, values in remove.items():
			current_values = [object[key]] if not module.property_descriptions[key].multivalue else list(object[key])
			if values is None:
				current_values = []
			else:
				vallist = [values] if isinstance(values, six.string_types) else values
				if univention.admin.syntax.is_syntax(module.property_descriptions[key].syntax, univention.admin.syntax.complex):
					vallist = _parse_complex_syntax_input(vallist)

				for val in vallist:
					try:
						normalized_val = module.property_descriptions[key].syntax.parse(val)
					except (univention.admin.uexceptions.valueInvalidSyntax, univention.admin.uexceptions.valueError):
						normalized_val = None

					if val in current_values:
						current_values.remove(val)
					elif normalized_val is not None and normalized_val in current_values:
						current_values.remove(normalized_val)
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
					with open(value, 'r') as fh:
						content = fh.read()
						if "----BEGIN CERTIFICATE-----" in content:
							content = content.replace('----BEGIN CERTIFICATE-----', '')
							content = content.replace('----END CERTIFICATE-----', '')
							object[key] = base64.decodestring(content)
						else:
							object[key] = content
				else:
					out.append('WARNING: file not found: %s' % value)

			else:
				if univention.admin.syntax.is_syntax(module.property_descriptions[key].syntax, univention.admin.syntax.complex):
					if isinstance(value, list):
						value = _parse_complex_syntax_input(value)[-1]
					else:
						value = _parse_complex_syntax_input([value])[0]

					if module.property_descriptions[key].multivalue:
						value = [value]
				try:
					object[key] = value
				except univention.admin.uexceptions.ipOverridesNetwork as exc:
					out.append('WARNING: %s' % exc.message)
				except univention.admin.uexceptions.valueMayNotChange as exc:
					raise univention.admin.uexceptions.valueMayNotChange("%s: %s" % (exc.message, key))
	return out


def _parse_complex_syntax_input(values):
	parsed_values = []
	for value in values:
		if '"' not in value:
			value = value.split(' ')
		else:
			value = [x.strip() for x in value.split('"') if x.strip()]
		parsed_values.append(value)
	return parsed_values


def list_available_modules(o=[]):
	o.append("Available Modules are:")
	for mod in sorted(univention.admin.modules.modules):
		o.append("  %s" % mod)
	return o


def doit(arglist):
	out = []
	try:
		out = _doit(arglist)
	except OperationFailed as exc:
		return exc.out + ["OPERATION FAILED"]
	except ldap.SERVER_DOWN:
		return out + ["E: The LDAP Server is currently not available.", "OPERATION FAILED"]
	except univention.admin.uexceptions.base as e:
		ud.debug(ud.ADMIN, ud.WARN, str(e))

		# collect error information
		msg = []
		if getattr(e, 'message', None):
			msg.append(e.message)
		if getattr(e, 'args', None):
			# avoid duplicate messages
			if not len(msg) or len(e.args) > 1 or e.args[0] != msg[0]:
				msg.extend(e.args)

		# strip elements and make sure that a ':' is printed if further information follows
		msg = [i.strip() for i in msg]
		if len(msg) == 1:
			msg[0] = '%s.' % msg[0].strip(':.')
		elif len(msg) > 1:
			msg[0] = '%s:' % msg[0].strip(':.')

		# append to the output
		out.append(' '.join(msg))
		return out + ["OPERATION FAILED"]
	except BaseException:
		ud.debug(ud.ADMIN, ud.ERROR, traceback.format_exc())
		raise
	return out


def _doit(arglist):
	out = []
	# parse module and action
	if len(arglist) < 2:
		raise OperationFailed(usage())

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
		raise OperationFailed(out, str(msg))

	if args and isinstance(args, list):
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
			position_dn = val
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
			except IOError as exc:
				raise OperationFailed(out, 'E: could not read bindpwd from file (%s)' % (exc,))
		elif opt == '--dn':
			dn = val
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
		ud.init(logfile, ud.FLUSH, ud.NO_FUNCTION)
	else:
		out.append("WARNING: no logfile specified")

	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()

	baseDN = configRegistry['ldap/base']

	debug_level = int(configRegistry.get('directory/manager/cmd/debug/level', 0))

	ud.set_level(ud.LDAP, debug_level)
	ud.set_level(ud.ADMIN, debug_level)

	if binddn and bindpwd:
		ud.debug(ud.ADMIN, ud.INFO, "using %s account" % binddn)
		try:
			lo = univention.admin.uldap.access(host=configRegistry['ldap/master'], port=int(configRegistry.get('ldap/master/port', '7389')), base=baseDN, binddn=binddn, start_tls=tls, bindpw=bindpwd)
		except Exception as exc:
			ud.debug(ud.ADMIN, ud.WARN, 'authentication error: %s' % (exc,))
			raise OperationFailed(out, 'authentication error: %s' % (exc,))
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
			with open(secretFileName, 'r') as secretFile:
				pwd = secretFile.read().strip('\n')
		except IOError:
			raise OperationFailed(out, 'E: Permission denied, try --binddn and --bindpwd')

		try:
			lo = univention.admin.uldap.access(host=configRegistry['ldap/master'], port=int(configRegistry.get('ldap/master/port', '7389')), base=baseDN, binddn=binddn, bindpw=pwd, start_tls=tls)
		except Exception as exc:
			ud.debug(ud.ADMIN, ud.WARN, 'authentication error: %s' % (exc,))
			raise OperationFailed(out, 'authentication error: %s' % (exc,))

	if not position_dn and superordinate_dn:
		position_dn = superordinate_dn
	elif not position_dn:
		position_dn = baseDN

	try:
		position = univention.admin.uldap.position(baseDN)
		position.setDn(position_dn)
	except univention.admin.uexceptions.noObject:
		raise OperationFailed(out, 'E: Invalid position')

	module = univention.admin.modules.get(module_name)
	if not module:
		out.append("unknown module %s." % module_name)
		out.append("")
		raise OperationFailed(list_available_modules(out))

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
			raise OperationFailed(out, 'E: %s is not a superordinate for %s.' % (superordinate_dn, univention.admin.modules.name(module)))

	if len(arglist) == 2:
		out = usage() + module_usage(information)
		raise OperationFailed(out)

	action = arglist[2]

	if len(arglist) == 3 and action != 'list':
		out = usage() + module_usage(information, action)
		raise OperationFailed(out)

	for opt, val in opts:
		if opt == '--set':
			name, delim, value = val.partition('=')

			for mod, (properties, options) in information.items():
				if name in properties:
					if properties[name].multivalue:
						input.setdefault(name, [])
						if value:
							input[name].append(value)
					else:
						input[name] = value

			if name not in input:
				out.append("WARNING: No attribute with name '%s' in this module, value not set." % name)
		elif opt == '--append':
			name, delim, value = val.partition('=')
			for mod, (properties, options) in information.items():
				if name in properties:
					if properties[name].multivalue:
						append.setdefault(name, [])
						if value:
							append[name].append(value)
					else:
						append[name] = value
			if name not in append:
				out.append("WARNING: No attribute with name %s in this module, value not appended." % name)

		elif opt == '--remove':
			name, delim, value = val.partition('=')
			value = value or None
			for mod, (properties, options) in information.items():
				if name in properties:
					if properties[name].multivalue:
						if value is None:
							remove[name] = value
						elif value:
							remove.setdefault(name, [])
							if remove[name] is not None:
								remove[name].append(value)
					else:
						remove[name] = value
			if name not in remove:
				out.append("WARNING: No attribute with name %s in this module, value not removed." % name)
		elif opt == '--remove_referring':
			remove_referring = True
		elif opt == '--recursive':
			recursive = True

	cli = CLI(module_name, module, dn, lo, position, superordinate)
	if action == 'create' or action == 'new':
		out.extend(cli.create(input, append, ignore_exists, parsed_options, parsed_append_options, parsed_remove_options, policy_reference))
	elif action == 'modify' or action == 'edit':
		out.extend(cli.modify(input, append, remove, parsed_append_options, parsed_remove_options, parsed_options, policy_reference, policy_dereference, ignore_not_exists=ignore_not_exists))
	elif action == 'move':
		out.extend(cli.move(position_dn))
	elif action == 'remove' or action == 'delete':
		out.extend(cli.remove(remove_referring=remove_referring, recursive=recursive, ignore_not_exists=ignore_not_exists, filter=filter))
	elif action == 'list' or action == 'lookup':
		out.extend(cli.list(list_policies, filter, superordinate_dn, policyOptions, policies_with_DN))
	else:
		out.append("Unknown or no action defined")
		out.append('')
		raise OperationFailed(out)

	return out  # nearly the only successful return


class CLI(object):

	def __init__(self, module_name, module, dn, lo, position, superordinate):
		self.module_name = module_name
		self.module = module
		self.dn = dn
		self.lo = lo
		self.position = position
		self.superordinate = superordinate

	def create(self, *args, **kwargs):
		return self._create(self.module_name, self.module, self.dn, self.lo, self.position, self.superordinate, *args, **kwargs)

	def modify(self, *args, **kwargs):
		return self._modify(self.module_name, self.module, self.dn, self.lo, self.position, self.superordinate, *args, **kwargs)

	def move(self, *args, **kwargs):
		return self._move(self.module_name, self.module, self.dn, self.lo, self.position, self.superordinate, *args, **kwargs)

	def remove(self, *args, **kwargs):
		return self._remove(self.module_name, self.module, self.dn, self.lo, self.position, self.superordinate, *args, **kwargs)

	def list(self, *args, **kwargs):
		return self._list(self.module_name, self.module, self.dn, self.lo, self.position, self.superordinate, *args, **kwargs)

	def _create(self, module_name, module, dn, lo, position, superordinate, input, append, ignore_exists, parsed_options, parsed_append_options, parsed_remove_options, policy_reference):
		out = []
		if not univention.admin.modules.supports(module_name, 'add'):
			raise OperationFailed(out, 'Create %s not allowed' % module_name)

		try:
			object = module.object(None, lo, position=position, superordinate=superordinate)
		except univention.admin.uexceptions.insufficientInformation as exc:
			raise OperationFailed(out, 'E: Insufficient information: %s' % (exc,))

		if parsed_options:
			object.options = parsed_options
		for option in parsed_append_options:
			object.options.append(option)
		for option in parsed_remove_options:
			try:
				object.options.remove(option)
			except ValueError:
				pass

		object.open()
		try:
			out.extend(object_input(module, object, input, append=append))
		except univention.admin.uexceptions.nextFreeIp:
			if not ignore_exists:
				raise OperationFailed(out, 'E: No free IP address found')
		except univention.admin.uexceptions.valueInvalidSyntax as err:
			raise OperationFailed(out, 'E: Invalid Syntax: %s' % err)

		default_containers = object.get_default_containers(lo)
		if default_containers and position.isBase() and not any(lo.compare_dn(default_container, position.getDn()) for default_container in default_containers):
			out.append('WARNING: The object is not going to be created underneath of its default containers.')

		object.policy_reference(*policy_reference)

		exists = False
		exists_msg = None
		created = False
		try:
			dn = object.create()
			created = True
		except univention.admin.uexceptions.objectExists as exc:
			exists_msg = '%s' % (exc,)
			dn = exc.args[0]
			if not ignore_exists:
				raise OperationFailed(out, 'E: Object exists: %s' % exists_msg)
			else:
				exists = 1
		except univention.admin.uexceptions.uidAlreadyUsed as user:
			exists_msg = '(uid) %s' % user
			if not ignore_exists:
				raise OperationFailed(out, 'E: Object exists: %s' % exists_msg)
			else:
				exists = 1
		except univention.admin.uexceptions.groupNameAlreadyUsed as group:
			exists_msg = '(group) %s' % group
			if not ignore_exists:
				raise OperationFailed(out, 'E: Object exists: %s' % exists_msg)
			else:
				exists = 1
		except univention.admin.uexceptions.dhcpServerAlreadyUsed as name:
			exists_msg = '(dhcpserver) %s' % name
			if not ignore_exists:
				raise OperationFailed(out, 'E: Object exists: %s' % exists_msg)
			else:
				exists = 1
		except univention.admin.uexceptions.macAlreadyUsed as mac:
			exists_msg = '(mac) %s' % mac
			if not ignore_exists:
				raise OperationFailed(out, 'E: Object exists: %s' % exists_msg)
			else:
				exists = 1
		except univention.admin.uexceptions.noLock as e:
			exists_msg = '(nolock) %s' % (e,)
			if not ignore_exists:
				raise OperationFailed(out, 'E: Object exists: %s' % exists_msg)
			else:
				exists = 1
		except univention.admin.uexceptions.invalidDhcpEntry:
			raise OperationFailed(out, 'E: The DHCP entry for this host should contain the zone dn, the ip address and the mac address.')
		except univention.admin.uexceptions.invalidOptions as e:
			out.append('E: invalid Options: %s' % e)
			if not ignore_exists:
				raise OperationFailed(out)
		except univention.admin.uexceptions.insufficientInformation as exc:
			raise OperationFailed(out, 'E: Insufficient information: %s' % (exc,))
		except univention.admin.uexceptions.noObject as e:
			raise OperationFailed(out, 'E: object not found: %s' % e)
		except univention.admin.uexceptions.circularGroupDependency as e:
			raise OperationFailed(out, 'E: circular group dependency detected: %s' % e)
		except univention.admin.uexceptions.invalidChild as e:
			raise OperationFailed(out, 'E: %s' % e)

		if exists:
			if exists_msg:
				out.append('Object exists: %s' % exists_msg)
			else:
				out.append('Object exists')
		elif created:
			out.append('Object created: %s' % dn)

		return out

	def _move(self, module_name, module, dn, lo, position, superordinate, position_dn):
		out = []
		if not dn:
			raise OperationFailed(out, 'E: DN is missing')

		object_modified = 0

		if not univention.admin.modules.supports(module_name, 'edit'):
			raise OperationFailed(out, 'Modify %s not allowed' % module_name)

		try:
			object = univention.admin.objects.get(module, None, lo, position='', dn=dn)
		except univention.admin.uexceptions.noObject:
			raise OperationFailed(out, 'E: object not found')

		object.open()

		if not univention.admin.modules.supports(module_name, 'move'):
			raise OperationFailed(out, 'Move %s not allowed' % module_name)

		if not position_dn:
			out.append("need new position for moving object")
		else:
			try:  # check if destination exists
				lo.get(position_dn, required=True)
			except (univention.admin.uexceptions.noObject, ldap.INVALID_DN_SYNTAX):
				raise OperationFailed(out, "position does not exists: %s" % position_dn)
			rdn = ldap.dn.dn2str([ldap.dn.str2dn(dn)[0]])
			newdn = "%s,%s" % (rdn, position_dn)
			try:
				object.move(newdn)
				object_modified += 1
			except univention.admin.uexceptions.noObject:
				raise OperationFailed(out, 'E: object not found')
			except univention.admin.uexceptions.ldapError as msg:
				raise OperationFailed(out, "ldap Error: %s" % msg)
			except univention.admin.uexceptions.nextFreeIp:
				raise OperationFailed(out, 'E: No free IP address found')
			except univention.admin.uexceptions.valueInvalidSyntax as err:
				raise OperationFailed(out, 'E: Invalid Syntax: %s' % err)
			except univention.admin.uexceptions.invalidOperation as msg:
				raise OperationFailed(out, str(msg))

		if object_modified > 0:
			out.append('Object modified: %s' % dn)
		else:
			out.append('No modification: %s' % dn)

		return out

	def _modify(self, module_name, module, dn, lo, position, superordinate, input, append, remove, parsed_append_options, parsed_remove_options, parsed_options, policy_reference, policy_dereference, ignore_not_exists):
		out = []
		if not dn:
			raise OperationFailed(out, 'E: DN is missing')

		object_modified = 0

		if not univention.admin.modules.supports(module_name, 'edit'):
			raise OperationFailed(out, 'Modify %s not allowed' % module_name)

		try:
			object = univention.admin.objects.get(module, None, lo, position='', dn=dn)
		except univention.admin.uexceptions.noObject:
			if ignore_not_exists:
				out.append('Object not found: %s' % (dn or filter,))
				return out
			raise OperationFailed(out, 'E: object not found')

		object.open()

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
			except univention.admin.uexceptions.valueMayNotChange as exc:
				raise OperationFailed(out, str(exc))

			object.policy_reference(*policy_reference)
			object.policy_dereference(*policy_dereference)

			if object.hasChanged(input.keys()) or object.hasChanged(append.keys()) or object.hasChanged(remove.keys()) or parsed_append_options or parsed_remove_options or parsed_options or object.policiesChanged():
				try:
					dn = object.modify()
					object_modified += 1
				except univention.admin.uexceptions.noObject:
					raise OperationFailed(out, 'E: object not found')
				except univention.admin.uexceptions.invalidDhcpEntry:
					raise OperationFailed(out, 'E: The DHCP entry for this host should contain the zone dn, the ip address and the mac address.')
				except univention.admin.uexceptions.circularGroupDependency as e:
					raise OperationFailed(out, 'E: circular group dependency detected: %s' % e)
				except univention.admin.uexceptions.valueInvalidSyntax as e:
					raise OperationFailed(out, 'E: Invalid Syntax: %s' % e)

		if object_modified > 0:
			out.append('Object modified: %s' % dn)
		else:
			out.append('No modification: %s' % dn)

		return out

	def _remove(self, module_name, module, dn, lo, position, superordinate, recursive, remove_referring, ignore_not_exists, filter):
		out = []
		if not univention.admin.modules.supports(module_name, 'remove'):
			raise OperationFailed(out, 'Remove %s not allowed' % module_name)

		try:
			if dn and filter:
				object = univention.admin.modules.lookup(module, None, lo, scope='sub', superordinate=superordinate, base=dn, filter=filter, required=True, unique=True)[0]
			elif dn:
				object = univention.admin.modules.lookup(module, None, lo, scope='base', superordinate=superordinate, base=dn, filter=filter, required=True, unique=True)[0]
			elif filter:
				object = univention.admin.modules.lookup(module, None, lo, scope='sub', superordinate=superordinate, base=position.getDn(), filter=filter, required=True, unique=True)[0]
			else:
				raise OperationFailed(out, 'E: dn or filter needed')
		except (univention.admin.uexceptions.noObject, IndexError):
			if ignore_not_exists:
				out.append('Object not found: %s' % (dn or filter,))
				return out
			raise OperationFailed(out, 'E: object not found')

		object.open()

		if remove_referring and univention.admin.objects.wantsCleanup(object):
			univention.admin.objects.performCleanup(object)

		if recursive:
			try:
				object.remove(recursive)
			except univention.admin.uexceptions.ldapError as msg:
				raise OperationFailed(out, str(msg))
		else:
			try:
				object.remove()
			except univention.admin.uexceptions.primaryGroupUsed:
				raise OperationFailed(out, 'E: object in use')
		out.append('Object removed: %s' % (dn or object.dn,))

		return out

	def _list(self, module_name, module, dn, lo, position, superordinate, list_policies, filter, superordinate_dn, policyOptions, policies_with_DN):
		out = []
		if not univention.admin.modules.supports(module_name, 'search'):
			raise OperationFailed(out, 'Search %s not allowed' % module_name)

		out.append(filter)

		try:
			for object in univention.admin.modules.lookup(module, None, lo, scope='sub', superordinate=superordinate, base=position.getDn(), filter=filter):
				out.append('DN: %s' % univention.admin.objects.dn(object))

				if not univention.admin.modules.virtual(module_name):
					object.open()
					for key, value in sorted(object.items()):
						s = module.property_descriptions[key].syntax
						if module.property_descriptions[key].multivalue:
							for v in value:
								if s.tostring(v):
									out.append('  %s: %s' % (key, s.tostring(v)))
								else:
									out.append('  %s: %s' % (key, None))
						else:
							if s.tostring(value):
								if module.module == 'settings/portal' and key == 'content':
									out.append('  %s:\n  %s' % (key, s.tostring(value).replace('\n', '\n  ')))
								else:
									out.append('  %s: %s' % (key, s.tostring(value)))
							else:
								out.append('  %s: %s' % (key, None))

					for el in object.policies:
						out.append('  %s: %s' % ('univentionPolicyReference', el))

				if list_policies:
					policyResults = subprocess.check_output(['univention_policy_result'] + policyOptions + [univention.admin.objects.dn(object)], close_fds=True).decode('utf-8').split(u'\n')

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
							ip_ = IPv4Address(u"%s" % (ip,))
							for subnet in univention.admin.modules.lookup(subnet_module, None, lo, scope='sub', superordinate=superordinate, base=superordinate_dn, filter=''):
								if ip_ in IPv4Network(u"%(subnet)s/%(subnetmask)s" % subnet, strict=False):
									policyResults = subprocess.check_output(['univention_policy_result'] + policyOptions + [subnet.dn], close_fds=True).decode('utf-8').split(u'\n')
									out.append("  Subnet-based Settings:")
									ddict = {}
									policy = ''
									value = []
									for line in policyResults:
										if not (line.strip() == "" or line.strip()[:4] == "DN: " or line.strip()[:7] == "POLICY "):
											out.append("    %s" % line.strip())
											if policies_with_DN:
												subsplit = line.strip().split(': ', 1)
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
												subsplit = line.strip().split('=', 1)
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
											for val in client[key][1]:
												out.append("    Value: " + val)
									else:
										for key in client.keys():
											for val in client[key]:
												out.append("    %s=%s" % (key, val))
									out.append('')

				out.append('')
		except univention.admin.uexceptions.ldapError as errmsg:
			raise OperationFailed(out, '%s' % (errmsg,))
		except univention.admin.uexceptions.valueInvalidSyntax as errmsg:
			raise OperationFailed(out, '%s' % (errmsg.message,))

		return out


if __name__ == '__main__':
	import sys
	print('\n'.join(doit(sys.argv)))
