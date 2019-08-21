#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  Univention Directory Manager Module
#
# Copyright 2019 Univention GmbH
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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
import argparse

import ldap
import ldap.dn

import univention.config_registry
from univention.management.server.client import UDM, NotFound, UnprocessableEntity

ucr = univention.config_registry.ConfigRegistry()
ucr.load()


class CLIClient(object):

	def init(self, parser, args):
		self.parser = parser
		username = args.binddn
		try:
			username = ldap.dn.str2dn(username)[0][0][1]
		except (ldap.DECODING_ERROR, IndexError):
			pass
		self.udm = UDM('https://%(hostname)s.%(domainname)s/univention/udm/' % ucr, username, args.bindpwd)

	def create_object(self, args):
		module = self.udm.get(args.object_type)
		obj = module.create_template(position=args.position, superordinate=args.superordinate)
		if args.position:
			obj.position = args.position
		self.set_properties(obj, args)
		self.save_object(obj)
		self.print_line('Object created', obj.dn)

	def modify_object(self, args):
		module = self.udm.get(args.object_type)
		# TODO: re-execute if changed in between
		obj = module.get(args.dn)
		self.set_properties(obj, args)
		self.save_object(obj)
		self.print_line('Object modified', obj.dn)

	def remove_object(self, args):
		module = self.udm.get(args.object_type)
		try:
			obj = module.get(args.dn)
		except NotFound:
			if self.args.ignore_not_exists:
				self.print_line('Object not found', args.dn)
			else:
				raise
		obj.delete(args.remove_referring)
		self.print_line('Object removed', obj.dn)

	def move_object(self, args):
		module = self.udm.get(args.object_type)
		obj = module.get(args.dn)
		obj.position = args.position
		self.save_object(obj)
		self.print_line('Object modified', obj.dn)

	def copy_object(self, args):
		pass

	def save_object(self, obj):
		try:
			obj.save()
		except UnprocessableEntity as exc:
			self.print_error(str(exc))
			raise SystemExit(2)

	def set_properties(self, obj, args):
		obj.superordinate = getattr(args, 'superordinate', None)
		for key, value in obj.options.items():
			if key in args.option or key in args.append_option:
				obj.options[key] = True
			if key in args.remove_option:
				obj.options[key] = False
		for key_val in args.set:
			key, value = key_val.split('=', 1)
			if value.startswith('{') or value.startswith('[') or value.startswith('"') or value.startswith("'"):
				value = eval(value)
			obj.properties[key] = value

		for key_val in args.append:
			key, value = key_val.split('=', 1)
			if value.startswith('{') or value.startswith('[') or value.startswith('"') or value.startswith("'"):
				value = eval(value)
			obj.properties[key].append(value)

		for key_val in getattr(args, 'remove', []):
			if '=' not in key_val:
				obj.properties[key_val] = None
			else:
				key, value = key_val.split('=', 1)
				if value.startswith('{') or value.startswith('[') or value.startswith('"') or value.startswith("'"):
					value = eval(value)
				if obj.properties[key] == value:
					obj.properties[key] = None
				elif isinstance(obj.properties[key], list) and value in obj.properties[key]:
					obj.properties[key].remove(value)

		for policy_dn in args.policy_reference:
			# FIXME: we need to know the type, use policies/policy so far
			obj.policies.setdefault('policies/policy', []).append(policy_dn)

		for policy_dn in getattr(args, 'policy_dereference', []):
			for key, values in list(obj.policies.items()):
				if policy_dn in values:
					values.remove(policy_dn)

	def list_objects(self, args):
		module = self.udm.get(args.object_type)
		for entry in module.search(args.filter, args.position, opened=True, superordinate=args.superordinate):
			self.print_line('')
			self.print_line('DN', entry.dn)
			self.print_line('URL', entry.uri)
			#entry = entry.open()
			for key, value in sorted(entry.props.items()):
				if isinstance(value, list):
					for item in value:
						if isinstance(item, (basestring, int, float)):
							self.print_line(key, item, '  ')
						else:
							self.print_line(key, json.dumps(item, ensure_ascii=False), '  ')
				elif value is None:
					self.print_line(key, '', '  ')
				elif isinstance(value, (bool, int, float)):
					self.print_line(key, str(value), '  ')
				elif isinstance(value, (basestring, int, float)):
					if set(value) & set('\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x7f'):
						key = key + ':'
						value = value.encode('base64').rstrip()
					self.print_line(key, value, '  ')
				elif isinstance(value, dict):
					self.print_line(key, json.dumps(value, ensure_ascii=False, indent=4), '  ')
				else:
					self.print_line(key, repr(value), '  ')
			if args.policies:  # FIXME: do a policy result
				self.print_line('Policy-based Settings:', '', '  ')
				for key, values in entry.policies.items():
					for value in values:
						self.print_line(key, value, '   ')

	def print_line(self, key, value='', prefix=''):
		# prints and makes sure that no ANSI escape sequences or binary data is printed
		if key:
			key = '%s: ' % (key,)
		value = '%s%s%s' % (prefix, key, value)
		value = value.replace('\n', '\n%s' % (prefix,))
		print(''.join(v for v in value if v not in '\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\r\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x7f'))

	def print_warning(self, value='', prefix='Warning'):
		self.print_line('', value, prefix)

	def print_error(self, value='', prefix='Error'):
		self.print_line(prefix, value, '')

	def infos(self, args):
		args.parser.print_help()
		for sub in args.subparsers.choices.values():
			sub.print_help()
		self.get_info(args)

	def get_info(self, args):
		module = self.udm.get(args.object_type)
		if module is None:
			self.print_error('The given module is unknown')
			for mod, modtitle in sorted(set((x.name, x.title) for x in self.udm.modules())):
				self.print_line(mod, modtitle, prefix='  ')
			return
		module.load_relations()
		resp = module.client.make_request('GET', module.relations['create-form'][0]['href'])  # TODO: integrate in client.py?
		mod = module.client.eval_response(resp)
		properties = dict((prop['id'], prop) for prop in mod['properties'])
		layout = mod['layout']

		for layout in layout:
			print('  %s - %s:' % (layout['label'], layout['description']))
			for sub in layout['layout']:
				self.print_layout(sub, properties)
			print()

	def print_layout(self, sub, properties, indent=1):
		def _print_prop(prop):
			def _print(prop):
				if isinstance(prop, dict):
					print(repr(prop))
					return
				print('\t\t%s%s' % (prop.ljust(41), properties.get(prop, {}).get('label')))

			if isinstance(prop, list):
				for prop in prop:
					_print(prop)
			else:
				_print(prop)

		if isinstance(sub, dict):
			print('\t%s %s' % (sub['label'], sub['description']))
			for prop in sub['layout']:
				if isinstance(prop, dict):
					self.print_layout(prop, properties, indent + 1)
				else:
					_print_prop(prop)
		else:
			if isinstance(sub, dict):
				self.print_layout(prop, properties, indent + 1)
			else:
				_print_prop(sub)

	def license(self, args):
		pass


def main():
	client = CLIClient()
	parser = argparse.ArgumentParser(
		prog='univention-directory-manager',
		description='copyright (c) 2001-2019 Univention GmbH, Germany',
		usage='%(prog)s command line interface for managing UCS',
		epilog='''Description:
univention-directory-manager is a tool to handle the configuration for UCS on command line level.
Use "univention-directory-manager modules" for a list of available modules.''',
	)
	parser.set_defaults(parser=parser)
	parser.add_argument('--binddn', help='bind DN', default='Administrator')
	parser.add_argument('--bindpwd', help='bind password', default='univention')
	parser.add_argument('--bindpwdfile', help='file containing bind password')
	parser.add_argument('--logfile', help='path and name of the logfile to be used')
	parser.add_argument('--tls', choices=['0', '1', '2'], default='2', help='0 (no); 1 (try); 2 (must)')
	parser.add_argument('object_type')

	try:
		class Format(argparse.ArgumentDefaultsHelpFormatter):
			def format_help(self):
				return ''

		parser.formatter_class = Format
		preargs = parser.parse_known_args()[0]
	except SystemExit:
		preargs = None

	subparsers = parser.add_subparsers(dest='action', title='actions', description='All available actions')
	parser.set_defaults(subparsers=subparsers)
	create = subparsers.add_parser('create', description='Create a new object')
	create.set_defaults(func=client.create_object)
	create.add_argument('--position', help='Set position in tree')
	# create.add_argument('--default-position', action='store_true', help='Create in the default position')  # TODO: probably better make this the default?
	# create.add_argument('--template', help='Use template for creation')
	create.add_argument('--set', action='append', help='Set property to value, e.g. foo=bar', default=[])
	create.add_argument('--append', action='append', help='Append value to property, e.g. foo=bar', default=[])
	create.add_argument('--remove', action='append', help='Remove value from property, e.g. foo=bar', default=[])
	create.add_argument('--superordinate', help='Use superordinate')
	create.add_argument('--option', action='append', help='Use only given module options', default=[])
	create.add_argument('--append-option', action='append', help='Append the module options', default=[])
	create.add_argument('--remove-option', action='append', help='Remove the module options', default=[])
	create.add_argument('--policy-reference', action='append', help='Reference to policy given by DN', default=[])
	create.add_argument('--ignore-exists', action='store_true', help='ignore if object already exists')

	modify = subparsers.add_parser('modify', description='Modify an existing object')
	modify.set_defaults(func=client.modify_object)
	modify.add_argument('--dn', help='Edit object with DN')
	modify.add_argument('--set', action='append', help='Set property to value, e.g. foo=bar', default=[])
	modify.add_argument('--append', action='append', help='Append value to property, e.g. foo=bar', default=[])
	modify.add_argument('--remove', action='append', help='Remove value from property, e.g. foo=bar', default=[])
	modify.add_argument('--option', action='append', help='Use only given module options', default=[])
	modify.add_argument('--append-option', action='append', help='Append the module options', default=[])
	modify.add_argument('--remove-option', action='append', help='Remove the module options', default=[])
	modify.add_argument('--policy-reference', action='append', help='Reference to policy given by DN', default=[])
	modify.add_argument('--policy-dereference', action='append', help='Remove reference to policy given by DN', default=[])

	remove = subparsers.add_parser('remove', description='Remove an existing object')
	remove.set_defaults(func=client.remove_object)
	remove.add_argument('--dn', help='Remove object with DN')
	# remove.add_argument('--superordinate', help='Use superordinate')  # not required
	remove.add_argument('--filter', help='Lookup filter e.g. foo=bar')
	remove.add_argument('--remove-referring', action='store_true', help='remove referring objects', default=False)
	remove.add_argument('--ignore-not-exists', action='store_true', help='ignore if object does not exists')

	list_ = subparsers.add_parser('list', description='List objects')
	list_.set_defaults(func=client.list_objects)
	list_.add_argument('--filter', help='Lookup filter e.g. foo=bar', default='')
	list_.add_argument('--position', help='Search underneath of position in tree')
	list_.add_argument('--superordinate', help='Use superordinate')
	list_.add_argument('--policies', help='List policy-based settings: 0:short, 1:long (with policy-DN)')

	move = subparsers.add_parser('move', description='Move object in directory tree')
	move.set_defaults(func=client.move_object)
	move.add_argument('--dn', help='Move object with DN')
	move.add_argument('--position', help='Move to position in tree')

	copy = subparsers.add_parser('copy', description='Copy object in directory tree')
	copy.set_defaults(func=client.copy_object)

	license = subparsers.add_parser('license', description='View or modify license information')
	license.set_defaults(func=client.license)
	license.add_argument('--request', action='store_true')
	license.add_argument('--check', action='store_true')
	license.add_argument('--import')

	reports = subparsers.add_parser('report', description='Create report for selected objects')
	reports.add_argument('report_type')
	reports.add_argument('dns', nargs='*')

	info = subparsers.add_parser('info', description='module info')
	info.set_defaults(func=client.infos)

	parser.add_argument('--version', action='version', version='%(prog)s VERSION TODO', help='print version information')

	class FormatModule(argparse.ArgumentDefaultsHelpFormatter):
		def format_help(self):
			if preargs:
				preargs.subparsers = subparsers
				client.init(parser, preargs)
				client.get_info(preargs)
			return super(FormatModule, self).format_help()

	parser.formatter_class = FormatModule

	args = parser.parse_args()
	client.init(parser, args)
	args.func(args)


if __name__ == '__main__':
	main()
