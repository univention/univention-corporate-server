# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for password part of the user
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

import os, sys, string, re, copy, time, types
import univention.admin
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
import univention.admin.uexceptions
import univention.admin.uldap
import univention.admin.handlers.users.user

import univention.debug

translation=univention.admin.localization.translation('univention.admin.handlers.users')
_=translation.translate

module='users/passwd'
operations=['edit']
uid_umlauts = 0

childs=0
short_description=_('User: Password')
long_description=''
options={}
property_descriptions={
	'username': univention.admin.property(
			short_description=_('User name'),
			long_description='',
			syntax=univention.admin.syntax.uid,
			multivalue=0,
			required=1,
			may_change=0,
			identifies=1
		),
	'password': univention.admin.property(
			short_description=_('Password'),
			long_description='',
			syntax=univention.admin.syntax.userPasswd,
			multivalue=0,
			options=['posix', 'samba', 'kerberos', 'mail'],
			required=1,
			may_change=1,
			identifies=0,
			dontsearch=1
		),
	'filler': univention.admin.property(
			short_description='',
			long_description='',
			syntax=univention.admin.syntax.none,
			multivalue=0,
			required=0,
			may_change=1,
			identifies=0,
			dontsearch=1
		)
}

layout=[
	univention.admin.tab(_('Change password'),_('Change password'),[
		[univention.admin.field("password"), univention.admin.field("filler")],
	]),
]

object=univention.admin.handlers.users.user.object
