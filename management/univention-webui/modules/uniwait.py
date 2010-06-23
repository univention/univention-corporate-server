# -*- coding: utf-8 -*-
#
# Univention Webui
#  uniwait.py
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

		header = htmltext ('', {}, \
			{'htmltext': [_("""
						<div id="header">
							<!-- @start header-title -->
							<h1 class="header-title">
								<span class="hide">univention</span> <a href="/univention-directory-manager/" title="Start">directory manager</a>
							</h1>
							<!-- @end header-title -->
						<!-- @end header -->
						</div>
					""")]})
		self.subobjs.append(header)

		notebook_message = htmltext ('', {}, \
				{'htmltext': ["""
					<!-- @end tab-navigation -->
					<div id=content-wrapper>
					<div id=content-head>
					<ul class="tabs">
					<li class="active"><p>%(progress)s</p></li>
					</ul>
					</div>
					<div id="content">
					""" % {'progress': _('Operation in progress')}]})
		self.subobjs.append(notebook_message)
			
		# self.subobjs.append(table("",{ 'type':self.save.get( 'header_table_type' , 'content_header' ) },{"obs":[tablerow('',{},{'obs':[tablecol("",{'type':'browse_layout'},{"obs":[]})]})]}))

		# self.nbook=notebook('', {}, {'buttons': [(_('Operation in progress'), _('Operation in progress'))], 'selected': 0})
		# self.subobjs.append(self.nbook)

		msg = ''
		if hasattr(self.pending_dialog, 'waitmessage'):
			msg = self.pending_dialog.waitmessage()
		if not msg:
			msg = _('The operation is in progress. Please wait.')
		info_message = htmltext ('', {}, \
				{'htmltext': ["""
					<div id="waittext"><p>%(text)s</p></div>
					""" % {'text': msg}]})
		self.subobjs.append(info_message)

		rows=[]
		rows.append(tablerow("",{},{"obs":[
			tablecol("",{'type':'wait_layout'},{"obs":[icon('', {'url':'/icon/progress.gif'},{})]}),
			tablecol("",{'type':'wait_layout'},{"obs":[text('', {}, {'text': [msg]})]})
			]}))


		self.refresh_button=button(_('Update status'), {'class':'submit'}, {'helptext': _('Update status')})
		self.cancel_button=button(_('Cancel'), {'class':'submit'}, {'helptext': _('Cancel operation')})
		self.subobjs.append(htmltext ('', {}, {'htmltext': ['<div id="waitdialog">']}))
		self.subobjs.append(self.cancel_button)
		self.subobjs.append(htmltext ('', {}, {'htmltext': ['</div>']}))
		# self.subobjs.append(self.refresh_button)

		rows.append(tablerow("",{},{"obs":[
			tablecol("",{'colspan':'2','type':'wait_layout'},{"obs":[self.cancel_button, self.refresh_button]})
			]}))

		# self.subobjs.append(table("",{'type':self.save.get( 'main_table_type' , 'content_main' )},{"obs":rows}))

		self.atts['refresh']='500'

	
		# This "link button" is needed in order for the refresh to work properly.
		hack_button=button('', {'link':'1'}, {'helptext': _('Update status')})
		self.subobjs.append(hack_button)

		notebook_message = htmltext ('', {}, \
				{'htmltext': ["""
					</div>
					</div>
					"""]})
		self.subobjs.append(notebook_message)
		
