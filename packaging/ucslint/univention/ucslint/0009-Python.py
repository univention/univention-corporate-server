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

import ast
import re

import univention.ucslint.base as uub
from univention.ucslint.python import RE_LENIENT
from univention.ucslint.python import Python36 as PythonVer
from univention.ucslint.python import python_files


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):

	"""Python specific checks."""

	def getMsgIds(self) -> uub.MsgIds:
		return {
			'0009-1': (uub.RESULT_WARN, 'failed to open file'),
			'0009-2': (uub.RESULT_ERROR, 'python file does not specify python version in hashbang'),
			'0009-3': (uub.RESULT_ERROR, 'python file specifies wrong python version in hashbang'),
			'0009-4': (uub.RESULT_WARN, 'python file contains whitespace and maybe arguments after python command'),
			'0009-5': (uub.RESULT_ERROR, 'dict.has_key is deprecated in python3 - please use "if key in dict:"'),
			'0009-6': (uub.RESULT_ERROR, 'raise "text" is deprecated in python3'),
			'0009-7': (uub.RESULT_STYLE, 'fragile comparison with None'),
			'0009-8': (uub.RESULT_STYLE, 'use ucr.is_true() or .is_false()'),
			'0009-9': (uub.RESULT_ERROR, 'hashbang contains more than one option'),
			'0009-10': (uub.RESULT_WARN, 'invalid Python string literal escape sequence'),
			'0009-11': (uub.RESULT_STYLE, 'Use uldap.searchDn() instead of uldap.search(attr=["dn"])'),
			'0009-12': (uub.RESULT_ERROR, 'variable names must not use reserved Python keywords'),
			'0009-13': (uub.RESULT_STYLE, 'variable names should not use internal Python keywords'),
		}

	RE_HASHBANG = re.compile(r'''^#!\s*/usr/bin/python(?:([0-9.]+))?(?:(\s+)(?:(\S+)(\s.*)?)?)?$''')
	RE_STRING = PythonVer.matcher()

	def check(self, path: str) -> None:
		""" the real check """
		super(UniventionPackageCheck, self).check(path)

		tester = uub.UPCFileTester()
		tester.addTest(re.compile(r'\.has_key\s*\('), '0009-5', 'dict.has_key is deprecated in python3 - please use "if key in dict:"', cntmax=0)
		tester.addTest(re.compile(r'''\braise\s*(?:'[^']+'|"[^"]+")'''), '0009-6', 'raise "text" is deprecated in python3', cntmax=0)
		tester.addTest(re.compile(r"""\b(?:if|while)\b.*(?:(?:!=|<>|==)\s*None\b|\bNone\s*(?:!=|<>|==)).*:"""), '0009-7', 'fragile comparison with None', cntmax=0)
		tester.addTest(re.compile(
			r'''(?:baseConfig|configRegistry|ucr)(?:\[.+\]|\.get\(.+\)).*\bin\s*
			[\[\(]
			(?:\s*(['"])(?:yes|no|1|0|true|false|on|off|enabled?|disabled?)\1\s*,?\s*){3,}
			[\]\)]''', re.VERBOSE | re.IGNORECASE),
			'0009-8', 'use ucr.is_true() or .is_false()', cntmax=0)
		tester.addTest(re.compile(
			r'''\.search\s*\(
			.*?\b
			attr
			\s*=\s*
			(?:(?P<list>\[)|(?P<tuple>\())
			\s*
			(?P<str>["'])
			dn
			(?P=str)
			\s*
			(?(list)\])(?(tuple)\))
			''', re.VERBOSE),
			'0009-11', 'Use uldap.searchDn() instead of uldap.search(attr=["dn"])', cntmax=0)

		for fn in python_files(path):
			tester.open(fn)
			if not tester.raw:
				continue
			msglist = tester.runTests()
			self.msg.extend(msglist)

			match = self.RE_HASHBANG.match(tester.lines[0])
			if match:
				version, space, option, tail = match.groups()
				if not version:
					self.addmsg('0009-2', 'file does not specify python version in hashbang', fn, 1)
				elif version not in {'2.7', '3'}:
					self.addmsg('0009-3', 'file specifies wrong python version in hashbang', fn, 1)
				if space and not option:
					self.addmsg('0009-4', 'file contains whitespace after python command', fn, 1)
				if tail:
					self.addmsg('0009-9', 'hashbang contains more than one option', fn, 1)

			for row, col, m in uub.line_regexp(tester.raw, RE_LENIENT):
				txt = m.group("str")
				if not txt:
					continue
				if self.RE_STRING.match(txt):
					continue

				self.addmsg('0009-10', 'invalid Python string literal: %s' % (txt,), fn, row, col)

			try:
				tree = ast.parse(tester.raw, fn)
				visitor = FindAssign(self, fn)
				visitor.visit(tree)
			except Exception as ex:
				self.addmsg('0009-1', 'Parsing failed: %s' % ex, fn)


class FindVariables(ast.NodeVisitor):
	def __init__(self, check: uub.UniventionPackageCheckDebian, fn: str) -> None:
		self.check = check
		self.fn = fn

	def visit_Name(self, node: ast.Name) -> None:
		if node.id in PYTHON_RESERVED:
			self.check.addmsg('0009-12', 'Variable uses reserved Python keyword: %r' % node.id, self.fn, node.lineno, node.col_offset)

		if node.id in PYTHON_INTERNAL:
			self.check.addmsg('0009-13', 'Variable uses internal Python keyword: %r' % node.id, self.fn, node.lineno, node.col_offset)


class FindAssign(ast.NodeVisitor):
	def __init__(self, check: uub.UniventionPackageCheckDebian, fn: str) -> None:
		self.visitor = FindVariables(check, fn)

	def visit_Assign(self, node: ast.Assign) -> None:
		for target in node.targets:
			self.visitor.visit(target)


PYTHON_RESERVED = """
adef
and
as
assert
async
await
break
class
continue
def
del
elif
else
except
exec
False
finally
for
from
global
if
import
in
is
lambda
None
nonlocal
not
or
pass
print
raise
return
True
try
while
with
yield
""".split()
# <https://docs.python.org/2.7/reference/lexical_analysis.html#keywords>
# <https://docs.python.org/3.8/reference/lexical_analysis.html#keywords>
PYTHON_INTERNAL = """
abs
all
any
apply
BaseException
basestring
bin
bool
buffer
bytearray
bytes
callable
chr
classmethod
cmp
coerce
compile
complex
copyright
credits
delattr
dict
dir
divmod
Ellipsis
enumerate
eval
Exception
execfile
exit
file
filter
float
format
frozenset
getattr
globals
hasattr
hash
help
hex
id
input
int
intern
isinstance
issubclass
iter
lambda
len
license
list
locals
long
map
max
memoryview
min
next
object
oct
open
ord
pow
property
quit
range
raw_input
reduce
reload
repr
reversed
round
set
setattr
slice
sorted
staticmethod
str
sum
super
tuple
type
unichr
unicode
vars
xrange
zip
""".split()
