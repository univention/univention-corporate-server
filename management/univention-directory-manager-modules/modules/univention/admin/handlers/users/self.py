# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the user himself
#
# Copyright (C) 2004-2009 Univention GmbH
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

import os, sys, string, re, copy, time, sha, types, struct, md5
import ldap, heimdal
import univention.admin
import univention.admin.handlers
import univention.admin.handlers.settings.user
import univention.admin.handlers.policies.admin_user
import univention.admin.localization
import univention.admin.uexceptions
import univention.admin.uldap
import base64

import univention.debug
import univention.admin.handlers.users.user

translation=univention.admin.localization.translation('univention.admin.handlers.users')
_=translation.translate

module='users/self'
operations=['edit','search']
options = {}

mapping = univention.admin.handlers.users.user.mapping
property_descriptions = univention.admin.handlers.users.user.property_descriptions
layout = [univention.admin.tab( _('General'),_('There are no options enabled.'),[
					[univention.admin.field("filler"), ]])]

uid_umlauts=0
childs=0
short_description=_('User: Self')
long_description=''

def _check_cell(cell, fields, options):
	if not cell.property in fields:
		return False
	prop = property_descriptions[cell.property]
	return prop.matches(options)

def _create_layout(fields, options):
	layout = []
	for tab in univention.admin.handlers.users.user.layout:
		newtab = copy.deepcopy( tab )
		newtab.fields = []
		for line in tab.fields:
			newline = []
			for cell in line:
				if isinstance( cell, univention.admin.field ):
					if _check_cell(cell, fields, options):
						newline.append( copy.copy( cell ) )
				else:
					newcell = []
					for subcell in cell:
						if isinstance( subcell, univention.admin.field ):
							if _check_cell(subcell, fields, options):
								newcell.append( copy.copy( subcell ) )
					if newcell: newline.append( newcell )
			if newline:
				newtab.fields.append( newline )
		if newtab.fields:
			layout.append( newtab )
		else:
			del newtab
	return layout

class object(univention.admin.handlers.users.user.object):
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, arg=None):
		univention.admin.handlers.users.user.object.__init__( self, co, lo, position, dn, superordinate, arg )
		self.__modifyLayout()

	def __modifyLayout( self ):
		global layout
		admin_settings_dn='uid=%s,cn=admin-settings,cn=univention,%s' % (self['username'], self.lo.base)
		policy = self.lo.getPolicies(self.dn)
		univention.debug.debug(univention.debug.ADMIN, univention.debug.ALL, 'self.py: policy: %s' % (policy))
		overrides = self.lo.get(admin_settings_dn, attr=['univentionAdminSelfAttributes'])
		fields = []
		if overrides:
			fields = overrides[ 'univentionAdminSelfAttributes' ]
		elif policy.has_key( 'univentionPolicyAdminSettings') and policy[ 'univentionPolicyAdminSettings' ].has_key( 'univentionAdminSelfAttributes' ):
			fields = policy[ 'univentionPolicyAdminSettings' ][ 'univentionAdminSelfAttributes' ][ 'value' ]
		univention.debug.debug(univention.debug.ADMIN, univention.debug.ALL, 'self.py: fields: %s' % (fields))
		self.layout = _create_layout(fields, self.options)
		if not self.layout:
			tab = univention.admin.tab( _('General'),_('There are no options enabled.'),[
					[univention.admin.field("filler"), ]])
			self.layout.append( tab )
		layout = self.layout
		univention.debug.debug(univention.debug.ADMIN, univention.debug.ALL, 'self.py: layout: %s' % (layout))
