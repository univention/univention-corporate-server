# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the computer objects
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
import univention.admin.handlers.computers.windows_domaincontroller
import univention.admin.handlers.computers.domaincontroller_master
import univention.admin.handlers.computers.domaincontroller_backup
import univention.admin.handlers.computers.domaincontroller_slave
import univention.admin.handlers.computers.memberserver
import univention.admin.handlers.computers.trustaccount

module='computers/computer'
usewizard=1
wizardmenustring=_("Computer")
wizarddescription=_("Add, edit and delete computers")
wizardoperations={"add":[_("Add"), _("Add Computer")],"find":[_("Search"), _("Search computer(s)")]}

childmodules=[	"computers/managedclient",
				"computers/macos",
				"computers/thinclient",
				"computers/windows",
				"computers/domaincontroller_master",
				"computers/domaincontroller_backup",
				"computers/domaincontroller_slave",
				"computers/memberserver",
				"computers/windows_domaincontroller",
				"computers/mobileclient",
				"computers/trustaccount",
				"computers/ipmanagedclient"]

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
	'dnsAlias': univention.admin.property(
			short_description=_('DNS alias'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'description': univention.admin.property(
			short_description=_('Description'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			required=0,
			may_change=1,
			identifies=0
		),
	'mac': univention.admin.property(
			short_description=_('MAC address'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'ip': univention.admin.property(
			short_description=_('IP address'),
			long_description='',
			syntax=univention.admin.syntax.ipAddress,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'inventoryNumber': univention.admin.property(
			short_description=_('Inventory number'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'fqdn' : univention.admin.property(
			short_description = 'FQDN',
			long_description = '',
			syntax=univention.admin.syntax.string,
			multivalue = False,
			options = [],
			required = False,
			may_change = False,
			identifies = 0
		)
}

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('inventoryNumber', 'univentionInventoryNumber')
mapping.register('mac', 'macAddress' )

class object(univention.admin.handlers.simpleLdap):
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes = [] ):
		global mapping
		global property_descriptions

		self.mapping=mapping
		self.descriptions=property_descriptions

		super(object, self).__init__(co, lo, position, dn, superordinate, attributes)

	def open( self ):
		super( object, self ).open()
		if 'name' in self.info and 'domain' in self.info:
			self[ 'fqdn' ] = '%s.%s' % ( self[ 'name' ], self[ 'domain' ] )

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	res=[]
	if str(filter_s).find('(dnsAlias=') != -1:
		filter_s=univention.admin.handlers.dns.alias.lookup_alias_filter(lo, filter_s)
		if filter_s:
			res+=lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)
	else:
		return univention.admin.handlers.computers.macos.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit) +\
				univention.admin.handlers.computers.thinclient.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit) +\
				univention.admin.handlers.computers.managedclient.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit) +\
				univention.admin.handlers.computers.mobileclient.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit) +\
				univention.admin.handlers.computers.windows.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit) +\
				univention.admin.handlers.computers.domaincontroller_master.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit) +\
				univention.admin.handlers.computers.domaincontroller_backup.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit) +\
				univention.admin.handlers.computers.domaincontroller_slave.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit) +\
				univention.admin.handlers.computers.memberserver.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit) +\
				univention.admin.handlers.computers.ipmanagedclient.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit) +\
				univention.admin.handlers.computers.trustaccount.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit) +\
				univention.admin.handlers.computers.windows_domaincontroller.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)
	return res

def identify(dn, attr, canonical=0):
	pass

