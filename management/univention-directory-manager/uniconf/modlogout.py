# -*- coding: utf-8 -*-
#
# Univention Directory Manager
#  the admin logout logic
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

from uniparts import *
import os
import sys
import time
import ldap
import string
import re
import unimodule
from local import _

def create(a,b,c):
	return modlogout(a,b,c)
def myinfo(settings):
	return unimodule.realmodule("logout", _("Logout"), _("Logout"))
def myrgroup():
	return ""
def mywgroup():
	return ""
def mymenunum():
	return 800
def mymenuicon():
	return unimodule.selectIconByName( 'exit' )

class modlogout(unimodule.unimodule):
	def mytype(self):
		return "dialog"

	def myinit(self):
		#from uniparts import *
		pass

	def myinit(self):
		self.authfail=None
		self.save=self.parent.save
		if not self.save.get("LOGOUT"):

			self.div_start('content-wrapper')
			#self.subobjs.append(table("",
			#		{'type':'content_header'},
			#		{"obs":[tablerow("",{},{"obs":[tablecol("",{},{"obs":[]})]})]})
			#	)
			self.nbook=notebook('', {}, {'buttons': [(_('Logout'), _('Logout'))], 'selected': 0})
			self.subobjs.append(self.nbook)
			self.div_start('content')

			self.okbut = button(_("OK"),{'class':'submit', 'defaultbutton': '1'},{"helptext":_("ok")})
			okbutcol = tablecol("",{'type':'note_layout'},{"obs":[self.okbut]})

			self.cabut = button(_("Cancel"),{'class':'cancel'},{"helptext":_("Cancel")})
			cabutcol = tablecol("",{'type':'note_layout'},{"obs":[self.cabut]})

			row1 = tablerow("",{},
					{"obs":[tablecol("",{"colspan":"2",'type':'note_layout_text'},
					{"obs":[text('',{},{'text':[_("Do you really want to logout?")]})]})]
					}
				)

			row2 = tablerow("",{},{"obs":[cabutcol, okbutcol]})
			tab = table("",{},{"obs":[row1, row2]})

			self.subobjs.append(table("",{'type':'logout'},
						{"obs":[tablerow("",{},
							{"obs":[tablecol("",{"colspan":"2"},
								{"obs":[tab]})]
							})]
						})
					)
			self.div_stop('content')
			self.div_stop('content-wrapper')

		else:
			self.subobjs.append(logout("",{},{}))

	def apply(self):
		if self.okbut.pressed():
			self.save.put("LOGOUT",1)
		if self.cabut.pressed():
			self.save.put("uc_module","none")
			self.save.put("uc_submodule","none")
