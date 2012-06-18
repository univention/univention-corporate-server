# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for printer shares
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

translation=univention.admin.localization.translation('univention.admin.handlers.shares')
_=translation.translate

import univention.admin.handlers.shares.printer
import univention.admin.handlers.shares.printergroup

module='shares/print'
usewizard=1
wizardmenustring=_("Printers")
wizarddescription=_("Add, edit and delete print shares")
wizardoperations={"add":[_("Add"), _("Add printer object")],"find":[_("Search"), _("Search printer object(s)")]}
wizardpath='univentionPrintersObject'
childmodules=['shares/printer','shares/printergroup']

childs=0
short_description=_('Printer share')
long_description=''
operations=['search']
virtual=1
options={
}
property_descriptions={
	'name': univention.admin.property(
			short_description=_('Name'),
			long_description='',
			syntax=univention.admin.syntax.printerName,
			multivalue=0,
			options=[],
			required=1,
			may_change=0,
			identifies=1
		),
	'spoolHost': univention.admin.property(
			short_description=_('Spool host'),
			long_description='',
			syntax=univention.admin.syntax.ServicePrint_FQDN,
			multivalue=1,
			options=[],
			required=1,
			may_change=1,
			identifies=0
		),
	'sambaName': univention.admin.property(
			short_description=_('Samba name'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			unique=1
		),
	'setQuota': univention.admin.property(
			short_description=_('Enable quota support'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'pagePrice': univention.admin.property(
			short_description=_('Price per page'),
			long_description='',
			syntax=univention.admin.syntax.integer,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'jobPrice': univention.admin.property(
			short_description=_('Price per print job'),
			long_description='',
			syntax=univention.admin.syntax.integer,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
}

mapping=univention.admin.mapping.mapping()

class object(univention.admin.handlers.simpleLdap):
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes = [] ):
		global mapping
		global property_descriptions

		self.mapping=mapping
		self.descriptions=property_descriptions

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate, attributes = attributes )

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	return univention.admin.handlers.shares.printer.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit) + univention.admin.handlers.shares.printergroup.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)

def identify(dn, attr, canonical=0):
	pass

