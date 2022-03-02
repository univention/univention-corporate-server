#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright 2016-2022 Univention GmbH
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
import subprocess
import sys
from argparse import ArgumentParser
from typing import Any, Dict, Iterable, List, Tuple  # noqa F401

import univention.ucslint.base as uub
from univention.ucslint.python import python_files

EXECUTE_TOKEN = re.compile('@!@(.+?)@!@', re.MULTILINE | re.DOTALL)
UCR_HEADER = '''\
# -*- coding: utf-8 -*-
import univention.config_registry  # noqa
from fake import configRegistry, baseConfig  # noqa

'''
PYTHON_VERSIONS = PY2, PY3 = ('python2', 'python3')

RE_PY2 = re.compile(r'\s*dh .*--with.*python2')
RE_PY3 = re.compile(r'\s*dh .*--with.*python3')


class UniventionPackageCheck(uub.UniventionPackageCheckBase):

	"""Python specific flake8 checks."""

	IGNORED_FILES = [
		re.compile(r'conffiles/[^/]+/'),  # UCR templates with markers contain syntax errors
		re.compile(r'univention-ldb-modules/buildtools/'),  # external code
		re.compile(r'ucslint/testframework/(?!0020)'),  # ucslint tests may contain error, but not for this module.
	]

	IGNORED_CODES_FOR_FILES = {
		re.compile(r'test/ucs-test/tests\/.*'): 'E266',  # UCS-Test headers begin with "## foo: bar"
		re.compile(r'ucs-test-ucsschool'): 'E266',
	}

	DEFAULT_IGNORE = os.environ.get('UCSLINT_FLAKE8_IGNORE', 'I,N,B,D,E501,W191')
	DEFAULT_SELECT = None
	MAX_LINE_LENGTH = 220
	GRACEFUL = not os.environ.get('UCSLINT_FLAKE8_STRICT')

	def __init__(self, *args: Any, **kwargs: Any) -> None:
		self.show_statistics = kwargs.pop('show_statistics', False)
		self.python_versions = list(PYTHON_VERSIONS)
		try:
			with open('debian/rules', 'r') as fd:
				content = fd.read()
			if not RE_PY2.search(content):
				self.python_versions.remove(PY2)
			if not RE_PY3.search(content):
				self.python_versions.remove(PY3)
		except EnvironmentError:
			pass
		super(UniventionPackageCheck, self).__init__(*args, **kwargs)  # type: ignore

	def getMsgIds(self) -> uub.MsgIds:
		ERROR_BUT_WARN = uub.RESULT_WARN if self.GRACEFUL else uub.RESULT_ERROR
		return {
			'0020-F401': (ERROR_BUT_WARN, 'module imported but unused'),
			'0020-F402': (uub.RESULT_ERROR, 'import module from line N shadowed by loop variable'),
			'0020-F403': (ERROR_BUT_WARN, '‘from module import *’ used; unable to detect undefined names'),
			'0020-F404': (ERROR_BUT_WARN, 'future import(s) name after other statements'),
			'0020-F405': (ERROR_BUT_WARN, 'name may be undefined, or defined from star imports: module'),
			'0020-F406': (uub.RESULT_ERROR, '‘from module import *’ only allowed at module level'),
			'0020-F407': (uub.RESULT_ERROR, 'an undefined __future__ feature name was imported'),

			'0020-F501': (uub.RESULT_ERROR, 'invalid % format literal'),
			'0020-F502': (uub.RESULT_ERROR, '% format expected mapping but got sequence'),
			'0020-F503': (uub.RESULT_ERROR, '% format expected sequence but got mapping'),
			'0020-F504': (uub.RESULT_ERROR, '% format unused named arguments'),
			'0020-F505': (uub.RESULT_ERROR, '% format missing named arguments'),
			'0020-F506': (uub.RESULT_ERROR, '% format mixed positional and named arguments'),
			'0020-F507': (uub.RESULT_ERROR, '% format mismatch of placeholder and argument count'),
			'0020-F508': (uub.RESULT_ERROR, '% format with * specifier requires a sequence'),
			'0020-F509': (uub.RESULT_ERROR, '% format with unsupported format character'),
			'0020-F521': (uub.RESULT_ERROR, '.format(...) invalid format string'),
			'0020-F522': (uub.RESULT_ERROR, '.format(...) unused named arguments'),
			'0020-F523': (uub.RESULT_ERROR, '.format(...) unused positional arguments'),
			'0020-F524': (uub.RESULT_ERROR, '.format(...) missing argument'),
			'0020-F525': (uub.RESULT_ERROR, '.format(...) mixing automatic and manual numbering'),
			'0020-F541': (uub.RESULT_ERROR, 'f-string without any placeholders'),

			'0020-F601': (uub.RESULT_WARN, 'dictionary key name repeated with different values'),
			'0020-F602': (uub.RESULT_WARN, 'dictionary key variable name repeated with different values'),
			'0020-F621': (uub.RESULT_ERROR, 'too many expressions in an assignment with star-unpacking'),
			'0020-F622': (uub.RESULT_ERROR, 'two or more starred expressions in an assignment (a, *b, *c = d)'),
			'0020-F631': (uub.RESULT_ERROR, 'assertion test is a tuple, which is always True'),
			'0020-F632': (uub.RESULT_WARN, 'use ==/!= to compare str, bytes, and int literals'),
			'0020-F633': (uub.RESULT_WARN, 'use of >> is invalid with print function'),
			'0020-F634': (uub.RESULT_ERROR, 'if test is a tuple, which is always True'),

			'0020-F701': (uub.RESULT_ERROR, 'a break statement outside of a while or for loop'),
			'0020-F702': (uub.RESULT_ERROR, 'a continue statement outside of a while or for loop'),
			'0020-F703': (uub.RESULT_ERROR, 'a continue statement in a finally block in a loop'),
			'0020-F704': (uub.RESULT_ERROR, 'a yield or yield from statement outside of a function'),
			'0020-F705': (uub.RESULT_ERROR, 'a return statement with arguments inside a generator'),
			'0020-F706': (uub.RESULT_ERROR, 'a return statement outside of a function/method'),
			'0020-F707': (uub.RESULT_ERROR, 'an except: block as not the last exception handler'),
			'0020-F721': (uub.RESULT_ERROR, 'syntax error in doctest'),
			'0020-F722': (uub.RESULT_ERROR, 'syntax error in forward annotation'),
			'0020-F723': (uub.RESULT_ERROR, 'syntax error in type comment'),

			'0020-F811': (ERROR_BUT_WARN, 'redefinition of unused name from line N'),
			'0020-F812': (uub.RESULT_ERROR, 'list comprehension redefines name from line N'),
			'0020-F821': (ERROR_BUT_WARN, 'undefined name name'),
			'0020-F822': (uub.RESULT_ERROR, 'undefined name name in __all__'),
			'0020-F823': (uub.RESULT_ERROR, 'local variable name ... referenced before assignment'),
			'0020-F831': (uub.RESULT_ERROR, 'duplicate argument name in function definition'),
			'0020-F841': (uub.RESULT_ERROR, 'local variable name is assigned to but never used'),

			'0020-F901': (uub.RESULT_WARN, 'raise NotImplemented should be raise NotImplementedError'),

			'0020-E1': (uub.RESULT_ERROR, 'Indentation'),
			'0020-E101': (uub.RESULT_WARN, 'indentation contains mixed spaces and tabs'),  # we won't be able to fix this, as flake8 has errors in the detection
			'0020-E111': (uub.RESULT_ERROR, 'indentation is not a multiple of four'),
			'0020-E112': (uub.RESULT_ERROR, 'expected an indented block'),
			'0020-E113': (uub.RESULT_ERROR, 'unexpected indentation'),
			'0020-E114': (uub.RESULT_ERROR, 'indentation is not a multiple of four (comment)'),
			'0020-E115': (uub.RESULT_ERROR, 'expected an indented block (comment)'),
			'0020-E116': (uub.RESULT_ERROR, 'unexpected indentation (comment)'),
			'0020-E117': (ERROR_BUT_WARN, 'over-indented'),

			'0020-E121': (uub.RESULT_ERROR, 'continuation line under-indented for hanging indent'),
			'0020-E122': (uub.RESULT_ERROR, 'continuation line missing indentation or outdented'),
			'0020-E123': (uub.RESULT_ERROR, 'closing bracket does not match indentation of opening bracket’s line'),
			'0020-E124': (uub.RESULT_ERROR, 'closing bracket does not match visual indentation'),
			'0020-E125': (uub.RESULT_ERROR, 'continuation line with same indent as next logical line'),
			'0020-E126': (ERROR_BUT_WARN, 'continuation line over-indented for hanging indent'),
			'0020-E127': (uub.RESULT_ERROR, 'continuation line over-indented for visual indent'),
			'0020-E128': (uub.RESULT_WARN, 'continuation line under-indented for visual indent'),  # hard to fix, maybe once ;-)
			'0020-E129': (uub.RESULT_ERROR, 'visually indented line with same indent as next logical line'),
			'0020-E131': (uub.RESULT_ERROR, 'continuation line unaligned for hanging indent'),
			'0020-E133': (uub.RESULT_ERROR, 'closing bracket is missing indentation'),

			'0020-E2': (uub.RESULT_ERROR, 'Whitespace'),
			'0020-E201': (uub.RESULT_ERROR, 'whitespace after ‘(‘'),
			'0020-E202': (uub.RESULT_ERROR, 'whitespace before ‘)’'),
			'0020-E203': (ERROR_BUT_WARN, 'whitespace before ‘:’'),  # conflicts with black!

			'0020-E211': (uub.RESULT_ERROR, 'whitespace before ‘(‘'),

			'0020-E221': (uub.RESULT_ERROR, 'multiple spaces before operator'),
			'0020-E222': (uub.RESULT_ERROR, 'multiple spaces after operator'),
			'0020-E223': (uub.RESULT_ERROR, 'tab before operator'),
			'0020-E224': (uub.RESULT_ERROR, 'tab after operator'),
			'0020-E225': (uub.RESULT_ERROR, 'missing whitespace around operator'),
			'0020-E226': (uub.RESULT_ERROR, 'missing whitespace around arithmetic operator'),
			'0020-E227': (uub.RESULT_ERROR, 'missing whitespace around bitwise or shift operator'),
			'0020-E228': (uub.RESULT_ERROR, 'missing whitespace around modulo operator'),

			'0020-E231': (uub.RESULT_ERROR, 'missing whitespace after ‘,’, ‘;’, or ‘:’'),

			'0020-E241': (uub.RESULT_ERROR, 'multiple spaces after ‘,’'),
			'0020-E242': (uub.RESULT_ERROR, 'tab after ‘,’'),

			'0020-E251': (uub.RESULT_ERROR, 'unexpected spaces around keyword / parameter equals'),

			'0020-E261': (uub.RESULT_ERROR, 'at least two spaces before inline comment'),
			'0020-E262': (uub.RESULT_ERROR, 'inline comment should start with ‘# ‘'),
			'0020-E265': (uub.RESULT_STYLE, 'block comment should start with ‘# ‘'),
			'0020-E266': (uub.RESULT_WARN, 'too many leading ‘#’ for block comment'),

			'0020-E271': (uub.RESULT_ERROR, 'multiple spaces after keyword'),
			'0020-E272': (uub.RESULT_ERROR, 'multiple spaces before keyword'),
			'0020-E273': (uub.RESULT_ERROR, 'tab after keyword'),
			'0020-E274': (uub.RESULT_ERROR, 'tab before keyword'),
			'0020-E275': (uub.RESULT_ERROR, 'missing whitespace after keyword'),

			'0020-E3': (uub.RESULT_ERROR, 'Blank line'),
			'0020-E301': (uub.RESULT_ERROR, 'expected 1 blank line, found 0'),
			'0020-E302': (uub.RESULT_ERROR, 'expected 2 blank lines, found 0'),
			'0020-E303': (uub.RESULT_ERROR, 'too many blank lines (3)'),
			'0020-E304': (uub.RESULT_ERROR, 'blank lines found after function decorator'),
			'0020-E305': (uub.RESULT_ERROR, 'expected 2 blank lines after end of function or class'),
			'0020-E306': (uub.RESULT_ERROR, 'expected 1 blank line before a nested definition, found 0'),

			'0020-E4': (uub.RESULT_ERROR, 'Import'),
			'0020-E401': (uub.RESULT_ERROR, 'multiple imports on one line'),
			'0020-E402': (uub.RESULT_WARN, 'module level import not at top of file'),  # Bug #42806: should be RESULT_ERROR when fixed

			'0020-E5': (ERROR_BUT_WARN, 'Line length'),
			'0020-E501': (uub.RESULT_STYLE, 'line too long (82 > 79 characters)'),
			'0020-E502': (ERROR_BUT_WARN, 'the backslash is redundant between brackets'),

			'0020-E7': (ERROR_BUT_WARN, 'Statement'),
			'0020-E701': (ERROR_BUT_WARN, 'multiple statements on one line (colon)'),
			'0020-E702': (ERROR_BUT_WARN, 'multiple statements on one line (semicolon)'),
			'0020-E703': (ERROR_BUT_WARN, 'statement ends with a semicolon'),
			'0020-E704': (ERROR_BUT_WARN, 'multiple statements on one line (def)'),
			'0020-E711': (ERROR_BUT_WARN, 'comparison to None should be ‘if cond is None:’'),
			'0020-E712': (ERROR_BUT_WARN, 'comparison to True should be ‘if cond is True:’ or ‘if cond:’'),
			'0020-E713': (ERROR_BUT_WARN, 'test for membership should be ‘not in’'),
			'0020-E714': (ERROR_BUT_WARN, 'test for object identity should be ‘is not’'),
			'0020-E721': (ERROR_BUT_WARN, 'do not compare types, use ‘isinstance()’'),
			'0020-E722': (uub.RESULT_WARN, "do not use bare 'except'"),
			'0020-E731': (ERROR_BUT_WARN, 'do not assign a lambda expression, use a def'),
			'0020-E741': (uub.RESULT_WARN, 'do not use variables named ‘l’, ‘O’, or ‘I’'),
			'0020-E742': (ERROR_BUT_WARN, 'do not define classes named ‘l’, ‘O’, or ‘I’'),
			'0020-E743': (ERROR_BUT_WARN, 'do not define functions named ‘l’, ‘O’, or ‘I’'),

			'0020-E9': (ERROR_BUT_WARN, 'Runtime'),
			'0020-E901': (ERROR_BUT_WARN, 'SyntaxError or IndentationError'),
			'0020-E902': (ERROR_BUT_WARN, 'IOError'),
			'0020-E999': (ERROR_BUT_WARN, 'SyntaxError: invalid syntax'),  # python3 only? should be RESULT_ERROR

			'0020-W1': (ERROR_BUT_WARN, 'Indentation warning'),
			'0020-W191': (uub.RESULT_STYLE, 'indentation contains tabs'),

			'0020-W2': (ERROR_BUT_WARN, 'Whitespace warning'),
			'0020-W291': (ERROR_BUT_WARN, 'trailing whitespace'),
			'0020-W292': (ERROR_BUT_WARN, 'no newline at end of file'),
			'0020-W293': (ERROR_BUT_WARN, 'blank line contains whitespace'),

			'0020-W3': (ERROR_BUT_WARN, 'Blank line warning'),
			'0020-W391': (ERROR_BUT_WARN, 'blank line at end of file'),

			'0020-W5': (ERROR_BUT_WARN, 'Line break warning'),
			'0020-W503': (ERROR_BUT_WARN, 'line break occurred before a binary operator'),  # TODO: decide for one?
			'0020-W504': (ERROR_BUT_WARN, 'line break after binary operator'),  # TODO: decide for one?
			'0020-W505': (uub.RESULT_STYLE, 'doc line too long (82 > 79 characters)'),

			'0020-W6': (ERROR_BUT_WARN, 'Deprecation warning'),
			'0020-W601': (uub.RESULT_WARN, '.has_key() is deprecated, use ‘in’'),  # Bug #42787: should be RESULT_ERROR when fixed in UDM
			'0020-W602': (ERROR_BUT_WARN, 'deprecated form of raising exception'),
			'0020-W603': (uub.RESULT_ERROR, '‘<>’ is deprecated, use ‘!=’'),
			'0020-W604': (uub.RESULT_ERROR, 'backticks are deprecated, use ‘repr()’'),
			'0020-W605': (uub.RESULT_WARN, "invalid escape sequence '\\s'"),
			'0020-W606': (uub.RESULT_ERROR, '‘async’ and ‘await’ are reserved keywords starting with Python 3.7'),

			'0020-N801': (uub.RESULT_STYLE, "class names should use CapWords convention"),
			'0020-N802': (uub.RESULT_STYLE, "function name should be lowercase"),
			'0020-N803': (uub.RESULT_STYLE, "argument name should be lowercase"),
			'0020-N804': (uub.RESULT_STYLE, "first argument of a classmethod should be named 'cls'"),
			'0020-N805': (uub.RESULT_STYLE, "first argument of a method should be named 'self'"),
			'0020-N806': (uub.RESULT_STYLE, "variable in function should be lowercase"),
			'0020-N811': (uub.RESULT_STYLE, "constant imported as non constant"),
			'0020-N812': (uub.RESULT_STYLE, "lowercase imported as non lowercase"),
			'0020-N813': (uub.RESULT_STYLE, "camelcase imported as lowercase"),
			'0020-N814': (uub.RESULT_STYLE, "camelcase imported as constant"),

			'0020-D100': (uub.RESULT_STYLE, 'Missing docstring in public module'),
			'0020-D101': (uub.RESULT_STYLE, 'Missing docstring in public class'),
			'0020-D102': (uub.RESULT_STYLE, 'Missing docstring in public method'),
			'0020-D103': (uub.RESULT_STYLE, 'Missing docstring in public function'),
			'0020-D104': (uub.RESULT_STYLE, 'Missing docstring in public package'),
			'0020-D105': (uub.RESULT_STYLE, 'Missing docstring in magic method'),
			'0020-D106': (uub.RESULT_STYLE, 'Missing docstring in public nested class'),
			'0020-D107': (uub.RESULT_STYLE, 'Missing docstring in __init__'),
			'0020-D200': (uub.RESULT_STYLE, 'One-line docstring should fit on one line with quotes'),
			'0020-D202': (uub.RESULT_STYLE, 'No blank lines allowed after function docstring'),
			'0020-D204': (uub.RESULT_STYLE, '1 blank line required after class docstring'),
			'0020-D205': (uub.RESULT_STYLE, '1 blank line required between summary line and description'),
			'0020-D206': (uub.RESULT_STYLE, 'Docstring should be indented with spaces, not tabs'),
			'0020-D208': (uub.RESULT_STYLE, 'Docstring is over-indented'),
			'0020-D209': (uub.RESULT_STYLE, 'Multi-line docstring closing quotes should be on a separate line'),
			'0020-D211': (uub.RESULT_STYLE, 'No blank lines allowed before class docstring'),
			'0020-D300': (uub.RESULT_STYLE, 'Use """triple double quotes"""'),
			'0020-D301': (uub.RESULT_STYLE, 'Use r""" if any backslashes in a docstring'),
			'0020-D400': (uub.RESULT_STYLE, 'First line should end with a period'),
			'0020-D401': (uub.RESULT_STYLE, 'First line should be in imperative mood; try rephrasing'),
			'0020-D402': (uub.RESULT_STYLE, 'First line should not be the function\'s "signature"'),
			'0020-D403': (uub.RESULT_STYLE, 'First word of the first line should be properly capitalized'),

			'0020-I001': (uub.RESULT_STYLE, 'isort found an import in the wrong position'),
			'0020-I002': (uub.RESULT_STYLE, 'no configuration found (.isort.cfg or [isort] in configs)'),
			'0020-I003': (uub.RESULT_STYLE, 'isort expected 1 blank line in imports, found 0'),
			'0020-I004': (uub.RESULT_STYLE, 'isort found an unexpected blank line in imports'),
			'0020-I005': (uub.RESULT_STYLE, 'isort found an unexpected missing import'),

			'0020-B001': (
				uub.RESULT_WARN,
				"Do not use bare `except:`, it also catches unexpected "
				"events like memory errors, interrupts, system exit, and so on.  "
				"Prefer `except Exception:`.  If you're sure what you're doing, "
				"be explicit and write `except BaseException:`.",
			),
			'0020-B002': (
				ERROR_BUT_WARN,
				" Python does not support the unary prefix increment. Writing "
				"++n is equivalent to +(+(n)), which equals n. You meant n += 1."
			),
			'0020-B003': (
				ERROR_BUT_WARN,
				" Assigning to `os.environ` doesn't clear the environment. "
				"Subprocesses are going to see outdated variables, in disagreement "
				"with the current process. Use `os.environ.clear()` or the `env=` "
				"argument to Popen."
			),
			'0020-B004': (
				ERROR_BUT_WARN,
				" Using `hasattr(x, '__call__')` to test if `x` is callable "
				"is unreliable. If `x` implements custom `__getattr__` or its "
				"`__call__` is itself not callable, you might get misleading "
				"results. Use `callable(x)` for consistent results."
			),
			'0020-B005': (
				uub.RESULT_WARN,
				"Using .strip() with multi-character strings is misleading "
				"the reader. It looks like stripping a substring. Move your "
				"character set to a constant if this is deliberate. Use "
				".replace() or regular expressions to remove string fragments."
			),
			'0020-B301': (
				uub.RESULT_WARN,
				"Python 3 does not include `.iter*` methods on dictionaries. "
				"Remove the `iter` prefix from the method name. For Python 2 "
				"compatibility, prefer the Python 3 equivalent unless you expect "
				"the size of the container to be large or unbounded. Then use "
				"`six.iter*` or `future.utils.iter*`."
			),
			'0020-B302': (
				uub.RESULT_WARN,
				"Python 3 does not include `.view*` methods on dictionaries. "
				"Remove the `view` prefix from the method name. For Python 2 "
				"compatibility, prefer the Python 3 equivalent unless you expect "
				"the size of the container to be large or unbounded. Then use "
				"`six.view*` or `future.utils.view*`."
			),
			'0020-B303': (
				uub.RESULT_WARN,
				"`__metaclass__` does nothing on Python 3. Use "
				"`class MyClass(BaseClass, metaclass=...)`. For Python 2 "
				"compatibility, use `six.add_metaclass`."
			),
			'0020-B304': (uub.RESULT_WARN, "`sys.maxint` is not a thing on Python 3. Use `sys.maxsize`."),
			'0020-B305': (
				uub.RESULT_WARN,
				"`.next()` is not a thing on Python 3. Use the `next()` "
				"builtin. For Python 2 compatibility, use `six.next()`."
			),
			'0020-B306': (
				uub.RESULT_WARN,
				"`BaseException.message` has been deprecated as of Python "
				"2.6 and is removed in Python 3. Use `str(e)` to access the "
				"user-readable message. Use `e.args` to access arguments passed "
				"to the exception."
			),
			'0020-B901': (
				uub.RESULT_WARN,
				"Using `yield` together with `return x`. Use native "
				"`async def` coroutines or put a `# noqa` comment on this "
				"line if this was intentional."
			),
		}

	def check(self, path: str) -> None:
		super(UniventionPackageCheck, self).check(path)

		errors = []
		for python in self.python_versions:
			for ignore, pathes in self._iter_pathes(path):
				errors += self.flake8(python, pathes, ignore)

		for python in PYTHON_VERSIONS:
			errors += self.check_conffiles(python)

		self.format_errors(errors)

	def check_conffiles(self, python: str) -> List[str]:
		errors = []  # type: List[str]
		header_length = len(UCR_HEADER.splitlines()) + 1
		for conffile in uub.FilteredDirWalkGenerator('conffiles'):
			with open(conffile, 'r') as fd:
				text = fd.read()

			for match in EXECUTE_TOKEN.findall(text):
				leading_lines = len(text[:text.index(match)].splitlines())
				match = match.rstrip() + '\n'  # prevent "blank line at end of file" and "blank line contains whitespace" false positives
				for error in self.flake8(python, ['-'], self.DEFAULT_IGNORE, UCR_HEADER + match):
					try:
						errno, filename, row, col, descr = error.split(' ', 4)
						row = str(int(row) - header_length + leading_lines)
					except ValueError as ex:
						# flake8 --show-source provides 2 extra lines
						self.debug('%s: %s' % (ex, error))
						continue
					errors.append(' '.join((errno, conffile, row, col, descr)))
		return errors

	def flake8(self, python: str, pathes: List[str], ignore: str = '', stdin: str = '') -> List[str]:
		cmd = [
			python,
			'-m', 'flake8',
			'--config=/dev/null',
			'--max-line-length', str(self.MAX_LINE_LENGTH),
			'--format', '0020-%(code)s %(path)s %(row)s %(col)s %(text)s',
		]
		if ignore:
			cmd += ['--ignore', ignore]
		if self.DEFAULT_SELECT:
			cmd += ['--select', self.DEFAULT_SELECT]
		if self.show_statistics:
			cmd.append('--statistics')
		if self.debuglevel > 0:
			cmd.append('--show-source')
		cmd.append('--')
		cmd.extend(pathes)

		process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE if stdin else None)
		stdout, stderr = process.communicate(stdin.encode('utf-8') if stdin else None)
		text = stdout.decode('utf-8', 'replace')
		return text.splitlines()

	def fix(self, path: str, *args: str) -> None:
		for ignore, pathes in self._iter_pathes(path):
			cmd = [
				'autopep8',
				'-i',
				'-aaa',
				'--max-line-length', str(self.MAX_LINE_LENGTH),
			]
			if ignore:
				cmd.extend(['--ignore', ignore])
			if self.DEFAULT_SELECT:
				cmd.extend(['--select', self.DEFAULT_SELECT])
			cmd.extend(args)
			cmd.append('--')
			cmd.extend(pathes)
			subprocess.call(cmd)

	def _iter_pathes(self, path: str) -> Iterable[Tuple[str, List[str]]]:
		files = [path for path in python_files(path) if not self.ignore_path(path)]
		if self.DEFAULT_SELECT or self.show_statistics:
			return {
				self.DEFAULT_IGNORE: files,
			}.items()

		ignored = {}  # type: Dict[str, List[str]]
		for path in files:
			ignore = ','.join(v for k, v in self.IGNORED_CODES_FOR_FILES.items() if k.search(os.path.abspath(path)))
			ignore = '%s,%s' % (self.DEFAULT_IGNORE, ignore)
			ignored.setdefault(ignore.rstrip(','), []).append(path)

		return ignored.items()

	def format_errors(self, errors: List[str]) -> None:
		done = set()
		for i, line in enumerate(errors, 1):
			if not line.startswith('0020-') or line in done:
				continue
			done.add(line)
			code, path, row, col, text = line.split(' ', 4)
			source = []
			while len(errors) > i + 1 and not errors[i].startswith('0020-'):
				source.append(errors[i])
				i += 1
			msg = '%s:\n%s\n' % (text, '\n'.join(source)) if source else text
			if not self.ignore_line(code, path, row, col, text, source):
				self.addmsg(code, msg, path, int(row), int(col))

	def ignore_line(self, code: str, path: str, row: str, col: str, text: str, source: List[str]) -> bool:
		allowed_names = ['_d', '_']
		if code == '0020-F841' and any("local variable '%s' is assigned to but never used" % (x,) in text for x in allowed_names):  # _d = univention.debug.function()
			return True
		return False

	def ignore_path(self, path: str) -> bool:
		return any(pattern.search(os.path.abspath(path)) for pattern in self.IGNORED_FILES)

	@classmethod
	def main(cls) -> int:
		parser = ArgumentParser()
		parser.add_argument('-d', '--debug', default=0, type=int, help='debuglevel (to show also source lines)')
		parser.add_argument('--statistics', default=False, action='store_true', help='Show a summary at the end.')
		parser.add_argument('--fix', default=False, action='store_true', help="Run autopep8 to automatically fix issues")
		parser.add_argument('--check', default=False, action='store_true', help="Check files - explicitly required with --fix")
		parser.add_argument('--path', default='.', help="Base path [%(default)s]")
		parser.add_argument('--select', default=cls.DEFAULT_SELECT, help='Comma-separated list of errors and warnings to enable [%(default)s]')
		parser.add_argument('--ignore', default=cls.DEFAULT_IGNORE, help='Comma-separated list of errors and warnings to ignore (or skip) [%(default)s]')
		parser.add_argument('--max-line-length', default=cls.MAX_LINE_LENGTH, help='Maximum line length [%(default)s]')
		parser.add_argument('--graceful', action='store_true', default=False, help='behave like calling ucslint would do: do not fail on certain errors')
		parser.add_argument('--versions', default='2,3', help='Which python versions to run [%(default)s]')
		args, args.arguments = parser.parse_known_args()  # type: ignore

		cls.DEFAULT_IGNORE = args.ignore
		cls.DEFAULT_SELECT = args.select
		cls.MAX_LINE_LENGTH = args.max_line_length
		cls.GRACEFUL = args.graceful
		self = cls(show_statistics=args.statistics)
		if args.versions:
			self.python_versions = ['python%s' % (x,) for x in args.versions.split(',')]
		self.setdebug(args.debug)
		self.postinit(args.path)
		if args.fix:
			self.fix(args.path, *args.arguments)
		if args.check or not args.fix:
			self.check(args.path)
		msgids = self.getMsgIds()
		exitcode = 0
		for msg in self.result():
			errno = msgids.get(msg.getId(), [-1])[0]
			if errno == uub.RESULT_ERROR:
				exitcode = 1
			print(uub.RESULT_INT2STR.get(errno, 'FIXME'), str(msg))
		return exitcode


if __name__ == '__main__':
	sys.exit(UniventionPackageCheck.main())
