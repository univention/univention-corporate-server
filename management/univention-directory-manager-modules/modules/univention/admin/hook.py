# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  hook definitions
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

import re, string, types, math, time, operator
import univention.debug
import univention.admin.modules
import univention.admin.uexceptions
import univention.admin.localization
import base64
import copy
import sys, os

translation=univention.admin.localization.translation('univention/admin')
_=translation.translate

#
# load all additional hook files from */site-packages/univention/admin/hooks.d/*.py
#
def import_hook_files():
	for dir in sys.path:
		if os.path.exists( os.path.join( dir, 'univention/admin/hook.py' ) ):
			if os.path.isdir( os.path.join( dir, 'univention/admin/hooks.d/' ) ):
				for f in os.listdir( os.path.join( dir, 'univention/admin/hooks.d/' ) ):
					if f.endswith('.py'):
						fn = os.path.join( dir, 'univention/admin/hooks.d/', f )
						try:
							fd = open( fn, 'r' )
							exec fd in univention.admin.hook.__dict__
							univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'admin.syntax.import_hook_files: importing "%s"' % fn)
						except:
							univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'admin.syntax.import_hook_files: loading %s failed' % fn )
							import traceback
							univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'admin.syntax.import_hook_files: TRACEBACK:\n%s' % traceback.format_exc() )



class simpleHook(object):
	type='simpleHook'

	def hook_open(self, module):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'admin.syntax.hook.simpleHook: _open called')
		pass


	def hook_ldap_pre_create(self, module):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'admin.syntax.hook.simpleHook: _ldap_pre_create called')
		pass

	def hook_ldap_addlist(self, module, al = []):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'admin.syntax.hook.simpleHook: _ldap_addlist called')
		return al

	def hook_ldap_post_create(self, module):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'admin.syntax.hook.simpleHook: _ldap_post_create called')
		pass


	def hook_ldap_pre_modify(self, module):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'admin.syntax.hook.simpleHook: _ldap_pre_modify called')
		pass

	def hook_ldap_modlist(self, module, ml = []):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'admin.syntax.hook.simpleHook: _ldap_modlist called')
		return ml

	def hook_ldap_post_modify(self, module):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'admin.syntax.hook.simpleHook: _ldap_post_modify called')
		pass


	def hook_ldap_pre_remove(self, module):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'admin.syntax.hook.simpleHook: _ldap_pre_remove called')
		pass

	def hook_ldap_post_remove(self, module):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'admin.syntax.hook.simpleHook: _ldap_post_remove called')
		pass
