# -*- coding: utf-8 -*-
#
"""Univention Configuration Registry command line implementation."""
#  main configuration registry classes
#
# Copyright 2004-2015 Univention GmbH
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

# API stability :pylint: disable-msg=W0613
# Rewrite       :pylint: disable-msg=R0912,R0914,R0915

import os
import sys
import re
import time
from pipes import quote as escape_value
from univention.config_registry.backend import \
		exception_occured, SCOPE, ConfigRegistry
from univention.config_registry.handler import \
		run_filter, ConfigHandlers
from univention.config_registry.misc import \
		validate_key
from univention.config_registry.filters import \
		Output, filter_shell, filter_keys_only, filter_sort

__all__ = [
		'REPLOG_FILE',
		'UnknownKeyException',
		'handler_set',
		'handler_unset',
		'handler_dump',
		'handler_update',
		'handler_commit',
		'handler_register',
		'handler_unregister',
		'handler_filter',
		'handler_search',
		'handler_get',
		'handler_info',
		'handler_version',
		'handler_help',
		'main',
		]

REPLOG_FILE = '/var/log/univention/config-registry.replog'

_SHOW_EMPTY, _SHOW_DESCRIPTION, _SHOW_SCOPE, _SHOW_CATEGORIES = \
		(1 << _ for _ in range(4))


class UnknownKeyException(Exception):
	"""Query for unknown key: no info file nor set."""
	def __init__(self, value):
		Exception.__init__(self, value)

	def __str__(self):
		return 'W: Unknown key: "%s"' % self.args


def replog(ucr, var, old_value, value=None):
	"""
	This function writes a new entry to replication logfile if
	this feature has been enabled.
	"""
	if ucr.is_true('ucr/replog/enabled', False):
		if value is not None:
			method = 'set'
			varvalue = "%s=%s" % (var, escape_value(value))
		else:
			method = 'unset'
			varvalue = "'%s'" % var

		scope_arg = {
				ConfigRegistry.LDAP: '--ldap-policy ',
				ConfigRegistry.FORCED: '--force ',
				ConfigRegistry.SCHEDULE: '--schedule ',
				}.get(ucr.scope, '')

		if old_value is None:
			old_value = "[Previously undefined]"

		log = '%s: %s %s%s old:%s\n' % (time.strftime("%Y-%m-%d %H:%M:%S"),
				method, scope_arg, varvalue, old_value)
		try:
			if not os.path.isfile(REPLOG_FILE):
				os.close(os.open(REPLOG_FILE, os.O_CREAT, 0640))
			logfile = open(REPLOG_FILE, "a+")
			logfile.write(log)
			logfile.close()
		except EnvironmentError, ex:
			print >> sys.stderr, ("E: exception occurred while writing to " +
				"replication log: %s" % (ex,))
			exception_occured()


def handler_set(args, opts=dict(), quiet=False):
	"""
	Set config registry variables in args.
	Args is an array of strings 'key=value' or 'key?value'.
	"""
	ucr = _ucr_from_opts(opts)
	with ucr:
		changes = {}
		for arg in args:
			sep_set = arg.find('=')  # set
			sep_def = arg.find('?')  # set if not already set
			if sep_set == -1 and sep_def == -1:
				print >> sys.stderr, \
					"W: Missing value for config registry variable '%s'" % \
					(arg,)
				continue
			else:
				if sep_set > 0 and sep_def == -1:
					sep = sep_set
				elif sep_def > 0 and sep_set == -1:
					sep = sep_def
				else:
					sep = min(sep_set, sep_def)
			key = arg[0:sep]
			value = arg[sep + 1:]
			old = ucr.get(key)
			if (old is None or sep == sep_set) and validate_key(key):
				if not quiet:
					if ucr.has_key(key, write_registry_only=True):
						print 'Setting %s' % key
					else:
						print 'Create %s' % key
				changes[key] = value
			else:
				if not quiet:
					if old is not None:
						print 'Not updating %s' % key
					else:
						print 'Not setting %s' % key
		changed = ucr.update(changes)

	_run_changed(ucr, changed,
			None if quiet else 'W: %s is overridden by scope "%s"')


def handler_unset(args, opts=dict()):
	"""
	Unset config registry variables in args.
	"""
	ucr = _ucr_from_opts(opts)
	with ucr:
		changes = {}
		for arg in args:
			if ucr.has_key(arg, write_registry_only=True):
				print 'Unsetting %s' % arg
				changes[arg] = None
			else:
				msg = "W: The config registry variable '%s' does not exist"
				print >> sys.stderr, msg % (arg,)
		changed = ucr.update(changes)

	_run_changed(ucr, changed, 'W: %s is still set in scope "%s"')


def ucr_update(ucr, changes):
	"""
	Set or unset the given config registry variables.
	"""
	with ucr:
		changed = ucr.update(changes)
	_run_changed(ucr, changed)


def _run_changed(ucr, changed, msg=None):
	for key, (old_value, new_value) in changed.iteritems():
		replog(ucr, key, old_value, new_value)
		if msg:
			scope, _value = ucr.get(key, (0, None), getscope=True)
			if scope > ucr.scope:
				print >> sys.stderr, msg % (key, SCOPE[scope])

	handlers = ConfigHandlers()
	handlers.load()
	handlers(changed.keys(), (ucr, changed))


def _ucr_from_opts(opts):
	if opts.get('ldap-policy', False):
		scope = ConfigRegistry.LDAP
	elif opts.get('force', False):
		scope = ConfigRegistry.FORCED
	elif opts.get('schedule', False):
		scope = ConfigRegistry.SCHEDULE
	else:
		scope = ConfigRegistry.NORMAL
	ucr = ConfigRegistry(write_registry=scope)
	return ucr


def handler_dump(args, opts=dict()):
	"""Dump all variables."""
	ucr = ConfigRegistry()
	ucr.load()
	for line in str(ucr).split('\n'):
		print line


def handler_update(args, opts=dict()):
	"""Update handlers."""
	handlers = ConfigHandlers()
	cur = handlers.update()
	handlers.update_divert(cur)


def handler_commit(args, opts=dict()):
	"""Commit all registered templated files."""
	ucr = ConfigRegistry()
	ucr.load()

	handlers = ConfigHandlers()
	handlers.load()
	handlers.commit(ucr, args)


def handler_register(args, opts=dict()):
	"""Register new info file."""
	ucr = ConfigRegistry()
	ucr.load()

	handlers = ConfigHandlers()
	handlers.update()  # cache must be current
	# Bug #21263: by forcing an update here, the new .info file is already
	# incorporated. Calling register for multifiles will increment the
	# def_count a second time, which is not nice, but uncritical, since the
	# diversion is (re-)done when >= 1.
	handlers.register(args[0], ucr)
	#handlers.commit((ucr, {}))


def handler_unregister(args, opts=dict()):
	"""Unregister old info file."""
	ucr = ConfigRegistry()
	ucr.load()

	handlers = ConfigHandlers()
	cur = handlers.update()  # cache must be current
	obsolete = handlers.unregister(args[0], ucr)
	handlers.update_divert(cur - obsolete)


def handler_filter(args, opts=dict()):
	"""Run filter on STDIN to STDOUT."""
	ucr = ConfigRegistry()
	ucr.load()
	sys.stdout.write(run_filter(sys.stdin.read(), ucr, opts=opts))


def handler_search(args, opts=dict()):
	"""Search for registry variable."""
	search_keys = opts.get('key', False)
	search_values = opts.get('value', False)
	search_all = opts.get('all', False)
	count_search = int(search_keys) + int(search_values) + int(search_all)
	if count_search > 1:
		print >> sys.stderr, \
				'E: at most one out of [--key|--value|--all] may be set'
		sys.exit(1)
	elif count_search == 0:
		search_keys = True
	search_values |= search_all
	search_keys |= search_all

	if not args:
		regex = [re.compile('')]
	else:
		try:
			regex = [re.compile(_) for _ in args]
		except re.error, ex:
			print >> sys.stderr, 'E: invalid regular expression: %s' % (ex,)
			sys.exit(1)

	# Import located here, because on module level, a circular import would be
	# created
	import univention.config_registry_info as cri  # pylint: disable-msg=W0403
	cri.set_language('en')
	info = cri.ConfigRegistryInfo(install_mode=False)

	category = opts.get('category', None)
	if category and not info.get_category(category):
		print >> sys.stderr, 'E: unknown category: "%s"' % (category,)
		sys.exit(1)

	ucr = ConfigRegistry()
	ucr.load()

	details = _SHOW_EMPTY | _SHOW_DESCRIPTION
	if opts.get('non-empty', False):
		details &= ~_SHOW_EMPTY
	if opts.get('brief', False) or ucr.is_true('ucr/output/brief', False):
		details &= ~_SHOW_DESCRIPTION
	if ucr.is_true('ucr/output/scope', False):
		details |= _SHOW_SCOPE
	if opts.get('verbose', False):
		details |= _SHOW_CATEGORIES | _SHOW_DESCRIPTION

	all_vars = {}  # key: (value, vinfo, scope)
	for key, var in info.get_variables(category).items():
		all_vars[key] = (None, var, None)
	for key, (scope, value) in ucr.items(getscope=True):
		try:
			all_vars[key] = (value, all_vars[key][1], scope)
		except LookupError:
			all_vars[key] = (value, None, scope)

	for key, (value, vinfo, scope) in all_vars.items():
		for reg in regex:
			if ((search_keys and reg.search(key)) or
					(search_values and value and reg.search(value)) or
					(search_all and vinfo and
						reg.search(vinfo.get('description', '')))):
				print_variable_info_string(key, value, vinfo, details=details)
				break

	if _SHOW_EMPTY & details and not OPT_FILTERS['shell'][2]:
		patterns = {}
		for arg in args or ('',):
			patterns.update(info.describe_search_term(arg))
		for pattern, vinfo in patterns.items():
			print_variable_info_string(pattern, None, vinfo, details=details)


def handler_get(args, opts=dict()):
	"""Return config registry variable."""
	ucr = ConfigRegistry()
	ucr.load()

	if not args[0] in ucr:
		return
	if OPT_FILTERS['shell'][2]:
		print '%s: %s' % (args[0], ucr.get(args[0], ''))
	else:
		print ucr.get(args[0], '')


def print_variable_info_string(key, value, variable_info, scope=None,
		details=_SHOW_DESCRIPTION):
	"""Print UCR variable key, value, description, scope and categories."""
	if value is None and not variable_info:
		raise UnknownKeyException(key)
	elif value in (None, '') and not _SHOW_EMPTY & details:
		return
	elif value is None:
		# if not shell filter option is set
		if not OPT_FILTERS['shell'][2]:
			value_string = '<empty>'
		else:
			value_string = ''
	else:
		value_string = '%s' % value

	if scope in (None, 0) or \
			scope > len(SCOPE) or \
			not _SHOW_SCOPE & details or \
			OPT_FILTERS['shell'][2]:  # Do not display scope in shell export
		key_value = '%s: %s' % (key, value_string)
	else:
		key_value = '%s (%s): %s' % (key, SCOPE[scope], value_string)

	info = [key_value]
	if variable_info and _SHOW_DESCRIPTION & details:
		# info.append(' ' + variable_info.get('description',
		#   'no description available'))
		# <https://forge.univention.org/bugzilla/show_bug.cgi?id=15556>
		# Workaround:
		description = variable_info.get('description')
		if not description or not description.strip():
			description = 'no description available'
		info.append(' ' + description)

	if variable_info and _SHOW_CATEGORIES & details:
		info.append(' Categories: ' + variable_info.get('categories', 'none'))

	if (_SHOW_CATEGORIES | _SHOW_DESCRIPTION) & details:
		info.append('')

	print '\n'.join(info)


def handler_info(args, opts=dict()):
	"""Print variable info."""
	ucr = ConfigRegistry()
	ucr.load()
	# Import located here, because on module level, a circular import would be
	# created
	import univention.config_registry_info as cri  # pylint: disable-msg=W0403
	cri.set_language('en')
	info = cri.ConfigRegistryInfo(install_mode=False)

	for arg in args:
		try:
			print_variable_info_string(arg, ucr.get(arg, None),
					info.get_variable(arg),
					details=_SHOW_EMPTY | _SHOW_DESCRIPTION | _SHOW_CATEGORIES)
		except UnknownKeyException, ex:
			print >> sys.stderr, ex


def handler_version(args, opts=dict()):
	"""Print version info."""
	print 'univention-config-registry @%@package_version@%@'
	sys.exit(0)


def handler_help(args, opts=dict(), out=sys.stdout):
	"""Print config registry command line usage."""
	print >> out, '''
univention-config-registry: base configuration for UCS
copyright (c) 2001-2015 Univention GmbH, Germany

Syntax:
  univention-config-registry [options] <action> [options] [parameters]

Options:

  -h | --help | -?:
    print this usage message and exit program

  --version | -v:
    print version information and exit program

  --shell (valid actions: dump, search):
    convert key/value pair into shell compatible format, e.g.
    `version/version: 1.0` => `version_version="1.0"`

  --keys-only (valid actions: dump, search):
    print only the keys

Actions:
  set [--force|--schedule|--ldap-policy] <key>=<value> [... <key>=<value>]:
    set one or more keys to specified values; if a key is non-existent
    in the configuration registry it will be created

  get <key>:
    retrieve the value of the specified key from the configuration
    database

  unset [--force|--schedule|--ldap-policy] <key> [... <key>]:
    remove one or more keys (and its associated values) from
    configuration database

  dump:
    display all key/value pairs which are stored in the
    configuration database

  search [--key|--value|--all] [--category <category>] [--brief|-verbose] \\
          [--non-empty] [... <regex>]:
    displays all key/value pairs and their descriptions that match at
    least one of the given regular expressions
    --key: only search the keys (default)
    --value: only search the values
    --all: search keys, values and descriptions
    --category: limit search to variables of <category>
    --brief: don't print descriptions (default controlled via ucr/output/brief)
    --verbose: also print category for each variable
    --non-empty: only search in non-empty variables
    no <regex> given: display all variables

  info <key> [... <key>]:
    display verbose information for the specified variable(s)

  shell [key]:
    convert key/value pair into shell compatible format, e.g.
    `version/version: 1.0` => `version_version="1.0"`
    (deprecated: use --shell dump instead)

  commit [file1 ...]:
    rebuild configuration file from univention template; if
    no file is specified ALL configuration files are rebuilt

  filter [file]:
    evaluate a template file, expects python inline code in UTF-8 or US-ASCII

Description:
  univention-config-registry is a tool to handle the basic configuration for
  Univention Corporate Server (UCS)
'''
	sys.exit(0)


def missing_parameter(action):
	"""Print missing parameter error."""
	print >> sys.stderr, 'E: too few arguments for command [%s]' % (action,)
	print >> sys.stderr, \
			'try `univention-config-registry --help` for more information'
	sys.exit(1)


HANDLERS = {
	'set': (handler_set, 1),
	'unset': (handler_unset, 1),
	'dump': (handler_dump, 0),
	'update': (handler_update, 0),
	'commit': (handler_commit, 0),
	'register': (handler_register, 1),
	'unregister': (handler_unregister, 1),
	'shell': (None, 0),    # for compatibility only
	'filter': (handler_filter, 0),
	'search': (handler_search, 0),
	'get': (handler_get, 1),
	'info': (handler_info, 1),
	}

# action options: each of these options perform an action
OPT_ACTIONS = {
	# name: [function, state, (alias list)]
	'help': [handler_help, False, ('-h', '-?')],
	'version': [handler_version, False, ('-v',)],
	'debug': [lambda args: None, False, ()],
	}

# filter options: these options define filter for the output
OPT_FILTERS = {
	# name: [prio, function, state, (valid actions)]
	'keys-only': [0, filter_keys_only, False, ('dump', 'search')],
	'sort': [10, filter_sort, False, ('dump', 'search', 'info')],
	'shell': [99, filter_shell, False, ('dump', 'search', 'shell', 'get')],
	}

BOOL, STRING = range(2)

OPT_COMMANDS = {
	'set': {
		'force': [BOOL, False],
		'ldap-policy': [BOOL, False],
		'schedule': [BOOL, False],
		},
	'unset': {
		'force': [BOOL, False],
		'ldap-policy': [BOOL, False],
		'schedule': [BOOL, False],
		},
	'search': {
		'key': [BOOL, False],
		'value': [BOOL, False],
		'all': [BOOL, False],
		'brief': [BOOL, False],
		'category': [STRING, None],
		'non-empty': [BOOL, False],
		'verbose': [BOOL, False],
		},
	'filter': {
		'encode-utf8': [BOOL, False],
		}
	}


def main(args):
	"""Run config registry."""
	try:
		# close your eyes ...
		if not args:
			args.append('--help')
		# search for options in command line arguments
		while args and args[0].startswith('-'):
			arg = args.pop(0)
			# is action option?
			for key, opt in OPT_ACTIONS.items():
				if arg[2:] == key or arg in opt[2]:
					opt[1] = True
					break
			else:
				# not an action option; is a filter option?
				try:
					OPT_FILTERS[arg[2:]][2] = True
				except LookupError:
					print >> sys.stderr, 'E: unknown option %s' % (arg,)
					sys.exit(1)

		# is action already defined by global option?
		for name, (func, state, _aliases) in OPT_ACTIONS.items():
			if state:
				func(args)

		# find action
		try:
			action = args.pop(0)
		except IndexError:
			print >> sys.stderr, 'E: missing action, see --help'
			sys.exit(1)
		# COMPAT: the 'shell' command is now an option and equivalent to
		# --shell search
		if action == 'shell':
			action = 'search'
			# activate shell option
			OPT_FILTERS['shell'][2] = True
			# switch to old, brief output
			OPT_COMMANDS['search']['brief'][1] = True

			tmp = []
			if not args:
				tmp.append('')
			else:
				for arg in args:
					if not arg.startswith('--'):
						tmp.append('^%s$' % arg)
					else:
						tmp.append(arg)
			args = tmp

		# set 'sort' option by default for dump and search
		if action in ['dump', 'search', 'info']:
			OPT_FILTERS['sort'][2] = True

		# set brief option when generating shell output
		if OPT_FILTERS['shell'][2]:
			OPT_COMMANDS['search']['brief'][1] = True

		# if a filter option is set: verify that a valid command is given
		post_filter = False
		for name, (_prio, func, state, actions) in OPT_FILTERS.items():
			if state:
				if not action in actions:
					print >> sys.stderr, \
							'E: invalid option --%s for command %s' % \
							(name, action)
					sys.exit(1)
				else:
					post_filter = True

		# check command options
		cmd_opts = OPT_COMMANDS.get(action, {})
		while args and args[0].startswith('--'):
			arg = args.pop(0)
			if action in ('set', 'unset') and arg == '--forced':
				arg = '--force'
			try:
				cmd_opt_tuple = cmd_opts[arg[2:]]
			except LookupError:
				print >> sys.stderr, \
					'E: invalid option %s for command %s' % (arg, action)
				sys.exit(1)
			else:
				if cmd_opt_tuple[0] == BOOL:
					cmd_opt_tuple[1] = True
				else:  # STRING
					try:
						cmd_opt_tuple[1] = args.pop(0)
					except IndexError:
						msg = 'E: option %s for command %s expects an argument'
						print >> sys.stderr, msg % (arg, action)
						sys.exit(1)

		# Drop type
		cmd_opts = dict(((key, value) for key, (typ, value) in
			cmd_opts.items()))

		# action!
		try:
			handler_func, min_args = HANDLERS[action]
		except LookupError:
			print >> sys.stderr, 'E: unknown action "%s", see --help' % (action,)
			sys.exit(1)
		else:
			# enough arguments?
			if len(args) < min_args:
				missing_parameter(action)
			# if any filter option is set
			if post_filter:
				old_stdout = sys.stdout
				sys.stdout = capture = Output()
			handler_func(args, cmd_opts)
			# let the filter options do their job
			if post_filter:
				sys.stdout = old_stdout
				text = capture.text
				for _prio, (name, filter_func, state, actions) in \
						sorted(OPT_FILTERS.items(), key=lambda (k, v): v[0]):
					if state:
						text = filter_func(args, text)
				for line in text:
					print line

	except (EnvironmentError, TypeError):
		if OPT_ACTIONS['debug'][1]:
			raise
		exception_occured()

# vim:set sw=4 ts=4 noet:
