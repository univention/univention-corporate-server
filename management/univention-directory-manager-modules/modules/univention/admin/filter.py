# -*- coding: utf-8 -*-
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2004-2022 Univention GmbH
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

"""
|UDM| functions to parse, modify and create |LDAP| style search filters
"""

import re
from typing import Callable, Iterator, List, Match, Optional, Sequence, TypeVar, Union  # noqa: F401

import six
from ldap.filter import filter_format

import univention.admin.uexceptions

T = TypeVar("T")


class conjunction(object):
	"""
	LDAP filter conjunction (`&`) or disjunction (`|`).
	"""

	OPS = frozenset({'&', '|', '!'})

	def __init__(self, type, expressions):
		# type: (str, List[Union[conjunction, expression]]) -> None
		"""
		Create LDAP filter conjunction or disjunction.

		>>> c = conjunction('&', ['(objectClass=*)'])
		>>> c = conjunction('|', ['(objectClass=*)'])
		"""
		assert type in self.OPS
		self.type = type
		self.expressions = expressions

	@classmethod
	def _parse(cls, text):
		# type: (str) -> conjunction
		op = text[0]
		expressions = [parse(s) for s in cls._split(text[1:])]
		return conjunction(op, expressions)

	@staticmethod
	def _split(text):
		# type: (str) -> Iterator[str]
		depth = 0
		begin = -1
		for i, c in enumerate(text):
			if c == '(':
				depth += 1
				if depth == 1:
					begin = i
			elif c == ')':
				depth -= 1
				if depth == 0 and begin > -1:
					yield text[begin:i + 1]
					begin = -1

	def __str__(self):
		# type: () -> str
		"""
		Return string representation.

		>>> str(conjunction('&', ['(objectClass=*)']))
		'(&(objectClass=*))'
		>>> str(conjunction('|', ['(objectClass=*)']))
		'(|(objectClass=*))'
		>>> str(conjunction('!', ['(objectClass=*)']))
		'(!(objectClass=*))'
		>>> str(conjunction('&', []))
		''
		"""
		if not self.expressions:
			return ''
		return '(%s%s)' % (self.type, ''.join(map(six.text_type, self.expressions)))

	def __unicode__(self):
		# type: () -> str
		return self.__str__()

	def __repr__(self):
		# type: () -> str
		"""
		Return canonical representation.

		>>> conjunction('&', ['(objectClass=*)'])
		conjunction('&', ['(objectClass=*)'])
		>>> conjunction('|', ['(objectClass=*)'])
		conjunction('|', ['(objectClass=*)'])
		"""
		return '%s(%r, %r)' % (self.__class__.__name__, self.type, self.expressions)

	def append_unmapped_filter_string(self, filter_s, rewrite_function, mapping):
		# type: (str, Callable[[expression, Optional[T]], None], T) -> None
		if filter_s:
			filter_p = parse(filter_s)
			walk(filter_p, rewrite_function, arg=mapping)
			self.expressions.append(filter_p)


class expression(object):
	"""
	LDAP filter expression.
	"""

	OPS = frozenset({'=', '>=', '<=', '~=', '=*'} | {'>', '<', '!='})
	# LDAP RFC 4515 + UCS specific extensions
	RE_OP = re.compile(r'([<>]=?|[!~]=|=(?:[*]$)?)')

	def __init__(self, variable='', value='', operator='=', escape=False):
		# type: (str, str, str, bool) -> None
		"""
		Create LDAP filter expression.

		>>> e = expression('objectClass', '*', escape=False)
		>>> e = expression('objectClass', '*', '!=', escape=False)
		>>> e = expression('uidNumber', '10', '<') # < <= > >=
		"""
		assert operator in self.OPS
		if operator == '=' and value == '*':
			operator, value = '=*', ''
		if operator == '=*' and value:
			raise univention.admin.uexceptions.valueInvalidSyntax(value)
		self.variable = variable
		self.value = value
		self.operator = operator
		self._escape = escape

	@classmethod
	def _parse(cls, text):
		# type: (str) -> expression
		var, op, val = cls.RE_OP.split(text, 1)
		return expression(var, val, operator=op)

	def __str__(self):
		# type: () -> str
		r"""
		Return string representation.

		>>> str(expression('objectClass', '*', escape=False))
		'(objectClass=*)'
		>>> str(expression('objectClass', '*', '!=', escape=False))
		'(!(objectClass=*))'
		>>> str(expression('uidNumber', '10', '<'))
		'(!(uidNumber>=10))'
		>>> str(expression('cn', '', '=*'))
		'(cn=*)'
		>>> str(expression('cn', '*', '='))
		'(cn=*)'
		>>> str(expression('cn', r'*\2A*', '='))
		'(cn=*\\2A*)'
		"""
		if self.operator == '<':
			return self.escape('(!(%s>=%s))', (self.variable, self.value))
		elif self.operator == '>':
			return self.escape('(!(%s<=%s))', (self.variable, self.value))
		elif self.operator == '!=':
			return self.escape('(!(%s=%s))', (self.variable, self.value))
		else:
			return self.escape('(%%s%s%%s)' % (self.operator,), (self.variable, self.value))

	def escape(self, string, args):
		# type: (str, Sequence[str]) -> str
		if self._escape:
			return filter_format(string, args)
		return string % args

	def transform_to_conjunction(self, con):
		# type: (conjunction) -> None
		if not isinstance(con, conjunction):
			raise TypeError('must be conjunction, got %s(%r)' % (type(con).__name__, con))
		self.__dict__.clear()
		self.__dict__.update(con.__dict__)
		self.__class__ = type(con)  # type: ignore

	def __unicode__(self):
		# type: () -> str
		return self.__str__()

	def __repr__(self):
		# type: () -> str
		"""
		Return canonical representation.

		>>> expression('objectClass', 'foo*', escape=False)
		expression('objectClass', 'foo*', '=')
		>>> expression('objectClass', '*', '!=', escape=False)
		expression('objectClass', '*', '!=')
		>>> expression('objectClass', '*', '=', escape=False)
		expression('objectClass', '', '=*')
		>>> expression('objectClass', '', '=*', escape=False)
		expression('objectClass', '', '=*')
		"""
		return '%s(%r, %r, %r)' % (self.__class__.__name__, self.variable, self.value, self.operator)


def parse(filter_s, begin=0, end=-1):
	# type: (Union[conjunction, expression, str], int, int) -> Union[conjunction, expression]
	r"""
	Parse LDAP filter string.

	>>> filter_s='(|(&(!(zone=univention.de))(soa=test))(nameserver=bar))'
	>>> parse(filter_s)
	conjunction('|', [conjunction('&', [conjunction('!', [expression('zone', 'univention.de', '=')]), expression('soa', 'test', '=')]), expression('nameserver', 'bar', '=')])
	>>> parse('(!(key>=29))')
	conjunction('!', [expression('key', '29', '>=')])
	>>> parse('(&(key=va\\\\28!\\\\29ue))')
	conjunction('&', [expression('key', 'va\\\\28!\\\\29ue', '=')])
	>>> parse('(cn=Babs Jensen)')
	expression('cn', 'Babs Jensen', '=')
	>>> parse('(!(cn=Tim Howes))')
	conjunction('!', [expression('cn', 'Tim Howes', '=')])
	>>> parse('(&(objectClass=Person)(|(sn=Jensen)(cn=Babs J*)))')
	conjunction('&', [expression('objectClass', 'Person', '='), conjunction('|', [expression('sn', 'Jensen', '='), expression('cn', 'Babs J*', '=')])])
	>>> parse('(o=univ*of*mich*)')
	expression('o', 'univ*of*mich*', '=')
	>>> parse('(seeAlso=)')
	expression('seeAlso', '', '=')
	>>> parse('(cn:caseExactMatch:=Fred Flintstone)')
	expression('cn:caseExactMatch:', 'Fred Flintstone', '=')
	>>> parse('(cn:=Betty Rubble)')
	expression('cn:', 'Betty Rubble', '=')
	>>> parse('(sn:dn:2.4.6.8.10:=Barney Rubble)')
	expression('sn:dn:2.4.6.8.10:', 'Barney Rubble', '=')
	>>> parse('(o:dn:=Ace Industry)')
	expression('o:dn:', 'Ace Industry', '=')
	>>> parse('(:1.2.3:=Wilma Flintstone)')
	expression(':1.2.3:', 'Wilma Flintstone', '=')
	>>> parse('(:DN:2.4.6.8.10:=Dino)')
	expression(':DN:2.4.6.8.10:', 'Dino', '=')
	>>> parse(r'(o=Parens R Us \28for all your parenthetical needs\29)')
	expression('o', 'Parens R Us \\28for all your parenthetical needs\\29', '=')
	>>> parse(r'(cn=*\2A*)')
	expression('cn', '*\\2A*', '=')
	>>> parse(r'(cn=*)')
	expression('cn', '', '=*')
	>>> parse(r'(filename=C:\5cMyFile)')
	expression('filename', 'C:\\5cMyFile', '=')
	>>> parse(r'(bin=\00\00\00\04)')
	expression('bin', '\\00\\00\\00\\04', '=')
	>>> parse(r'(sn=Lu\c4\8di\c4\87)')
	expression('sn', 'Lu\\c4\\8di\\c4\\87', '=')
	>>> parse(r'(1.3.6.1.4.1.1466.0=\04\02\48\69)')
	expression('1.3.6.1.4.1.1466.0', '\\04\\02\\48\\69', '=')
	"""
	# filter is already parsed
	if not isinstance(filter_s, six.string_types):
		return filter_s

	if end == -1:
		end = len(filter_s) - 1

	if filter_s[begin] == '(' and filter_s[end] == ')':
		begin += 1
		end -= 1

	part = filter_s[begin:end + 1]
	try:
		if filter_s[begin] in conjunction.OPS:
			return conjunction._parse(part)
		else:
			return expression._parse(part)
	except (AssertionError, ValueError):
		raise univention.admin.uexceptions.valueInvalidSyntax(part)


def walk(filter_p, expression_walk_function=None, conjunction_walk_function=None, arg=None):
	# type: (Union[conjunction, expression], Optional[Callable[[expression, Optional[T]], None]], Optional[Callable[[conjunction, Optional[T]], None]], Optional[T]) -> None
	"""
	Walk LDAP filter expression tree.

	:param filter_p: expression tree.
	:param expression_walk_function: Callback for expressions.
	:param conjunction_walk_function: Callback for conjunctions.
	:param arg: Argument to the callback functions.

	>>> filter_s = '(|(&(!(zone=univention.de))(soa=test))(nameserver=bar))'
	>>> filter_p = parse(filter_s)
	>>> def trace(e, a): print((a, str(e)))
	>>> walk(filter_p, trace, None, 'e')
	('e', '(zone=univention.de)')
	('e', '(soa=test)')
	('e', '(nameserver=bar)')
	>>> walk(filter_p, None, trace, 'c')
	('c', '(!(zone=univention.de))')
	('c', '(&(!(zone=univention.de))(soa=test))')
	('c', '(|(&(!(zone=univention.de))(soa=test))(nameserver=bar))')
	"""
	if isinstance(filter_p, conjunction):
		for e in filter_p.expressions:
			walk(e, expression_walk_function, conjunction_walk_function, arg)
		if conjunction_walk_function:
			conjunction_walk_function(filter_p, arg)
	elif isinstance(filter_p, expression):
		if expression_walk_function:
			expression_walk_function(filter_p, arg)
	else:
		raise TypeError(type(filter_p))


FQDN_REGEX = re.compile(r'(?:^|\()fqdn=([^)]+)(?:\)|$)')


def replace_fqdn_filter(filter_s):
	# type: (str) -> str
	"""
	Replaces a filter expression for the read-only attribute fqdn. If no
	such expression can be found the unmodified filter is returned.

	>>> replace_fqdn_filter('fqdn=host.domain.tld')
	'(&(cn=host)(associatedDomain=domain.tld))'
	>>> replace_fqdn_filter('(fqdn=host.domain.tld)')
	'(&(cn=host)(associatedDomain=domain.tld))'
	>>> replace_fqdn_filter('fqdn=domain')
	'(|(cn=domain)(associatedDomain=domain))'
	>>> replace_fqdn_filter('(|(fqdn=host.domain.tld)(fqdn=other.domain.tld2))')
	'(|(&(cn=host)(associatedDomain=domain.tld))(&(cn=other)(associatedDomain=domain.tld2)))'
	"""
	if not isinstance(filter_s, six.string_types):
		return filter_s
	return FQDN_REGEX.sub(_replace_fqdn_filter, filter_s)


def _replace_fqdn_filter(match):
	# type: (Match[str]) -> str
	value, = match.groups()
	try:
		host, domain = value.split('.', 1)
		operator = '&'
	except ValueError:
		host = domain = value
		operator = '|'
	return '(%s(cn=%s)(associatedDomain=%s))' % (operator, host, domain)
