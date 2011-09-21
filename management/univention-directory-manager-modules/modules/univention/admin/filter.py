# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  parse, modify and create ldap-style search filters
#
# Copyright 2004-2011 Univention GmbH
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
import types
import univention.admin.uexceptions

def escapeForLdapFilter(txt):
	"""Escape LDAP filter value.
	Bug #19976: According to RFC2254 [*()\\\0] must be \\%02x encoded.

	>>> escapeForLdapFilter('key=value')
	'key=value'
	>>> escapeForLdapFilter('description=Number (1)')
	'description=Number \\\\281\\\\29'
	"""
	# parenthesis mess up ldap filters - they should be escaped
	return txt.replace('(', '\(').replace(')', '\)')

class conjunction:
	"""LDAP filter conjunction (&) or disjunction (|)."""
	_type_='conjunction'

	def __init__(self, type, expressions):
		'''Create LDAP filter conjunction or disjunction.

		>>> c = conjunction('&', '(objectClass=*)')
		>>> c = conjunction('|', '(objectClass=*)')
		'''
		self.type=type
		self.expressions=expressions

	def __str__(self):
		'''Return string representation.

		>>> str(conjunction('&', '(objectClass=*)'))
		'(&(objectClass=*))'
		>>> str(conjunction('|', '(objectClass=*)'))
		'(|(objectClass=*))'
		'''
		return '(%s%s)' % (self.type, ''.join(map(unicode, self.expressions)))

	def __unicode__(self):
		return self.__str__()

	def __repr__(self):
		'''Return canonical representation.

		>>> conjunction('&', '(objectClass=*)')
		conjunction('&', '(objectClass=*)')
		>>> conjunction('|', '(objectClass=*)')
		conjunction('|', '(objectClass=*)')
		'''
		return '%s(%r, %r)' % (self.__class__._type_, self.type, self.expressions)

class expression:
	"""LDAP filter expression."""
	_type_='expression'

	def __init__(self, variable='', value='', operator='='):
		'''Create LDAP filter expression.

		>>> e = expression('objectClass', '*')
		>>> e = expression('objectClass', '*', '!=')
		'''
		self.variable=variable
		self.value=value
		self.operator=operator

	def __str__(self):
		'''Return string representation.

		>>> str(expression('objectClass', '*'))
		'(objectClass=*)'
		>>> str(expression('objectClass', '*', '!='))
		'(!(objectClass=*))'
		'''
		if self.operator == '!=':
			return '(!(%s=%s))' % ( self.variable, self.value )
		else:
			return '(%s=%s)' % ( self.variable, self.value )

	def __unicode__(self):
		return self.__str__()

	def __repr__(self):
		'''Return canonical representation.

		>>> expression('objectClass', '*')
		expression('objectClass', '*', '=')
		>>> expression('objectClass', '*', '!=')
		expression('objectClass', '*', '!=')
		'''
		return '%s(%r, %r, %r)' % (self.__class__._type_, self.variable, self.value, self.operator)

def parse(filter_s, begin=0, end=-1):
	"""Parse LDAP filter string.

	>>> filter_s='(|(&(!(zone=univention.de))(soa=test))(nameserver=bar))'
	>>> parse(filter_s)
	conjunction('|', [conjunction('&', [conjunction('!', [expression('zone', 'univention.de', '=')]), expression('soa', 'test', '=')]), expression('nameserver', 'bar', '=')])
	>>> parse('(&(key=va\\\\28!\\\\29ue))')
	conjunction('&', [expression('key', 'va\\\\28!\\\\29ue', '=')])

	Bug: This will break if parentheses are not quoted correctly:
	>> parse('(&(key=va\\)!\\(ue))')
	conjunction('&', [expression('key', 'va)!(ue', '=')])
	"""
	def split(str):
		expressions=[]
		depth=0
		i=0
		begin=-1
		for c in str:
			if c == '(':
				depth+=1
				if depth == 1:
					begin=i
			elif c == ')':
				depth-=1
				if depth == 0 and begin > -1:
					expressions.append(str[begin:i+1])
					begin=-1
			i+=1
		return expressions

	# filter is already parsed
	if type(filter_s) == types.InstanceType:
		return filter_s

	if end == -1:
		end=len(filter_s)-1

	if filter_s[begin] == '(' and filter_s[end] == ')':
		begin+=1
		end-=1

	if filter_s[begin] in ['&', '|', '!']:
		# new conjunction
		ftype=filter_s[begin]
		begin+=1
		expressions=[]
		for s in split(filter_s[begin:end+1]):
			expressions.append(parse(s))
		c=conjunction(ftype, expressions)
		return c
	else:
		if filter_s.find ('=') == -1:
			raise univention.admin.uexceptions.valueInvalidSyntax ()

		# new expression
		variable, value=filter_s[begin:end+1].split('=', 1)
		return expression(variable, value)

def walk(filter, expression_walk_function=None, conjunction_walk_function=None, arg=None):
	"""Walk LDAP filter expression tree.

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

FQDN_REGEX = re.compile( '^(.*?)\(?fqdn=([^)]+)\)?(.*)$' )
def replace_fqdn_filter( filter_s ):
	'''
	Replaces a filter expression for the read-only attribute fqdn. If no
	such expression can be found the unmodified filter is returned.

	fqdn=host.doain.tld -> (&(cn=host)(associatedDomain=domain.tld))
	'''
	if not isinstance( filter_s, basestring ):
		return filter_s
	if filter_s.find( 'fqdn=' ) != -1:
		match = FQDN_REGEX.match( str( filter_s ) )
		if match:
			prefix, value, suffix = match.groups()
			if value.find( '.' ) >= 0:
				host, domain = value.split( '.', 1 )
				operator = '&'
			else:
				host = value
				domain = value
				operator = '|'
			fqdn_filter = '(%s(cn=%s)(associatedDomain=%s))' % ( operator, host, domain )
			return prefix + fqdn_filter + suffix

	return filter_s

if __name__ == '__main__':
	import doctest
	doctest.testmod()
