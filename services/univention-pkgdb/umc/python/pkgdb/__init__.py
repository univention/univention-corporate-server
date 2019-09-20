#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: software monitor
#
# Copyright 2011-2019 Univention GmbH
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

import pgdb

from univention.management.console import Translation
from univention.management.console.modules import Base, UMC_Error
import univention.config_registry
import univention.pkgdb as updb

from univention.management.console.log import MODULE

from univention.management.console.modules.decorators import simple_response, log, sanitize
from univention.management.console.modules.sanitizers import ChoicesSanitizer

_ = Translation('univention-management-console-module-pkgdb').translate

RECORD_LIMIT = 100000  # never return more than this many records

CRITERIA = {
	'systems': [
		'all_properties', 'sysname', 'sysrole', 'sysversion', 'sysversion_greater', 'sysversion_lower'
	],
	'packages': [
		'pkgname', 'currentstate',  # head fields
		'selectedstate', 'inststate',  # state fields
	]
}

CRITERIA_OPERATOR = {
	'sysname': '~',
	'pkgname': '~',
	'sysversion': '=',
	'vername': '=',
	'sysrole': '=',
	'selectedstate': '=',
	'inststate': '=',
	'currentstate': '=',
	'sysversion_greater': '>',
	'sysversion_lower': '<',
	'all_properties': '~',
}

MAPPED_TABLES = {
	'all_properties': ['sysname', 'sysrole', 'sysversion'],
	'sysversion_greater': ['sysversion'],
	'sysversion_lower': ['sysversion'],
}
MAPPED_PATTERNS_TO_KEYS = {
	'incomplete': ['unpacked', 'halfinstalled', 'halfconfigured', 'triggers-awaited', 'triggers-pending'],
	'notinstalled': ['notinstalled', 'uninstalled'],
}

# Search string proposals:
#
#	-	array: turns into a ComboBox
#	-	string:	turns into a TextBox
#
# *** NOTE ***	the 'system_roles' and 'ucs_version' lists are fetched
#				dynamically from the pkgdb object.
PROPOSALS = {
	'selectedstate': [
		'install', 'hold', 'deinstall', 'purge', 'unknown'
	],
	'inststate': [
		'ok', 'reinst_req', 'hold', 'hold_reinst_req'
	],
	'currentstate': [
		'installed', 'notinstalled', 'incomplete', 'configfiles'
		# 'uninstalled', 'unpacked', 'halfconfigured', 'halfinstalled',
	],
}

# Describes our query types:
#
#	'columns'	the result set. Equally used as field list for the query as well
#				as the column list for the results grid.
#	'db_fields' (optional) define this if the list of database fields is different from the
#				list of columns to display (as it is the case for the 'packages' query)
#	'function'	the function of the pkgdb object to use.
#	'args'		(optional) if the corresponding function of the pkgdb object needs more args,
#				you can specify them here. Args are passed as 'named args' in the Python sense.
#
QUERIES = {
	# 'select sysname,sysversion,sysrole,to_char(scandate,\'YYYY-MM-DD HH24:MI:SS\'),ldaphostdn from systems where '+query+' order by sysname
	'systems': {
		'columns': ['sysname', 'sysversion', 'sysrole', 'inventory_date'],
		'function': updb.sql_get_systems_by_query
	},
	# 'select sysname,pkgname,vername,to_char(packages_on_systems.scandate,\'YYYY-MM-DD HH24:MI:SS\'),inststatus,selectedstate,inststate,currentstate from packages_on_systems join systems using(sysname) where '+query+' order by sysname,pkgname,vername
	'packages': {
		'columns': ['sysname', 'pkgname', 'vername', 'selectedstate', 'inststate', 'currentstate'],
		'db_fields': ['sysname', 'pkgname', 'vername', 'inventory_date', 'inststatus', 'selectedstate', 'inststate', 'currentstate'],
		'function': updb.sql_get_packages_in_systems_by_query,
		# They allow querying for the UCS version, and then they don't display it? Who would use that at all?
		# But nevertheless, if 'sysversion' is an allowed search key we have to switch this 'Join' flag on,
		# or we get always empty result sets.
		# (No, this join is not the performance bottleneck, believe me.)
		'args': {
			'join_systems': True,
			'limit': RECORD_LIMIT,
			# 'orderby' ..avoids doing a sort that only consumes time and memory, and afterwards
			# 			the data is sorted again by the grid or its store
			'orderby': ''
		}
	}

}

# These are the values that are stored into the database using
# 'coded' values. Key is the code as used in the database, value
# is the value being shown to the outside, and used as 'id' property
# in the ComboBox data arrays.
#
CODED_VALUES = {
	'selectedstate': {'0': 'unknown', '1': 'install', '2': 'hold', '3': 'deinstall', '4': 'purge'},
	'currentstate': {'0': 'notinstalled', '1': 'unpacked', '2': 'halfconfigured', '3': 'uninstalled', '4': 'halfinstalled', '5': 'configfiles', '6': 'installed', '7': 'triggers-awaited', '8': 'triggers-pending'},
	'inststate': {'0': 'ok', '1': 'reinst_req', '2': 'hold', '3': 'hold_reinst_req'},
}

# We introduce a 'reverse index' of the CODED_VALUES here.
DECODED_VALUES = dict((f, dict((CODED_VALUES[f][key], key) for key in CODED_VALUES[f])) for f in CODED_VALUES)

# This helps translating labels. We don't make separate functions
# or such things as we don't have any name clashes.
LABELS = {
	# ------------- search fields (keys) ---------
	# 'incomplete_packages':		_("Find packages installed incompletely"),
	'inststate': _("Installation state"),
	'inventory_date': _("Inventory date"),
	# 'compare_with_version':		_("Compared to version"),
	'pkgname': _("Package name"),
	# 'vername':					_("Package version"),
	'currentstate': _("Package state"),
	'selectedstate': _("Selection state"),
	'sysname': _("Hostname"),
	'sysrole': _("System role"),
	'sysversion': _("UCS Version"),
	'sysversion_greater': _("UCS Version is greater than"),
	'sysversion_lower': _("UCS Version is lower than"),
	'all_properties': _("All properties"),
	# ----------- server roles --------------------
	'domaincontroller_master': _("Domain controller Master"),
	'domaincontroller_backup': _("Domain controller Backup"),
	'domaincontroller_slave': _("Domain controller Slave"),
	'memberserver': _("Member Server"),
	# ------------------ selection states --------------
	'install': _("Install"),
	'hold': _("Hold"),
	'deinstall': _("Deinstall"),
	'purge': _("Purge"),
	'unknown': _("Not installed"),
	# ----------------- installation states ------------
	'ok': _("OK"),
	'reinst_req': _("Reinstall required"),
	# 'hold' already defined
	'hold_reinst_req': _("Hold + Reinstall required"),
	# -------------------- package states --------------
	'notinstalled': _("Not installed"),
	'unpacked': _("Unpacked"),
	'halfconfigured': _("Half-configured"),
	'uninstalled': _("Uninstalled"),
	'halfinstalled': _("Half-installed"),
	'configfiles': _("Config files only"),
	'installed': _("Installed"),
	'incomplete': _("Incomplete"),
	'triggers-pending': _("Triggers pending"),
	'triggers-awaited': _("Triggers awaited"),
}

PAGES = ('systems', 'packages')


def _server_not_running_msg():
	return _('Maybe the PostgreSQL server is not running.\nIt can be started with the UMC module "System services".')


class Instance(Base):

	def init(self):
		self.ucr = univention.config_registry.ConfigRegistry()
		self.ucr.load()

		self.connect()

		self._update_system_roles_and_versions()

	def connection(func):
		def _connect(self, *args, **kwargs):
			if self.dbConnection is None:
				self.connect()
			else:
				self.test_connection()
			return func(self, *args, **kwargs)

		return _connect

	def connect(self):
		# Create a connection to the pkgdb
		try:
			self.dbConnection = updb.open_database_connection(self.ucr, pkgdbu=True)
		except pgdb.InternalError as ex:
			MODULE.error('Could not establish connection to the PostgreSQL server: %s' % (ex,))
			raise UMC_Error(_('Could not establish connection to the database.\n\n%s') % (_server_not_running_msg(),))
		else:
			self.cursor = self.dbConnection.cursor()

	def test_connection(self):
		# test if connection is still active
		try:
			self.cursor.execute('SELECT TRUE')
		except pgdb.OperationalError as ex:
			MODULE.error('Connection to the PostgreSQL server lost: %s' % (ex,))
			self.dbConnection = None
			try:
				self.connect()
			except UMC_Error:
				raise UMC_Error(_('Connection to the database lost.\n\n%s') % (_server_not_running_msg(),))

	@simple_response
	def reinit(self):
		"""Method invoked when opening the module in the frontend to cache and update some values"""
		self._update_system_roles_and_versions()

	def _update_system_roles_and_versions(self):
		""" refetchs the variable lists (system roles and system versions) """
		PROPOSALS['sysrole'] = self._get_system_roles()

		PROPOSALS['sysversion'] = self._get_system_versions()

		PROPOSALS['sysversion_lower'] = PROPOSALS['sysversion']
		PROPOSALS['sysversion_greater'] = PROPOSALS['sysversion']

	@connection
	def _get_system_roles(self):
		return [role[0] for role in updb.sql_getall_systemroles(self.cursor)]

	@connection
	def _get_system_versions(self):
		return [version[0] for version in updb.sql_getall_systemversions(self.cursor)]

	@sanitize(
		page=ChoicesSanitizer(choices=PAGES, required=True),
		key=ChoicesSanitizer(choices=CRITERIA_OPERATOR.keys())
	)
	@connection
	@simple_response
	def query(self, page, key, pattern=''):
		""" Query to fill the grid. The structure of the corresponding grid
			has already been fetched by the 'pkgdb/columns' command.
		"""

		desc = QUERIES[page]
		operator = CRITERIA_OPERATOR[key]

		function = desc['function']

		kwargs = desc.get('args', {})
		kwargs['query'] = _make_query(key, operator, pattern)

		result = function(self.cursor, **kwargs)

		names = desc.get('db_fields', desc['columns'])
		return [_convert_to_grid(record, names) for record in result]

	@sanitize(page=ChoicesSanitizer(choices=PAGES, required=True))
	@connection
	@simple_response
	@log
	def keys(self, page):
		""" returns the set of search criteria suitable for the given page. """
		return _combobox_data(CRITERIA[page])

	@sanitize(page=ChoicesSanitizer(choices=PAGES, required=True))
	@connection
	@simple_response
	@log
	def proposals(self, page, key=''):
		"""	returns proposals for the query pattern that can be
			presented in the frontend. This can be a single pattern
			(the corresponding field will turn into a text entry)
			or an array (the field will turn into a ComboBox,
			with optionally translated labels)
		"""

		if key in PROPOSALS:
			return _combobox_data(PROPOSALS[key])

		# fallback for everything not explicitly listed here.
		return ''

	@sanitize(page=ChoicesSanitizer(choices=PAGES, required=True))
	@connection
	@simple_response
	@log
	def columns(self, page, key=''):
		"""	returns the structure of the results grid for a given
			page+key combination. Note that design properties (width etc)
			are added at the JS page (KeyTranslator.js)
		"""
		return QUERIES[page]['columns']


def _combobox_data(data):
	"""	returns a (id, label) dict with translated values """
	return [dict(id=identifier, label=_id_to_label(identifier)) for identifier in data]


def _make_query(key, operator, pattern):
	"""	consumes a tuple of 'key','operator','pattern' and converts it
		into a valid Postgres WHERE clause. Features here:

			-	translates keyed values into their database representation
			-	tweaks this DOS-glob-style pattern notation into a correct
				regular expression
	"""

	def __make_query(key, operator, pattern):
		if not key:
			return None

		# Translate keyed values. That function returns the input
		# value unchanged if there's no reason to translate anything.
		pattern = _coded_value(key, pattern)

		pattern = pgdb.escape_string(pattern)
		key = key.replace('"', r'\"')

		if '~' in operator:

			# 1. dot is not a wildcard here but rather a literal dot
			pattern = pattern.replace('.', '\.')

			# 2. a * indicates to not do a substring search
			if '*' in pattern:
				pattern = pattern.replace('*', '.*')
				pattern = '^%s$' % (pattern)

			# 3. empty pattern means search for everything
			if pattern == '':
				pattern = '.*'

		return "\"%s\" %s '%s'" % (key, operator, pattern)

	if pattern in MAPPED_PATTERNS_TO_KEYS:
		patterns = MAPPED_PATTERNS_TO_KEYS[pattern]
		return ' OR '.join(__make_query(key, operator, pattern) for pattern in patterns)
	else:
		keys = MAPPED_TABLES.get(key, [key])
		return ' OR '.join(__make_query(key, operator, pattern) for key in keys)


def _decoded_value(field, key):
	"""	accepts a field name and the database value of this field
		and translates this into the codeword that represents this value.
	"""

	if field in CODED_VALUES:
		return CODED_VALUES[field].get(str(key), key)
	# unchanged if no match
	return key


def _coded_value(field, value):
	"""	this is the inverse of the above function: it accepts a field name
		and a value and translates it back into the 'keyed' value to be
		used when talking to the database.
	"""

	if field in DECODED_VALUES:
		return DECODED_VALUES[field].get(str(value), value)
	# unchanged if no match
	return value


def _convert_to_grid(data, names):
	"""	The queries here return arrays of values. But our grid
		only accepts dicts where the values are prefixed by
		the field names. This function converts one record.
	"""
	# find smaller length
	length = min(len(data), len(names))

	# This expression does the main work:
	#	(1)	assigns the field name to a value
	#	(2)	converts database representation into keyed values (_decoded_value)
	#	(3)	translates keyed values for display (_id_to_label)
	return dict((names[i], _id_to_label(_decoded_value(names[i], data[i]))) for i in range(length))


def _id_to_label(identifier):
	"""	translates any id into the corresponding label.
		if no translation found -> returns id unchanged.
	"""
	return LABELS.get(identifier, identifier)
