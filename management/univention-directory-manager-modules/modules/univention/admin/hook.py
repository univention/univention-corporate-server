# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  hook definitions
#
# Copyright 2004-2018 Univention GmbH
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

import univention.debug
import univention.admin.modules
import univention.admin.uexceptions
from univention.admin import localization
import sys
import os
import traceback

translation = localization.translation('univention/admin')
_ = translation.translate

#
# load all additional hook files from */site-packages/univention/admin/hooks.d/*.py
#


def import_hook_files():
	for dir in sys.path:
		if os.path.exists(os.path.join(dir, 'univention/admin/hook.py')):
			if os.path.isdir(os.path.join(dir, 'univention/admin/hooks.d/')):
				for f in os.listdir(os.path.join(dir, 'univention/admin/hooks.d/')):
					if f.endswith('.py'):
						fn = os.path.join(dir, 'univention/admin/hooks.d/', f)
						try:
							with open(fn, 'r') as fd:
								exec fd in sys.modules[__name__].__dict__
							univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'admin.syntax.import_hook_files: importing "%s"' % fn)
						except:
							univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'admin.syntax.import_hook_files: loading %s failed' % fn)
							univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'admin.syntax.import_hook_files: TRACEBACK:\n%s' % traceback.format_exc())


class simpleHook(object):
	type = 'simpleHook'

	#
	# To use the LDAP connection of the parent UDM call in any of the following
	# methods, use obj.lo and obj.position.
	#

	def hook_open(self, obj):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'admin.syntax.hook.simpleHook: _open called')

	def hook_ldap_pre_create(self, obj):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'admin.syntax.hook.simpleHook: _ldap_pre_create called')

	def hook_ldap_addlist(self, obj, al=[]):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'admin.syntax.hook.simpleHook: _ldap_addlist called')
		return al

	def hook_ldap_post_create(self, obj):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'admin.syntax.hook.simpleHook: _ldap_post_create called')

	def hook_ldap_pre_modify(self, obj):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'admin.syntax.hook.simpleHook: _ldap_pre_modify called')

	def hook_ldap_modlist(self, obj, ml=[]):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'admin.syntax.hook.simpleHook: _ldap_modlist called')
		return ml

	def hook_ldap_post_modify(self, obj):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'admin.syntax.hook.simpleHook: _ldap_post_modify called')

	def hook_ldap_pre_remove(self, obj):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'admin.syntax.hook.simpleHook: _ldap_pre_remove called')

	def hook_ldap_post_remove(self, obj):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'admin.syntax.hook.simpleHook: _ldap_post_remove called')


# ATTENTION: Only derive from this class when you are sure
# every system in your domain has the update installed that
# introduced this hook. (Nov 2018; UCS 4.3-2)
# Otherwise you will get errors when you are distributing your new
# hook via ucs_registerLDAPExtension --udm_hook
class AttributeHook(simpleHook):
	'''Convenience Hook that essentially implements a mapping
	between UDM and LDAP for your extended attributes.
	Derive from this class, set attribute_name to the name of
	the (udm) attribute and implement map_attribute_value_to_udm
	and map_attribute_value_to_ldap'''
	udm_attribute_name = None
	ldap_attribute_name = None

	def hook_open(self, obj):
		assert isinstance(self.udm_attribute_name, basestring), "udm_attribute_name has to be a str"
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'admin.syntax.hook.AttributeHook: Mapping %s (LDAP) -> %s (UDM)' % (self.ldap_attribute_name, self.udm_attribute_name))
		old_value = obj[self.udm_attribute_name]
		new_value = self.map_attribute_value_to_udm(old_value)
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'admin.syntax.hook.AttributeHook: Setting UDM value from %r to %r' % (old_value, new_value))
		obj[self.udm_attribute_name] = new_value

	def hook_ldap_addlist(self, obj, al):
		return self.hook_ldap_modlist(obj, al)

	def hook_ldap_modlist(self, obj, ml):
		assert isinstance(self.ldap_attribute_name, basestring), "ldap_attribute_name has to be a str"
		new_ml = []
		for ml_value in ml:
			if len(ml_value) == 2:
				key, old_value, new_value = ml_value[0], [], ml_value[1]
			else:
				key, old_value, new_value = ml_value
			if key == self.ldap_attribute_name:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'admin.syntax.hook.AttributeHook: Mapping %s (UDM) -> %s (LDAP)' % (self.udm_attribute_name, self.ldap_attribute_name))
				old_value = self.map_attribute_value_to_ldap(old_value)
				new_new_value = self.map_attribute_value_to_ldap(new_value)
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'admin.syntax.hook.AttributeHook: Setting LDAP value from %r to %r' % (new_value, new_new_value))
				new_value = new_new_value
			new_ml.append((key, old_value, new_value))
		return new_ml

	def map_attribute_value_to_ldap(self, value):
		# return value as it shall be saved in ldap
		return value

	def map_attribute_value_to_udm(self, value):
		# return value as it shall be used in udm objects
		# needs to be syntax compliant
		return value
