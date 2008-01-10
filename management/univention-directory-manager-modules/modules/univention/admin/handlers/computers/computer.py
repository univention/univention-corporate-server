# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the computer objects
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

translation=univention.admin.localization.translation('univention.admin.handlers.computers')
_=translation.translate

import univention.admin.handlers.computers.thinclient
import univention.admin.handlers.computers.managedclient
import univention.admin.handlers.computers.macos
import univention.admin.handlers.computers.mobileclient
import univention.admin.handlers.computers.ipmanagedclient
import univention.admin.handlers.computers.windows
import univention.admin.handlers.computers.domaincontroller_master
import univention.admin.handlers.computers.domaincontroller_backup
import univention.admin.handlers.computers.domaincontroller_slave
import univention.admin.handlers.computers.memberserver
import univention.admin.handlers.computers.trustaccount

module='computers/computer'
usewizard=1
wizardmenustring=_("Computer")
wizarddescription=_("Add, edit and delete computers")
wizardoperations={"add":[_("Add"), _("Add Computer")],"find":[_("Find"), _("Find Computer(s)")]}

childmodules=["computers/managedclient","computers/macos","computers/thinclient","computers/windows","computers/domaincontroller_master", "computers/domaincontroller_backup", "computers/domaincontroller_slave", "computers/memberserver", "computers/mobileclient", "computers/trustaccount", "computers/ipmanagedclient"]

childs=0
short_description=_('Computer')
long_description=''
operations=['search']
virtual=1
options={
}
property_descriptions={
	'name': univention.admin.property(
			short_description=_('Name'),
			long_description='',
			syntax=univention.admin.syntax.hostName,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=1
		),
	'mac': univention.admin.property(
			short_description=_('MAC Address'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'ip': univention.admin.property(
			short_description=_('IP Address'),
			long_description='',
			syntax=univention.admin.syntax.ipAddress,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'inventoryNumber': univention.admin.property(
			short_description=_('Inventory Number'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		)
}

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('inventoryNumber', 'univentionInventoryNumber')
mapping.register('mac', 'macAddress' )
mapping.register('ip', 'aRecord' )

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

	return univention.admin.handlers.computers.macos.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit) + univention.admin.handlers.computers.thinclient.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit) + univention.admin.handlers.computers.managedclient.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit) + univention.admin.handlers.computers.mobileclient.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit) + univention.admin.handlers.computers.windows.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit) + univention.admin.handlers.computers.domaincontroller_master.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit) + univention.admin.handlers.computers.domaincontroller_backup.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit) + univention.admin.handlers.computers.domaincontroller_slave.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit) + univention.admin.handlers.computers.memberserver.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit) + univention.admin.handlers.computers.ipmanagedclient.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit) + univention.admin.handlers.computers.trustaccount.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)

def identify(dn, attr, canonical=0):
	pass

