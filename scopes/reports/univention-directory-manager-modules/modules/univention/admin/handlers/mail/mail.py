# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for mail objects
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
import univention.admin.localization

import univention.admin.handlers
import univention.admin.handlers.mail.domain
import univention.admin.handlers.mail.folder
import univention.admin.handlers.mail.lists


translation=univention.admin.localization.translation('univention.admin.handlers.mail')
_=translation.translate


module='mail/mail'

childs=0
short_description=_('Mail')
long_description=''
operations=['search']
usewizard=1
wizardmenustring=_("Mail")
wizarddescription=_("Add, edit and delete Mail Objects")
wizardoperations={"add":[_("Add"), _("Add Mail Object")],"find":[_("Find"), _("Find Mail Object(s)")]}

childmodules=["mail/folder","mail/domain", "mail/lists"]
wizardpath='univentionMailObject'
virtual=1
options={
}
property_descriptions={
	'name': univention.admin.property(
			short_description=_('Name'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=1
		)
}
layout=[ univention.admin.tab(_('General'),_('Basic Values'),[ [univention.admin.field("name")] ]) ]

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

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate)

	def exists(self):
		return self._exists


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):
	ret=[]
	ret+=univention.admin.handlers.mail.domain.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)
	ret+=univention.admin.handlers.mail.folder.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)
	ret+=univention.admin.handlers.mail.lists.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)
	return ret
	
	

def identify(dn, attr, canonical=0):
	pass


