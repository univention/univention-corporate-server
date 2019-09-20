# -*- coding: utf-8 -*-
"""
|UDM| functions to parse, modify and create |LDAP|\ -style search filters
"""
# Copyright 2004-2019 Univention GmbH
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

from ldap.filter import filter_format
import re
import univention.admin.uexceptions


class conjunction(object):
	"""
	LDAP filter conjunction (`&`) or disjunction (`|`).
	"""
	_type_ = 'conjunction'

	def __init__(self, type, expressions):
		"""
		Create LDAP filter conjunction or disjunction.

		>>> c = conjunction('&', '(objectClass=*)')
		>>> c = conjunction('|', '(objectClass=*)')
		"""
		self.type = type
		self.expressions = expressions

	def __str__(self):
		"""
		Return string representation.

		>>> str(conjunction('&', '(objectClass=*)'))
		'(&(objectClass=*))'
		>>> str(conjunction('|', '(objectClass=*)'))
		'(|(objectClass=*))'
		>>> str(conjunction('&', ''))
		''
		"""
		if not self.expressions:
			return ''
		return '(%s%s)' % (self.type, ''.join(map(unicode, self.expressions)))

	def __unicode__(self):
		return self.__str__()

	def __repr__(self):
		"""
		Return canonical representation.

		>>> conjunction('&', '(objectClass=*)')
		conjunction('&', '(objectClass=*)')
		>>> conjunction('|', '(objectClass=*)')
		conjunction('|', '(objectClass=*)')
		"""
		return '%s(%r, %r)' % (self.__class__._type_, self.type, self.expressions)

	def append_unmapped_filter_string(self, filter_s, rewrite_function, mapping):
		if filter_s:
			filter_p = parse(filter_s)
			walk(filter_p, rewrite_function, arg=mapping)
			self.expressions.append(filter_p)


class expression(object):
	"""
	LDAP filter expression.
	"""
	_type_ = 'expression'

	def __init__(self, variable='', value='', operator='=', escape=False):
		"""
		Create LDAP filter expression.

		>>> e = expression('objectClass', '*', escape=False)
		>>> e = expression('objectClass', '*', '!=', escape=False)
		>>> e = expression('uidNumber', '10', '<') # < <= > >=
		"""
		self.variable = variable
		self.value = value
		self.operator = operator
		self._escape = escape

	def __str__(self):
		"""
		Return string representation.

		>>> str(expression('objectClass', '*', escape=False))
		'(objectClass=*)'
		>>> str(expression('objectClass', '*', '!=', escape=False))
		'(!(objectClass=*))'
		>>> str(expression('uidNumber', '10', '<'))
		'(!(uidNumber>=10))'
		"""
		if self.operator == '<=':
			return self.escape('(%s<=%s)', (self.variable, self.value))
		elif self.operator == '<':
			return self.escape('(!(%s>=%s))', (self.variable, self.value))
		elif self.operator == '>=':
			return self.escape('(%s>=%s)', (self.variable, self.value))
		elif self.operator == '>':
			return self.escape('(!(%s<=%s))', (self.variable, self.value))
		elif self.operator == '!=':
			return self.escape('(!(%s=%s))', (self.variable, self.value))
		else:
			return self.escape('(%s=%s)', (self.variable, self.value))

	def escape(self, string, args):
		if self._escape:
			return filter_format(string, args)
		return string % args

	def transform_to_conjunction(self, con):
		if not isinstance(con, conjunction):
			raise TypeError('must be conjunction, got %r (%r)' % (type(con).__name__, repr(con)))
		self.__dict__.clear()
		self.__dict__.update(con.__dict__.copy())
		self.__class__ = type(con)

	def __unicode__(self):
		return self.__str__()

	def __repr__(self):
		"""
		Return canonical representation.

		>>> expression('objectClass', '*', escape=False)
		expression('objectClass', '*', '=')
		>>> expression('objectClass', '*', '!=', escape=False)
		expression('objectClass', '*', '!=')
		"""
		return '%s(%r, %r, %r)' % (self.__class__._type_, self.variable, self.value, self.operator)


def parse(filter_s, begin=0, end=-1):
	"""
	Parse LDAP filter string.

	>>> filter_s='(|(&(!(zone=univention.de))(soa=test))(nameserver=bar))'
	>>> parse(filter_s)
	conjunction('|', [conjunction('&', [conjunction('!', [expression('zone', 'univention.de', '=')]), expression('soa', 'test', '=')]), expression('nameserver', 'bar', '=')])
	>>> parse('(!(key>=29))')
	conjunction('!', [expression('key', '29', '>=')])
	>>> parse('(&(key=va\\\\28!\\\\29ue))')
	conjunction('&', [expression('key', 'va\\\\28!\\\\29ue', '=')])

	Bug: This will break if parentheses are not quoted correctly:
	>> parse('(&(key=va\\)!\\(ue))')
	conjunction('&', [expression('key', 'va)!(ue', '=')])
	"""
	# filter is already parsed
	if not isinstance(filter_s, basestring):
		return filter_s

	def split(str):
		expressions = []
		depth = 0
		i = 0
		begin = -1
		for c in str:
			if c == '(':
				depth += 1
				if depth == 1:
					begin = i
			elif c == ')':
				depth -= 1
				if depth == 0 and begin > -1:
					expressions.append(str[begin:i + 1])
					begin = -1
			i += 1
		return expressions

	if end == -1:
		end = len(filter_s) - 1

	if filter_s[begin] == '(' and filter_s[end] == ')':
		begin += 1
		end -= 1

	if filter_s[begin] in ['&', '|', '!']:
		# new conjunction
		ftype = filter_s[begin]
		begin += 1
		expressions = []
		for s in split(filter_s[begin:end + 1]):
			expressions.append(parse(s))
		c = conjunction(ftype, expressions)
		return c
	else:
		if filter_s.find('=') == -1:
			raise univention.admin.uexceptions.valueInvalidSyntax()

		# new expression
		if '<=' in filter_s:
			delim = '<='
		elif '>=' in filter_s:
			delim = '>='
		else:
			delim = '='
		variable, value = filter_s[begin:end + 1].split(delim, 1)
		return expression(variable, value, operator=delim)


def walk(filter, expression_walk_function=None, conjunction_walk_function=None, arg=None):
	"""
	Walk LDAP filter expression tree.

	>>> filter='(|(&(!(zone=univention.de))(soa=test))(nameserver=bar))'
	>>> tree = parse(filter)
	>>> def trace(e, a): print a, e
	>>> walk(tree, trace, None, 'e')
	e (zone=univention.de)
	e (soa=test)
	e (nameserver=bar)
	>>> walk(tree, None, trace, 'c')
	c (!(zone=univention.de))
	c (&(!(zone=univention.de))(soa=test))
	c (|(&(!(zone=univention.de))(soa=test))(nameserver=bar))
	"""
	if filter._type_ == 'conjunction':
		for e in filter.expressions:
			walk(e, expression_walk_function, conjunction_walk_function, arg)
		if conjunction_walk_function:
			conjunction_walk_function(filter, arg)
	elif filter._type_ == 'expression':
		if expression_walk_function:
			expression_walk_function(filter, arg)


FQDN_REGEX = re.compile(r'(?:^|\()fqdn=([^)]+)(?:\)|$)')


def replace_fqdn_filter(filter_s):
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
	if not isinstance(filter_s, basestring):
		return filter_s
	return FQDN_REGEX.sub(_replace_fqdn_filter, filter_s)


def _replace_fqdn_filter(match):
	value, = match.groups()
	try:
		host, domain = value.split('.', 1)
		operator = '&'
	except ValueError:
		host = domain = value
		operator = '|'
	return '(%s(cn=%s)(associatedDomain=%s))' % (operator, host, domain)


if __name__ == '__main__':
	import doctest
	doctest.testmod()
