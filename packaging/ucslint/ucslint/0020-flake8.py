#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2016 Univention GmbH
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

import re
import subprocess
from argparse import ArgumentParser

try:
	import univention.ucslint.base as uub
except ImportError:
	import ucslint.base as uub


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):

	"""Python specific flake8 checks."""

	name = '0020-flake8'

	PYTHON_HASH_BANG = re.compile('^#!.*[ /]python[0-9.]*')

	IGNORED_FILES = [
		re.compile('/conffiles/'),  # UCR templates with markers contain syntax errors
		re.compile('/python-notifier/'),  # external code
		re.compile('/univention-novnc/'),  # external code
		re.compile('/univention-ldb-modules/buildtools/'),  # external code
		re.compile('/ucslint/testframework/'),  # don't care about tests for ucslint
		re.compile('univention/pyDes.py'),  # external code
		re.compile('services/univention-printserver/modules/univention/management/console/handlers/cups'),  # UCS 2.4 code
		re.compile('univention-directory-manager-modules/test/'),  # unrelevant, should be removed imho
	]

	IGNORE = {
		re.compile('/__init__.py'): 'F403',  # some package provide all members of subpackages
		re.compile('/test/ucs-test/tests\/.*'): 'E266',  # UCS-Test headers begin with "## foo: bar"
		re.compile('/syntax.d/.*'): 'E821',  # some variables are undefined, as these files are mixins
		re.compile('management/univention-directory-manager-modules'): 'W601',  # UDM allows has_key() Bug #W601
	}

	DEFAULT_IGNORE = 'N,E501,W191,E265'
	DEFAULT_SELECT = None
	MAX_LINE_LENGTH = 220

	def getMsgIds(self):
		return {
			'0020-F401': [uub.RESULT_ERROR, 'module imported but unused'],
			'0020-F402': [uub.RESULT_ERROR, 'import module from line N shadowed by loop variable'],
			'0020-F403': [uub.RESULT_ERROR, '‘from module import *’ used; unable to detect undefined names'],
			'0020-F404': [uub.RESULT_ERROR, 'future import(s) name after other statements'],
			'0020-F405': [uub.RESULT_ERROR, 'name may be undefined, or defined from star imports: module'],

			'0020-F811': [uub.RESULT_ERROR, 'redefinition of unused name from line N'],
			'0020-F812': [uub.RESULT_ERROR, 'list comprehension redefines name from line N'],
			'0020-F821': [uub.RESULT_ERROR, 'undefined name name'],
			'0020-F822': [uub.RESULT_ERROR, 'undefined name name in __all__'],
			'0020-F823': [uub.RESULT_ERROR, 'local variable name ... referenced before assignment'],
			'0020-F831': [uub.RESULT_ERROR, 'duplicate argument name in function definition'],
			'0020-F841': [uub.RESULT_ERROR, 'local variable name is assigned to but never used'],

			'0020-E1': [uub.RESULT_ERROR, 'Indentation'],
			'0020-E101': [uub.RESULT_ERROR, 'indentation contains mixed spaces and tabs'],
			'0020-E111': [uub.RESULT_ERROR, 'indentation is not a multiple of four'],
			'0020-E112': [uub.RESULT_ERROR, 'expected an indented block'],
			'0020-E113': [uub.RESULT_ERROR, 'unexpected indentation'],
			'0020-E114': [uub.RESULT_ERROR, 'indentation is not a multiple of four (comment)'],
			'0020-E115': [uub.RESULT_ERROR, 'expected an indented block (comment)'],
			'0020-E116': [uub.RESULT_ERROR, 'unexpected indentation (comment)'],

			'0020-E121': [uub.RESULT_WARN, 'continuation line under-indented for hanging indent'],
			'0020-E122': [uub.RESULT_WARN, 'continuation line missing indentation or outdented'],
			'0020-E123': [uub.RESULT_WARN, 'closing bracket does not match indentation of opening bracket’s line'],
			'0020-E124': [uub.RESULT_WARN, 'closing bracket does not match visual indentation'],
			'0020-E125': [uub.RESULT_WARN, 'continuation line with same indent as next logical line'],
			'0020-E126': [uub.RESULT_WARN, 'continuation line over-indented for hanging indent'],
			'0020-E127': [uub.RESULT_WARN, 'continuation line over-indented for visual indent'],
			'0020-E128': [uub.RESULT_WARN, 'continuation line under-indented for visual indent'],
			'0020-E129': [uub.RESULT_WARN, 'visually indented line with same indent as next logical line'],
			'0020-E131': [uub.RESULT_WARN, 'continuation line unaligned for hanging indent'],
			'0020-E133': [uub.RESULT_WARN, 'closing bracket is missing indentation'],

			'0020-E2': [uub.RESULT_ERROR, 'Whitespace'],
			'0020-E201': [uub.RESULT_ERROR, 'whitespace after ‘(‘'],
			'0020-E202': [uub.RESULT_ERROR, 'whitespace before ‘)’'],
			'0020-E203': [uub.RESULT_ERROR, 'whitespace before ‘:’'],

			'0020-E211': [uub.RESULT_ERROR, 'whitespace before ‘(‘'],

			'0020-E221': [uub.RESULT_ERROR, 'multiple spaces before operator'],
			'0020-E222': [uub.RESULT_ERROR, 'multiple spaces after operator'],
			'0020-E223': [uub.RESULT_ERROR, 'tab before operator'],
			'0020-E224': [uub.RESULT_ERROR, 'tab after operator'],
			'0020-E225': [uub.RESULT_ERROR, 'missing whitespace around operator'],
			'0020-E226': [uub.RESULT_ERROR, 'missing whitespace around arithmetic operator'],
			'0020-E227': [uub.RESULT_ERROR, 'missing whitespace around bitwise or shift operator'],
			'0020-E228': [uub.RESULT_ERROR, 'missing whitespace around modulo operator'],

			'0020-E231': [uub.RESULT_ERROR, 'missing whitespace after ‘,’, ‘;’, or ‘:’'],

			'0020-E241': [uub.RESULT_ERROR, 'multiple spaces after ‘,’'],
			'0020-E242': [uub.RESULT_ERROR, 'tab after ‘,’'],

			'0020-E251': [uub.RESULT_ERROR, 'unexpected spaces around keyword / parameter equals'],

			'0020-E261': [uub.RESULT_ERROR, 'at least two spaces before inline comment'],
			'0020-E262': [uub.RESULT_ERROR, 'inline comment should start with ‘# ‘'],
			'0020-E265': [uub.RESULT_STYLE, 'block comment should start with ‘# ‘'],
			'0020-E266': [uub.RESULT_WARN, 'too many leading ‘#’ for block comment'],

			'0020-E271': [uub.RESULT_ERROR, 'multiple spaces after keyword'],
			'0020-E272': [uub.RESULT_ERROR, 'multiple spaces before keyword'],
			'0020-E273': [uub.RESULT_ERROR, 'tab after keyword'],
			'0020-E274': [uub.RESULT_ERROR, 'tab before keyword'],

			'0020-E3': [uub.RESULT_ERROR, 'Blank line'],
			'0020-E301': [uub.RESULT_ERROR, 'expected 1 blank line, found 0'],
			'0020-E302': [uub.RESULT_ERROR, 'expected 2 blank lines, found 0'],
			'0020-E303': [uub.RESULT_ERROR, 'too many blank lines (3)'],
			'0020-E304': [uub.RESULT_ERROR, 'blank lines found after function decorator'],

			'0020-E4': [uub.RESULT_ERROR, 'Import'],
			'0020-E401': [uub.RESULT_ERROR, 'multiple imports on one line'],
			'0020-E402': [uub.RESULT_WARN, 'module level import not at top of file'],  # Bug #42806: should be RESULT_ERROR when fixed

			'0020-E5': [uub.RESULT_ERROR, 'Line length'],
			'0020-E501': [uub.RESULT_STYLE, 'line too long (82 > 79 characters)'],
			'0020-E502': [uub.RESULT_ERROR, 'the backslash is redundant between brackets'],

			'0020-E7': [uub.RESULT_ERROR, 'Statement'],
			'0020-E701': [uub.RESULT_ERROR, 'multiple statements on one line (colon)'],
			'0020-E702': [uub.RESULT_ERROR, 'multiple statements on one line (semicolon)'],
			'0020-E703': [uub.RESULT_ERROR, 'statement ends with a semicolon'],
			'0020-E704': [uub.RESULT_ERROR, 'multiple statements on one line (def)'],
			'0020-E711': [uub.RESULT_ERROR, 'comparison to None should be ‘if cond is None:’'],
			'0020-E712': [uub.RESULT_ERROR, 'comparison to True should be ‘if cond is True:’ or ‘if cond:’'],
			'0020-E713': [uub.RESULT_ERROR, 'test for membership should be ‘not in’'],
			'0020-E714': [uub.RESULT_ERROR, 'test for object identity should be ‘is not’'],
			'0020-E721': [uub.RESULT_ERROR, 'do not compare types, use ‘isinstance()’'],
			'0020-E731': [uub.RESULT_ERROR, 'do not assign a lambda expression, use a def'],

			'0020-E9': [uub.RESULT_ERROR, 'Runtime'],
			'0020-E901': [uub.RESULT_ERROR, 'SyntaxError or IndentationError'],
			'0020-E902': [uub.RESULT_ERROR, 'IOError'],

			'0020-W1': [uub.RESULT_ERROR, 'Indentation warning'],
			'0020-W191': [uub.RESULT_STYLE, 'indentation contains tabs'],

			'0020-W2': [uub.RESULT_ERROR, 'Whitespace warning'],
			'0020-W291': [uub.RESULT_ERROR, 'trailing whitespace'],
			'0020-W292': [uub.RESULT_ERROR, 'no newline at end of file'],
			'0020-W293': [uub.RESULT_ERROR, 'blank line contains whitespace'],

			'0020-W3': [uub.RESULT_ERROR, 'Blank line warning'],
			'0020-W391': [uub.RESULT_ERROR, 'blank line at end of file'],

			'0020-W5': [uub.RESULT_ERROR, 'Line break warning'],
			'0020-W503': [uub.RESULT_ERROR, 'line break occurred before a binary operator'],

			'0020-W6': [uub.RESULT_ERROR, 'Deprecation warning'],
			'0020-W601': [uub.RESULT_WARN, '.has_key() is deprecated, use ‘in’'],  # Bug #42787: should be RESULT_ERROR when fixed
			'0020-W602': [uub.RESULT_ERROR, 'deprecated form of raising exception'],
			'0020-W603': [uub.RESULT_ERROR, '‘<>’ is deprecated, use ‘!=’'],
			'0020-W604': [uub.RESULT_ERROR, 'backticks are deprecated, use ‘repr()’'],

			'0020-N801': [uub.RESULT_STYLE, "class names should use CapWords convention"],
			'0020-N802': [uub.RESULT_STYLE, "function name should be lowercase"],
			'0020-N803': [uub.RESULT_STYLE, "argument name should be lowercase"],
			'0020-N804': [uub.RESULT_STYLE, "first argument of a classmethod should be named 'cls'"],
			'0020-N805': [uub.RESULT_STYLE, "first argument of a method should be named 'self'"],
			'0020-N806': [uub.RESULT_STYLE, "variable in function should be lowercase"],
			'0020-N811': [uub.RESULT_STYLE, "constant imported as non constant"],
			'0020-N812': [uub.RESULT_STYLE, "lowercase imported as non lowercase"],
			'0020-N813': [uub.RESULT_STYLE, "camelcase imported as lowercase"],
			'0020-N814': [uub.RESULT_STYLE, "camelcase imported as constant"],
		}

	def postinit(self, path):
		""" checks to be run before real check or to create precalculated data for several runs. Only called once! """

	def check(self, path):
		super(UniventionPackageCheck, self).check(path)

		errors = []
		for ignore, pathes in self._iter_pathes(path):
			cmd = ['flake8', '--config=/dev/null']
			if ignore:
				cmd.extend(['--ignore', ignore])
			if self.DEFAULT_SELECT:
				cmd.extend(['--select', self.DEFAULT_SELECT])
			cmd.extend(['--max-line-length', str(self.MAX_LINE_LENGTH)])
			cmd.extend(['--format', '0020-%(code)s %(path)s %(row)s %(col)s %(text)s'])
			if self.debuglevel > 0:
				cmd.append('--show-source')
			cmd.append('--')
			cmd.extend(pathes)

			process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
			errors.extend(process.communicate()[0].splitlines())

		self.format_errors(errors)

	def fix(self, path, *args):
		for ignore, pathes in self._iter_pathes(path):
			cmd = ['autopep8', '-i', '-aaa']
			if ignore:
				cmd.extend(['--ignore', ignore])
			if self.DEFAULT_SELECT:
				cmd.extend(['--select', self.DEFAULT_SELECT])
			cmd.extend(['--max-line-length', str(self.MAX_LINE_LENGTH)])
			cmd.extend(args)
			cmd.append('--')
			cmd.extend(pathes)
			subprocess.call(cmd)

	def _iter_pathes(self, path):
		files = list(self.find_python_files(path))

		ignored = {}
		for path in files:
			ignore = ','.join(v for k, v in self.IGNORE.iteritems() if k.search(path))
			ignore = '%s,%s' % (self.DEFAULT_IGNORE, ignore)
			ignored.setdefault(ignore.rstrip(','), []).append(path)

		return ignored.iteritems()

	def format_errors(self, errors):
		for i, line in enumerate(errors, 1):
			if not line.startswith('0020-'):
				continue
			code, path, row, col, text = line.split(' ', 4)
			source = []
			while len(errors) > i + 1 and not errors[i].startswith('0020-'):
				source.append(errors[i])
				i += 1
			msg = '%s:\n%s\n' % (text, '\n'.join(source)) if source else text
			if not self.ignore_line(code, path, row, col, text, source):
				self.addmsg(code, msg, path, row, col)

	def ignore_line(self, code, path, row, col, text, source):
		if code == '0020-F841' and "local variable '_d' is assigned to but never used" in text:  # _d = univention.debug.function()
			return True
		return False

	def find_python_files(self, base):
		pathes = set(list(uub.FilteredDirWalkGenerator(base, suffixes=['.py'])) + list(uub.FilteredDirWalkGenerator(base, ignore_suffixes=['.py'], reHashBang=self.PYTHON_HASH_BANG)))
		for path in pathes:
			if not self.ignore_path(path):
				yield path

	def ignore_path(self, path):
		return any(pattern.search(path) for pattern in self.IGNORED_FILES)

	@classmethod
	def main(cls):
		parser = ArgumentParser()
		parser.add_argument('--fix', default=False, action='store_true')
		parser.add_argument('--path', default='.')
		parser.add_argument('--select', default=cls.DEFAULT_SELECT, help='default=%(default)s')
		parser.add_argument('--ignore', default=cls.DEFAULT_IGNORE, help='default=%(default)s')
		parser.add_argument('--max-line-length', default=cls.MAX_LINE_LENGTH, help='default=%(default)s')
		args, args.arguments = parser.parse_known_args()
		cls.DEFAULT_IGNORE = args.ignore
		cls.DEFAULT_SELECT = args.select
		cls.MAX_LINE_LENGTH = args.max_line_length
		self = cls()
		self.postinit(args.path)
		if args.fix:
			self.fix(args.path, *args.arguments)
		self.check(args.path)
		for msg in self.result():
			print str(msg)


if __name__ == '__main__':
	UniventionPackageCheck.main()
