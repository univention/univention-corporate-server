#def main():
#	return
#	description = '%(prog)s: command line interface for managing UCS'
#	epilog = '%(prog)s is a tool to handle the configuration for UCS on command line level. Use "%(prog)s modules" for a list of available modules.'
#	parser = argparse.ArgumentParser(description=description, epilog=epilog)
#	parser.add_argument('module', help='UDM type, e.g. users/user or computers/memberserver')
#	parser.add_argument('--binddn', help='bind DN')
#	parser.add_argument('--bindpwd', help='bind password')
#	parser.add_argument('--bindpwdfile', help='file containing bind password')
#	parser.add_argument('--logfile', help='path and name of the logfile to be used')
#	parser.add_argument('--tls', help='0 (no); 1 (try); 2 (must)')
#
#	subparsers = parser.add_subparsers(description='type %(prog)s <module> <action> --help for further help and possible arguments', metavar='action')
#
#	# CREATE
#	create_parser = subparsers.add_parser('create', help='Create a new UDM object')
#	create_parser.add_argument('--position', help='Set position in tree')
#	create_parser.add_argument('--set', help='Set variable to value, e.g. foo=bar')
#	create_parser.add_argument('--superordinate', help='Use superordinate module')
#	create_parser.add_argument('--option', help='Use only given module options')
#	create_parser.add_argument('--append-option', help='Append the module option')
#	create_parser.add_argument('--remove-option', help='Remove the module option')
#	create_parser.add_argument('--policy-reference', help='Reference to policy given by DN')
#	create_parser.add_argument('--ignore_exists')
#
#	# MODIFY
#	modify_parser = subparsers.add_parser('modify', help='Modify an existing UDM object')
#	modify_parser.add_argument('--dn', help='Edit object with DN')
#	modify_parser.add_argument('--set', help='Set variable to value, e.g. foo=bar')
#	modify_parser.add_argument('--append', help='Append value to variable, e.g. foo=bar')
#	modify_parser.add_argument('--remove', help='Remove value from variable, e.g. foo=bar')
#	modify_parser.add_argument('--option', help='Use only given module options')
#	modify_parser.add_argument('--append-option', help='Append the module option')
#	modify_parser.add_argument('--remove-option', help='Remove the module option')
#	modify_parser.add_argument('--policy-reference', help='Reference to policy given by DN')
#	modify_parser.add_argument('--policy-dereference', help='Remove reference to policy given by DN')
#
#	# REMOVE
#	remove_parser = subparsers.add_parser('remove', help='Remove a UDM object')
#	remove_parser.add_argument('--dn', help='Remove object with DN')
#	remove_parser.add_argument('--superordinate', help='Use superordinate module')
#	remove_parser.add_argument('--filter', help='Lookup filter e.g. foo=bar')
#	remove_parser.add_argument('--remove_referring', help='remove referring objects')
#	remove_parser.add_argument('--ignore_not_exists')
#
#	# LIST
#	list_parser = subparsers.add_parser('list', help='Search and list UDM objects')
#	list_parser.add_argument('--filter', help='Lookup filter e.g. foo=bar')
#	list_parser.add_argument('--position', help='Search underneath of position in tree')
#	list_parser.add_argument('--policies', choices=['0', '1'], help='List policy-based settings: 0:short, 1:long (with policy-DN)')
#
#	# MOVE
#	move_parser = subparsers.add_parser('move', help='Move a UDM object to a different position in tree')
#	move_parser.add_argument('--dn', help='Move object with DN')
#	move_parser.add_argument('--position', help='Move to position in tree')
#
#	#args = parser.parse_args()
