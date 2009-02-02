# -*- coding: utf-8 -*-
#
# Univention Directory Manager
#  the admin logout logic
#
# Copyright (C) 2004, 2005, 2006, 2007 Univention GmbH
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

            self.subobjs.append(table("",
                                      {'type':'content_header'},
                                      {"obs":[tablerow("",{},{"obs":[tablecol("",{},{"obs":[]})]})]})
                                )
            self.nbook=notebook('', {}, {'buttons': [(_('Logout'), _('Logout'))], 'selected': 0})
            self.subobjs.append(self.nbook)

            self.okbut = button(_("OK"),{'icon':'/style/ok.gif'},{"helptext":_("ok")})
            okbutcol = tablecol("",{'type':'note_layout'},{"obs":[self.okbut]})

            self.cabut = button(_("Cancel"),{'icon':'/style/cancel.gif'},{"helptext":_("Cancel")})
            cabutcol = tablecol("",{'type':'note_layout'},{"obs":[self.cabut]})

            row1 = tablerow("",{},
                            {"obs":[tablecol("",{"colspan":"2",'type':'note_layout'},
                                             {"obs":[text('',{},{'text':[_("Do you really want to logout?")]})]})]
                             }
                            )

            row2 = tablerow("",{},{"obs":[okbutcol,cabutcol]})
            tab = table("",{},{"obs":[row1, row2]})

            self.subobjs.append(table("",{'type':'content_main'},
                                      {"obs":[tablerow("",{},
                                                       {"obs":[tablecol("",{"colspan":"2"},
                                                                        {"obs":[tab]})]
                                                        })]
                                       })
                                )

        else:
            self.subobjs.append(logout("",{},{}))

    def apply(self):

        if self.okbut.pressed():
	     self.save.put("LOGOUT",1)
        if self.cabut.pressed():
             self.save.put("uc_module","none")
             self.save.put("uc_submodule","none")
