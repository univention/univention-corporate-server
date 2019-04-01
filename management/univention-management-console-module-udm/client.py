import sys
import json
import argparse
import requests
import defusedxml.ElementTree as ET
import xml.etree.cElementTree as ET2
from urlparse import urljoin

host = "192.168.188.129"
base = "http://%s:8888" % (host,)


def get_session(args):
	sess = requests.session()
	sess.auth = (args.binddn, args.bindpwd)
	try:
		from cachecontrol import CacheControl
	except ImportError:
		print 'Cannot cache!'
	else:
		sess = CacheControl(sess)
	return sess


def get_method(sess, method):
	return {
		'GET': sess.get,
		'POST': sess.post,
		'PUT': sess.put,
		'DELETE': sess.delete,
		'PATCH': sess.patch,
		'OPTIONS': sess.options,
	}.get(method.upper(), sess.get)


def create_object(args):
	pass


def modify_object(args):
	pass


def remove_object(args):
	pass


def get_module(sess):
	module = args.object_type.split('/')[0]
	root = ET.fromstring(sess.get(urljoin(base, 'udm/')).content)
	module = root.find('.//link[@rel="/udm/relation/object-modules"][@name="%s"]' % (module,))
	if module is None:
		debug(root)
		args.parser.error('Not a module')

	root = ET.fromstring(sess.get(urljoin(base, module.attrib.get('href'))).content)
	module = root.find('.//link[@rel="/udm/relation/object-types"][@name="%s"]' % (args.object_type,))
	if module is None:
		debug(root)
		args.parser.error('Not a subtype')

	root = ET.fromstring(sess.get(urljoin(base, module.attrib.get('href'))).content)
	return root


def list_objects(args):
	sess = get_session(args)
	root = get_module(sess)
	module = root.find('.//link[@rel="search"]')
	if module is None:
		debug(root)
		args.parser.error('Module does not provide searching.')

	root = ET.fromstring(sess.get(urljoin(base, module.attrib.get('href'))).content)
	module = root.find('.//form[@rel="search"]')
	if module is None:
		pass  # args.parser.error('Module does not provide form.')
	args.position
	args.filter
	for object_ in root.findall('.//a[@rel="/udm/relation/object"]'):
		obj = ET.fromstring(sess.get(urljoin(base, object_.attrib.get('href'))).content)
		data = json.loads(obj.find('.//pre').text)
		print 'DN: %s' % (data.pop('$dn$'),)
		for key, value in sorted(data.iteritems()):
			if key.startswith('$'):
				continue
			if isinstance(value, list):
				for val in value:
					if isinstance(val, list):
						val = ' '.join(val)
					print '%s: %s' % (key, repr(val).strip('u').strip("'"))
			else:
				print '%s: %s' % (key, repr(value).strip('u').strip("'"))
		print
#	print repr(module.attrib)


def get_info(args):
	sess = get_session(args)
	root = get_module(sess)
	module = root.find('.//link[@rel="udm/relation/layout"]')
	if module is None:
		debug(root)
		args.parser.error('Module does not provide layout.')
	href_layout = module.attrib.get('href')

	module = root.find('.//link[@rel="udm/relation/properties"]')
	if module is None:
		debug(root)
		args.parser.error('Module does not provide properties.')
	href_properties = module.attrib.get('href')

	layout = sess.get(urljoin(base, href_layout), headers={'Accept': 'application/json'})
	layout = layout.json()

	properties = sess.get(urljoin(base, href_properties), headers={'Accept': 'application/json'})
	properties = properties.json()
	properties = dict((prop['id'], prop) for prop in properties)

	def _print_prop(prop):
		def _print(prop):
			print '\t\t%s%s' % (prop.ljust(41), properties.get(prop, {}).get('label'))

		if isinstance(prop, list):
			for prop in prop:
				_print(prop)
		else:
			_print(prop)

	args.parser.print_help()
	for sub in args.subparsers.choices.values():
		sub.print_help()

	for layout in layout:
		print '  %s - %s:' % (layout['label'], layout['description'])
		for sub in layout['layout']:
			if isinstance(sub, dict):
				print '\t%s %s' % (sub['label'], sub['description'])
				for prop in sub['layout']:
					_print_prop(prop)
			else:
				_print_prop(sub)
		print


def debug(root):
	ET2.ElementTree(root).write(sys.stdout)


def move_object(args):
	pass


def copy_object(args):
	pass


if __name__ == '__main__':
	parser = argparse.ArgumentParser(
		prog='univention-directory-manager',
		description='copyright (c) 2001-2018 Univention GmbH, Germany',
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

	subparsers = parser.add_subparsers(title='actions', description='All available actions')
	parser.set_defaults(subparsers=subparsers)
	create = subparsers.add_parser('create', description='Create a new object')
	create.set_defaults(func=create_object)
	create.add_argument('--position', help='Set position in tree')
	create.add_argument('--set', action='append', help='Set variable to value, e.g. foo=bar')
	create.add_argument('--superordinate', help='Use superordinate module')
	create.add_argument('--option', action='append', help='Use only given module options')
	create.add_argument('--policy-reference', help='Reference to policy given by DN')
	create.add_argument('--ignore_exists', help='')

	modify = subparsers.add_parser('modify', description='Modify an existing object')
	modify.set_defaults(func=modify_object)
	modify.add_argument('--dn', help='Edit object with DN')
	modify.add_argument('--set', action='append', help='Set variable to value, e.g. foo=bar')
	modify.add_argument('--append', action='append', help='Append value to variable, e.g. foo=bar')
	modify.add_argument('--remove', action='append', help='Remove value from variable, e.g. foo=bar')
	modify.add_argument('--option', action='append', help='Use only given module options')
	modify.add_argument('--append-option', action='append', help='Append the module options')
	modify.add_argument('--policy-reference', help='Reference to policy given by DN')
	modify.add_argument('--policy-dereference', help='Remove reference to policy given by DN')

	remove = subparsers.add_parser('remove', description='Remove an existing object')
	remove.set_defaults(func=remove_object)
	remove.add_argument('--dn', help='Remove object with DN')
	remove.add_argument('--superordinate', help='Use superordinate module')
	remove.add_argument('--filter', help='Lookup filter e.g. foo=bar')
	remove.add_argument('--remove_referring', help='remove referring objects')
	remove.add_argument('--ignore_not_exists')

	list_ = subparsers.add_parser('list', description='List objects')
	list_.set_defaults(func=list_objects)
	list_.add_argument('--filter', help='Lookup filter e.g. foo=bar')
	list_.add_argument('--position', help='Search underneath of position in tree')
	list_.add_argument('--policies', help='List policy-based settings: 0:short, 1:long (with policy-DN)')

	move = subparsers.add_parser('move', description='Move object in directory tree')
	move.set_defaults(func=move_object)
	move.add_argument('--dn', help='Move object with DN')
	move.add_argument('--position', help='Move to position in tree')

	copy = subparsers.add_parser('copy', description='Copy object in directory tree')
	copy.set_defaults(func=copy_object)

	license = subparsers.add_parser('license', description='View or modify license information')

	reports = subparsers.add_parser('report', description='Create report for selected objects')
	reports.add_argument('report_type')
	reports.add_argument('dns', nargs='*')

	info = subparsers.add_parser('info', description='ot info')
	info.set_defaults(func=get_info)

	parser.add_argument('--version', action='version', version='%(prog)s VERSION TODO', help='print version information')
	args = parser.parse_args()
	args.func(args)
