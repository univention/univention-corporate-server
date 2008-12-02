# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  parse, modify and create ldap-style search filters
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
#
# http://www.univention.de/
# 
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import string, types

def escapeForLdapFilter(txt):
	# parenthesis mess up ldap filters - they should be escaped
	return txt.replace('(', '\(').replace(')', '\)')


class conjunction:
	_type_='conjunction'
	def __init__(self, type, expressions):
		self.type=type
		self.expressions=expressions
	def __str__(self):
		return '('+self.type+string.join(map(lambda(x): unicode(x), self.expressions), '')+')'
	def __unicode__(self):
		return self.__str__()

class expression:
	_type_='expression'
	def __init__(self, variable='', value=''):
		self.variable=variable
		self.value=value
		self.operator='='

	def __str__(self):
		if self.operator == '!=':
			return '(!(%s=%s))' % ( self.variable, self.value )
		else:
			return '(%s=%s)' % ( self.variable, self.value )

def parse(filter_s, begin=0, end=-1):
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
	
	if filter_s[begin] == '(':
		begin+=1
	if filter_s[end] == ')':
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
		# new expression
		variable, value=filter_s[begin:end+1].split('=', 1)
		return expression(variable, value)

def walk(filter, expression_walk_function=None, conjunction_walk_function=None, arg=None):
	if filter._type_ == 'conjunction':
		for e in filter.expressions:
			walk(e, expression_walk_function, conjunction_walk_function, arg)
		if conjunction_walk_function:
			conjunction_walk_function(filter, arg)
	elif filter._type_ == 'expression':
		if expression_walk_function:
			expression_walk_function(filter, arg)

if __name__ == '__main__':
	filter='(|(&(!(zone=univention.de))(soa=test))(nameserver=bar))'
	print filter
	p=parse(filter)
	print p
