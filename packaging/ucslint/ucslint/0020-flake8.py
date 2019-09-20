#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2016-2019 Univention GmbH
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
import re
import os
import sys
import subprocess
from argparse import ArgumentParser

try:
	import univention.ucslint.base as uub
except ImportError:
	import ucslint.base as uub


class UniventionPackageCheck(uub.UniventionPackageCheckBase):

	"""Python specific flake8 checks."""

	PYTHON_HASH_BANG = re.compile('^#!.*[ /]python[0-9.]*')

	IGNORED_FILES = [
		re.compile('conffiles/[^/]+/'),  # UCR templates with markers contain syntax errors
		re.compile('python-notifier/'),  # external code
		re.compile('univention-novnc/'),  # external code
		re.compile('univention-ldb-modules/'),  # external code
		re.compile('univention/pyDes.py'),  # external code
		re.compile('ucslint/testframework/'),  # don't care about tests for ucslint
		re.compile('services/univention-printserver/modules/univention/management/console/handlers/cups'),  # UCS 2.4 code
		re.compile('univention-directory-manager-modules/test/'),  # unrelevant, should be removed imho
	]

	IGNORE = {
		re.compile('(^|/)__init__.py$'): 'F403',  # some package provide all members of subpackages
		re.compile('test/ucs-test/tests\/.*'): 'E266',  # UCS-Test headers begin with "## foo: bar"
		re.compile('ucs-test-ucsschool'): 'E266',
		re.compile('(^|/)syntax.d/.*'): 'E821',  # some variables are undefined, as these files are mixins
		re.compile('univention-directory-manager-modules/'): 'W601',  # UDM allows has_key() Bug #W601
	}

	DEFAULT_IGNORE = os.environ.get('UCSLINT_FLAKE8_IGNORE', 'N,B,E501,W191,E265,E266')
	DEFAULT_SELECT = None
	MAX_LINE_LENGTH = 220
	GRACEFUL = not os.environ.get('UCSLINT_FLAKE8_STRICT')

	def __init__(self, *args, **kwargs):
		self.show_statistics = kwargs.pop('show_statistics', False)
		self.python_versions = ['python2.7', 'python3.5']
		try:
			with open('debian/rules') as fd:
				content = fd.read()
			if not re.search('\s*dh .*--with.*python2', content):
				self.python_versions.remove('python2.7')
			if not re.search('\s*dh .*--with.*python3', content):
				self.python_versions.remove('python3.5')
		except EnvironmentError:
			pass
		super(UniventionPackageCheck, self).__init__(*args, **kwargs)

	def getMsgIds(self):
		ERROR_BUT_WARN = uub.RESULT_WARN if self.GRACEFUL else uub.RESULT_ERROR
		return {
			'0020-F401': [ERROR_BUT_WARN, 'module imported but unused'],
			'0020-F402': [ERROR_BUT_WARN, 'import module from line N shadowed by loop variable'],
			'0020-F403': [ERROR_BUT_WARN, '‘from module import *’ used; unable to detect undefined names'],
			'0020-F404': [ERROR_BUT_WARN, 'future import(s) name after other statements'],
			'0020-F405': [ERROR_BUT_WARN, 'name may be undefined, or defined from star imports: module'],

			'0020-F811': [ERROR_BUT_WARN, 'redefinition of unused name from line N'],
			'0020-F812': [ERROR_BUT_WARN, 'list comprehension redefines name from line N'],
			'0020-F821': [ERROR_BUT_WARN, 'undefined name name'],
			'0020-F822': [ERROR_BUT_WARN, 'undefined name name in __all__'],
			'0020-F823': [ERROR_BUT_WARN, 'local variable name ... referenced before assignment'],
			'0020-F831': [ERROR_BUT_WARN, 'duplicate argument name in function definition'],
			'0020-F841': [ERROR_BUT_WARN, 'local variable name is assigned to but never used'],

			'0020-E1': [ERROR_BUT_WARN, 'Indentation'],
			'0020-E101': [ERROR_BUT_WARN, 'indentation contains mixed spaces and tabs'],
			'0020-E111': [ERROR_BUT_WARN, 'indentation is not a multiple of four'],
			'0020-E112': [ERROR_BUT_WARN, 'expected an indented block'],
			'0020-E113': [ERROR_BUT_WARN, 'unexpected indentation'],
			'0020-E114': [ERROR_BUT_WARN, 'indentation is not a multiple of four (comment)'],
			'0020-E115': [ERROR_BUT_WARN, 'expected an indented block (comment)'],
			'0020-E116': [ERROR_BUT_WARN, 'unexpected indentation (comment)'],

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

			'0020-E2': [ERROR_BUT_WARN, 'Whitespace'],
			'0020-E201': [ERROR_BUT_WARN, 'whitespace after ‘(‘'],
			'0020-E202': [ERROR_BUT_WARN, 'whitespace before ‘)’'],
			'0020-E203': [ERROR_BUT_WARN, 'whitespace before ‘:’'],

			'0020-E211': [ERROR_BUT_WARN, 'whitespace before ‘(‘'],

			'0020-E221': [ERROR_BUT_WARN, 'multiple spaces before operator'],
			'0020-E222': [ERROR_BUT_WARN, 'multiple spaces after operator'],
			'0020-E223': [ERROR_BUT_WARN, 'tab before operator'],
			'0020-E224': [ERROR_BUT_WARN, 'tab after operator'],
			'0020-E225': [ERROR_BUT_WARN, 'missing whitespace around operator'],
			'0020-E226': [ERROR_BUT_WARN, 'missing whitespace around arithmetic operator'],
			'0020-E227': [ERROR_BUT_WARN, 'missing whitespace around bitwise or shift operator'],
			'0020-E228': [ERROR_BUT_WARN, 'missing whitespace around modulo operator'],

			'0020-E231': [ERROR_BUT_WARN, 'missing whitespace after ‘,’, ‘;’, or ‘:’'],

			'0020-E241': [ERROR_BUT_WARN, 'multiple spaces after ‘,’'],
			'0020-E242': [ERROR_BUT_WARN, 'tab after ‘,’'],

			'0020-E251': [ERROR_BUT_WARN, 'unexpected spaces around keyword / parameter equals'],

			'0020-E261': [ERROR_BUT_WARN, 'at least two spaces before inline comment'],
			'0020-E262': [ERROR_BUT_WARN, 'inline comment should start with ‘# ‘'],
			'0020-E265': [uub.RESULT_STYLE, 'block comment should start with ‘# ‘'],
			'0020-E266': [uub.RESULT_WARN, 'too many leading ‘#’ for block comment'],

			'0020-E271': [ERROR_BUT_WARN, 'multiple spaces after keyword'],
			'0020-E272': [ERROR_BUT_WARN, 'multiple spaces before keyword'],
			'0020-E273': [ERROR_BUT_WARN, 'tab after keyword'],
			'0020-E274': [ERROR_BUT_WARN, 'tab before keyword'],

			'0020-E3': [ERROR_BUT_WARN, 'Blank line'],
			'0020-E301': [ERROR_BUT_WARN, 'expected 1 blank line, found 0'],
			'0020-E302': [ERROR_BUT_WARN, 'expected 2 blank lines, found 0'],
			'0020-E303': [ERROR_BUT_WARN, 'too many blank lines (3)'],
			'0020-E304': [ERROR_BUT_WARN, 'blank lines found after function decorator'],
			'0020-E305': [ERROR_BUT_WARN, 'expected 2 blank lines after end of function or class'],
			'0020-E306': [ERROR_BUT_WARN, 'expected 1 blank line before a nested definition, found 0'],

			'0020-E4': [ERROR_BUT_WARN, 'Import'],
			'0020-E401': [ERROR_BUT_WARN, 'multiple imports on one line'],
			'0020-E402': [uub.RESULT_WARN, 'module level import not at top of file'],  # Bug #42806: should be RESULT_ERROR when fixed

			'0020-E5': [ERROR_BUT_WARN, 'Line length'],
			'0020-E501': [uub.RESULT_STYLE, 'line too long (82 > 79 characters)'],
			'0020-E502': [ERROR_BUT_WARN, 'the backslash is redundant between brackets'],

			'0020-E7': [ERROR_BUT_WARN, 'Statement'],
			'0020-E701': [ERROR_BUT_WARN, 'multiple statements on one line (colon)'],
			'0020-E702': [ERROR_BUT_WARN, 'multiple statements on one line (semicolon)'],
			'0020-E703': [ERROR_BUT_WARN, 'statement ends with a semicolon'],
			'0020-E704': [ERROR_BUT_WARN, 'multiple statements on one line (def)'],
			'0020-E711': [ERROR_BUT_WARN, 'comparison to None should be ‘if cond is None:’'],
			'0020-E712': [ERROR_BUT_WARN, 'comparison to True should be ‘if cond is True:’ or ‘if cond:’'],
			'0020-E713': [ERROR_BUT_WARN, 'test for membership should be ‘not in’'],
			'0020-E714': [ERROR_BUT_WARN, 'test for object identity should be ‘is not’'],
			'0020-E721': [ERROR_BUT_WARN, 'do not compare types, use ‘isinstance()’'],
			'0020-E731': [ERROR_BUT_WARN, 'do not assign a lambda expression, use a def'],
			'0020-E741': [uub.RESULT_WARN, 'do not use variables named ‘l’, ‘O’, or ‘I’'],
			'0020-E742': [ERROR_BUT_WARN, 'do not define classes named ‘l’, ‘O’, or ‘I’'],
			'0020-E743': [ERROR_BUT_WARN, 'do not define functions named ‘l’, ‘O’, or ‘I’'],

			'0020-E9': [ERROR_BUT_WARN, 'Runtime'],
			'0020-E901': [ERROR_BUT_WARN, 'SyntaxError or IndentationError'],
			'0020-E902': [ERROR_BUT_WARN, 'IOError'],
			'0020-E999': [ERROR_BUT_WARN, 'SyntaxError: invalid syntax'],  # python3 only? should be RESULT_ERROR

			'0020-W1': [ERROR_BUT_WARN, 'Indentation warning'],
			'0020-W191': [uub.RESULT_STYLE, 'indentation contains tabs'],

			'0020-W2': [ERROR_BUT_WARN, 'Whitespace warning'],
			'0020-W291': [ERROR_BUT_WARN, 'trailing whitespace'],
			'0020-W292': [ERROR_BUT_WARN, 'no newline at end of file'],
			'0020-W293': [ERROR_BUT_WARN, 'blank line contains whitespace'],

			'0020-W3': [ERROR_BUT_WARN, 'Blank line warning'],
			'0020-W391': [ERROR_BUT_WARN, 'blank line at end of file'],

			'0020-W5': [ERROR_BUT_WARN, 'Line break warning'],
			'0020-W503': [ERROR_BUT_WARN, 'line break occurred before a binary operator'],

			'0020-W6': [ERROR_BUT_WARN, 'Deprecation warning'],
			'0020-W601': [uub.RESULT_WARN, '.has_key() is deprecated, use ‘in’'],  # Bug #42787: should be RESULT_ERROR when fixed in UDM
			'0020-W602': [ERROR_BUT_WARN, 'deprecated form of raising exception'],
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

			'0020-B001': [
				uub.RESULT_WARN,
				"Do not use bare `except:`, it also catches unexpected "
				"events like memory errors, interrupts, system exit, and so on.  "
				"Prefer `except Exception:`.  If you're sure what you're doing, "
				"be explicit and write `except BaseException:`.",
			],
			'0020-B002': [
				ERROR_BUT_WARN,
				" Python does not support the unary prefix increment. Writing "
				"++n is equivalent to +(+(n)), which equals n. You meant n += 1."
			],
			'0020-B003': [
				ERROR_BUT_WARN,
				" Assigning to `os.environ` doesn't clear the environment. "
				"Subprocesses are going to see outdated variables, in disagreement "
				"with the current process. Use `os.environ.clear()` or the `env=` "
				"argument to Popen."
			],
			'0020-B004': [
				ERROR_BUT_WARN,
				" Using `hasattr(x, '__call__')` to test if `x` is callable "
				"is unreliable. If `x` implements custom `__getattr__` or its "
				"`__call__` is itself not callable, you might get misleading "
				"results. Use `callable(x)` for consistent results."
			],
			'0020-B005': [
				uub.RESULT_WARN,
				"Using .strip() with multi-character strings is misleading "
				"the reader. It looks like stripping a substring. Move your "
				"character set to a constant if this is deliberate. Use "
				".replace() or regular expressions to remove string fragments."
			],
			'0020-B301': [
				uub.RESULT_WARN,
				"Python 3 does not include `.iter*` methods on dictionaries. "
				"Remove the `iter` prefix from the method name. For Python 2 "
				"compatibility, prefer the Python 3 equivalent unless you expect "
				"the size of the container to be large or unbounded. Then use "
				"`six.iter*` or `future.utils.iter*`."
			],
			'0020-B302': [
				uub.RESULT_WARN,
				"Python 3 does not include `.view*` methods on dictionaries. "
				"Remove the `view` prefix from the method name. For Python 2 "
				"compatibility, prefer the Python 3 equivalent unless you expect "
				"the size of the container to be large or unbounded. Then use "
				"`six.view*` or `future.utils.view*`."
			],
			'0020-B303': [
				uub.RESULT_WARN,
				"`__metaclass__` does nothing on Python 3. Use "
				"`class MyClass(BaseClass, metaclass=...)`. For Python 2 "
				"compatibility, use `six.add_metaclass`."
			],
			'0020-B304': [uub.RESULT_WARN, "`sys.maxint` is not a thing on Python 3. Use `sys.maxsize`."],
			'0020-B305': [
				uub.RESULT_WARN,
				"`.next()` is not a thing on Python 3. Use the `next()` "
				"builtin. For Python 2 compatibility, use `six.next()`."
			],
			'0020-B306': [
				uub.RESULT_WARN,
				"`BaseException.message` has been deprecated as of Python "
				"2.6 and is removed in Python 3. Use `str(e)` to access the "
				"user-readable message. Use `e.args` to access arguments passed "
				"to the exception."
			],
			'0020-B901': [
				uub.RESULT_WARN,
				"Using `yield` together with `return x`. Use native "
				"`async def` coroutines or put a `# noqa` comment on this "
				"line if this was intentional."
			],
		}

	def postinit(self, path):
		""" checks to be run before real check or to create precalculated data for several runs. Only called once! """

	def check(self, path):
		super(UniventionPackageCheck, self).check(path)

		errors = []
		for python in self.python_versions:
			for ignore, pathes in self._iter_pathes(path):
				cmd = [python, '/usr/bin/flake8', '--config=/dev/null']
				if ignore:
					cmd.extend(['--ignore', ignore])
				if self.DEFAULT_SELECT:
					cmd.extend(['--select', self.DEFAULT_SELECT])
				cmd.extend(['--max-line-length', str(self.MAX_LINE_LENGTH)])
				cmd.extend(['--format', '0020-%(code)s %(path)s %(row)s %(col)s %(text)s'])
				if self.show_statistics:
					cmd.append('--statistics')
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
		if self.DEFAULT_SELECT or self.show_statistics:
			return {
				self.DEFAULT_IGNORE: files,
			}.iteritems()

		ignored = {}
		for path in files:
			ignore = ','.join(v for k, v in self.IGNORE.iteritems() if k.search(os.path.abspath(path)))
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
		allowed_names = ['_d', '_']
		if code == '0020-F841' and any("local variable '%s' is assigned to but never used" % (x,) in text for x in allowed_names):  # _d = univention.debug.function()
			return True
		return False

	def find_python_files(self, base):
		pathes = set(list(uub.FilteredDirWalkGenerator(base, suffixes=['.py'])) + list(uub.FilteredDirWalkGenerator(base, ignore_suffixes=['.py'], reHashBang=self.PYTHON_HASH_BANG)))
		for path in pathes:
			if not self.ignore_path(path):
				yield path

	def ignore_path(self, path):
		return any(pattern.search(os.path.abspath(path)) for pattern in self.IGNORED_FILES)

	@classmethod
	def main(cls):
		parser = ArgumentParser()
		parser.add_argument('-d', '--debug', default=0, type=int, help='debuglevel (to show also source lines)')
		parser.add_argument('--statistics', default=False, action='store_true', help='Show a summary at the end.')
		parser.add_argument('--fix', default=False, action='store_true')
		parser.add_argument('--check', default=False, action='store_true')
		parser.add_argument('--path', default='.')
		parser.add_argument('--select', default=cls.DEFAULT_SELECT, help='default: %(default)s')
		parser.add_argument('--ignore', default=cls.DEFAULT_IGNORE, help='default: %(default)s')
		parser.add_argument('--max-line-length', default=cls.MAX_LINE_LENGTH, help='default: %(default)s')
		parser.add_argument('--graceful', action='store_true', default=False, help='behave like calling ucslint would do: do not fail on certain errors')
		parser.add_argument('--versions', default='2.7,3.5', help='Which python versions to run (e.g. 2.7,3.5)')
		args, args.arguments = parser.parse_known_args()
		cls.DEFAULT_IGNORE = args.ignore
		cls.DEFAULT_SELECT = args.select
		cls.MAX_LINE_LENGTH = args.max_line_length
		cls.GRACEFUL = args.graceful
		self = cls(show_statistics=args.statistics)
		if args.versions:
			self.python_versions = ['python%s' % (float(x),) for x in args.versions.split(',')]
		self.setdebug(args.debug)
		self.postinit(args.path)
		if args.fix:
			self.fix(args.path, *args.arguments)
		if args.check or not args.fix:
			self.check(args.path)
		msgids = self.getMsgIds()
		exitcode = 0
		for msg in self.result():
			errno = msgids.get(msg.getId(), [None])[0]
			if errno == uub.RESULT_ERROR:
				exitcode = 1
			print(uub.RESULT_INT2STR.get(errno) or 'FIXME', str(msg))
		return exitcode


if __name__ == '__main__':
	sys.exit(UniventionPackageCheck.main())
