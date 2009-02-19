# -*- coding: utf-8 -*-
#
# Univention Webui
#  uniwait.py
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

import os
import sys
import time
import ldap
import string
import re

import unimodule

from uniparts import *
from localwebui import _

def create(a,b,c):
	return uniwait(a,b,c)

def myrgroup():
	return ""

def mywgroup():
	return ""

class uniwait(unimodule.unimodule):
	def mytype(self):
		return "dialog"

	def myinit(self):
		self.save=self.parent.save

		if self.inithandlemessages():
			return

		for att in [ 'layout_type' , 'site_title' , 'header_img' ]:
			if self.save.get( att , False):
				self.atts[ att ] = self.save.get( att , False)
			
		self.subobjs.append(table("",{ 'type':self.save.get( 'header_table_type' , 'content_header' ) },{"obs":[tablerow('',{},{'obs':[tablecol("",{'type':'browse_layout'},{"obs":[]})]})]}))

		self.nbook=notebook('', {}, {'buttons': [(_('Operation in progress'), _('Operation in progress'))], 'selected': 0})
		self.subobjs.append(self.nbook)

		msg = ''
		if hasattr(self.pending_dialog, 'waitmessage'):
			msg = self.pending_dialog.waitmessage()
		if not msg:
			msg = _('The operation is in progress. Please wait.')

		rows=[]
		rows.append(tablerow("",{},{"obs":[
			tablecol("",{'type':'wait_layout'},{"obs":[icon('', {'url':'/icon/progress.gif'},{})]}),
			tablecol("",{'type':'wait_layout'},{"obs":[text('', {}, {'text': [msg]})]})
			]}))


		self.refresh_button=button(_('Update status'), {'icon':'/style/ok.gif'}, {'helptext': _('Update status')})
		self.cancel_button=button(_('Cancel'), {'icon':'/style/cancel.gif'}, {'helptext': _('Cancel operation')})

		rows.append(tablerow("",{},{"obs":[
			tablecol("",{'colspan':'2','type':'wait_layout'},{"obs":[self.refresh_button, self.cancel_button]})
			]}))

		self.subobjs.append(table("",{'type':self.save.get( 'main_table_type' , 'content_main' )},{"obs":rows}))

		self.atts['refresh']='1000'

	
		# This "link button" is needed in order for the refresh to work properly.
		hack_button=button('', {'link':'1'}, {'helptext': _('Update status')})
		self.subobjs.append(hack_button)
		
