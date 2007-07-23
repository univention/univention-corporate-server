#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Univention Nagios
#  univention admin nagios module
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

import sys, string
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
					 'find' : [ _('Find'), _('Find Nagios objects') ] }

default_containers = [ 'cn=nagios' ]

childmodules=[ 'nagios/service',
			   'nagios/timeperiod' ]

childs=0
short_description=_('Nagios Object')
long_description=''
operations=[]
virtual=1
options={
}

property_descriptions={}

mapping=univention.admin.mapping.mapping()

class object(univention.admin.handlers.simpleLdap):
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, arg=None):
		global mapping
		global property_descriptions

		self.co=co
		self.lo=lo
		self.dn=dn
		self.position=position
		self._exists=0
		self.mapping=mapping
		self.descriptions=property_descriptions

		super(object, self).__init__(co, lo, position, dn, superordinate)

	def exists(self):
		return self._exists

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	return univention.admin.handlers.nagios.service.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit) + univention.admin.handlers.nagios.timeperiod.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)

def identify(dn, attr, canonical=0):
	pass
