#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#
# Copyright (C) 2006, 2007 Univention GmbH
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

import univention.management.console as umc

import univention.debug as ud

import base

import uniparts
import v

import univention_baseconfig

_ = umc.Translation( 'univention.management.console.frontend' ).translate

class About( base.Page ):
	def __init__( self, notebook ):
		base.Page.__init__( self, 'about', _( 'About' ) )
		self.__notebook = notebook
		self.module_buttons = {}

	def layout( self ):
		rows = []

		baseConfig = univention_baseconfig.baseConfig()
		baseConfig.load()

		build_version = v.build

		if baseConfig.has_key("version/releasename"):
			build_version = build_version + "(" + baseConfig["version/releasename"] + ")"

		## UMC
		rows.append( uniparts.tablerow("",{},{"obs":[
				uniparts.tablecol("",{"colspan":"2",'type':'about_layout'},{"obs":[
				uniparts.header(_("Univention Management Console"),{"type":"4"},{})
				]})
				]}))

		rows.append(uniparts.tablerow("",{},{"obs":[
				uniparts.tablecol("",{'type':'about_layout'},{"obs":[uniparts.text('',{},{'text':[ _('Version')]})]}),
				uniparts.tablecol("",{'type':'about_layout'},{"obs":[uniparts.text('',{},{'text':[v.version]})]})
				]}))

		rows.append(uniparts.tablerow("",{},{"obs":[
				uniparts.tablecol("",{'type':'about_layout'},{"obs":[uniparts.text('',{},{'text':[ _('Build')]})]}),
				uniparts.tablecol("",{'type':'about_layout'},{"obs":[uniparts.text('',{},{'text':[build_version]})]})
				]}))

		## UCS
		rows.append(uniparts.tablerow("",{},{"obs":[
				uniparts.tablecol("",{"colspan":"2",'type':'about_layout'},{"obs":[]})
				]}))

		rows.append(uniparts.tablerow("",{},{"obs":[
				uniparts.tablecol("",{'type':'about_layout'},{"obs":[uniparts.text('',{},{'text':[ _('Hostname')]})]}),
				uniparts.tablecol("",{'type':'about_layout'},{"obs":[uniparts.text('',{},{'text':[baseConfig['hostname']]})]})
				]}))

		version_string = ""
		for key in ['version/version','version/patchlevel','version/security-patchlevel']:
			if baseConfig.has_key(key) and baseConfig[key]:
				if version_string:
					version_string = "%s-%s" % (version_string,baseConfig[key])
				else:
					version_string = baseConfig[key]

		rows.append(uniparts.tablerow("",{},{"obs":[
				uniparts.tablecol("",{'type':'about_layout'},{"obs":[uniparts.text('',{},{'text':[ _('local Installation')]})]}),
				uniparts.tablecol("",{'type':'about_layout'},{"obs":[uniparts.text('',{},{'text':["%s %s" % (_('UCS Version'), version_string)]})]})
				]}))

		rows.append(uniparts.tablerow("",{},{"obs":[
				uniparts.tablecol("",{"colspan":"2",'type':'about_layout'},{"obs":[]})
				]}))

		## Contact
		rows.append(uniparts.tablerow("",{},{"obs":[
				uniparts.tablecol("",{"colspan":"2",'type':'about_layout'},{"obs":[
				uniparts.header(_("Contact"),{"type":"4"},{})
				]})
				]}))

		rows.append(uniparts.tablerow("",{},{"obs":[
				uniparts.tablecol("",{'type':'about_layout'},{"obs":[uniparts.text('',{},{'text':['Univention GmbH']})]}),
				uniparts.tablecol("",{'type':'about_layout'},{"obs":[uniparts.htmltext('',{},{'htmltext':[
				'<a href=http://www.univention.de target=parent>www.univention.de</a>'
				]})]})
				]}))

		rows.append(uniparts.tablerow("",{},{"obs":[
				uniparts.tablecol("",{'type':'about_layout'},{"obs":[uniparts.text('',{},{'text':[_('ALL RIGHTS RESERVED')]})]}),
				uniparts.tablecol("",{'type':'about_layout'},{"obs":[uniparts.htmltext('',{},{'htmltext':[
				'<a href="mailto:info@univention.de">info@univention.de</a>'
				]})]})
				]}))

		rows.append(uniparts.tablerow("",{},{"obs":[
				uniparts.tablecol("",{"colspan":"2",'type':'about_layout'},{"obs":[]})
				]}))

		# logout
		rows.append(uniparts.tablerow("",{},{"obs":[
				uniparts.tablecol("",{"colspan":"2",'type':'about_layout'},{"obs":[]})
				]}))

		self.logoutbutton = uniparts.button( _( 'Logout from Univention Management Console' ), { 'icon' : '/style/cancel.gif' }, { 'helptext' : _( 'Logout from Univention Management Console' ) } )
		rows.append(uniparts.tablerow("",{},{"obs":[
				uniparts.tablecol("",{'type':'about_layout'},{"obs":[ self.logoutbutton ]}),
				]}))

		return rows

	def apply( self ):
		ud.debug( ud.ADMIN, ud.INFO, 'About.apply' )
		# see if the user has clicked anything on this page
		if self.logoutbutton.pressed():
			self.__notebook.logout()
