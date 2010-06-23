# -*- coding: utf-8 -*-
#
# Univention Webui
#  tabbing.py
#
# Copyright 2004-2010 Univention GmbH
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

from itertools import *
from localwebui import _

import types
import univention.admin
import univention.admin.modules
import univention.debug

_options_description = _('Options')
_options_short_description = _options_description
_policies_description = _('Policies')

def _format_tab(tab):
	return (tab.short_description, tab.long_description)

class Tabbing(list):
	def __init__(self, module = None, object = None, more = False, options = False, advanced = True):
		self._module = None
		self._object = None
		self.mod_tabs = []
		self.pol_tabs = []
		self.pol_sel = None
		self.opt_tab = None
		self.advanced = advanced
		if object is None:
			if isinstance(module, types.ModuleType):
				# "Edit Policy" case
				self._module = module
				super(Tabbing, self).__init__(self.__mk_edt_pol())
			else:
				# "List Compatibility" case
				# "module" is really a list in this case!
				super(Tabbing, self).__init__(self.__all_tabs())
		else:
			# "Arbitraty Module" case
			self._module = module
			self._object = object
			self.mod_tabs = self.__mk_mod_tabs()
			if more:
				self.pol_tabs = self.__mk_pol_tabs()
				self.pol_sel = self.__mk_pol_sel()
				if options:
					self.opt_tab = self.__mk_opt_tab()
			super(Tabbing, self).__init__(self.__all_tabs())

	def __mk_mod_tabs(self):		
		tab_list = []

		for tab in univention.admin.modules.layout(self._module, self._object):
			advanced = univention.admin.ucr_overwrite_layout(self._module.module, 'advanced', tab)
			if advanced == False:
				value = False
			elif advanced == None:
				value = tab.advanced # read the default value from the modul
			else:
				value = True
				
			if not self.advanced and value:
				pass
			else:
				tab_list.append( (tab, self._module) )

		return tab_list

	def __mk_pol_tabs(self):
		return [ (univention.admin.tab(shrt, long, fields), module)
			 for type in univention.admin.modules.policyTypes(self._module)
			 for module in [univention.admin.modules.get(type)]
			 for layout in [univention.admin.modules.layout(module)]
			 if len(layout) > 1
			 if self.advanced
			 for short in [univention.admin.modules.policy_short_description(module)]
			 for shrt in ['[%s]' % short]
			 for long in [layout[0].long_description]
			 for fields in [layout[0].fields] ]

	def __mk_pol_sel(self):
		if univention.admin.modules.isContainer(self._module):
			description = _policies_description
			return univention.admin.tab(description, description), self._module
		return None

	def __mk_opt_tab(self):
		short = '(%s)' % _options_short_description
		long  = _options_description
		if self.advanced:
			return univention.admin.tab(short, long), self._module
		else:
			return None

	def __mk_edt_pol(self):
		short  = "[%s]" % univention.admin.modules.policy_short_description(self._module)
		long   = univention.admin.modules.long_description(self._module)
		fields = univention.admin.modules.layout(self._module)[0].fields
		return [(univention.admin.tab(short, long, fields), self._module)]

	def __all_tabs(self):
		result = list(self.mod_tabs)
		if self.pol_tabs:
			result.extend(self.pol_tabs)
		if self.pol_sel:
			result.append(self.pol_sel)
		if self.opt_tab:
			result.append(self.opt_tab)
		return result

	def __by_name(self, name):
		for tab, mod in self:
			if name == tab.short_description:
				return tab, mod
		return None, None

	def module_tabs(self):
		return (tab for tab, mod in self.mod_tabs)

	def tabs(self):
		return (_format_tab(tab) for tab, mod in self)

	def previoustabs(self, name):
		def pred(tab):
			return name != tab.short_description
		return takewhile(pred, self.module_tabs())

	def at(self, index):
		if not type( index ) == int:
			return None

		if len(self) > index and len(self[index]) > 0:
			return self[index][0].short_description
		else:
			return None

	def selected(self, name):
		for index, (tab, mod) in enumerate(self):
			if name == tab.short_description:
				return index
		return 0

	def name(self, name = None):
		if name:
			tab, mod = self.__by_name(name)
			if tab is not None:
				return name
		try:
			return self[0][0].short_description
		except (IndexError, AttributeError):
			return None

	def short_description(self, name):
		tab, mod = self.__by_name(name)
		if tab:
			return tab.short_description
		return ''

	def long_description(self, name):
		tab, mod = self.__by_name(name)
		if tab:
			return tab.long_description
		return ''

	def fields(self, name):
		tab, mod = self.__by_name(name)
		if tab:
			return tab.fields
		return []

	def module(self, name):
		tab, mod = self.__by_name(name)
		if mod:
			return mod
		return self._module

	def object(self, name):
		if self.module(name) == self._module:
			return self._object
		return None

	def is_module_tab(self, name):
		for tab in self.module_tabs():
			if name == tab.short_description:
				return True
		return False

	def is_options(self, name):
		return self.opt_tab and name == '(%s)' % _options_short_description

	def is_policy_selection(self, name):
		return self.pol_sel and name == _policies_description
