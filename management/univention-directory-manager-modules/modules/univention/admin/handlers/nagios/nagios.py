#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Nagios
#  univention admin nagios module
#
# Copyright 2004-2012 Univention GmbH
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

from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

translation=univention.admin.localization.translation('univention.admin.handlers.nagios')
_=translation.translate

import univention.admin.handlers.nagios.service
import univention.admin.handlers.nagios.timeperiod

module = 'nagios/nagios'
usewizard = 1
wizardmenustring = _('Nagios')
wizarddescription =  _('Add, edit, delete and search Nagios objects')
wizardoperations = { 'add' : [ _('Add'), _('Add new Nagios object') ],
					 'find' : [ _('Search'), _('Search Nagios objects') ] }

default_containers = [ 'cn=nagios' ]

childmodules=[ 'nagios/service',
			   'nagios/timeperiod' ]

childs=0
short_description=_('Nagios object')
long_description=''
operations=[ 'search' ]
virtual=1
options={
}

property_descriptions = {
	'name': univention.admin.property(
		short_description = _( 'Name' ),
		long_description = _( 'Nagios object name' ),
		syntax=univention.admin.syntax.string_numbers_letters_dots,
		multivalue = False,
		options = [],
		required = True,
		may_change = False,
		identifies = True
		),
	}

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)

class object(univention.admin.handlers.simpleLdap):
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes = [] ):
		global mapping
		global property_descriptions

		self.mapping=mapping
		self.descriptions=property_descriptions

		univention.admin.handlers.simpleLdap.__init__( self, co, lo, position, dn, superordinate, attributes )

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	return univention.admin.handlers.nagios.service.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit) + univention.admin.handlers.nagios.timeperiod.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)

def identify(dn, attr, canonical=0):
	pass
