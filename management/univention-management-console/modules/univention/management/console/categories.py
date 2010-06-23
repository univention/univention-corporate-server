#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  defines default categories for modules
#
# Copyright 2006-2010 Univention GmbH
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

import univention.management.console.locales as locales

__all__ = [ 'Category', 'get', 'insert', 'exists' ]

_ = locales.Translation( 'univention.management.console' ).translate

_categories = []

class Category( object ):
	def __init__( self, id, name, description = '', priority = 0 ):
		self.id = id
		self.name = name
		self.description = description
		self.priority = priority

def get( id = None ):
	global _categories
	if not id:
		return _categories
	else:
		for cat in _categories:
			if cat.id == id:
				return cat
		return None

def exists( id ):
	global _categories
	for cat in _categories:
		if cat.id == id:
			return true
	return False

def insert( cat ):
	global _categories
	i = 0
	while i < len( _categories ):
		if _categories[ i ].priority < cat.priority:
			_categories.insert( i, cat )
			break
		i += 1
	else:
		_categories.append( cat )

insert( Category( 'all', _( 'All modules' ),
				  _( 'Configuration and monitoring of system services' ), priority = 100 ) )
insert( Category( 'system', _( 'System' ),
                  _( 'System overview' ), priority = 90 ) )
insert( Category( 'wizards', _( 'Wizards' ),
				  _( 'Wizards for simple configuration' ), priority = 80 ) )
