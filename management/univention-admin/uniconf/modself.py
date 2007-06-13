# -*- coding: utf-8 -*-
#
# Univention Admin
#  module for editing the self object
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

import os
import sys
import time
import ldap
import string
import re

import unimodule
from uniparts import *
from local import _
import modedit

import univention.admin.uldap
import univention.admin.modules
import univention_baseconfig
import univention.debug

import univention.admin.handlers.users.user
import univention.admin.handlers.users.self

def create(a,b,c):
	return modself(a,b,c)

def _get_opts(settings):
	ocs = set(settings.userentry['objectClass'])
	return [key for key in univention.admin.handlers.users.user.options
		    for opt in [univention.admin.handlers.users.user.options[key]]
		    if opt.matches(ocs)]

def _get_fields(settings):
	if settings.list_selfOverrides:
		return settings.list_selfOverrides
	return settings.list_selfAttributes

def myinfo(settings):
	if settings.listAdminModule('modself'):
		options = _get_opts(settings)
		fields = _get_fields(settings)
		has_layout = bool(univention.admin.handlers.users.self._create_layout(fields, options))
		passwd = univention.admin.handlers.users.user.property_descriptions['password']
		has_passwd = passwd.matches(options)
		submodules = []
		if has_layout:
			submodules.append(unimodule.submodule('users/self', _("Account"), _("Edit my account")))
		if has_passwd:
			submodules.append(unimodule.submodule('users/passwd', _("Password"), _("Change my password")))
		if settings.may_override:
			submodules.append(unimodule.submodule('settings/user', _("Admin"), _("Edit my Univention Admin settings")))
		if not submodules:
			return unimodule.realmodule("self", '')
		try:
			name=settings.userentry['cn'][0]
		except KeyError:
			name='Myself'
		virtualmodules=[
			unimodule.virtualmodule('self', name, _("My personal objects"), submodules)
		]
		return unimodule.realmodule("self", name, _("My personal objects"), virtualmodules=virtualmodules)
	else:
		return unimodule.realmodule("self", '')

def myrgroup():
	return ""

def mywgroup():
	return ""

def mymenunum():	
	return 101

def mymenuicon():
	return '/icon/settings/cn.gif'
	
class modself(modedit.modedit):
	def myinit(self):
		self.save=self.parent.save
		self.lo=self.args["uaccess"]
		settings=self.save.get("settings")

		if self.inithandlemessages():
			return

		options = _get_opts(settings)
		fields = _get_fields(settings)
		has_layout = bool(univention.admin.handlers.users.self._create_layout(fields, options))
		passwd = univention.admin.handlers.users.user.property_descriptions['password']
		has_passwd = passwd.matches(options)

		self.save.put('edit_return_to', 'self')
		if self.save.get('uc_submodule') == 'settings/user':
			self.save.put('edit_type', 'settings/user')
			self.save.put('edit_dn', self.lo.explodeDn(settings.userdn, 0)[0]+',cn=admin-settings,cn=univention,'+self.lo.base)
		elif self.save.get('uc_submodule') == 'users/passwd':
			self.save.put('edit_type', 'users/passwd')
			self.save.put('edit_dn', settings.userdn)
		elif has_layout:
			self.save.put('edit_type', 'users/self')
			self.save.put('edit_dn', settings.userdn)
		elif has_passwd:
			self.save.put('edit_type', 'users/passwd')
			self.save.put('edit_dn', settings.userdn)
		else:
			self.save.put('edit_type', 'settings/user')
			self.save.put('edit_dn', self.lo.explodeDn(settings.userdn, 0)[0]+',cn=admin-settings,cn=univention,'+self.lo.base)

		modedit.modedit.myinit(self)

	def apply(self):
		self.save.put('edit_return_to', 'self') # modedit
		self.save.put('backtomodule', 'self') # usermessage
		modedit.modedit.apply(self,
				      cancelMessage=_("Request canceled, your changes were discarded."),
				      okMessage=_("Request commited, your changes were accepted."))

