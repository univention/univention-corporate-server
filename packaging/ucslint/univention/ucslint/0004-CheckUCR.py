# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright (C) 2008-2022 Univention GmbH
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

import os
import re
import sys
from configparser import DuplicateOptionError, DuplicateSectionError, MissingSectionHeaderError, ParsingError, RawConfigParser
from typing import Any, Dict, Iterator, List, Set, Tuple, Union  # noqa: F401

import univention.ucslint.base as uub

# Check 4
# 1) Nach UCR-Templates suchen und prüfen, ob die Templates in einem info-File auftauchen
# 2) In den UCR-Templates nach UCR-Variablen suchen (Code-Blöcke) und prüfen, ob diese in den info-Files registriert sind
# 3) In den UCR-Templates nach einem UCR-Header suchen
# 3.1) check, ob @%@BCWARNING=# @%@ verwendet wird
# 3.2) check, ob @%@UCRWARNING=# @%@ verwendet wird
# 4) Prüfen, ob der Pfad zum UCR-Template im File steht und stimmt
# 5) check, ob für jedes Subfile auch ein Multifile-Eintrag vorhanden ist
# 6) check, ob jede Variable/jedes VarPattern im SubFile auch am Multifile-Eintrag steht
# 7) check, ob univention-install-config-registry in debian/rules vorhanden ist, sofern debian/*.univention-config-registry existiert
# 8) check, ob univention-install-config-registry-info in debian/rules vorhanden ist, sofern debian/*.univention-config-registry-variables existiert

#
# TODO / FIXME
# - 0004-29: Different (conflicting) packages might provide the same Multifile with different definitions (e.g. univention-samba/etc/smb.conf)
UcrInfo = Dict[str, List[str]]


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):
	RE_PYTHON = re.compile(r'@!@')
	RE_VAR = re.compile(r'@%@')
	RE_VALID_UCR = re.compile(r'^(?:[-/0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz]|%[sd])+$')
	RE_UCR_HEADER_FILE = re.compile(r'#[\t ]+(/etc/univention/templates/files(/[^ \n\t\r]*?))[ \n\t\r]')
	RE_UICR = re.compile(r'[\n\t ]univention-install-(baseconfig|config-registry)[\n\t ]|\tdh\b.*--with\b.*\bucr\b')

	def getMsgIds(self) -> uub.MsgIds:
		return {
			'0004-1': (uub.RESULT_WARN, 'The given path in UCR header seems to be incorrect'),
			'0004-2': (uub.RESULT_ERROR, 'debian/rules seems to be missing'),
			'0004-3': (uub.RESULT_ERROR, 'UCR .info-file contains entry without "Type:" line'),
			'0004-4': (uub.RESULT_ERROR, 'UCR .info-file contains entry of "Type: multifile" without "Multifile:" line'),
			'0004-5': (uub.RESULT_ERROR, 'UCR .info-file contains entry of "Type: subfile" without "Subfile:" line'),
			'0004-6': (uub.RESULT_ERROR, 'UCR .info-file contains entry of "Type: subfile" without "Multifile:" line'),
			'0004-7': (uub.RESULT_ERROR, 'UCR .info-file contains entry of "Type: subfile" with multiple "Subfile:" line'),
			'0004-8': (uub.RESULT_ERROR, 'UCR .info-file contains entry of "Type: subfile" with multiple "Multifile:" line'),
			'0004-9': (uub.RESULT_ERROR, 'UCR .info-file contains entry without valid "Type:" line'),
			'0004-10': (uub.RESULT_WARN, 'UCR .info-file contains entry of "Type: subfile" without corresponding entry of "Type: multifile"'),
			'0004-11': (uub.RESULT_ERROR, 'DEPRECATED: UCR .info-file contains entry of "Type: subfile" with variables that are not registered at corresponding multifile entry'),
			'0004-12': (uub.RESULT_ERROR, 'UCR template file contains UCR variables that are not registered in .info-file'),
			'0004-13': (uub.RESULT_ERROR, 'UCR template file contains UCR variables with invalid characters'),
			'0004-14': (uub.RESULT_WARN, 'UCR template file is found in directory conffiles/ but is not registered in any debian/*.univention-config-registry file '),
			'0004-15': (uub.RESULT_WARN, 'UCR template file is registered in UCR .info-file but cannot be found in conffiles/'),
			'0004-16': (uub.RESULT_WARN, 'UCR template file contains no UCR header (please use "@%@UCSWARNING=# @%@")'),
			'0004-17': (uub.RESULT_WARN, 'UCR template file is registered in UCR .info-file but cannot be found in conffiles/'),
			'0004-18': (uub.RESULT_WARN, 'UCR header is maybe missing in UCR multifile (please check all subfiles)'),
			'0004-19': (uub.RESULT_ERROR, 'UCR .info-file contains entry of "Type: subfile" with multiple "Preinst:" line'),
			'0004-20': (uub.RESULT_ERROR, 'UCR .info-file contains entry of "Type: subfile" with multiple "Postinst:" line'),
			'0004-21': (uub.RESULT_ERROR, 'UCR .info-file contains entry of "Type: file" with multiple "Preinst:" line'),
			'0004-22': (uub.RESULT_ERROR, 'UCR .info-file contains entry of "Type: file" with multiple "Postinst:" line'),
			'0004-23': (uub.RESULT_ERROR, 'debian/*.univention-config-registry exists but debian/rules contains no univention-install-config-registry'),
			'0004-24': (uub.RESULT_STYLE, 'debian/*.univention-config-registry exists but no corresponding debian/*.univention-config-registry-variables file'),
			'0004-25': (uub.RESULT_STYLE, 'debian/rules contains old univention-install-baseconfig call'),
			'0004-26': (uub.RESULT_STYLE, 'DEPRECATED: debian/*.univention-config-registry-variables exists but debian/rules contains no univention-install-config-registry-info'),
			'0004-27': (uub.RESULT_WARN, 'cannot open/read file'),
			'0004-28': (uub.RESULT_ERROR, 'invalid formatted line without ":" found'),
			'0004-29': (uub.RESULT_ERROR, 'UCR template file contains UCR variables that are not registered in .info-file'),
			'0004-30': (uub.RESULT_ERROR, 'debian/*.univention-config-registry-variables contains non-UTF-8 strings'),
			'0004-31': (uub.RESULT_ERROR, 'UCR template file contains odd number of %!% markers'),
			'0004-32': (uub.RESULT_ERROR, 'UCR template file contains odd number of %@% markers'),
			'0004-33': (uub.RESULT_ERROR, 'UCR .info-file contains entry of "Type: file" without "File:" line'),
			'0004-34': (uub.RESULT_ERROR, 'UCR warning before file type magic'),
			'0004-35': (uub.RESULT_WARN, 'Invalid module file name'),
			'0004-36': (uub.RESULT_ERROR, 'Module file does not exist'),
			'0004-37': (uub.RESULT_ERROR, 'Missing Python function "preinst(ucr, changes)"'),
			'0004-38': (uub.RESULT_ERROR, 'Missing Python function "postinst(ucr, changes)"'),
			'0004-39': (uub.RESULT_ERROR, 'Missing Python function "handler(ucr, changes)"'),
			'0004-40': (uub.RESULT_ERROR, 'UCR .info-file contains entry of "Type: module" with multiple "Module:" line'),
			'0004-41': (uub.RESULT_ERROR, 'UCR .info-file contains entry of "Type: script" with multiple "Script:" line'),
			'0004-42': (uub.RESULT_WARN, 'UCR .info-file contains entry with unexpected key'),
			'0004-43': (uub.RESULT_WARN, 'UCR .info-file contains entry of "Type: file" with invalid "User: " line'),
			'0004-44': (uub.RESULT_WARN, 'UCR .info-file contains entry of "Type: file" with multiple "User: " line'),
			'0004-45': (uub.RESULT_WARN, 'UCR .info-file contains entry of "Type: file" with invalid "Group: " line'),
			'0004-46': (uub.RESULT_WARN, 'UCR .info-file contains entry of "Type: file" with multiple "Group: " line'),
			'0004-47': (uub.RESULT_WARN, 'UCR .info-file contains entry of "Type: file" with invalid "Mode: " line'),
			'0004-48': (uub.RESULT_WARN, 'UCR .info-file contains entry of "Type: file" with multiple "Mode: " line'),
			'0004-49': (uub.RESULT_WARN, 'UCR .info-file contains entry of "Type: multifile" with invalid "User: " line'),
			'0004-50': (uub.RESULT_WARN, 'UCR .info-file contains entry of "Type: multifile" with multiple "User: " line'),
			'0004-51': (uub.RESULT_WARN, 'UCR .info-file contains entry of "Type: multifile" with invalid "Group: " line'),
			'0004-52': (uub.RESULT_WARN, 'UCR .info-file contains entry of "Type: multifile" with multiple "Group: " line'),
			'0004-53': (uub.RESULT_WARN, 'UCR .info-file contains entry of "Type: multifile" with invalid "Mode: " line'),
			'0004-54': (uub.RESULT_WARN, 'UCR .info-file contains entry of "Type: multifile" with multiple "Mode: " line'),
			'0004-55': (uub.RESULT_WARN, 'UCR .info-file may contain globbing pattern instead of regular expression'),
			'0004-56': (uub.RESULT_INFO, 'No UCR variables used'),
			'0004-57': (uub.RESULT_INFO, 'No description found for UCR variable'),
			'0004-58': (uub.RESULT_ERROR, 'UCR .info-file contains entry of "Type: multifile" with multiple "Preinst:" line'),
			'0004-59': (uub.RESULT_ERROR, 'UCR .info-file contains entry of "Type: multifile" with multiple "Postinst:" line'),
			'0004-60': (uub.RESULT_ERROR, 'Duplicate entry'),
			'0004-61': (uub.RESULT_ERROR, 'Invalid entry'),
			'0004-62': (uub.RESULT_ERROR, 'UCR template file using `custom_username()` must register for UCRV "users/default/.*"'),
			'0004-63': (uub.RESULT_ERROR, 'UCR template file using `custom_groupname()` must register for UCRV "groups/default/.*"'),
		}

	@classmethod
	def check_invalid_variable_name(cls, var: str) -> bool:
		"""
		Returns True if given variable name contains invalid characters

		:param var: variable name to check.
		:returns: `False` if the name is valid, `True` otherwise.

		>>> UniventionPackageCheck.check_invalid_variable_name('')
		True
		>>> UniventionPackageCheck.check_invalid_variable_name('var')
		False
		>>> UniventionPackageCheck.check_invalid_variable_name('sub-section/var_name')
		False
		>>> UniventionPackageCheck.check_invalid_variable_name('ä')
		True
		>>> UniventionPackageCheck.check_invalid_variable_name('%x')
		True
		"""
		return cls.RE_VALID_UCR.match(var) is None

	RE_UCR_VARLIST = [
		re.compile(r"""(?:baseConfig|configRegistry) \s* \[ \s* ['"] ([^'"]+) ['"] \s* \]""", re.VERBOSE),
		re.compile(r"""(?:baseConfig|configRegistry)\.has_key \s* \( \s* ['"] ([^'"]+) ['"] \s* \)""", re.VERBOSE),
		re.compile(r"""(?:baseConfig|configRegistry)\.get \s* \( \s* ['"] ([^'"]+) ['"] \s* [,)]""", re.VERBOSE),
		re.compile(r"""(?:baseConfig|configRegistry)\.is_(?:true|false) \s* \( \s* ['"] ([^'"]+) ['"] \s* [,)]""", re.VERBOSE),
		re.compile(r"""['"] ([^'"]+) ['"] \s+ in \s+ (?:baseConfig|configRegistry) (?!\.)""", re.VERBOSE),
	]
	RE_UCR_PLACEHOLDER_VAR1 = re.compile(r'@%@([^@]+)@%@')
	RE_IDENTIFIER = re.compile(r"""<!DOCTYPE|<\?xml|<\?php|#!\s*/\S+""", re.MULTILINE)
	RE_PYTHON_FNAME = re.compile(r'^[0-9A-Z_a-z][0-9A-Z_a-z-]*(?:/[0-9A-Z_a-z-][0-9A-Z_a-z-]*)*\.py$')
	RE_FUNC_HANDLER = re.compile(r'^def\s+handler\s*\(\s*\w+\s*,\s*\w+\s*\)\s*:', re.MULTILINE)
	RE_FUNC_PREINST = re.compile(r'^def\s+preinst\s*\(\s*\w+\s*,\s*\w+\s*\)\s*:', re.MULTILINE)
	RE_FUNC_POSTINST = re.compile(r'^def\s+postinst\s*\(\s*\w+\s*,\s*\w+\s*\)\s*:', re.MULTILINE)
	RE_FUNC_CUSTOM_USER = re.compile(r'(?: univention\.lib\.misc\. | ^\s* from \s+ univention\.lib\.misc \s+ import \s+ (?:\(.*?)? ) \b custom_username \b', re.MULTILINE | re.VERBOSE)
	RE_FUNC_CUSTOM_GROUP = re.compile(r'(?: univention\.lib\.misc\. | ^\s* from \s+ univention\.lib\.misc \s+ import \s+ (?:\(.*?)? ) \b custom_groupname \b', re.MULTILINE | re.VERBOSE)

	def check_conffiles(self, path: str) -> Dict[str, Any]:
		"""Analyze UCR templates below :file:`conffiles/`."""
		conffiles = {}  # type: Dict[str, Dict[str, Any]]

		confdir = os.path.join(path, 'conffiles')
		for fn in uub.FilteredDirWalkGenerator(confdir, ignore_suffixes=uub.FilteredDirWalkGenerator.BINARY_SUFFIXES):
			checks = {
				'headerfound': False,
				'variables': [],  # List[str] # Python code
				'placeholder': [],  # List[str] # @%@
				'ucrwarning': False,
				'pythonic': False,
				'preinst': False,
				'postinst': False,
				'handler': False,
				'custom_user': False,
				'custom_group': False,
			}  # type: Dict[str, Any]
			conffiles[fn] = checks

			match = self.RE_PYTHON_FNAME.match(os.path.relpath(fn, confdir))
			if match:
				checks['pythonic'] = True

			try:
				content = open(fn, 'r').read()
			except EnvironmentError:
				self.addmsg('0004-27', 'cannot open/read file', fn)
				continue
			except UnicodeDecodeError as ex:
				self.addmsg('0004-30', 'contains invalid characters', fn, ex.start)
				continue

			match = self.RE_FUNC_PREINST.search(content)
			if match:
				checks['preinst'] = True
			match = self.RE_FUNC_POSTINST.search(content)
			if match:
				checks['postinst'] = True
			match = self.RE_FUNC_HANDLER.search(content)
			if match:
				checks['handler'] = True
			match = self.RE_FUNC_CUSTOM_USER.search(content)
			if match:
				checks['custom_user'] = True
			match = self.RE_FUNC_CUSTOM_GROUP.search(content)
			if match:
				checks['custom_group'] = True

			warning_pos = 0
			for match in self.RE_UCR_PLACEHOLDER_VAR1.finditer(content):
				var = match.group(1)
				if var.startswith('BCWARNING=') or var.startswith('UCRWARNING=') or var.startswith('UCRWARNING_ASCII='):
					checks['ucrwarning'] = True
					warning_pos = warning_pos or match.start() + 1
				elif var not in checks['placeholder']:
					checks['placeholder'].append(var)
			if checks['placeholder']:
				self.debug('found UCR placeholder variables in %s\n- %s' % (fn, '\n- '.join(checks['placeholder'])))

			match = self.RE_IDENTIFIER.search(content, 0)
			if warning_pos and match:
				identifier = match.group()
				pos = match.start()
				self.debug('Identifier "%s" found at %d' % (identifier, pos))
				if warning_pos < pos:
					self.addmsg('0004-34', 'UCR warning before file type magic "%s"' % (identifier,), fn)

			#
			# subcheck: check if UCR header is present
			#
			if 'Warning: This file is auto-generated and might be overwritten by' in content and \
				'Warnung: Diese Datei wurde automatisch generiert und kann durch' in content:
				checks['headerfound'] = True

			for regEx in self.RE_UCR_VARLIST:
				for match in regEx.finditer(content):
					var = match.group(1)
					if var not in checks['variables']:
						checks['variables'].append(var)
			if checks['variables']:
				self.debug('found UCR variables in %s\n- %s' % (fn, '\n- '.join(checks['variables'])))

			if checks['headerfound']:
				#
				# subcheck: check if path in UCR header is correct
				#
				match = self.RE_UCR_HEADER_FILE.search(content)
				if match:
					fname = fn[fn.find('/conffiles/') + 10:]
					if match.group(2) != fname:
						self.addmsg('0004-1', 'Path in UCR header seems to be incorrect.\n      - template filename = /etc/univention/templates/files%s\n      - path in header    = %s' % (fname, match.group(1)), fn)

		self.debug('found conffiles: %s' % conffiles.keys())

		return conffiles

	def read_ucr(self, fn: str) -> Iterator[UcrInfo]:
		self.debug('Reading %s' % fn)
		try:
			entry = {}  # type: UcrInfo
			with open(fn, 'r') as stream:
				for row, line in enumerate(stream, start=1):
					line = line.strip()
					if not line and entry:
						yield entry
						entry = {}
						continue

					try:
						key, val = line.split(': ', 1)
					except ValueError:
						self.addmsg('0004-28', 'file contains line without ":"', fn, row, line=line)
						continue

					values = entry.setdefault(key, [])
					if val in values:
						self.addmsg('0004-60', 'Duplicate entry for %s: %s' % (key, val), fn, row, line=line)

					values.append(val)

				if entry:
					yield entry
		except EnvironmentError:
			self.addmsg('0004-27', 'cannot open/read file', fn)

	def read_ini(self, fn: str) -> RawConfigParser:
		self.debug('Reading %s' % fn)

		cfg = RawConfigParser(interpolation=None)
		try:
			if not cfg.read(fn):
				self.addmsg('0004-27', 'cannot open/read file', fn)

			return cfg
		except DuplicateSectionError as ex:
			self.addmsg('0004-60', 'Duplicate section entry: %s' % (ex.section), ex.source, ex.lineno)
		except MissingSectionHeaderError as ex:
			self.addmsg('0004-61', 'Invalid entry: %s' % (ex,), fn, ex.lineno)
		except DuplicateOptionError as ex:
			self.addmsg('0004-61', 'Invalid entry: %s' % (ex,), fn)
		except ParsingError as ex:
			self.addmsg('0004-61', 'Invalid entry: %s' % (ex,), fn)
		except UnicodeDecodeError as ex:
			self.addmsg('0004-30', 'contains invalid characters', fn, ex.start)

		cfg = RawConfigParser(strict=False, interpolation=None)
		try:
			cfg.read(fn)
		except (DuplicateSectionError, ParsingError, UnicodeDecodeError):
			pass

		return cfg

	def check(self, path: str) -> None:
		""" the real check """
		super(UniventionPackageCheck, self).check(path)

		conffiles = self.check_conffiles(path)

		#
		# check UCR templates
		#
		all_multifiles = {}  # type: Dict[str, List[UcrInfo]] # { MULTIFILENAME ==> [ OBJ... ] }
		all_subfiles = {}    # type: Dict[str, List[UcrInfo]] # { MULTIFILENAME ==> [ OBJ... ] }
		all_files = []       # type: List[UcrInfo] # [ OBJ... ]
		all_preinst = set()  # type: Set[str] # { FN... }
		all_postinst = set()  # type: Set[str] # { FN... }
		all_module = set()   # type: Set[str] # { FN... }
		all_script = set()   # type: Set[str] # { FN... }
		all_definitions = {}  # type: Dict[str, Set[str]] # { SHORT-FN ==> { FULL-FN... } }
		all_descriptions = set()  # type: Set[str] # { FN... }
		all_variables = set()  # type: Set[str] # { VAR... }
		objlist = {}         # type: Dict[str, List[UcrInfo]] # { CONF-FN ==> [ OBJ... ] }

		# read debian/rules
		fn_rules = os.path.join(path, 'debian', 'rules')
		try:
			rules_content = open(fn_rules, 'r').read()
		except EnvironmentError:
			self.addmsg('0004-2', 'file is missing', fn_rules)
			rules_content = ''

		if 'univention-install-baseconfig' in rules_content:
			self.addmsg('0004-25', 'file contains old univention-install-baseconfig call', fn_rules)

		# find debian/*.u-c-r and check for univention-config-registry-install in debian/rules
		for f in os.listdir(os.path.join(path, 'debian')):
			fn = os.path.join(path, 'debian', f)
			if f.endswith('.univention-config-registry-categories'):
				self.read_ini(fn)
			elif f.endswith('.univention-config-registry-mapping'):
				pass
			elif f.endswith('.univention-config-registry-variables'):
				cfg = self.read_ini(fn)
				all_descriptions |= set(cfg.sections())
			elif f.endswith('.univention-service'):
				self.read_ini(fn)
			elif f.endswith('.univention-config-registry') or f.endswith('.univention-baseconfig'):
				tmpfn = os.path.join(path, 'debian', '%s.univention-config-registry-variables' % f.rsplit('.', 1)[0])
				self.debug('testing %s' % tmpfn)
				if not os.path.exists(tmpfn):
					self.addmsg('0004-24', '%s exists but corresponding %s is missing' % (f, tmpfn), tmpfn)

				if not self.RE_UICR.search(rules_content):
					self.addmsg('0004-23', '%s exists but debian/rules contains no univention-install-config-registry' % f, fn_rules)
					break

		for f in os.listdir(os.path.join(path, 'debian')):
			if f.endswith('.univention-config-registry') or f.endswith('.univention-baseconfig'):
				fn = os.path.join(path, 'debian', f)

				# OBJ = { 'Type': [ STRING, ... ],
				#         'Subfile': [ STRING, ... ] ,
				#         'Multifile': [ STRING, ... ],
				#         'Variables': [ STRING, ... ]
				# or instead of "Subfile" and "Multifile" one of the following:
				#         'File': [ STRING, ... ] ,
				#         'Module': [ STRING, ... ] ,
				#         'Script': [ STRING, ... ] ,
				#       }
				multifiles = {}  # type: Dict[str, UcrInfo] # { MULTIFILENAME ==> OBJ }
				subfiles = {}  # type: Dict[str, List[UcrInfo]] # { MULTIFILENAME ==> [ OBJ, OBJ, ... ] }
				files = []  # type: List[UcrInfo] # [ OBJ, OBJ, ... ]
				unique = set()  # type: Set[Union[str, Tuple[str, str]]]

				for entry in self.read_ucr(fn):
					self.debug('Entry: %s' % entry)

					try:
						typ = entry['Type'][0]
					except LookupError:
						self.addmsg('0004-3', 'file contains entry without "Type:"', fn)
					else:
						if typ == 'multifile':
							mfile = entry.get('Multifile', [])
							if not mfile:
								self.addmsg('0004-4', 'file contains multifile entry without "Multifile:" line', fn)
							elif len(mfile) != 1:
								self.addmsg('0004-4', 'file contains multifile entry with %d "Multifile:" line' % (len(mfile),), fn)
							else:
								multifiles[mfile[0]] = entry
							for conffn in mfile:
								if conffn in unique:
									self.addmsg('0004-60', 'Duplicate entry: Multifile %s' % (conffn,), fn)
								else:
									unique.add(conffn)

							user = entry.get('User', [])
							if len(user) > 1:
								self.addmsg('0004-44', 'UCR .info-file contains entry of "Type: file" with multiple "User: " line', fn)
							elif len(user) == 1:
								if user[0].isdigit():  # must be an symbolic name
									self.addmsg('0004-43', 'UCR .info-file contains entry of "Type: file" with invalid "User: " line', fn)

							group = entry.get('Group', [])
							if len(group) > 1:
								self.addmsg('0004-46', 'UCR .info-file contains entry of "Type: file" with multiple "Group: " line', fn)
							elif len(group) == 1:
								if group[0].isdigit():  # must be an symbolic name
									self.addmsg('0004-45', 'UCR .info-file contains entry of "Type: file" with invalid "Group: " line', fn)

							mode = entry.get('Mode', [])
							if len(mode) > 1:
								self.addmsg('0004-48', 'UCR .info-file contains entry of "Type: file" with multiple "Mode: " line', fn)
							elif len(mode) == 1:
								try:
									if not 0 <= int(mode[0], 8) <= 0o7777:
										self.addmsg('0004-47', 'UCR .info-file contains entry of "Type: file" with invalid "Mode: " line', fn)
								except (TypeError, ValueError):
									self.addmsg('0004-47', 'UCR .info-file contains entry of "Type: file" with invalid "Mode: " line', fn)

							pre = entry.get('Preinst', [])
							if len(pre) > 1:
								self.addmsg('0004-58', 'file contains multifile entry with %d "Preinst:" lines' % (len(pre),), fn)
							all_preinst |= set(pre)

							post = entry.get('Postinst', [])
							if len(post) > 1:
								self.addmsg('0004-59', 'file contains multifile entry with %d "Postinst:" lines' % (len(post),), fn)
							all_postinst |= set(post)

							for key in set(entry) - set(('Type', 'Multifile', 'Variables', 'User', 'Group', 'Mode', 'Preinst', 'Postinst')):
								self.addmsg('0004-42', 'UCR .info-file contains entry with unexpected key "%s"' % (key,), fn)

						elif typ == 'subfile':
							sfile = entry.get('Subfile', [])
							if not sfile:
								self.addmsg('0004-5', 'file contains subfile entry without "Subfile:" line', fn)
								continue
							elif len(sfile) != 1:
								self.addmsg('0004-7', 'file contains subfile entry with %d "Subfile:" lines' % (len(sfile),), fn)
							for conffn in sfile:
								objlist.setdefault(conffn, []).append(entry)
								all_definitions.setdefault(conffn, set()).add(fn)

							mfile = entry.get('Multifile', [])
							if not mfile:
								self.addmsg('0004-6', 'file contains subfile entry without "Multifile:" line', fn)
							elif len(mfile) != 1:
								self.addmsg('0004-8', 'file contains subfile entry with %d "Multifile:" lines' % (len(mfile),), fn)
							for _ in mfile:
								subfiles.setdefault(_, []).append(entry)
								all_definitions.setdefault(_, set()).add(fn)

							for conffn in sfile:
								for _ in mfile:
									key2 = (_, conffn)
									if key2 in unique:
										self.addmsg('0004-60', 'Duplicate entry: Multifile %s, Subfile %s' % key2, fn)
									else:
										unique.add(key2)

							pre = entry.get('Preinst', [])
							if len(pre) > 0:
								self.addmsg('0004-19', 'file contains subfile entry with %d "Preinst:" lines' % (len(pre),), fn)
							all_preinst |= set(pre)

							post = entry.get('Postinst', [])
							if len(post) > 0:
								self.addmsg('0004-20', 'file contains subfile entry with %d "Postinst:" lines' % (len(post),), fn)
							all_postinst |= set(post)

							for key in set(entry) - set(('Type', 'Subfile', 'Multifile', 'Variables')):
								self.addmsg('0004-42', 'UCR .info-file contains entry with unexpected key "%s"' % (key,), fn)

						elif typ == 'file':
							sfile = entry.get('File', [])
							if len(sfile) != 1:
								self.addmsg('0004-33', 'file contains file entry with %d "File:" lines' % (len(sfile),), fn)
							for conffn in sfile:
								objlist.setdefault(conffn, []).append(entry)
								all_definitions.setdefault(conffn, set()).add(fn)
								if conffn in unique:
									self.addmsg('0004-60', 'Duplicate entry: File %s' % (conffn,), fn)
								else:
									unique.add(conffn)
							files.append(entry)

							user = entry.get('User', [])
							if len(user) > 1:
								self.addmsg('0004-50', 'UCR .info-file contains entry of "Type: multifile" with multiple "User: " line', fn)
							elif len(user) == 1:
								if user[0].isdigit():  # must be an symbolic name
									self.addmsg('0004-49', 'UCR .info-file contains entry of "Type: multifile" with invalid "User: " line', fn)

							group = entry.get('Group', [])
							if len(group) > 1:
								self.addmsg('0004-52', 'UCR .info-file contains entry of "Type: multifile" with multiple "Group: " line', fn)
							elif len(group) == 1:
								if group[0].isdigit():  # must be an symbolic name
									self.addmsg('0004-51', 'UCR .info-file contains entry of "Type: multifile" with invalid "Group: " line', fn)

							mode = entry.get('Mode', [])
							if len(mode) > 1:
								self.addmsg('0004-54', 'UCR .info-file contains entry of "Type: multifile" with multiple "Mode: " line', fn)
							elif len(mode) == 1:
								try:
									if not 0 <= int(mode[0], 8) <= 0o7777:
										self.addmsg('0004-53', 'UCR .info-file contains entry of "Type: multifile" with invalid "Mode: " line', fn)
								except (TypeError, ValueError):
									self.addmsg('0004-53', 'UCR .info-file contains entry of "Type: multifile" with invalid "Mode: " line', fn)

							pre = entry.get('Preinst', [])
							if len(pre) > 1:
								self.addmsg('0004-21', 'file contains file entry with %d "Preinst:" lines' % (len(pre),), fn)
							all_preinst |= set(pre)

							post = entry.get('Postinst', [])
							if len(post) > 1:
								self.addmsg('0004-22', 'file contains file entry with %d "Postinst:" lines' % (len(post),), fn)
							all_postinst |= set(post)

							for key in set(entry) - set(('Type', 'File', 'Variables', 'User', 'Group', 'Mode', 'Preinst', 'Postinst')):
								self.addmsg('0004-42', 'UCR .info-file contains entry with unexpected key "%s"' % (key,), fn)

						elif typ == 'module':
							module = entry.get('Module', [])
							if len(module) != 1:
								self.addmsg('0004-38', 'UCR .info-file contains entry of "Type: module" with %d "Module:" lines' % (len(module),), fn)
							for conffn in module:
								objlist.setdefault(conffn, []).append(entry)
								if conffn in unique:
									self.addmsg('0004-60', 'Duplicate entry: Module %s' % (conffn,), fn)
								else:
									unique.add(conffn)
							all_module |= set(module)

							for key in set(entry) - set(('Type', 'Module', 'Variables')):
								self.addmsg('0004-42', 'UCR .info-file contains entry with unexpected key "%s"' % (key,), fn)

						elif typ == 'script':
							script = entry.get('Script', [])
							if len(script) != 1:
								self.addmsg('0004-39', 'UCR .info-file contains entry of "Type: script" with %d "Script:" lines' % (len(script),), fn)
							for conffn in script:
								objlist.setdefault(conffn, []).append(entry)
								if conffn in unique:
									self.addmsg('0004-60', 'Duplicate entry: Script %s' % (conffn,), fn)
								else:
									unique.add(conffn)
							all_script |= set(script)

							for key in set(entry) - set(('Type', 'Script', 'Variables')):
								self.addmsg('0004-42', 'UCR .info-file contains entry with unexpected key "%s"' % (key,), fn)

						else:
							self.addmsg('0004-9', 'file contains entry with invalid "Type: %s"' % (typ,), fn)
							continue

						variables = entry.get('Variables', [])
						for var in variables:
							if '*' in var and '.*' not in var:
								self.addmsg('0004-55', 'UCR .info-file may contain globbing pattern instead of regular expression: "%s"' % (var,), fn)
								break

				self.debug('Multifiles: %s' % multifiles)
				self.debug('Subfiles: %s' % subfiles)
				self.debug('Files: %s' % files)
				for multifile, subfileentries in subfiles.items():
					if multifile not in multifiles:
						self.addmsg('0004-10', 'file contains subfile entry without corresponding multifile entry.\n      - subfile = %s\n      - multifile = %s' % (subfileentries[0]['Subfile'][0], multifile), fn)

				# merge into global list
				for mfn, item in multifiles.items():
					all_multifiles.setdefault(mfn, []).append(item)
				for sfn, items in subfiles.items():
					all_subfiles.setdefault(sfn, []).extend(items)
				all_files.extend(files)

		#
		# check if all variables are registered
		#
		short2conffn = {}  # type: Dict[str, str] # relative name -> full path

		def find_conf(fn: str) -> str:
			"""Find file in conffiles/ directory.
			Mirror base/univention-config/python/univention-install-config-registry#srcPath
			"""
			try:
				return short2conffn[fn]
			except KeyError:
				if fn.startswith('conffiles/'):
					return short2conffn[fn[len('conffiles/'):]]
				elif fn.startswith('etc/'):
					return short2conffn[fn[len('etc/'):]]
				else:
					raise

		for conffn, checks in conffiles.items():
			conffnfound = False
			shortconffn = conffn[conffn.find('/conffiles/') + 11:]
			short2conffn[shortconffn] = conffn

			try:
				try:
					obj = objlist[shortconffn][0]
				except LookupError:
					try:
						obj = objlist['conffiles/' + shortconffn][0]
					except LookupError:
						obj = objlist['etc/' + shortconffn][0]
			except LookupError:
				self.debug('"%s" not found in %r' % (conffn, objlist.keys()))
			else:
				conffnfound = True
				notregistered = []  # type: List[str]
				invalidUCRVarNames = set()  # type: Set[str]

				mfn = obj.get('Multifile', [''])[0]
				if mfn and mfn in all_multifiles:
					# "Multifile" entry exists ==> obj is a subfile
					# add known variables from ALL multifile entry - there may me multiple due to multiple packages
					knownvars = set(
						var
						for mf in all_multifiles[mfn]
						for var in mf.get('Variables', [])
					)
					# iterate over all subfile entries for this multifile
					for sf in all_subfiles[mfn]:
						# if subfile matches current subtemplate...
						if shortconffn == sf.get('Subfile', [''])[0]:
							# ...then add variables to list of known variables
							knownvars.update(sf.get('Variables', []))
				else:
					# no subfile ==> File, Module, Script
					knownvars = set(obj.get('Variables', []))

				# check only variables against knownvars, @%@-placeholder are auto-detected
				for var in checks['variables']:
					if var not in knownvars:
						# if not found check if regex matches
						for rvar in knownvars:
							if '.*' in rvar:
								if re.match(rvar, var):
									all_variables.add(rvar)
									break
						else:
							notregistered.append(var)
							all_variables.add(var)
					else:
						all_variables.add(var)
					# check for invalid UCR variable names
					if self.check_invalid_variable_name(var):
						invalidUCRVarNames.add(var)

				if len(notregistered):
					if mfn and mfn in all_multifiles:
						# "Multifile" entry exists ==> obj is a subfile
						self.debug('cfn = %r' % shortconffn)
						self.debug('knownvars(mf+sf) = %r' % knownvars)
						self.addmsg('0004-29', 'template file contains variables that are not registered in multifile or subfile entry:\n	- %s' % ('\n	- '.join(notregistered)), conffn)
					else:
						# no subfile ==> File, Module, Script
						self.addmsg('0004-12', 'template file contains variables that are not registered in file entry:\n	- %s' % ('\n	- '.join(notregistered)), conffn)

				if checks['custom_user'] and not any('users/default/' in v for v in knownvars):
					self.addmsg('0004-62', 'UCR template file using `custom_username()` must register for UCRV "users/default/.*"', conffn)

				if checks['custom_group'] and not any('groups/default/' in v for v in knownvars):
					self.addmsg('0004-63', 'UCR template file using `custom_groupname()` must register for UCRV "groups/default/.*"', conffn)

				for var in checks['placeholder']:
					# check for invalid UCR placeholder variable names
					if self.check_invalid_variable_name(var):
						invalidUCRVarNames.add(var)
					knownvars.add(var)
					all_variables.add(var)

				if invalidUCRVarNames:
					self.addmsg(
						'0004-13',
						'template contains invalid UCR variable names:\n      - %s' % (
							'\n      - '.join(sorted(invalidUCRVarNames))),
						conffn)

				# Last test: add all Subfile variables
				if mfn and mfn in all_multifiles:
					for sf in all_subfiles[mfn]:
						knownvars.update(sf.get('Variables', []))
				if not knownvars:
					self.addmsg('0004-56', 'No UCR variables used', conffn)

			conffnfound |= conffn.rsplit('/')[-1] in (all_preinst | all_postinst | all_module | all_script)

			if not conffnfound:
				self.addmsg('0004-14', 'template file is not registered in *.univention-config-registry', conffn)

		#
		# check if headers are present
		#
		# Part1: simple templates
		for obj in all_files:
			try:
				fn = obj['File'][0]
			except LookupError:
				print('FIXME: no File entry in obj: %s' % obj, file=sys.stderr)
			else:
				try:
					conffn = find_conf(fn)
				except LookupError:
					for _ in all_definitions[fn]:
						self.addmsg('0004-15', 'UCR template file "%s" is registered but not found in conffiles/ (1)' % (fn,), _)
				else:
					if not any(conffiles[conffn][typ] for typ in ('headerfound', 'ucrwarning')):
						self.addmsg('0004-16', 'UCR header is missing', conffn)
				self.test_marker(os.path.join(path, 'conffiles', fn))

		# Part2: subfile templates
		for mfn, items in all_subfiles.items():
			found = False
			for obj in items:
				try:
					fn = obj['Subfile'][0]
				except LookupError:
					print('FIXME: no Subfile entry in obj: %s' % obj, file=sys.stderr)
				else:
					try:
						conffn = find_conf(fn)
					except LookupError:
						for _ in all_definitions[fn]:
							self.addmsg('0004-17', 'UCR template file "%s" is registered but not found in conffiles/ (2)' % (fn,), _)
					else:
						found |= any(conffiles[conffn][typ] for typ in ('headerfound', 'ucrwarning'))
			if not found:
				for _ in all_definitions[mfn]:
					self.addmsg('0004-18', 'UCR header is maybe missing in multifile "%s"' % (mfn,), _)

		# Test modules / scripts
		for f in all_preinst | all_postinst | all_module | all_script:
			fn = os.path.join(path, 'conffiles', f)
			try:
				checks = conffiles[fn]
			except KeyError:
				self.addmsg('0004-36', 'Module file "%s" does not exist' % (f,))
				continue
			if f in all_preinst | all_postinst | all_module and not checks['pythonic']:
				self.addmsg('0004-35', 'Invalid module file name', fn)
			if f in all_preinst and not checks['preinst']:
				self.addmsg('0004-37', 'Missing Python function "preinst(ucr, changes)"', fn)
			if f in all_postinst and not checks['postinst']:
				self.addmsg('0004-38', 'Missing Python function "postinst(ucr, changes)"', fn)
			if f in all_module and not checks['handler']:
				self.addmsg('0004-39', 'Missing Python function "handler(ucr, changes)"', fn)

		# Disable the following test to check for descriptions because it is too verbose
		return
		for var in all_variables - all_descriptions:
			self.addmsg('0004-57', 'No description found for UCR variable "%s"' % (var,))

	def test_marker(self, fn: str) -> None:
		"""Bug #24728: count of markers must be even."""
		count_python = 0
		count_var = 0
		try:
			with open(fn, 'r') as fd:
				for line in fd:
					for _ in self.RE_PYTHON.finditer(line):
						count_python += 1
					for _ in self.RE_VAR.finditer(line):
						count_var += 1
		except EnvironmentError:
			# self.addmsg('0004-27', 'cannot open/read file', fn)
			return
		except UnicodeDecodeError:
			# self.addmsg('0004-30', 'contains invalid characters', fn, ex.start)
			return

		if count_python % 2:
			self.addmsg('0004-31', 'odd number of @!@ markers', fn)
		if count_var % 2:
			self.addmsg('0004-32', 'odd number of @%@ markers', fn)


if __name__ == '__main__':
	import doctest
	doctest.testmod()
