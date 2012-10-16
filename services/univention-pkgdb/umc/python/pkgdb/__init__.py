#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: software monitor
#
# Copyright 2011-2012 Univention GmbH
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

import pprint
import univention.management.console as umc
import univention.management.console.modules as umcm
import univention.config_registry
import univention.pkgdb as updb

from univention.management.console.log import MODULE

from univention.management.console.protocol.definitions import *

_ = umc.Translation('univention-management-console-module-pkgdb').translate

RECORD_LIMIT = 100000			# never return more than this many records

CRITERIA = {
	'systems': [
		'sysname','sysrole','sysversion'
	],
	'packages':	[
		'pkgname','vername',							# head fields
		'selectedstate','inststate','currentstate',		# state fields
		'sysversion'									# informational
	],
	'problems': [
		'systems_not_updated',
		'incomplete_packages'
	]
}

OPERATORS = {
	'string':	[ '~','!~',],							# string match. missing asterisk is replaced by edge expression (^ or $)
	'number':	[ '<','>','<=','>=','=','!='],			# suitable for numeric comparisons
	'choice':	[ '=','!=']								# selections (combobox): checked only for (non-)equality
}

CRITERIA_TYPES = {
	'sysname':				'string',
	'pkgname':				'string',
	'sysversion':			'number',
	'vername':				'number',
	'sysrole':				'choice',
	'selectedstate':		'choice',
	'inststate':			'choice',
	'currentstate':			'choice',
	'systems_not_updated':	'compare_with_version'
}

# Search string proposals:
#
#	-	array: turns into a ComboBox
#	-	string:	turns into a TextBox
#	-	string starting with '_': interpreted as method name of our
#		module class, result will be treated as above.
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
		'notinstalled', 'unpacked', 'halfconfigured', 'uninstalled',
		'halfinstalled', 'configfiles', 'installed'
	],
	'systems_not_updated':		'_ucs_version'		# UCS version as string
}

# Associates pages (or page:key combinations) to query types.
RESULTS = {
	'systems':							'systems',
	'packages':							'packages',
	'problems:systems_not_updated':		'systems',
	'problems:incomplete_packages':		'packages'
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
		'columns':	['sysname','sysversion','sysrole','inventory_date' ],
		'function':	'sql_get_systems_by_query'
	},
	# 'select sysname,pkgname,vername,to_char(packages_on_systems.scandate,\'YYYY-MM-DD HH24:MI:SS\'),inststatus,selectedstate,inststate,currentstate from packages_on_systems join systems using(sysname) where '+query+' order by sysname,pkgname,vername
	'packages': {
		'columns':		['sysname','pkgname','vername','inventory_date',              'selectedstate','inststate','currentstate' ],
		'db_fields':	['sysname','pkgname','vername','inventory_date', 'inststatus','selectedstate','inststate','currentstate' ],
		'function':		'sql_get_packages_in_systems_by_query',
		# They allow querying for the UCS version, and then they don't display it? Who would use that at all?
		# But nevertheless, if 'sysversion' is an allowed search key we have to switch this 'Join' flag on,
		# or we get always empty result sets.
		# (No, this join is not the performance bottleneck, believe me.)
		'args':			{
			'join_systems':		True,
# /usr/share/pyshared/univention/pkgdb.py needs to be patched to understand these args:
#
#	'limit' ... avoids fetching large amounts of data that can't be processed either
#	'orderby' ..avoids doing a sort that only consumes time and memory, and afterwards
#				the data is sorted again by the grid or its store
#
#			'limit':			RECORD_LIMIT,
#			'orderby':			''
#
# As long as this is not done -> the 'packages' query is not usable if your domain contains
# more than 20 machines.
#
# Change the sql_get_packages_in_systems_by_query() function to look like this:-
#
#	def sql_get_packages_in_systems_by_query( db_connect_string, query, join_systems , orderby='sysname,pkgname,vername' , limit=0):
#		if not query:
#			return []
#		if join_systems:
#			sqlcmd = 'select sysname,pkgname,vername,to_char(packages_on_systems.scandate,\'YYYY-MM-DD HH24:MI:SS\'),inststatus,selectedstate,inststate,currentstate from packages_on_systems join systems using(sysname) where '+query
#		else:
#			sqlcmd = 'select sysname,pkgname,vername,to_char(packages_on_systems.scandate,\'YYYY-MM-DD HH24:MI:SS\'),inststatus,selectedstate,inststate,currentstate from packages_on_systems where '+query
#		if orderby != '':
#			sqlcmd += ' order by %s' % orderby
#		if limit != 0:
#			sqlcmd += ' limit %d' % limit
#		return sql_select( db_connect_string, sqlcmd )
#

			}
	}

}

# These are the values that are stored into the database using
# 'coded' values. Key is the code as used in the database, value
# is the value being shown to the outside, and used as 'id' property
# in the ComboBox data arrays.
#
CODED_VALUES = {
	'selectedstate':	{ '0': 'unknown', '1':'install', '2':'hold', '3':'deinstall', '4':'purge' },
	'currentstate':		{ '0': 'notinstalled', '1': 'unpacked', '2': 'halfconfigured', '3': 'uninstalled', '4': 'halfinstalled', '5': 'configfiles', '6': 'installed' },
	'inststate':		{ '0': 'ok', '1': 'reinst_req', '2': 'hold', '3': 'hold_reinst_req' }
}

# We introduce a 'reverse index' of the CODED_VALUES here. To keep it
# automatically in sync with CODED_VALUES, we don't fill it here.
# Instead, it will be filled from CODED_VALUES when we first need
# it (by calling self._coded_value(field,value))
DECODED_VALUES = {
}

# This helps translating labels. We don't make seperate functions
# or such things as we don't have any name clashes.
#
# Strictly spoken, we could simply call the _() function and translate
# anything coming from the database, but then the automatic builder
# wouldn't be able to maintain our '.po' file(s). That's why we have
# this dictionary.
LABELS = {
	# ------------- search fields (keys) ---------
	'incomplete_packages':		_("Find packages installed incompletely"),
	'inststate':				_("Installation state"),
	'inventory_date':			_("Inventory date"),
	'systems_not_updated':		_("Systems not updated"),
	'compare_with_version':		_("Compared to version"),
	'pkgname':					_("Package name"),
	'vername':					_("Package version"),
	'currentstate':				_("Package state"),
	'selectedstate':			_("Selection state"),
	'sysname':					_("System name"),
	'sysrole':					_("System role"),
	'sysversion':				_("UCS Version"),
	# --------------- comparison operators -----------
	'=':						_("is"),
	'!=':						_("is not"),
	'~':						_("matches"),
	'!~':						_("doesn't match"),
	'>':						_("is greater than"),
	'>=':						_("is greater or equal"),
	'<':						_("is smaller than"),
	'<=':						_("is smaller or equal"),
	# ----------- server roles --------------------
	'domaincontroller_master':	_("Domaincontroller Master"),
	'domaincontroller_backup':	_("Domaincontroller Backup"),
	'domaincontroller_slave':	_("Domaincontroller Slave"),
	'member_server':			_("Member Server"),
	'managed_client':			_("IP-managed Client"),
	'mobile_client':			_("Mobile Client"),
	# ------------------ selection states --------------
	'install':					_("Install"),
	'hold':						_("Hold"),
	'deinstall':				_("Deinstall"),
	'purge':					_("Purge"),
	'unknown':					_("Unknown"),
	# ----------------- installation states ------------
	'ok':						_("OK"),
	'reinst_req':				_("Reinstall required"),
	# 'hold' already defined
	'hold_reinst_req':			_("Hold + Reinstall required"),
	# -------------------- package states --------------
	'notinstalled':				_("not installed"),
	'unpacked':					_("unpacked"),
	'halfconfigured':			_("half-configured"),
	'uninstalled':				_("uninstalled"),
	'halfinstalled':			_("half-installed"),
	'configfiles':				_("configfiles"),
	'installed':				_("installed")
}


class Instance(umcm.Base):
	def init(self):
		MODULE.info("Initializing 'pkgdb' module with LANG = '%s'" % (self.locale, ))

		what = ''
		try:
			what = 'opening registry'
			self.ucr = univention.config_registry.ConfigRegistry()
			what = 'loading registry'
			self.ucr.load()

			# Create a suitable connect string
			what = 'building connect string'
			self.connection= updb.open_database_connection(self.ucr, pkgdbu=True)
			MODULE.info("Created database connection: %r" % (self.connection, ))
			self.cursor = self.connection.cursor()
			MODULE.info("Created database cursor: %r" % (self.cursor, ))

			what = 'checking variable lists'
			self._check_variable_lists()

			# initialize some member variables
			self._last_query = 0
			self._last_result = []

		except Exception, ex:
			MODULE.warn("[INIT] while %s: %s" % (what, ex, ))

	def _check_variable_lists(self):
		""" checks if the variable lists (system roles and system versions)
			are already in the PROPOSALS dict, and if not -> fetches them.
		"""
		what = ''
		try:
			if not 'sysrole' in PROPOSALS:
				what = 'fetching system roles'
				sysroles = self._execute_query('sql_getall_systemroles')
				PROPOSALS['sysrole'] = sysroles
				MODULE.info("   ++ system roles: ['%s']" % "','".join(sysroles))

			if not 'sysversion' in PROPOSALS:
				what = 'fetching system versions'
				sysversions = self._execute_query('sql_getall_systemversions')
				PROPOSALS['sysversion'] = sysversions
				MODULE.info("   ++ system versions: ['%s']" % "','".join(sysversions))

				# make 'systems not updated' pattern to a selection too
				PROPOSALS['systems_not_updated'] = PROPOSALS['sysversion']

		except Exception, ex:
			MODULE.warn("[check_variable_lists] while %s: %s" % (what, ex, ))

	def query(self, request):
		""" Query to fill the grid. The structure of the corresponding grid
			has already been fetched by the 'pkgdb/columns' command.
		"""
		# ----------- DEBUG -----------------
		MODULE.info("pkgdb/query invoked with:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(request.options).split("\n")
		for s in st:
			MODULE.info("   << %s" % s)
		# -----------------------------------

		# When a sort header is clicked, the frontend will issue the same query
		# again. We're prepared for this, remembering the last query options and
		# the result set.

		if cmp(self._last_query, request.options) == 0:
			MODULE.info("   ++ Same query: returning same result (%d entries) again." % len(self._last_result))
			result = self._last_result
			self.finished(request.id, result)
			return

		self._last_query = request.options

		result = []

		# Normally, we can use the request options as they are passed to us. But for
		# the predefined queries at the 'problems' page, we get only a name and must
		# construct the corresponding query args here. We search for a method of
		# our own instance that has the name of the query name (with '_opt_' prepended),
		# and that method is supposed to accept the options and to return changed options.
		options = request.options
		optfunc = '_opt_' + options.get('key','')
		try:
			options = eval('self.%s(options=options)' % optfunc)

			# -------------- DEBUG ----------------
			MODULE.info("   ++ changed options:")
			pp = pprint.PrettyPrinter(indent=4)
			st = pp.pformat(options).split("\n")
			for s in st:
				MODULE.info("   ++ %s" % s)
			# -----------------------------------
		except Exception, ex:
			MODULE.info('optfunc: ' + str(ex))

		page =		options.get('page','')
		key =		options.get('key','')
		operator =	options.get('operator','')
		pattern = 	options.get('pattern','')

		desc = self._query_description(page, key)
		query = self._make_query(key, operator, pattern)

		# Multiple query tuples: we already need them at least for the
		# predefined query 'packages with problems'.
		for idx in range(10):
			key =		options.get('key%s' % (idx, ), '')
			operator =	options.get('operator%s' % (idx, ), '')
			pattern = 	options.get('pattern%s' % (idx, ), '')
			tmpq = self._make_query(key, operator, pattern)
			if tmpq != '':
				query = '%s and %s' % (query, tmpq)

		# invoke query only if our definitions are complete
		if (desc is not None) and ('function' in desc) and (query is not None):
			try:
				if query == '':
					query = None
				args = None
				if 'args' in desc:
					args = desc['args']
				temp = self._execute_query(desc['function'], query, args)

				MODULE.info("   ++ Start converting %d entries" % len(temp))
				for record in temp:
					dbf = desc['columns']
					if 'db_fields' in desc:
						dbf = desc['db_fields']
					result.append(self._convert_to_grid(record, dbf))
				MODULE.info("   ++ Conversion finished.")
			except Exception, ex:
				MODULE.warn("   !! execute query: %s" % str(ex))

		request.status = SUCCESS

		# Remember result for repeated invocation of the same query
		# (e.g. click on any sort header)
		self._last_result = result

		# ---------- DEBUG --------------
		MODULE.info("pkgdb/query returns:")
		pp = pprint.PrettyPrinter(indent=4)
		st = ''
		if len(result) > 5:
			tmp = result[0:5]
			MODULE.info("   >> %d entries, first 5 are:" % len(result))
			st = pp.pformat(tmp).split("\n")
		else:
			st = pp.pformat(result).split("\n")
		for s in st:
			MODULE.info("   >> %s" % s)
		# --------------------------------

		self.finished(request.id, result)

	# ---------------------------------------------------------------------------
	#
	#		information about structures
	#
	#		We establish some helper functions that make it easy to change structures.
	#		This means that the frontend does only have to know a given page key, and
	#		the rest of the structure definition is coming from here (the UPPERCASED
	#		dictionaries at the start). The only information being maintained here and
	#		there are the page keys to start with.
	#

	def keys(self, request):
		""" returns the set of search criteria suitable for the
			given page.
		"""
		# ----------- DEBUG -----------------
		MODULE.info("pkgdb/keys invoked with:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(request.options).split("\n")
		for s in st:
			MODULE.info("   << %s" % s)
		# -----------------------------------

		page = request.options.get('page','')
		result = []
		if page in CRITERIA:
			result = self._combobox_data(CRITERIA[page])

		# ---------- DEBUG --------------
		MODULE.info("pkgdb/keys returns:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(result).split("\n")
		for s in st:
			MODULE.info("   >> %s" % s)
		# --------------------------------

		self.finished(request.id, result)

	def operators(self, request):
		"""	returns the query operators that are suitable for
			the given page+key combination. The selection is
			made of 'id' values directly usable as SQL comparison
			operators, and the 'label's are already localized here.
		"""
		# ----------- DEBUG -----------------
		MODULE.info("pkgdb/operators invoked with:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(request.options).split("\n")
		for s in st:
			MODULE.info("   << %s" % s)
		# -----------------------------------

		page = request.options.get('page','')
		key = request.options.get('key','')

		# *** NOTE *** Currently there are no 'combined' conditions:
		#				the proposals shown here depend on the 'key'
		#				only.

		c_type = ''
		result = []
		if key in CRITERIA_TYPES:
			c_type = CRITERIA_TYPES[key]
			if c_type in OPERATORS:
				result = self._combobox_data(OPERATORS[c_type])
			else:
				# a single operator will not show up in the 'operators' ComboBox: the ComboBox
				# will be hidden, and only the 'pattern' argument will be shown, labelled by
				# this result value (already localized).
				result = self._id_to_label(c_type)

		# ---------- DEBUG --------------
		MODULE.info("pkgdb/operators returns:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(result).split("\n")
		for s in st:
			MODULE.info("   >> %s" % s)
		# --------------------------------

		self.finished(request.id, result)

	def proposals(self, request):
		"""	returns proposals for the query pattern that can be
			presented in the frontend. This can be a single pattern
			(the corresponding field will turn into a text entry)
			or an array (the field will turn into a ComboBox,
			with optionally translated labels)
		"""
		# ----------- DEBUG -----------------
		MODULE.info("pkgdb/proposals invoked with:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(request.options).split("\n")
		for s in st:
			MODULE.info("   << %s" % s)
		# -----------------------------------

		# at least here we should have the PROPOSALS dictionary
		# properly filled, so we check it for the last time:
		self._check_variable_lists()

		page = request.options.get('page','')
		key = request.options.get('key','')
		operator = request.options.get('operator','')

		# *** NOTE *** Currently there are no 'combined' conditions:
		#				the proposals shown here depend on the 'key'
		#				only.

		result = '*'			# fallback for everything not listed here.

		if key in PROPOSALS:
			result = PROPOSALS[key]
			# starts with underscore? try to call it as a method of 'self'
			if isinstance(result, str) and result.startswith('_'):
				try:
					r = eval('self.%s()' % result)
					result = r
				finally:
					pass
			# make up array values into {id, label} entries.
			if isinstance(result, (list, tuple, )):
				result = self._combobox_data(result)

		# ---------- DEBUG --------------
		MODULE.info("pkgdb/proposals returns:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(result).split("\n")
		for s in st:
			MODULE.info("   >> %s" % s)
		# --------------------------------

		self.finished(request.id, result)


	def columns(self, request):
		"""	returns the structure of the results grid for a given
			page+key combination. Note that design properties (width etc)
			are added at the JS page (KeyTranslator.js)
		"""
		# ----------- DEBUG -----------------
		MODULE.info("pkgdb/columns invoked with:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(request.options).split("\n")
		for s in st:
			MODULE.info("   << %s" % s)
		# -----------------------------------

		page = request.options.get('page', '')
		key = request.options.get('key', '')

		result = None
		query = self._query_description(page, key)
		if query is not None:
			result = []
			for col in query['columns']:
				# introduce exception fields: present in the returned result set
				# but not to be included into the grid
				if col != '':
					result.append(col)

		# ---------- DEBUG --------------
		MODULE.info("pkgdb/columns returns:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(result).split("\n")
		for s in st:
			MODULE.info("   >> %s" % s)
		# --------------------------------

		self.finished(request.id, result)

	def _combobox_data(self, data):
		"""	returns the given array of strings as an array of (id,label) tuples
			with the given values, just as needed by the 'dynamicValues'
			query of a ComboBox.

			Additionally, tries to replace the labels by the translated
			value of the 'id'.
		"""
		result = []
		if isinstance(data, (list, tuple, )):
			for identifier in data:
				entry = {}
				entry['id'] = identifier
				entry['label'] = self._id_to_label(identifier)
				result.append(entry)
		return result

	def _ucs_version(self):
		"""	returns the current UCS version; will be needed
			at different places.
		"""
		st = '%s-%s' % (self.ucr.get('version/version', ''), self.ucr.get('version/patchlevel', ''), )
		spl = self.ucr.get('version/security-patchlevel', '')
		if spl != '':
			st = '%s-%s' % (st, spl, )

		return st

	def _query_description(self, page, key):
		""" internal function that finds the query description
			for a given page+key. Will be used for the result grid (columns)
			as well as for the construction of the query.
		"""
		query = ''
		if page in RESULTS:
			query = RESULTS[page]
		else:
			qkey = '%s:%s' % (page, key, )
			if qkey in RESULTS:
				query = RESULTS[qkey]

		if query in QUERIES:
			return QUERIES[query]
		return None

	def _make_query(self, key, operator, pattern):
		"""	consumes a tuple of 'key','operator','pattern' and converts it
			into a valid Postgres WHERE clause. Features here:

				-	translates keyed values into their database representation
				-	tweaks this DOS-glob-style pattern notation into a correct
					regular expression
		"""

		try:
			if key != '' and operator != '' and pattern != '':
				MODULE.info("make_query('%s','%s','%s')" % (key, operator, pattern, ))
				# Translate keyed values. That function returns the input
				# value unchanged if there's no reason to translate anything.
				pattern = self._coded_value(key, pattern)

				# For matching operators, we have to tweak the expression:
				#
				#	(1)	force the pattern to match the whole field
				#	(2)	force dot to lose special meaning by prefixing it '.' -> '\.'
				#	(3)	translate glob '*' into regexp '.*'
				#
				if '~' in operator:

					# (1a) anchor at string start if not starting with wildcard
					if not pattern.startswith('*'):
						pattern = '^%s' % pattern

					# (1b) anchor at string end if not ending with wildcard
					if not pattern.endswith('*'):
						pattern = '%s$' % pattern

					# (2) dot is not a wildcard here but rather a literal dot
					pattern = pattern.replace('.','\.')

					# (3) asterisk means: any char, 0-n times (.*)
					pattern = pattern.replace('*','.*')

				return "%s %s '%s'" % (key, operator, pattern, )
		finally:
			pass
		return ''

	def _id_to_label(self, identifier):
		"""	translates any id into the corresponding label.
			if no translation found -> returns id unchanged.
		"""
		return LABELS.get(identifier, identifier)

	def _decoded_value(self, field, key):
		"""	accepts a field name and the database value of this field
			and translates this into the codeword that represents this value.
		"""

		if field in CODED_VALUES:
			if str(key) in CODED_VALUES[field]:
				return CODED_VALUES[field][str(key)]
		# unchanged if no match
		return key

	def _coded_value(self, field, value):
		"""	this is the inverse of the above function: it accepts a field name
			and a value and translates it back into the 'keyed' value to be
			used when talking to the database.
		"""
		# Fill the DECODED_VALUES if not already done
		for f in CODED_VALUES:
			if not f in DECODED_VALUES:
				tmp = {}
				for key in CODED_VALUES[f]:
					tmp[CODED_VALUES[f][key]] = key
				DECODED_VALUES[f] = tmp

		MODULE.info("   -> Translating field = '%s'  value = '%s'" % (field, value, ))
		if field in DECODED_VALUES:
			if str(value) in DECODED_VALUES[field]:
				MODULE.info("   -> Found '%s'" % DECODED_VALUES[field][str(value)])
				return DECODED_VALUES[field][str(value)]
		# unchanged if no match
		return value

	def _execute_query(self, function, query=None, args=None):
		"""	Executes a pkgdb query """

		what = 'starting'
		MODULE.info("Executing query (function='%s',query='%s',args='%s'):" % (function, query, args, ))
		try:
			moreargs = ''
			kwargs = {}
			if query is not None:
				kwargs['query'] = query
			if args is not None:
				kwargs.update(args)

			if function == 'sql_getall_systems':
				function = updb.sql_getall_systems
			elif function == 'sql_getall_systemroles':
				function = updb.sql_getall_systemroles
			elif function == 'sql_getall_systemversions':
				function = updb.sql_getall_systemversions
			elif function == 'sql_getall_packages_in_systems':
				function = updb.sql_getall_packages_in_systems
			elif function == 'sql_get_systems_by_query':
				function = updb.sql_get_systems_by_query
			elif function == 'sql_get_packages_in_systems_by_query':
				function = updb.sql_get_packages_in_systems_by_query
			else:
				assert False
			what = 'evaluating cmdstr'
			result = function(self.cursor, **kwargs)
			MODULE.info("-> result: %r" % (result, ))
			# Uuh, and sometimes it returns None, not telling why...
			if result is None:
				result = []
			# DEBUG for #22896: the fetchall() call can return different data types.
			# Usually we expect an array of dictionaries:
			#
			#	result = [
			#				{ 'field1':'value1', 'field2':'value2' },
			#				{ ... }
			#			]
			#
			# but depending on the type of query, the fields are sometimes returned without names, as in:
			#
			#	result = [
			#				['one', 'two'],
			#				['three', 'four']
			#			]
			#
			# For Grid-driven queries, this is not relevant. But for 'distinct' queries that are meant
			# for ComboBox data, we need one array containing all those values, so converting them here:
			#
			what = 'checking result type'

			if (len(result) > 0) and ("'list'" in str(type(result[0]))) and (len(result[0]) == 1):
				MODULE.info("   ++ Converting %d entries from single-element arrays to strings" % (len(result), ))
				tmp = []
				for element in result:
					tmp.append(element[0])
				result = tmp

			# Marshaler isn't able to handle too much data, so we limit the record count. Better SQL
			# execution should avoid returning too much data, but in the meantime, we work around here.
			what = 'checking for record limit'
			if len(result) > RECORD_LIMIT:
				what = 'limiting record count'
				MODULE.warn("   >> QUERY returned %d entries -> showing only first %d" % (len(result), RECORD_LIMIT, ))
				del result[RECORD_LIMIT:]
			return result
		except Exception, ex:
			MODULE.warn("   !! Query (function='%s',query='%s',args='%s') failed:" % (function, query, args, ))
			MODULE.warn('   !! [while %s]: %s' % (what, ex, ))
		return []

	def _convert_to_grid(self, data, names):
		"""	The queries here return arrays of values. But our grid
			only accepts dicts where the values are prefixed by
			the field names. This function converts one record.
		"""
		try:
			result = {}
			if isinstance(data, (list, tuple, )) and isinstance(names, (list, tuple, )):

				# find smaller length
				l = len(data)
				if len(names) < l:
					l = len(names)

				i = 0
				while i < l:
					# This expression does the main work:
					#	(1)	assigns the field name to a value
					#	(2)	converts database representation into keyed values (_decoded_value)
					#	(3)	translates keyed values for display (_id_to_label)
					result[names[i]] = self._id_to_label(self._decoded_value(names[i], data[i]))
					i += 1
		except Exception, ex:
			MODULE.warn("convert_to_grid: %s" % str(ex))
		return result

	# ---------------------------------------------------------------------
	#
	#		special option handlers
	#
	#		For the predefined queries at the 'problems' page, the frontend
	#		only emits the page and key (= query) to us. Here we construct
	#		the options for these queries that can be processed by the same
	#		toolchain as other queries.

	def _opt_systems_not_updated(self, options):
		""" Changes the given options to match the 'systems not updated' query:
			Systems not updated means 'systems with a sysversion lower than the given pattern

			We make this look like the query was invoked from a 'sysversion < pattern' query
			at the 'systems' page.
		"""

		options['page']		= 'systems'
		options['key']		= 'sysversion'
		options['operator'] = '<'

		return options

	def _opt_incomplete_packages(self, options):
		"""	Changes the given options to match the 'incomplete packages' query.
			in 2.4 the query looked like:

			query = "currentstate!='0' and currentstate!='6' and selectedstate!='3'"
		"""

		options['page']			= 'packages'

		# three query tuples here
		options['key']			= 'currentstate'
		options['operator']		= '!='
		options['pattern']		= 'notinstalled'

		options['key0']			= 'currentstate'
		options['operator0']	= '!='
		options['pattern0']		= 'installed'

		options['key1']			= 'selectedstate'
		options['operator1']	= '!='
		options['pattern1']		= 'deinstall'

		return options
