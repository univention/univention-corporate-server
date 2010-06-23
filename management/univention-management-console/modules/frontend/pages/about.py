# #!/usr/bin/python2.4
# # -*- coding: utf-8 -*-
# #
# # Univention Management Console
# #
# # Copyright 2006-2010 Univention GmbH
# #
# # http://www.univention.de/
# #
# # All rights reserved.
# #
# # The source code of this program is made available
# # under the terms of the GNU Affero General Public License version 3
# # (GNU AGPL V3) as published by the Free Software Foundation.
# #
# # Binary versions of this program provided by Univention to you as
# # well as other copyrighted, protected or trademarked materials like
# # Logos, graphics, fonts, specific documentations and configurations,
# # cryptographic keys etc. are subject to a license agreement between
# # you and Univention and not subject to the GNU AGPL V3.
# #
# # In the case you use this program under the terms of the GNU AGPL V3,
# # the program is provided in the hope that it will be useful,
# # but WITHOUT ANY WARRANTY; without even the implied warranty of
# # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# # GNU Affero General Public License for more details.
# #
# # You should have received a copy of the GNU Affero General Public
# # License with the Debian GNU/Linux or Univention distribution in file
# # /usr/share/common-licenses/AGPL-3; if not, see
# # <http://www.gnu.org/licenses/>.
# 
# import univention.management.console as umc
# 
# import univention.debug as ud
# 
# import base
# 
# import uniparts
# import v
# 
# import univention_baseconfig
# 
# _ = umc.Translation( 'univention.management.console.frontend' ).translate
# 
# def about_layout( ):
# 	rows = []
# 
# 	baseConfig = univention_baseconfig.baseConfig()
# 	baseConfig.load()
# 
# 	build_version = v.build
# 
# 	if baseConfig.has_key("version/releasename"):
# 		build_version = build_version + "(" + baseConfig["version/releasename"] + ")"
# 
# 	## UMC
# 	rows.append( uniparts.tablerow("",{},{"obs":[
# 			uniparts.tablecol("",{"colspan":"2",'type':'about_layout'},{"obs":[
# 			uniparts.header(_("Univention Management Console"),{"type":"4"},{})
# 			]})
# 			]}))
# 
# 	rows.append(uniparts.tablerow("",{},{"obs":[
# 			uniparts.tablecol("",{'type':'about_layout'},{"obs":[uniparts.text('',{},{'text':[ _('Version')]})]}),
# 			uniparts.tablecol("",{'type':'about_layout'},{"obs":[uniparts.text('',{},{'text':[v.version]})]})
# 			]}))
# 
# 	rows.append(uniparts.tablerow("",{},{"obs":[
# 			uniparts.tablecol("",{'type':'about_layout'},{"obs":[uniparts.text('',{},{'text':[ _('Build')]})]}),
# 			uniparts.tablecol("",{'type':'about_layout'},{"obs":[uniparts.text('',{},{'text':[build_version]})]})
# 			]}))
# 
# 	## UCS
# 	rows.append(uniparts.tablerow("",{},{"obs":[
# 			uniparts.tablecol("",{"colspan":"2",'type':'about_layout'},{"obs":[]})
# 			]}))
# 
# 	rows.append(uniparts.tablerow("",{},{"obs":[
# 			uniparts.tablecol("",{'type':'about_layout'},{"obs":[uniparts.text('',{},{'text':[ _('Hostname')]})]}),
# 			uniparts.tablecol("",{'type':'about_layout'},{"obs":[uniparts.text('',{},{'text':[baseConfig['hostname']]})]})
# 			]}))
# 
# 	version_string = ""
# 	for key in ['version/version','version/patchlevel','version/security-patchlevel']:
# 		if baseConfig.has_key(key) and baseConfig[key]:
# 			if version_string:
# 				version_string = "%s-%s" % (version_string,baseConfig[key])
# 			else:
# 				version_string = baseConfig[key]
# 
# 	rows.append(uniparts.tablerow("",{},{"obs":[
# 			uniparts.tablecol("",{'type':'about_layout'},{"obs":[uniparts.text('',{},{'text':[ _('Local installation')]})]}),
# 			uniparts.tablecol("",{'type':'about_layout'},{"obs":[uniparts.text('',{},{'text':["%s %s" % (_('UCS version'), version_string)]})]})
# 			]}))
# 
# 	rows.append(uniparts.tablerow("",{},{"obs":[
# 			uniparts.tablecol("",{"colspan":"2",'type':'about_layout'},{"obs":[]})
# 			]}))
# 
# 	## Contact
# 	rows.append(uniparts.tablerow("",{},{"obs":[
# 			uniparts.tablecol("",{"colspan":"2",'type':'about_layout'},{"obs":[
# 			uniparts.header(_("Contact"),{"type":"4"},{})
# 			]})
# 			]}))
# 
# 	rows.append(uniparts.tablerow("",{},{"obs":[
# 			uniparts.tablecol("",{'type':'about_layout'},{"obs":[uniparts.text('',{},{'text':['Univention GmbH']})]}),
# 			uniparts.tablecol("",{'type':'about_layout'},{"obs":[uniparts.htmltext('',{},{'htmltext':[
# 			'<a href=http://www.univention.de target=parent>www.univention.de</a>'
# 			]})]})
# 			]}))
# 
# 	rows.append(uniparts.tablerow("",{},{"obs":[
# 			uniparts.tablecol("",{'type':'about_layout'},{"obs":[uniparts.text('',{},{'text':[_('ALL RIGHTS RESERVED')]})]}),
# 			uniparts.tablecol("",{'type':'about_layout'},{"obs":[uniparts.htmltext('',{},{'htmltext':[
# 			'<a href="mailto:info@univention.de">info@univention.de</a>'
# 			]})]})
# 			]}))
# 
# 	rows.append(uniparts.tablerow("",{},{"obs":[
# 			uniparts.tablecol("",{"colspan":"2",'type':'about_layout'},{"obs":[]})
# 			]}))
# 
# 	return rows
# 
# class About( base.Page ):
# 	def __init__( self, notebook ):
# 		base.Page.__init__( self, 'about', _( 'About' ) )
# 		self.__notebook = notebook
# 		self.module_buttons = {}
# 
# 	def layout( self ):
# 		return about_layout
# 
# 	def apply( self ):
# 		ud.debug( ud.ADMIN, ud.INFO, 'About.apply' )
# 		# see if the user has clicked anything on this page
# 		#if self.logoutbutton.pressed():
# 		#	self.__notebook.logout()
