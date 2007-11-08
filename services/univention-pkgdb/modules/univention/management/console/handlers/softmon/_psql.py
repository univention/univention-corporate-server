#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module softmon: software monitor
#
# Copyright (C) 2007 Univention GmbH
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

#  [ {'operator': u'ne', 'pattern': u'domaincontroller_backup', 'key': u'role'},
#    {'operator': u'gt', 'pattern': u'1.3-0-0', 				   'key': u'ucs_version'},
#    {'operator': u'eq', 'pattern': u'mein-master', 			   'key': u'name'} ]

import univention.debug as ud

QUERY_TYPE_2_SQL = { 'ne': ('!~', True),
					 'gt': ('>',  False),
					 'lt': ('<',  False),
					 'ge': ('>=', False),
					 'le': ('<=', False),
					 'default': ('~', True)
					 }

def convertSearchFilterToQuery( filterlist ):
	query = 'true'
	need_join_systems = 0

	ud.debug( ud.ADMIN, ud.INFO, 'SOFTMON: filterlist=%s' % filterlist )
	for filteritem in filterlist:
		if not(filteritem.has_key('operator') and filteritem.has_key('pattern') and filteritem.has_key('key')):
			ud.debug( ud.ADMIN, ud.INFO, 'SOFTMON: value is missing: %s' % filteritem )
			continue

		(qt, re) = QUERY_TYPE_2_SQL['default']
		if QUERY_TYPE_2_SQL.has_key( filteritem['operator'] ):
			(qt, re) = QUERY_TYPE_2_SQL[ filteritem['operator'] ]


		# leeren Parameter korrigieren
		s = filteritem['pattern']

		# HACK: since frontend is unable to handle '0' as key of selections
		# (after translation to 'ascii-null-escape' the UMC syntax check goes bananas)
		# all integer keys are prepended by 'key-'
		if filteritem['key'] in [ 'selected_state', 'installed_state', 'current_state' ] and s.startswith('key-'):
			s = s[4:]

		if s == 'ascii-null-escape':
			s = '0'
		elif s == 'None':
			s = ''

		if re:
			# convert simple regular expression into postgres reg exp

			# leading asterisk
			s0 = ''
			if len(s) > 0:
				if s[0] == '*':
					s = s[1:]
				else:
					s0 = '^'

			# trailing asterisk
			s1 = ''
			if len(s) > 0:
				if s[-1] == '*':
					s = s[:-1]
				else:
					s1 = '$'

			# remove weird characters {string.punctuation without '.', '*', '-', '_'}
			# convert '*' into '.*' 
			# '.' bleibt RE für beliebiges Zeichen
			sv=''
			for i in s:
				if i not in '!"#$%&\'()+,/:;<=>?@[\\]^`{|}~':
					if i == '*':
						sv = sv +'.*'
					else:
						sv = sv + i
			s = s0 + sv + s1

		else:
			# no regular expressions if operator is GT, GE, LT, LE

			# remove weird characters {string.punctuation without '.', '*', '-', '_'}
			# mask '.'
			sv=''
			for i in s:
				if i not in '!"#$%&\'()+,/:;<=>?@[\\]^`{|}~*':
					if i == '.':
						sv = sv +'\.'
					else:
						sv = sv + i
			s = sv

		sv = "'" + s + "'"

		if filteritem['pattern']:
			if filteritem['key'] == 'name':
				query += ' and sysname' + qt + sv

			elif filteritem['key'] == 'role':
				query += ' and sysrole' + qt + sv
				need_join_systems = 0

			elif filteritem['key'] == 'ucs_version':
				query += ' and sysversion' + qt + sv
				need_join_systems = 0

			elif filteritem['key'] == 'pkg_name':
				query += ' and pkgname' + qt + sv

			elif filteritem['key'] == 'pkg_version':
				query += ' and vername' + qt + sv

			elif filteritem['key'] == 'selected_state':
				query += ' and selectedstate' + qt + sv

			elif filteritem['key'] == 'installed_state':
				query += ' and inststate' + qt + sv

			elif filteritem['key'] == 'current_state':
				query += ' and currentstate' + qt + sv

			else:
				ud.debug( ud.ADMIN, ud.INFO, 'SOFTMON: unknown key: %s' % filteritem['key'] )


	return (query, need_join_systems)
