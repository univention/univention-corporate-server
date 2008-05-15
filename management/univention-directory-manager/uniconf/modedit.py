# -*- coding: utf-8 -*-
#
# Univention Directory Manager
#  edit objects module
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

import unimodule
import uniconf
from uniparts import *
from local import _
from syntax import *

import univention.debug
import univention.admin.uldap
import univention.admin.modules
import univention.admin.objects
import univention.admin.syntax
import univention.admin.uexceptions

import string, ldap, copy, types, codecs, traceback
import base64, tempfile, re, operator

from M2Crypto import X509

co=None

# update choices-lists which are defined in LDAP
univention.admin.syntax.update_choices()

def make_options_check(object):
	if hasattr(object, 'options'):
		options = set(object.options)
		return lambda opts: opts and not options.intersection(opts)
	return lambda opts: False

def create(a,b,c):
	return modedit(a,b,c)
def myrgroup():
	return ""
def mywgroup():
	return ""

def get_okcancelbuttons(self, edit_policy=None):
	if edit_policy:
		self.edit_policy_ok=button(_("OK"),{'icon':'/style/ok.gif'},{"helptext":_("ok")})
		self.edit_policy_cancel=button(_("Cancel"),{'icon':'/style/cancel.gif'},{"helptext":_("Cancel")})
		return [self.edit_policy_ok, self.edit_policy_cancel]
	else:
		self.okbut=button(_("OK"),{'icon':'/style/ok.gif'},{"helptext":_("ok")})
		self.cabut=button(_("Cancel"),{'icon':'/style/cancel.gif'},{"helptext":_("Cancel")})
		return [self.okbut, self.cabut]

def get_iconbutton(attributes, helptext, path):
	tmp_atts=copy.deepcopy(attributes)
	tmp_atts['icon']=path
	return button("",tmp_atts,{"helptext":helptext})

def get_addbutton(attributes, helptext):
	return get_iconbutton(attributes, helptext, '/style/add.gif')

def get_removebutton(attributes, helptext):
	return get_iconbutton(attributes, helptext, '/style/remove.gif')

def get_upbutton(attributes, helptext):
	return get_iconbutton(attributes, helptext, '/style/up.gif')

def get_downbutton(attributes, helptext):
	return get_iconbutton(attributes, helptext, '/style/down.gif')

def get_leftbutton(attributes, helptext):
	return get_iconbutton(attributes, helptext, '/style/left.gif')

def get_rightbutton(attributes, helptext):
	return get_iconbutton(attributes, helptext, '/style/right.gif')

class modedit(unimodule.unimodule):
	def mytype(self):
		return "dialog"

	def mydescription(self):
		return mydescription()

	def mysubmodules(self):
		return []

	def myinit(self):
		self.save=self.parent.save
		if self.inithandlemessages():
			return

		self.lo=self.args["uaccess"]

		# get current position
		position=self.save.get('ldap_position')
		self.position=position
		settings=self.save.get('settings')
		superordinate=self.save.get('wizard_superordinate')
		if type(superordinate) == type(u''):
			#we need a object
			superordinatetype=self.save.get('wizard_superordinatetype')
			superordinate=univention.admin.objects.get(univention.admin.modules.get(superordinatetype), co, self.lo, '', dn=superordinate)

		if not self.save.get('edit_type'):
			return

		if self.save.get('edit_dn'):
			add=0
			modify=1
			multiedit=0
		elif self.save.get('edit_dn_list'):
			add=0
			modify=0
			multiedit=1
		else:
			add=1
			modify=0
			multiedit=0

		self.input={}
		self.minput={}
		self.finput={}
		self.ginput={}
		self.pinput={}
		self.rinput={}
		self.xinput={}
		self.zinput={}
		self.tinput={}
		self.registryinput={}
		self.fileinput={}
		self.input_multiedit_overwrite = {}

		# create self.object
		arg=None
		module=univention.admin.modules.get(self.save.get('edit_type'))

		if add and self.save.get('template_dn') and not self.save.get('template_dn')=="None":
			# if add get template and pass it to init
			if hasattr(module,'template') and module.template:
				template_module = univention.admin.modules.get(module.template)
				template_object = None
				# there must be a more efficient way then parsing all templates...
				for template in univention.admin.modules.lookup(template_module,None,self.lo,scope='sub'):
					if template.dn == self.save.get('template_dn'):
						template_object = template
				if template_object :
					univention.admin.modules.init(self.lo, position, module, template_object=template_object)
				else:
					raise univention.admin.uexceptions.valueRequired, 'template object with given dn '+self.save.get('template_dn')+' not found'
			else:
				raise univention.admin.uexceptions.valueRequired, 'template object for created object required'

		else:
			univention.admin.modules.init(self.lo, position, module)

		if not hasattr(self,'object'):
			self.object=self.save.get('edit_object')
			if not self.object:
				if add or multiedit:
					self.object=univention.admin.objects.get(module, None, self.lo, position, superordinate=superordinate)
				else:
					dn=self.save.get('edit_dn')
					arg=self.save.get('edit_arg')
					self.object=univention.admin.objects.get(module, None, self.lo, position, dn=dn, arg=arg, superordinate=superordinate)

		if not self.save.get('edit_object_opened'):
			try:
				univention.admin.objects.open(self.object)
			except univention.admin.uexceptions.insufficientInformation, ex:
				self.usermessage(_('Error opening Object: %s <br> You may encounter further errors editing this object.')%ex)

			if hasattr(self.object,'open_warning') and self.object.open_warning:
				self.usermessage(_('Warning opening Object: <ul>%s</ul> You may encounter further errors editing this object.')%string.replace(self.object.open_warning,'\n','<li>'))

			self.save.put('edit_object_opened', 1)

		self.save.put('edit_object', self.object)
		if self.inithandlemessages():
			return

		mode=self.save.get('edit_mode')

		# was there invalid input?
		invalid_values=self.save.get('edit_invalid')
		if not invalid_values:
			invalid_values={}

		# UI START

		######## generate header #######

		header_rows = []

		# do not show position bar if called from modbrowse
		if not self.save.get('edit_return_to'):

			# If base dn is "dc=foo,dc=bar" and settings.base_dn is "cn=users,dc=foo,dc=bar",
			# create string root_label "foo.bar/users/"

			domain_components=univention.admin.uldap.explodeDn(position.getBase(), 1)
			root_components=univention.admin.uldap.explodeDn(settings.base_dn, 1)[0:-len(domain_components)]
			root_label=string.join(domain_components, '.')
			if root_components:
				root_label = root_label+'/'+string.join(root_components, '/')

			# Create list of "buttons" (label, dn). If the object does already exist,
			# the last entry is the current DN and will hence be displayed as a label
			# rather than a button (if add ...)
			current_dn = settings.base_dn
			buttons=[(root_label, current_dn)]
			self.positionbuttons = []
			colcontent = []

			if add or not self.object.dn:
				# Object does not seem to exist, use the current position
				parent_dn=position.getDn()
			else:
				parent_dn=self.object.dn
			path_components=univention.admin.uldap.explodeDn(parent_dn, 0)[0:-len(domain_components)-len(root_components)]
			path_components.reverse()
			for p in path_components:
				label = p[p.find('=')+1:]
				current_dn = p+','+current_dn
				buttons.append((label, current_dn))

			if add or not self.object.dn:
				for label, dn in buttons:
					tmp_button = button(label, {"link": "1"}, {"helptext": dn})
					self.positionbuttons.append(tmp_button)
					colcontent.append(tmp_button)
					colcontent.append(text("",{},{"text":["/"]}))
			else:
				for label, dn in buttons[:-1]:
					tmp_button = button(label, {"link": "1"}, {"helptext": dn})
					self.positionbuttons.append(tmp_button)
					colcontent.append(tmp_button)
					colcontent.append(text("",{},{"text":["/"]}))
				colcontent.append(text("",{},{"text":[buttons[-1][0]]}))

			# create "widgets"
			header_rows.append(tablerow("",{},{"obs":[tablecol("",{'colspan':'4','type':'content_position'},{"obs":[text("",{},{"text":["%s /" % _("Position:")]})] + colcontent})]}))
		else:
			# need an empty position-row
			header_rows.append(tablerow("",{},{"obs":[tablecol("",{'colspan':'4'},{"obs":[htmltext("",{},{'htmltext':['&nbsp;']})]})]}))

		############################################################################
		
		if univention.admin.modules.childs(module):
			icon_path = unimodule.selectIconByName( univention.admin.modules.name(module),
							   iconNameGeneric = 'folder' )
		else:
			icon_path = unimodule.selectIconByName( univention.admin.modules.name(module) )

		head_icon=icon('',{'url':icon_path},{})
		# heading
		if modify:
			head_name = [
				text("",{},{"text":['%s %s' %(_("name:"),univention.admin.objects.description(self.object))]}),
				     ]
			head_type = [
				text("",{},{"text":['%s %s' %(_("type:"),univention.admin.modules.short_description(module))]})
				]

		elif multiedit:
			head_name = [
				text("",{},{"text":
					    ['%s %d %s'%(_("edit"),
							   len(self.save.get('edit_dn_list')),
							   _("objects"))]})
				]
			head_type = [
				text("",{},{"text":["%s %s" % (_("type:"),univention.admin.modules.short_description(module))]})
				]

		elif add:
			head_name = [
				text("",{},{"text":[_("name:")]})
				]
			head_type = [
				text("",{},{"text":['%s %s "%s"%s' %(_('type:'),_("new"), univention.admin.modules.short_description(module), _("-object"))]})
				]

		if hasattr(self.object,'link'):
			linktext=''
			res=self.object.link()
			if not res:
				links=[htmltext('',{},{'htmltext':[""]})]
			else:
				for link in res:
					if link.has_key('name') and link.has_key('url'):
						if link.has_key('icon'):
							linktext+=' <a href="%s" target="_blank"><img src="/icon/%s" alt="%s"></a>'%(link['url'],link['icon'],link['name'])
						else:
							linktext+=' <a href="%s" target="_blank">%s</a>'%(link['url'],link['name'])

				links=[htmltext('',{},{'htmltext':[linktext]})]
		else:
			links=[htmltext('',{},{'htmltext':[""]})]
		header_rows.append(
			tablerow('',{},{'obs':
					[tablecol('',{'type':'content_icon'},{'obs':[head_icon]}),
					 tablecol('',{},{'obs':head_name}),
					 tablecol('',{},{'obs':head_type}),
					 tablecol('',{'type':'object_links'},{'obs':links})
					 ]}))

		# build header-table
		self.subobjs.append(table("",{'type':'content_header'},{"obs":header_rows}))

		####### header generated ######

		####### generate tabs #######

		edit_policy = self.save.get('edit_policy')
		edit_options = False
		tab = self.save.get('tab')

		if edit_policy:
			tabbing = Tabbing(univention.admin.modules.get(edit_policy))
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "edit_policy: opened module of type: %s" % edit_policy)
		else:
			edit_options = hasattr(module, 'options') and module.options \
				       and (add or [key for key in module.options.keys() if module.options[key].editable])
			tabbing = Tabbing(module, self.object, not multiedit, edit_options)

		new_tab = tabbing.name(tab)
		if new_tab != tab:
			tab = new_tab
			self.save.put('tab', tab)

		self.nbook = notebook('', {}, {'buttons': tabbing.tabs(), 'selected': tabbing.selected(tab)})
		self.subobjs.append(self.nbook)

		current_module = tabbing.module(tab)
		current_object = tabbing.object(tab)

		####### tabs generated #######


		####### generate content ######

		main_rows = []

		# options tab
		if not edit_policy and edit_options and tabbing.is_options(tab):
			self.option_checkboxes={}
			row=[]
			col=tablecol("",{'type':'tab_layout'},{"obs":[header(_('Option'),{"type":"4"},{})]})
			row.append(tablerow("",{},{"obs":[col]}))

			for name, option in module.options.items():
				if self.object.options:
					value = '1'
					if not name in self.object.options:
						value = ''
				else:
					value = ''
				attr = {}
				if ( not add and not option.editable ) or option.disabled:
					attr[ 'passive' ] = 'true'
				if ( add and not option.default ) or option.disabled:
					value == ''

				self.option_button = button('go',{},{'helptext':_('go ahead')})
				self.option_checkboxes[name] = question_bool(option.short_description, attr,{'helptext': option.short_description, 'usertext': value, 'button': self.option_button})

				col=tablecol("",{'type':'tab_layout'},{"obs":[self.option_checkboxes[name]]})
				row.append(tablerow("",{},{"obs":[col]}))

			main_rows.append(tablerow("",{},{"obs":[tablecol("",{},{"obs":[table("",{},{"obs":row})]})]}))

		# policy selection tab (for containers only)
		elif not edit_policy and not multiedit and tabbing.is_policy_selection(tab):
			self.policy_edit_buttons={}
			self.policy_disconnect_boxes={}
			rows=[]
			cols=[]

			nbhead=header(_("Available Policy Types:"), {'type': '4'}, {})
			cols.append(tablecol("",{},{"obs":[nbhead]}))
			rows.append(tablerow("",{},{"obs":[
				tablecol("",{"colspan":"6",'type':'policy_layout'},{"obs":[
					table("",{},{"obs":[
						tablerow("",{},{"obs":cols})
					]})
				]})
			]}))

			rows_borderless=[]

			cols=[]
			cols.append(tablecol("",{'type':'policy_left'},{"obs":[header(_("Policy Type"),{"type":"6"},{})]}))
			cols.append(tablecol("",{'type':'policy_middle'},{"obs":[header(_("Location"),{"type":"6"},{})]}))
			cols.append(tablecol("",{'type':'policy_right'},{"obs":[header(_("Disconnect"),{"type":"6"},{})]}))
			rows_borderless.append(tablerow("",{},{"obs": cols}))

			firstrow=1
			for policies_group in univention.admin.modules.policies():
				if firstrow:
					firstrow=0
				else:
					rows_borderless.append(tablerow("",{},{"obs":[
						tablecol("",{'colspan':'3', },{"obs":[
						space('',{'size':'1'},{})
						]})
						]}))
				# Sort according to short_description...
				sorting_helper_list=[]
				sorting_helper_dict={}
				for n in range(len(policies_group.members)):
					policy_module=univention.admin.modules.get(policies_group.members[n])
					name=univention.admin.modules.short_description(policy_module)
					sorting_helper_list.append(name)
					sorting_helper_dict[name]=n
				sorting_helper_list.sort()

				sorted_type=[]
				for helper in sorting_helper_list:
					sorted_type.append(policies_group.members[sorting_helper_dict[helper]])

				# Now display...
				for policy_type in sorted_type:
					cols=[]

					policy_module=univention.admin.modules.get(policy_type)
					name=univention.admin.modules.short_description(policy_module)

					if name.find(":") > 0:
						name = name[name.find(":")+2:]

					icon_path = unimodule.selectIconByName( policy_type )

					policy_edit_button=button(name,{'icon':icon_path},{"helptext":_("edit policy object")})
					cols.append(tablecol('',{'type':'policy_left'}, {'obs': [policy_edit_button]}))

					self.policy_edit_buttons[policy_type]=policy_edit_button

					connected_policy='inherited'
					for pdn in self.object.policies:
						try:
							if univention.admin.modules.recognize(policy_module, pdn, self.lo.get(pdn)):
								connected_policy=pdn
								break
						except:
							pass
					if not connected_policy == 'inherited':
						policypos=univention.admin.uldap.position(self.position.getBase())
						try:
							policypos.setDn(connected_policy)
						except:
							continue
						connected_policy=policypos.getPrintable(long=1, trailingslash=0)
						if connected_policy.find(":") > 0:
							connected_policy = connected_policy[connected_policy.find(":")+1:]
						cols.append(tablecol('',{'type':'policy_middle'}, {'obs': [
							text('',{},{'text':[connected_policy]})
							]}))
						self.policy_disconnect_boxes[policy_type]=question_bool('',{},{'helptext':_('select %s for disconnection') % name})
						cols.append(tablecol('',{'type':'policy_right'}, {'obs': [self.policy_disconnect_boxes[policy_type]]}))
					else:
						cols.append(tablecol('',{'type':'policy_middle'}, {'obs': [
							text('',{},{'text':[_('inherited')]})
							]}))
						cols.append(tablecol('',{'type':'policy_right'}, {'obs': [
							text('',{},{'text':[""]})
						]}))

					rows_borderless.append(tablerow("",{},{"obs":cols}))

			self.policy_disconnect_button=button(_("Disconnect"),{'icon':'/style/remove.gif'},{"helptext":_("Disconnect selected policies")})
			rows_borderless.append(tablerow("",{},{"obs":[
				tablecol("",{"colspan":"2"},{"obs":[
				htmltext('',{},{'htmltext':[""]})
				]}),
				tablecol("",{"colspan":"2"},{"obs":[
					self.policy_disconnect_button
				]})
			]}))

			rows.append(tablerow("",{},{"obs":[
				tablecol("",{'type':'policy_layout'},{"obs":[
					table("",{},{"obs":rows_borderless})
				]})
			]}))

			main_rows.append(tablerow("",{},{"obs":[tablecol("",{'type':'content_main'},{"obs":[table("",{},{"obs":rows})]})]}))

		# module and policy tabs
		else:
			rows=[]
			cols=[]

			# tab heading
			if edit_policy:
				if not add:
					dncomponents=univention.admin.uldap.explodeDn(self.object.dn,1)
					nbhead=header(_("%s for Container %s") % (univention.admin.modules.policy_short_description(current_module), dncomponents[0]), {'type': '4'}, {})
				else:
					nbhead=header(_("%s for new Container") % (univention.admin.modules.policy_short_description(current_module)), {'type': '4'}, {})
			else:
				nbhead = header(tabbing.long_description(tab), {'type': '4'}, {})
			cols.append(tablecol("",{'type':'tab_description'},{"obs":[nbhead]}))

			current_object=self.object
			if not current_module == module:
				policydn_preselect=self.save.get('edit_policydn_preselect')
				current_policydn_selected=None
				reset=0
				if policydn_preselect:
					current_policydn_selected=policydn_preselect.get(univention.admin.modules.name(current_module), None)
					if current_policydn_selected == "inherited":
						reset=1

					if current_policydn_selected:
						policydn_preselect[univention.admin.modules.name(current_module)]=None
						self.save.put('edit_policydn_preselect',policydn_preselect)

				current_policydn_selected='inherited'
				for pdn in self.object.policies:
					try:
						if univention.admin.modules.recognize(current_module, pdn, self.lo.get(pdn)):
							current_policydn_selected=pdn
							break
					except:
						pass

				current_object=self.object.loadPolicyObject(univention.admin.modules.name(current_module), reset=reset)
				self.save.put('edit_object', self.object)

				# policy select box
				pathlist=[]

				# receive path info from 'cn=directory,cn=univention,<current domain>' object
				pathResult = self.lo.get('cn=directory,cn=univention,'+self.position.getDomain())
				if not pathResult:
					pathResult = self.lo.get('cn=default containers,cn=univention,'+self.position.getDomain())
				infoattr="univentionPolicyObject"
				if pathResult.has_key(infoattr) and pathResult[infoattr]:
					for i in pathResult[infoattr]:
						try:
							self.lo.searchDn(base=i, scope='base')
							pathlist.append(i)
						except:
							pass

				policydnlist=[]
				for i in pathlist:
					try:
						policydns=self.lo.searchDn(base=i, scope="domain")
						for policydn in policydns:
							if univention.admin.modules.recognize(current_module, policydn, self.lo.get(policydn)):
								if not policydn in policydnlist: # if containers and their subcontainers are in pathlist we get results twice
									policydnlist.append(policydn)
							else:
								pass
					except:
						pass

				displaypolicydnlist=[]
				if policydnlist:
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "modedit policydnlist %s" % (policydnlist))
					# temporary position object
					policypos=univention.admin.uldap.position(position.getBase())

					for policydn in policydnlist:
						policypos.setDn(policydn)
						displaypolicydnlist.append({"name":policypos.getDn(),"description":policypos.getPrintable(long=1, trailingslash=0)})
					displaypolicydnlist.sort()
					for item in displaypolicydnlist:
						if item['name'] == current_policydn_selected:
							item['selected']='1'

				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "modedit displaypolicydnlist %s" % (displaypolicydnlist))
				displaypolicydnlist.insert(0, {"name":"inherited", "description":_("inherited")})
				if current_policydn_selected=='inherited':
					displaypolicydnlist[0]['selected']='1'
				self.policydn_select_button=button(_("apply"),{'icon':'/style/ok.gif'},{"helptext":""})
				self.policydn_select=question_select(_("Select Configuration:"),{},{"helptext":_("Choose a configuration for your object"),"choicelist":displaypolicydnlist,"button":self.policydn_select_button})

				cols.append(tablecol('',{'type':'tab_layout'},{'obs':[self.policydn_select]}))

			rows.append(tablerow("",{},{"obs":[
				tablecol("",{"colspan":"6"},{"obs":[
					table("",{'type':'policy_choice'},{"obs":[
						tablerow("",{},{"obs":cols})
					]})
				]})
			]}))

			# compare functions to sort dictionairies
			def compare_dicts_by_attr(attr):
				def compare_dicts(dict1,dict2):
					if attr in dict1.keys() and attr in dict2.keys():
						return cmp(dict1[attr],dict2[attr])
					else:
						return cmp(dict1,dict2)
				return compare_dicts

			def compare_dicts_by_two_attr(attr1,attr2):
				def compare_dicts(dict1,dict2):
					if attr1 in dict1.keys() and attr1 in dict2.keys():
						if dict1[attr1] == dict2[attr1] and attr2 in dict1.keys() and attr2 in dict2.keys():
							return cmp(dict1[attr2],dict2[attr2])
						else:
							return cmp(dict1[attr1],dict2[attr1])
					elif attr2 in dict1.keys() and attr2 in dict2.keys():
						return cmp(dict1[attr2],dict2[attr2])
					else:
						return cmp(dict1,dict2)
				return compare_dicts

			def split_dns_line( entry ):
				ip = entry.split( ' ' )[ -1 ]
				if is_ip ( ip ):
					zone = ldap.explode_rdn(string.join( entry.split( ' ' )[ :-1 ], ' ' ),1)[0]
					return ( zone, ip )
				else:
					if current_object.info.has_key( 'ip' ) and len( current_object[ 'ip' ] ) == 1:
						zone = ldap.explode_rdn( entry, 1 )[ 0 ]
						return ( zone, current_object[ 'ip' ][ 0 ] )
				return ( None, None )

			def is_mac( mac ):
				_re = re.compile( '^[ 0-9a-fA-F ][ 0-9a-fA-F ]??$' )
				m = mac.split( ':' )
				if len( m) == 6:
					for i in range(0,6):
						if not _re.match( m[ i ] ):
							return False
					return True
				return False

			def split_dhcp_line( entry ):
				mac = entry.split( ' ' )[ -1 ]
				if is_mac ( mac ):
					ip = entry.split( ' ' )[ -2 ]
					if is_ip ( ip ):
						zone = ldap.explode_rdn(string.join( entry.split( ' ' )[ :-2 ], ' ' ),1)[0]
						return ( zone, ip, mac )
					else:
						if current_object.info.has_key( 'ip' ) and len( current_object[ 'ip' ] ) == 1:
							zone = ldap.explode_rdn(string.join( entry.split( ' ' )[ :-1 ], ' ' ),1)[0]
							return ( zone, current_object[ 'ip' ][ 0 ], mac )
						zone = ldap.explode_rdn(string.join( entry.split( ' ' )[ :-1 ], ' ' ),1)[0]
						return ( zone, None, mac )
				else:
					if current_object.info.has_key( 'ip' ) and len( current_object[ 'ip' ] ) == 1:
						ip = current_object[ 'ip' ][ 0 ]
					else:
						 ip = None
					if current_object.info.has_key( 'mac' ) and len( current_object[ 'mac' ] ) == 1:
						mac = current_object[ 'mac' ][ 0 ]
					else:
						 mac = None

					zone = ldap.explode_rdn(entry,1)[0]

					return ( zone, ip, mac )

			def is_ip( ip ):
				_re = re.compile( '^[ 0-9 ]+\.[ 0-9 ]+\.[ 0-9 ]+\.[ 0-9 ]+$' )
				if _re.match ( ip ):
					return True
				return False

			# check options of the current object
			check_options = make_options_check(current_object)

			layout = copy.deepcopy(tabbing.fields(tab))
			newlayout=[]
			temp=[]

			for row in layout: #rearange layout to fit structure of php input
				newrow=[]
				for col in row: #find rowspan multiplicator
					if not isinstance(col,types.ListType):
						newrow.append([col])
					else:
						newrow.append(col)
				temp.append(newrow)

			for row in temp:
				mult=1
				mults=[]
				for col in row:
					collength=len(col)
					if collength not in mults:
						mult=mult*collength
						mults.append(collength)
				for col in row: #find rowspan for columns
					collength=len(col)
					if collength>1:
						for subcol in col:
							subcol.rowspan=unicode(divmod(mult,collength)[0])
					elif collength>0:
						col[0].rowspan=unicode(mult)
				notDone=1
				while notDone:
					newrow=[]
					for col in row:
						notDone=0
						if len(col)>0:
							newrow.append(col[0])
							del(col[0])
							notDone=1
					newlayout.append(newrow)

			for fields in newlayout:
				cols=[]
				for field in fields:
					colspan=0
					rowspan=0
					if field.colspan:
						colspan=field.colspan
					if field.rowspan:
						rowspan=field.rowspan

					if field.hide_in_resultmode and (edit_policy or not tabbing.is_module_tab(tab)):
						continue
					elif field.hide_in_normalmode and (not edit_policy or tabbing.is_module_tab(tab)):
						continue

					name=field.property
					if name:
						property=current_module.property_descriptions[name]
						if property:
							syntax=property.syntax
					attributes={}
					if field.width:
						attributes['width']=unicode(field.width)

					if invalid_values.has_key(name):
						value=invalid_values[name]
						attributes['warning']='1'

					# not in options
					elif not multiedit and check_options(property.options):
						value=''
						attributes['passive']='true'

					else:
						value=current_object[name]

					# check if property can be changed
					if not property.may_change and not add or univention.admin.objects.fixedAttribute(current_object, name) \
					   or univention.admin.objects.emptyAttribute(current_object, name) or not property.editable:
						# disable input field (not editable; displayed in grey)
						attributes['passive']='true'

					if not add and multiedit and (property.identifies or property.unique):
						attributes['passive']='true'

					# edit only the first value of multi-value property

					if univention.admin.modules.name(current_module) == 'users/user':
						univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'lastname: %s' % current_object.info.get( 'lastname', '' ) )
						univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'description: %s' % current_object.info.get( 'description', '' ) )
					# select a way to build out contens
					if property.multivalue and field.first_only:
						if value:
							first_value=value[0]
						else:
							first_value=''
						self.finput[name]=question_property('',attributes,{'property': property, 'field': field, 'value': first_value, 'name': name, 'lo': self.lo})
						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [\
									self.finput[name]\
							]}))

					elif property.syntax.name == 'dnsEntry':
						dns_entry_choicelist = []

						self.minput[name]=[]
						self.xinput[name]=[]
						minput_rows=[]

						atts=copy.deepcopy(attributes)

						mvaluelist=[]
						i=0

						if name:
							domainPos=univention.admin.uldap.position(position.getDomain())
							dnsZone=self.lo.searchDn('(&(objectClass=dnsZone)(relativeDomainName=@)(!(zoneName=*.in-addr.arpa)))', base=domainPos.getBase(), scope='domain')

							if self.save.get('x_choice_value_of_%s'%name,'') == '':
								self.save.put('x_choice_value_of_%s'%name, 'None' )

							if dnsZone:
								groups=dnsZone
								groups+=self.lo.searchDn(base=dnsZone[0],filter='(!(objectClass=dnsZone))')

								tmppos=univention.admin.uldap.position(position.getDomain())


								oldlevel=''
								item=0
								found = False
								i = 0
								for group in groups:
									tmppos.setDn(group)
									(displaypos,displaydepth)=tmppos.getPrintable_depth()
									if not unicode(displaydepth) == oldlevel:
										item+=1
									oldlevel=unicode(displaydepth)
									dns_entry_choicelist.append({'item':item,"level":unicode(displaydepth),"name":group,"description":displaypos})
									i = i + 1
									if self.save.get('x_choice_value_of_%s'%name) == group:
										dns_entry_choicelist[-1]['selected']='1'
										found = True
								if not found:
									if i > 0:
										self.save.put('x_choice_value_of_%s'%name, dns_entry_choicelist[0][ 'name' ])

								dns_entry_choicelist.sort(compare_dicts_by_two_attr('item','description'))

								atts=copy.deepcopy(attributes)

							if value:
								i = 0
								for v in value:
									vstr =  syntax.tostring(v)

									zone, ip = split_dns_line( vstr )
									if zone and ip:
										mvaluelist.append({'name': unicode(i), 'description': '%s&nbsp;&nbsp;&nbsp;%s' % ( zone, ip ) } )
										i+=1
									elif zone:
										mvaluelist.append({'name': unicode(i), 'description': '%s' % ( zone ) } )
										i+=1
									else:
										univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'Multiip: failed to decode the line: "%s"' % vstr )

							update_choices=button('lmanusel',{},{'helptext':_('Select the DNS Forward Zone')})
							self.xinput[name].append(update_choices)
							self.xinput[name].append(question_select(property.short_description,atts,
																{'choicelist':dns_entry_choicelist,'helptext':_('Select the DNS Forward Zone object'),
																'button':update_choices}))

							ip_choicelist = []
							if current_object.info.has_key( 'ip' ):
								for ip in current_object[ 'ip' ]:
									ip_choicelist.append( { 'name': ip, 'description': ip } )

							atts=copy.deepcopy(attributes)
							b_atts=copy.deepcopy(attributes)
							b2_atts=copy.deepcopy(attributes)
							ip_atts=copy.deepcopy(attributes)

							self.minput[name].append(question_select( 'IP Address' ,ip_atts,{'choicelist':ip_choicelist,'width': 10, 'helptext':_('Select the IP address')}))
							# [1]: add button
							self.minput[name].append(get_addbutton(b_atts,_("Add %s") % name))
							# [2]: mselect list widget
							self.minput[name].append(question_mselect(_("Entries:"),atts,{"helptext":_("Current entries for '%s'") % name,"choicelist":mvaluelist}))
							# [3]: remove button
							self.minput[name].append(get_removebutton(b_atts,_("Remove selected '%s' entrie(s) from list") % name))

							# move buttons:
							# [4]: up button [ ^ ]
							self.minput[name].append(get_upbutton(b2_atts,_("Move upwards")))
							# [5]: down button [ v ]
							self.minput[name].append(get_downbutton(b2_atts,_("Move downwards")))

							# put the widgets/buttons from minput[name] into a table
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'rowspan':'2'}, {'obs': [\
											#input field
											self.xinput[name][1],\
											self.minput[name][0],\
										]}),\
										tablecol('',{}, {'obs': [\
											# needed freespace
											htmltext("",{},{'htmltext':['&nbsp;']})
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'type':'multi_add_top'}, {'obs': [\
											#add button
											self.minput[name][1]\
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablerow("",{},{"obs":[\
											tablecol('',{'rowspan':'3'}, {'obs': [\
												#mselect list
												self.minput[name][2]\
											]}),\
											tablecol('',{'type':'multi_remove'}, {'obs': [\
												#up button
												self.minput[name][4]\
											]})\
										]}),\
										tablerow("",{},{"obs":[\
											tablecol('',{'type':'multi_remove'}, {'obs': [\
												#remove button
												self.minput[name][3]\
											]})\
										]}),\
										tablerow("",{},{"obs":[\
											tablecol('',{'type':'multi_remove_img'}, {'obs': [\
												#down button
												self.minput[name][5]\
											]})\
										]})\
									]}))
						else:
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
										]}),\
										tablecol('',{}, {'obs': [\
										]})\
									]}))
						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [table("",{'type':'multi'},{"obs":minput_rows})]}))
					elif property.syntax.name == 'dnsEntryReverse':
						dns_entry_reverse_choicelist=[]

						self.minput[name]=[]
						self.xinput[name]=[]
						minput_rows=[]

						atts=copy.deepcopy(attributes)

						mvaluelist=[]
						i=0

						if name:
							domainPos=univention.admin.uldap.position(position.getDomain())
							dnsZone=self.lo.searchDn('(&(objectClass=dNSZone)(relativeDomainName=@)(zoneName=*.in-addr.arpa))', base=domainPos.getBase(), scope='domain')

							if self.save.get('x_choice_value_of_%s'%name,'') == '':
								self.save.put('x_choice_value_of_%s'%name, 'None' )
							if dnsZone:
								groups=dnsZone
								groups+=self.lo.searchDn(base=dnsZone[0],filter='(!(objectClass=dnsZone))')

								tmppos=univention.admin.uldap.position(position.getDomain())

								oldlevel=''
								item=0
								found = False
								i = 0
								for group in groups:
									tmppos.setDn(group)
									(displaypos,displaydepth)=tmppos.getPrintable_depth()
									if not unicode(displaydepth) == oldlevel:
										item+=1
									oldlevel=unicode(displaydepth)
									dns_entry_reverse_choicelist.append({'item':item,"level":unicode(displaydepth),"name":group,"description":displaypos})
									i = i + 1
									if self.save.get('x_choice_value_of_%s'%name) == group:
										dns_entry_reverse_choicelist[-1]['selected']='1'
										found = True
								if not found:
									if i > 0:
										self.save.put('x_choice_value_of_%s'%name, dns_entry_reverse_choicelist[ 0 ][ 'name' ] )

								dns_entry_reverse_choicelist.sort(compare_dicts_by_two_attr('item','description'))

								atts=copy.deepcopy(attributes)

							if value:
								i = 0
								for v in value:
									vstr =  syntax.tostring(v)
									zone, ip = split_dns_line( vstr )
									if zone and ip:
										mvaluelist.append({'name': unicode(i), 'description': '%s&nbsp;&nbsp;&nbsp;%s' % ( zone, ip ) } )
										i+=1
									elif zone:
										mvaluelist.append({'name': unicode(i), 'description': '%s' % ( zone ) } )
										i+=1


							update_choices=button('lmanusel',{},{'helptext':_('Select the DNS Forward Zone')})
							self.xinput[name].append(update_choices)
							self.xinput[name].append(question_select(property.short_description,atts,
																{'choicelist':dns_entry_reverse_choicelist,'helptext':_('Select the DNS Forward Zone object'),
																'button':update_choices}))

							ip_choicelist = []
							if current_object.info.has_key( 'ip' ):
								for ip in current_object[ 'ip' ]:
									ip_choicelist.append( { 'name': ip, 'description': ip } )

							atts=copy.deepcopy(attributes)
							b_atts=copy.deepcopy(attributes)
							b2_atts=copy.deepcopy(attributes)
							ip_atts=copy.deepcopy(attributes)

							self.minput[name].append(question_select( 'IP Address' ,ip_atts,{'choicelist':ip_choicelist,'width': 10, 'helptext':_('Select the IP address')}))
							# [1]: add button
							self.minput[name].append(get_addbutton(b_atts,_("Add %s") % name))
							# [2]: mselect list widget
							self.minput[name].append(question_mselect(_("Entries:"),atts,{"helptext":_("Current entries for '%s'") % name,"choicelist":mvaluelist}))
							# [3]: remove button
							self.minput[name].append(get_removebutton(b_atts,_("Remove selected '%s' entrie(s) from list") % name))

							# move buttons:
							# [4]: up button [ ^ ]
							self.minput[name].append(get_upbutton(b2_atts,_("Move upwards")))
							# [5]: down button [ v ]
							self.minput[name].append(get_downbutton(b2_atts,_("Move downwards")))

							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'rowspan':'2'}, {'obs': [\
											#input field
											self.xinput[name][1],\
											self.minput[name][0],\
										]}),\
										tablecol('',{}, {'obs': [\
											# needed freespace
											htmltext("",{},{'htmltext':['&nbsp;']})
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'type':'multi_add_top'}, {'obs': [\
											#add button
											self.minput[name][1]\
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablerow("",{},{"obs":[\
											tablecol('',{'rowspan':'3'}, {'obs': [\
												#mselect list
												self.minput[name][2]\
											]}),\
											tablecol('',{'type':'multi_remove'}, {'obs': [\
												#up button
												self.minput[name][4]\
											]})\
										]}),\
										tablerow("",{},{"obs":[\
											tablecol('',{'type':'multi_remove'}, {'obs': [\
												#remove button
												self.minput[name][3]\
											]})\
										]}),\
										tablerow("",{},{"obs":[\
											tablecol('',{'type':'multi_remove_img'}, {'obs': [\
												#down button
												self.minput[name][5]\
											]})\
										]})\
									]}))
						else:
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
										]}),\
										tablecol('',{}, {'obs': [\
										]})\
									]}))
						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [table("",{'type':'multi'},{"obs":minput_rows})]}))

					elif property.syntax.name == 'dhcpEntry':
						primary_group_choicelist=[]

						foundDns=self.lo.searchDn('(|(objectClass=univentionDhcpService)(objectClass=dhcpService))', base=position.getDomain(), scope='domain')

						if name:
							dhcpServices=[]
							for j in foundDns:
								dhcpServices.append(j)
								searchResult=self.lo.searchDn('(|(objectClass=organizationalRole)(objectClass=organizationalUnit))', base=j, scope='domain')
								for i in searchResult:
									search_base=i
									sResult=''
									while search_base != j:
										b=ldap.explode_dn(search_base)[1:]
										search_base=string.join(b,',')
										if search_base == j:
											sResult='1'
											break
										sResult=self.lo.searchDn('(|(objectClass=organizationalRole)(objectClass=organizationalUnit))', base=search_base, scope='base')
										if not sResult:
											univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "dhcpService Path:  irgnore %s" % i )
											break

									if sResult:
										dhcpServices.append(i)


							if dhcpServices:
								groups=dhcpServices

								tmppos=univention.admin.uldap.position(position.getDomain())

								oldlevel=''
								item=0
								i = 0
								found = False
								for group in groups:
									tmppos.setDn(group)
									(displaypos,displaydepth)=tmppos.getPrintable_depth()
									if not oldlevel == unicode(displaydepth):
										item+=1
									oldlevel=unicode(displaydepth)

									primary_group_choicelist.append({"name":group,"description":displaypos})
									i = i + 1

									if self.save.get('x_choice_value_of_%s'%name) == group:
										primary_group_choicelist[-1]['selected']='1'
										found = True


								if not found:
									if i > 0:
										self.save.put('x_choice_value_of_%s'%name, primary_group_choicelist[0][ 'name' ])

								atts=copy.deepcopy(attributes)

							self.minput[name]=[]
							self.xinput[name]=[]
							self.zinput[name]=[]
							minput_rows=[]

							atts=copy.deepcopy(attributes)

							mvaluelist=[]
							i=0

							if value:
								for v in value:
									vstr =  syntax.tostring(v)
									zone, ip, mac = split_dhcp_line( vstr )
									if zone:
										line = "%s" % zone
										if ip:
											line = "%s&nbsp;&nbsp;&nbsp;%s" % ( line, ip )
										if mac:
											line = "%s&nbsp;&nbsp;&nbsp;%s" % ( line, mac )
										mvaluelist.append({'name': unicode(i), 'description': line } )
										i+=1

							update_choices=button('lmanusel',{},{'helptext':_('Select the DHCP Zone')})
							self.xinput[name].append(update_choices)
							self.xinput[name].append(question_select(property.short_description,atts,
																{'choicelist':primary_group_choicelist,'helptext':_('Select the DHCP Zone object'),
																'button':update_choices}))

							ip_choicelist = []
							if current_object.info.has_key( 'ip' ):
								for ip in current_object[ 'ip' ]:
									ip_choicelist.append( { 'name': ip, 'description': ip } )

							atts=copy.deepcopy(attributes)
							b_atts=copy.deepcopy(attributes)
							b2_atts=copy.deepcopy(attributes)
							ip_atts=copy.deepcopy(attributes)
							mac_atts=copy.deepcopy(attributes)

							self.minput[name].append(question_select( 'IP Address' ,ip_atts,{'choicelist':ip_choicelist,'helptext':_('Select the IP address')}))
							# [1]: add button
							self.minput[name].append(get_addbutton(b_atts,_("Add %s") % name))
							# [2]: mselect list widget
							self.minput[name].append(question_mselect(_("Entries:"),atts,{"helptext":_("Current entries for '%s'") % name,"choicelist":mvaluelist}))
							# [3]: remove button
							self.minput[name].append(get_removebutton(b_atts,_("Remove selected '%s' entrie(s) from list") % name))

							# move buttons:
							# [4]: up button [ ^ ]
							self.minput[name].append(get_upbutton(b2_atts,_("Move upwards")))
							# [5]: down button [ v ]
							self.minput[name].append(get_downbutton(b2_atts,_("Move downwards")))

							i = 0
							mac_choicelist = []
							found = False
							if current_object.info.has_key( 'mac' ):
								for mac in current_object[ 'mac' ]:
									mac_choicelist.append( { 'name': mac, 'description': mac } )
									i = i + 1
									if self.save.get('z_choice_value_of_%s'%name) == mac:
										mac_choicelist[-1]['selected']='1'
										found = True
								if not found:
									if i > 0:
										self.save.put('z_choice_value_of_%s'%name, mac_choicelist[0]['name' ] )

							update_choices2=button('lmanusel',{},{'helptext':_('Select a MAC Address')})
							self.zinput[name].append(update_choices2)
							self.zinput[name].append(question_select('MAC Address', mac_atts,
																{'choicelist':mac_choicelist,'helptext':_('Select a MAC Address'),
																'button':update_choices2}))
							# put the widgets/buttons from minput[name] into a table
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'rowspan':'2'}, {'obs': [\
											#input field
											self.xinput[name][1],\
											self.zinput[name][1],\
											self.minput[name][0],\
										]}),\
										tablecol('',{}, {'obs': [\
											# needed freespace
											htmltext("",{},{'htmltext':['&nbsp;']})
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'type':'multi_add_top'}, {'obs': [\
											#add button
											self.minput[name][1]\
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablerow("",{},{"obs":[\
											tablecol('',{'rowspan':'3'}, {'obs': [\
												#mselect list
												self.minput[name][2]\
											]}),\
											tablecol('',{'type':'multi_remove'}, {'obs': [\
												#up button
												self.minput[name][4]\
											]})\
										]}),\
										tablerow("",{},{"obs":[\
											tablecol('',{'type':'multi_remove'}, {'obs': [\
												#remove button
												self.minput[name][3]\
											]})\
										]}),\
										tablerow("",{},{"obs":[\
											tablecol('',{'type':'multi_remove_img'}, {'obs': [\
												#down button
												self.minput[name][5]\
											]})\
										]})\
									]}))
						else:
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
										]}),\
										tablecol('',{}, {'obs': [\
										]})\
									]}))
						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [table("",{'type':'multi'},{"obs":minput_rows})]}))

					elif property.syntax.name == 'dnsEntryNetwork':
						primary_group_choicelist=[]

						domainPos=univention.admin.uldap.position(position.getDomain())
						dnsZone=self.lo.searchDn('(&(objectClass=dnsZone)(relativeDomainName=@)(!(zoneName=*.in-addr.arpa)))', base=domainPos.getBase(), scope='domain')

						if dnsZone:
							groups=dnsZone
							groups+=self.lo.searchDn(base=dnsZone[0],filter='(!(objectClass=dnsZone))')

							tmppos=univention.admin.uldap.position(position.getDomain())

							primary_group_choicelist.append({'item':-1,'name': 'None', 'description': _('None')})

							oldlevel=''
							item=0
							for group in groups:
								tmppos.setDn(group)
								(displaypos,displaydepth)=tmppos.getPrintable_depth()
								if not unicode(displaydepth) == oldlevel:
									item+=1
								oldlevel=unicode(displaydepth)
								primary_group_choicelist.append({'item':item,"level":unicode(displaydepth),"name":group,"description":displaypos})
								if group == value:
									primary_group_choicelist[-1]['selected']='1'

							primary_group_choicelist.sort(compare_dicts_by_two_attr('item','description'))

							atts=copy.deepcopy(attributes)
							primary_group_select=question_select(property.syntax.description,atts,{'choicelist':primary_group_choicelist,'helptext':_('select forward lookup zone')})
							cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [\
										primary_group_select\
								]}))

							self.pinput[name]=primary_group_select
					elif property.syntax.name == 'dnsEntryReverseNetwork':
						dns_entry_reverse_choicelist=[]

						domainPos=univention.admin.uldap.position(position.getDomain())
						dnsZone=self.lo.searchDn('(&(objectClass=dNSZone)(relativeDomainName=@)(zoneName=*.in-addr.arpa))', base=domainPos.getBase(), scope='domain')

						if dnsZone:
							groups=dnsZone
							groups+=self.lo.searchDn(base=dnsZone[0],filter='(!(objectClass=dnsZone))')

							tmppos=univention.admin.uldap.position(position.getDomain())

							dns_entry_reverse_choicelist.append({'item':-1,'name': 'None', 'description': _('None')})
							dns_entry_reverse_choicelist[-1]['selected']='1'

							oldlevel=''
							item=0
							for group in groups:
								tmppos.setDn(group)
								(displaypos,displaydepth)=tmppos.getPrintable_depth()
								if not unicode(displaydepth) == oldlevel:
									item+=1
								oldlevel=unicode(displaydepth)
								dns_entry_reverse_choicelist.append({'item':item,"level":unicode(displaydepth),"name":group,"description":displaypos})
								if group == value:
									dns_entry_reverse_choicelist[-1]['selected']='1'

							dns_entry_reverse_choicelist.sort(compare_dicts_by_two_attr('item','description'))

							atts=copy.deepcopy(attributes)
							dns_entry_reverse_select=question_select(property.syntax.description,atts,{'choicelist':dns_entry_reverse_choicelist,'helptext':_('select reverse lookup zone')})
							cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [\
										dns_entry_reverse_select\
								]}))

							self.rinput[name]=dns_entry_reverse_select
					elif property.syntax.name == 'dhcpEntryNetwork':
						primary_group_choicelist=[]

						foundDns=self.lo.searchDn('(|(objectClass=univentionDhcpService)(objectClass=dhcpService))', base=position.getDomain(), scope='domain')

						dhcpServices=[]
						for j in foundDns:
							dhcpServices.append(j)
							searchResult=self.lo.searchDn('(|(objectClass=organizationalRole)(objectClass=organizationalUnit))', base=j, scope='domain')
							for i in searchResult:
								search_base=i
								sResult=''
								while search_base != j:
									b=ldap.explode_dn(search_base)[1:]
									search_base=string.join(b,',')
									if search_base == j:
										sResult='1'
										break
									sResult=self.lo.searchDn('(|(objectClass=organizationalRole)(objectClass=organizationalUnit))', base=search_base, scope='base')
									if not sResult:
										univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "dhcpService Path:  irgnore %s" % i )
										break

								if sResult:
									dhcpServices.append(i)

						if dhcpServices:
							groups=dhcpServices

							tmppos=univention.admin.uldap.position(position.getDomain())

							primary_group_choicelist.append({'item':-1,'name': 'None', 'description': _('None')})
							primary_group_choicelist[-1]['selected']='1'

							oldlevel=''
							item=0
							for group in groups:
								tmppos.setDn(group)
								(displaypos,displaydepth)=tmppos.getPrintable_depth()
								if not oldlevel == unicode(displaydepth):
									item+=1
								oldlevel=unicode(displaydepth)
								primary_group_choicelist.append({'item':item,"level":unicode(displaydepth),"name":group,"description":displaypos})
								if group == value:
									primary_group_choicelist[-1]['selected']='1'

							primary_group_choicelist.sort(compare_dicts_by_two_attr('item','description'))

							atts=copy.deepcopy(attributes)
							primary_group_select=question_select(property.syntax.description,atts,{'choicelist':primary_group_choicelist,'helptext':_('select attribute')})
							cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [\
										primary_group_select\
								]}))

							self.pinput[name]=primary_group_select
						else:
							primary_group_choicelist.append({'name': 'None', 'description': _('None')})
							primary_group_choicelist[-1]['selected']='1'

							atts=copy.deepcopy(attributes)
							primary_group_select=question_select(property.syntax.description,atts,{'choicelist':primary_group_choicelist,'helptext':_('select attribute')})
							cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [\
										primary_group_select\
								]}))

							self.pinput[name]=primary_group_select

					elif property.syntax.name == 'primaryGroup':
						primary_group_choicelist=[]

						try:
							if property.syntax.searchFilter:
								groups=self.lo.searchDn(property.syntax.searchFilter, base=position.getDomain(), scope='domain')
						except:
							if self.object.has_key('groups'):
								groups=self.object['groups']
							else:
								groups=""

						for group in groups:
							primary_group_choicelist.append({'name': group, 'description': univention.admin.uldap.explodeDn(group, 1)[0]})
							if group == value:
								primary_group_choicelist[-1]['selected']='1'

						primary_group_choicelist.sort()

						atts=copy.deepcopy(attributes)
						primary_group_select=question_select(property.short_description,atts,{'choicelist':primary_group_choicelist,'helptext':_('select attribute')})
						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [\
									primary_group_select\
							]}))

						self.pinput[name]=primary_group_select

					elif property.syntax.name == 'groupID' or property.syntax.name == 'userID':
						too_many_results = 0
						try:
							if property.syntax.searchFilter:
								dns=self.lo.searchDn(property.syntax.searchFilter, base=position.getDomain(), scope='domain', timeout=10, sizelimit=200)
						except: #univention.admin.uexceptions.ldapError, msg: #more than 200 results, timeout or whatever
							too_many_results = 1
							dns=[]

						if not too_many_results: # Multiselect
							id_choicelist_sort={}
							dns.sort()

							id_attrib='uidNumber'
							if property.syntax.name == 'groupID':
								id_attrib='gidNumber'

							univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'modedit: ID: value is %s %s %s' % (id_attrib,value,type(value)) )
							for dn in dns:
								id=self.lo.get(dn=dn, attr=[id_attrib])[id_attrib][0]
								dict={'name': "%s"%id, 'description': univention.admin.uldap.explodeDn(dn, 1)[0]}
								if '%s'%id == value:
									dict['selected']='1'
								id_choicelist_sort[univention.admin.uldap.explodeDn(dn, 1)[0].lower()]=dict
							dict={'name': "00", 'description': "root"}
							try:
								if int('0') == int(value):
									dict['selected']='1'
							except:
								# value is not set, can happen after updates, we assume it's root then (which will be set by the listener-modules)
								dict['selected']='1'

							id_choicelist_sort['root']=dict
							keys=id_choicelist_sort.keys()
							keys.sort()
							id_choicelist=[]
							for key in keys:
								id_choicelist.append(id_choicelist_sort[key])

							atts=copy.deepcopy(attributes)
							id_select=question_select(property.short_description,atts,{'choicelist':id_choicelist,'helptext':_('select attribute')})
							self.pinput[name]=id_select
						else: # normal field
							self.userinfo_append(_("%s: Too many entries for selectbox")%property.short_description)
							if not property.short_description[-2:] == "ID":
								property.short_description=property.short_description+" ID"
							id_select=question_property('',attributes,{'property': property, 'field': field, 'value': value, 'name': name, 'lo': self.lo})
							self.input[name]=id_select
						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [id_select]}))

					elif property.syntax.name == 'genericSelect':
						generic_choicelist=[]

						tmplist=self.lo.get(dn=property.configObjectPosition+","+position.getDomain(), attr=[property.configAttributeName])
						if tmplist.has_key(property.configAttributeName):
							univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'Choices: %s ' % (unicode(tmplist)) )
							for choice in tmplist[property.configAttributeName]:
								generic_choicelist.append({'name': choice, 'description': choice})
								if choice == value:
									generic_choicelist[-1]['selected']='1'

						atts=copy.deepcopy(attributes)
						generic_select=question_select(property.short_description,atts,{'choicelist':generic_choicelist,'helptext':_('select attribute')})

						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [\
									generic_select\
							]}))

						self.pinput[name]=generic_select

					elif property.syntax.name == 'kdeProfiles':
						self.minput[name]=[]
						minput_rows=[]
						mvaluelist=[]

						atts=copy.deepcopy(attributes)

						active_profiles=self.lo.get(dn='cn=default,cn=univention,'+position.getDomain(), attr=['univentionDesktopProfile'])
						i=0
						if value:
							for v in value:
								try:
									mvaluelist.append({'name': unicode(i), 'description': syntax.tostring(v)})
								except univention.admin.uexceptions.valueInvalidSyntax, e:
									pass
								i+=1

						profiles=self.lo.get(dn='cn=default,cn=univention,'+position.getDomain(), attr=['univentionDefaultKdeProfiles'])

						b_atts = copy.deepcopy(attributes)
						b2_atts = copy.deepcopy(attributes)

						profile_choicelist=[]
						if profiles.has_key('univentionDefaultKdeProfiles'):
							for pn in profiles['univentionDefaultKdeProfiles']:
								univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, ('pn: %s' % pn))
								profile_choicelist.append({'name': pn, 'description': pn})

						if not atts.get('width'):
							atts['width']='450' # FIXME

						self.minput[name].append(question_select(property.short_description,atts,{'choicelist':profile_choicelist,'helptext':_('select profile')}))

						# UI elements for adding and removing KDE profiles from the select boxes
						# [1]: add button
						self.minput[name].append(get_addbutton(b_atts,_("Add %s") % name))
						# [2]: mselect list widget
						self.minput[name].append(question_mselect(_("Entries:"),atts,{"helptext":_("Current entries for '%s'") % name,"choicelist":mvaluelist}))
						# [3]: remove button
						self.minput[name].append(get_removebutton(b_atts,_("Remove selected '%s' entrie(s) from list") % name))
						# move buttons:
						# [4]: up button [ ^ ]
						self.minput[name].append(get_upbutton(b2_atts,_("Move upwards")))
						# [5]: down button [ v ]
						self.minput[name].append(get_downbutton(b2_atts,_("Move downwards")))


						self.pinput[name]=self.minput[name][0] #profile_select


						minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'rowspan':'2'}, {'obs': [\
											#input field
											self.minput[name][0]\
										]}),\
										tablecol('',{}, {'obs': [\
											# needed freespace
											htmltext("",{},{'htmltext':['&nbsp;']})
										]})\
									]}))
						minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'type':'multi_add_top'}, {'obs': [\
											#add button
											self.minput[name][1]\
										]})\
									]}))
						minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'rowspan':'3'}, {'obs': [\
											#mselect list
											self.minput[name][2]\
										]}),\
										tablecol('',{'type':'multi_remove'}, {'obs': [\
											#up button
											self.minput[name][4]\
										]})\
									]}))
						minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'type':'multi_remove'}, {'obs': [\
											#remove button
											self.minput[name][3]\
										]})\
									]}))
						minput_rows.append(tablerow("",{},{"obs":[\
									tablecol('',{'type':'multi_remove_img'}, {'obs': [\
										#down button
										self.minput[name][5]\
										]})\
									]}))

						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [table("",{'type':'multi'},{"obs":minput_rows})]}))

					elif property.syntax.name == 'shareHost':

						host_choicelist=[]

						host_choicelist_has_current=0
						for dn, attr in self.lo.search('(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))', attr=['objectClass', 'aRecord', 'cn']):
							# TODO: ckeck for multiple aRecord?
							if attr.has_key('aRecord') and attr['aRecord'][0]:
								res=self.lo.search('(&(objectClass=dNSZone)(aRecord=%s)(zoneName=*)(relativeDomainName=*))' % attr['aRecord'][0])
								if not res:
									if 'univentionWindows' in attr['objectClass']:
										host_choicelist.append({'name': attr['cn'][0], 'description': attr['cn'][0]})
									else:
										host_choicelist.append({'name': attr['aRecord'][0], 'description': attr['aRecord'][0]})
									continue
								fqdn = res[0][1]['relativeDomainName'][0]+'.'+res[0][1]['zoneName'][0]
								host_choicelist.append({'name': fqdn, 'description': fqdn})
								if value and fqdn in value:
									host_choicelist[-1]['selected']='1'
									host_choicelist_has_current=1
							else:
								if 'univentionWindows' in attr['objectClass']:
									host_choicelist.append({'name': attr['cn'][0], 'description': attr['cn'][0]})


						if not host_choicelist_has_current and value:
							for v in value:
								host_choicelist.append({'name': v, 'description': v, 'selected': '1'})

						host_choicelist.sort()

						atts=copy.deepcopy(attributes)
						host_select=question_select(property.short_description,atts,{'choicelist':host_choicelist,'helptext':_('select host')})
						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [\
									host_select\
							]}))

						self.pinput[name]=host_select


					elif property.syntax.name == "binaryfile":
						fileinput_rows=[]
						# |---------------------------------------------------------------------------------------------------|
						# |                                                                        <download/import link >    |
						# |---------------------------------------------------------------------------------------------------|
						# | <display certificate readonly >                                                                   |
						# |---------------------------------------------------------------------------------------------------|
						# | <uploadfield with searchbutton>                                                                   |
						# |---------------------------------------------------------------------------------------------------|
						# | <upload-button>                                                                                   |
						# |---------------------------------------------------------------------------------------------------|
						if name:
							if value:
								certString=base64.encodestring(string.join(value))
							else:
								certString=''
							certificate=''
							if len(certString):
								certificate='-----BEGIN CERTIFICATE-----\n%s-----END CERTIFICATE-----\n' % certString

							self.certBrowse = question_file('', {} , {"helptext":_("Select a file")})
							self.certLoadBtn = button(_("Load file"),{'icon':'/style/ok.gif'},{"helptext":_("Upload selected file")})

							self.certDeleteBtn = button(_("Delete certificate"),{'icon':'/style/cancel.gif'},{"helptext":_("Delete certificate")})

							if self.save.get('certTempFile'):
								tmpCert=('',self.save.get('certTempFile'))
							else:
								tmpCert=tempfile.mkstemp('.crt.tmp', 'univention-admin', '/tmp/webui')
							self.save.put('certTempFile',tmpCert[1])
							certFile=open(tmpCert[1],'w')
							certFile.write(certificate)
							certFile.close()

							link_vars='mime-type=application/x-x509-ca-cert&tmpFile=%s' % tmpCert[1]
							link_text=_('Download Certificate')

							linktext=' <a href="file.php?%s">%s</a>'%(link_vars,link_text)

						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [table("",{'type':'multi'},{"obs":\
										[tablerow("",{},{"obs":[\
													tablecol('',{}, {'obs': [\
														#upload field
														self.certBrowse\
													]}),\
												]}),\
										tablerow("",{},{"obs":[\
													tablecol('',{}, {'obs': [\
														# needed freespace
														htmltext("",{},{'htmltext':['&nbsp;']})
													]})\
												]}),
										tablerow("",{},{"obs":[\
													tablecol('',{}, {'obs': [\
														#upload button
														self.certLoadBtn\
													]}),\
												]})]\
										})]}))
						if len(certString):
							cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [table("",{'type':'multi'},{"obs":\
											[tablerow("",{},{"obs":[\
														tablecol('',{}, {'obs': [\
															# import link
															htmltext('',{},{'htmltext':[linktext]})\
														]}),\
													]}),\
											tablerow("",{},{"obs":[\
														tablecol('',{}, {'obs': [\
															# needed freespace
															htmltext("",{},{'htmltext':['&nbsp;']})
														]})\
													]}),
											tablerow("",{},{"obs":[\
														tablecol('',{}, {'obs': [\
															#delete button
															self.certDeleteBtn\
														]}),\
													]})]\
											})]}))


					elif property.syntax.name == 'printerServer':
						self.minput[name]=[]
						minput_rows=[]

						atts=copy.deepcopy(attributes)

						mvaluelist=[]
						i=0
						if value:
							for v in value:
								try:
									mvaluelist.append({'name': unicode(i), 'description': syntax.tostring(v)})
								except univention.admin.uexceptions.valueInvalidSyntax, e:
									pass
								i+=1

						if name:
							packages=[]

							for dn, attr in self.lo.search('(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))', attr=['objectClass', 'aRecord', 'cn']):
								if attr.has_key('aRecord') and attr['aRecord'][0]:
									res=self.lo.search('(&(objectClass=dNSZone)(aRecord=%s)(zoneName=*)(relativeDomainName=*))' % attr['aRecord'][0])
									if not res:
										continue
									fqdn = res[0][1]['relativeDomainName'][0]+'.'+res[0][1]['zoneName'][0]
									packages.append({'name': fqdn, 'description': fqdn})

							self.minput[name].append(question_select(property.short_description,atts,{'choicelist':packages,'helptext':_('select Server')}))
							# [1]: add button
							self.minput[name].append(get_addbutton(attributes,_("Add %s")))
							# [2]: mselect list widget
							self.minput[name].append(question_mselect(_("Entries:"),{},{"helptext":_("Current entries for '%s'") % name,"choicelist":mvaluelist}))
							# [3]: remove button
							self.minput[name].append(get_removebutton(attributes,_("Remove selected '%s' entrie(s) from list") % name))

							# move buttons:
							# [4]: up button [ ^ ]
							self.minput[name].append(get_upbutton(attributes,_("Move upwards")))
							# [5]: down button [ v ]
							self.minput[name].append(get_downbutton(attributes,_("Move downwards")))

							# put the widgets/buttons from minput[name] into a table
							#----------------------------------|
							#                 |                |
							#                 |----------------|
							#  <input field>  | <add button>   |
							# ---------------------------------|
							#                 | <up button>    |
							#                 |----------------|
							#                 | <remove button>|
							#  <mselect list> |----------------|
							#                 | <down button>  |
							#----------------------------------|
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'rowspan':'2'}, {'obs': [\
											#input field
											self.minput[name][0]\
										]}),\
										tablecol('',{}, {'obs': [\
											# needed freespace
											htmltext("",{},{'htmltext':['&nbsp;']})
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'type':'multi_add_top'}, {'obs': [\
											#add button
											self.minput[name][1]\
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablerow("",{},{"obs":[\
											tablecol('',{'rowspan':'3'}, {'obs': [\
												#mselect list
												self.minput[name][2]\
											]}),\
											tablecol('',{'type':'multi_remove'}, {'obs': [\
												#up button
												self.minput[name][4]\
											]})\
										]}),\
										tablerow("",{},{"obs":[\
											tablecol('',{'type':'multi_remove'}, {'obs': [\
												#remove button
												self.minput[name][3]\
											]})\
										]}),\
										tablerow("",{},{"obs":[\
											tablecol('',{'type':'multi_remove_img'}, {'obs': [\
												#down button
												self.minput[name][5]\
											]})\
										]})\
									]}))
						else:
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
										]}),\
										tablecol('',{}, {'obs': [\
										]})\
									]}))
						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [table("",{'type':'multi'},{"obs":minput_rows})]}))

					elif property.syntax.name == 'repositoryServer':

						host_choicelist=[]
						host_choicelist_has_current=0

						for dn, attr in self.lo.search('(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))', attr=['objectClass', 'aRecord', 'cn']):
							# TODO: ckeck for multiple aRecord?
							if attr.has_key('aRecord') and attr['aRecord'][0]:
								res=self.lo.search('(&(objectClass=dNSZone)(aRecord=%s)(zoneName=*)(relativeDomainName=*))' % attr['aRecord'][0])
								if not res:
									continue
								fqdn = res[0][1]['relativeDomainName'][0]+'.'+res[0][1]['zoneName'][0]
								host_choicelist.append({'name': fqdn, 'description': fqdn})
								if fqdn == value:
									host_choicelist[-1]['selected']='1'
									host_choicelist_has_current=1


						if not host_choicelist_has_current and value:
							host_choicelist.append({'name': value, 'description': value, 'selected': '1'})

						host_choicelist.sort()

						if not host_choicelist_has_current:
							host_choicelist.insert(0, {'name': "", 'description': "", 'selected': '1'})
						else:
							host_choicelist.insert(0, {'name': "", 'description': "", 'selected': '0'})


						atts=copy.deepcopy(attributes)
						host_select=question_select(property.short_description,atts,{'choicelist':host_choicelist,'helptext':_('select host')})
						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [\
									host_select\
							]}))

						self.pinput[name]=host_select
					elif property.syntax.name == 'kolabHomeServer':

						host_choicelist=[]

						host_choicelist_has_current=0
						for dn, attr in self.lo.search('(&(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))(univentionService=kolab2))', attr=['objectClass', 'aRecord', 'cn']):
							# TODO: ckeck for multiple aRecord?
							if attr.has_key('aRecord') and attr['aRecord'][0]:
								res=self.lo.search('(&(objectClass=dNSZone)(aRecord=%s)(zoneName=*)(relativeDomainName=*))' % attr['aRecord'][0])
								if not res:
									host_choicelist.append({'name': attr['aRecord'][0], 'description': attr['aRecord'][0]})
									continue
								fqdn = res[0][1]['relativeDomainName'][0]+'.'+res[0][1]['zoneName'][0]
								host_choicelist.append({'name': fqdn, 'description': fqdn})
								if fqdn == value:
									host_choicelist[-1]['selected']='1'
									host_choicelist_has_current=1

						host_choicelist.sort()

						atts=copy.deepcopy(attributes)
						host_select=question_select(property.short_description,atts,{'choicelist':host_choicelist,'helptext':_('select host')})
						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [\
									host_select\
							]}))

						self.pinput[name]=host_select

					elif property.syntax.name == 'mailDomain':

						host_choicelist=[]

						host_choicelist_has_current=0
						for dn, attr in self.lo.search('objectClass=univentionMailDomainname', attr=['cn']):
							if attr['cn'][0] == value:
								host_choicelist.append({'name': attr['cn'][0], 'description': attr['cn'][0], 'selected': '1'})
							else:
								host_choicelist.append({'name': attr['cn'][0], 'description': attr['cn'][0]})


						host_choicelist.sort()

						atts=copy.deepcopy(attributes)
						host_select=question_select(property.short_description,atts,{'choicelist':host_choicelist,'helptext':_('select host')})
						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [\
									host_select\
							]}))

						self.pinput[name]=host_select

					elif property.syntax.name == 'sharedFolderUserACL' or property.syntax.name == 'sharedFolderGroupACL':
						minput_rows=[]
						too_many_results = 0
						acls={"none": _("none"), "read": _("read"), "post": _("post"), "append": _("append"), "write": _("write"), "all": _("all")}
						# create variables if they don't exist
						try:
							x=self.sharedFolderACLAddButton
						except:
							self.sharedFolderACLUserList={}
							self.sharedFolderACLRightsList={}
							self.sharedFolderACLAddButton={}
							self.sharedFolderACLList={}
							self.sharedFolderACLRemoveButton={}
							self.sharedFolderACLRegEx={}
						self.sharedFolderACLUserName=self.save.get("sharedFolderACLUserName", "")
						self.sharedFolderACLRegEx[property.syntax.name]=property.syntax._re

						try:
							if property.syntax.searchFilter:
								users=self.lo.searchDn(property.syntax.searchFilter, base=position.getDomain(), scope='domain', timeout=10, sizelimit=200)
						except: #univention.admin.uexceptions.ldapError, msg: #more than 200 results, timeout or whatever
							too_many_results = 1



						if not too_many_results: # Multiselect
							id_choicelist_sorted={}
							users.sort()

							if property.syntax.name == 'sharedFolderUserACL':
								id_choicelist_sorted["anyone"]={'name': "anyone", "description": _("Anyone")}
								# create list of users
								for user in users:
									try:
										mailAddress=self.lo.get(dn=user, attr=['mailPrimaryAddress'])['mailPrimaryAddress'][0]
									except:
										continue
									dict={'name': "%s"%mailAddress, 'description': mailAddress}
									id_choicelist_sorted[univention.admin.uldap.explodeDn(user, 1)[0].lower()]=dict
							else:
								# create list of groups
								for user in users:
									gname = univention.admin.uldap.explodeDn(user, 1)[0]
									dict={'name': "%s"%gname, 'description': gname}
									id_choicelist_sorted[gname]=dict

							dict={}

							keys=id_choicelist_sorted.keys()
							keys.sort()
							id_choicelist=[]
							for key in keys:
								id_choicelist.append(id_choicelist_sorted[key])

							lst_user = question_select(property.short_description,{"width":"250"},{'choicelist':id_choicelist,'helptext':_('select attribute')})
							self.sharedFolderACLUserList[property.syntax.name]=lst_user
						else: # normal field
							self.userinfo_append(_("%s: Too many entries for selectbox")%property.short_description)
							if not self.sharedFolderACLUserName == "":
								warn={'warning':'1'}
							else:
								warn={}
							lst_user = question_text(property.short_description, warn, {"helptext":"", "usertext":self.sharedFolderACLUserName})
							self.sharedFolderACLUserList[property.syntax.name]=lst_user

						# input fields
						acllist=[]
						for key in acls.keys():
							acllist.append({"name": key, "description":acls[key]})

						lst_right = question_select(_("Access right"), {}, {'choicelist': acllist, 'helptext':_('select access right')})
						self.sharedFolderACLRightsList[property.syntax.name] = lst_right

						btn_add = get_addbutton(attributes,_("Add"))
						self.sharedFolderACLAddButton[property.syntax.name]=btn_add

						# field with current values
						vals=self.object[property.syntax.name]
						univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'Syntax: %s, vals: %s' % (property.syntax.name, vals))
						acl_list=[]
						for acl in vals:
							acl_trans = acl
							# find access right an translate it
							last_space = acl.rfind(" ")
							if not last_space == -1:
								right = acl[acl.rfind(" ")+1:]
								user = acl[:acl.rfind(" ")]
								try:
									acl_trans = "%s %s"%(user, acls[right])
								except:
									pass
							acl_list.append({"name": acl, "description": acl_trans})

						btn_remove=get_removebutton(attributes,_("Remove"))
						self.sharedFolderACLList[property.syntax.name] = question_mselect(_("Existing ACLs:"),{}, {"helptext":"", "choicelist":acl_list})
						self.sharedFolderACLRemoveButton[property.syntax.name] = btn_remove

						#|----------------------------------------------|
						#|                              |               |
						#|                              |---------------|
						#|           list               |               |
						#|------------------------------|		|
						#|                              |       +       |
						#|          list                |               |
						#|----------------------------------------------|
						#|                              |       ^       |
						#|           mvalue             |       -       |
						#|                              |       v       |
						#|----------------------------------------------|
						minput_rows.append(tablerow('',{}, {'obs':[
							tablecol('',{'rowspan':'2'}, {'obs': [lst_user]}),
							tablecol('',{}, {'obs': [
								# needed freespace
								htmltext("",{},{'htmltext':['&nbsp;']})
							]})
						]}))
						minput_rows.append(tablerow('',{}, {'obs':[
							tablecol('',{'rowspan':'2','type':'multi_add_top'}, {'obs': [btn_add]})
						]}))
						minput_rows.append(tablerow('',{}, {'obs':[
							tablecol('',{}, {'obs': [lst_right]})
						]}))
						minput_rows.append(tablerow('',{}, {'obs':[
							tablecol('',{}, {'obs': [self.sharedFolderACLList[property.syntax.name]]}),
							tablecol('',{'type':'multi_remove_img'}, {'obs': [btn_remove]})
						]}))


						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [table("",{'type':'multi'},{"obs":minput_rows})]}))


					elif property.syntax.name == 'kolabInvitationPolicy':
						minput_rows=[]
						too_many_results = 0
						acls={"ACT_ALWAYS_ACCEPT": _("Always accept"), "ACT_REJECT_IF_CONFLICTS": _("Reject if conflicts"), "ACT_MANUAL_IF_CONFLICTS": _("Manual if conflicts"), "ACT_MANUAL": _("Manual"), "ACT_ALWAYS_REJECT": _("Always reject")}


						# create variables if they don't exist
						try:
							x=self.kolabIntevationPolicyAddButton
						except:
							self.kolabIntevationPolicyUserList={}
							self.kolabIntevationPolicyRightsList={}
							self.kolabIntevationPolicyAddButton={}
							self.kolabIntevationPolicyList={}
							self.kolabIntevationPolicyRemoveButton={}

						try:
							if property.syntax.searchFilter:
								users=self.lo.searchDn(property.syntax.searchFilter, base=position.getDomain(), scope='domain', timeout=10, sizelimit=200)
						except: #univention.admin.uexceptions.ldapError, msg: #more than 200 results, timeout or whatever
							too_many_results = 1

						atts=copy.deepcopy(attributes)

						if not too_many_results: # Multiselect
							id_choicelist_sorted={}
							users.sort()

							# create list of users
							for user in users:
								try:
									mailAddress=self.lo.get(dn=user, attr=['mailPrimaryAddress'])['mailPrimaryAddress'][0]
								except:
									continue
								dict={'name': "%s"%mailAddress, 'description': mailAddress}
								if '%s'%mailAddress == value:
									dict['selected']='1'
								id_choicelist_sorted[univention.admin.uldap.explodeDn(user, 1)[0].lower()]=dict

							dict={}

							keys=id_choicelist_sorted.keys()
							keys.sort()
							id_choicelist=[]
							for key in keys:
								id_choicelist.append(id_choicelist_sorted[key])
							id_choicelist.append({'name': "anyone", "description": _("Anyone")})

							lst_user = question_select(_("E-Mail address"),atts,{'choicelist':id_choicelist,'helptext':_('select attribute')})
							self.kolabIntevationPolicyUserList[property.syntax.name]=lst_user
						else: # normal field
							self.userinfo_append(_("%s: Too many entries for selectbox")%property.short_description)
							if not property.short_description[-2:] == "ID":
								property.short_description=property.short_description+" ID"
							lst_user = question_text(_("User "), atts, {"helptext":_("E-Mail address of user"), "usertext":""})
							self.kolabIntevationPolicyUserList[property.syntax.name]=lst_user

						# input fields
						acllist=[]
						for key in acls.keys():
							acllist.append({"name": key, "description":acls[key]})

						lst_right = question_select(_("Policy"), atts, {'choicelist': acllist, 'helptext':_('select access right')})
						self.kolabIntevationPolicyRightsList[property.syntax.name] = lst_right

						btn_add = get_addbutton(attributes,_("Add"))
						self.kolabIntevationPolicyAddButton[property.syntax.name]=btn_add

						# field with current values
						vals=self.object[property.syntax.name]
						acl_list=[]
						for acl in vals:
							acl_trans = acl
							# find access right an translate it
							last_space = acl.rfind(":")
							if not last_space == -1:
								right = acl[acl.rfind(":")+1:]
								user = acl[:acl.rfind(":")]
								try:
									acl_trans = "%s:%s"%(user, acls[right])
								except:
									pass
							elif acl:
								acl_trans = acls[ acl ]
							if acl and acl_trans:
								acl_list.append( { "name": acl, "description": acl_trans } )

						btn_remove=get_removebutton(attributes, _("Remove"))
						self.kolabIntevationPolicyList[property.syntax.name] = question_mselect(_("Existing Invitation Policies:"),atts, {"helptext":"", "choicelist":acl_list})
						self.kolabIntevationPolicyRemoveButton[property.syntax.name] = btn_remove

						#|----------------------------------------------|
						#|                              |               |
						#|                              |---------------|
						#|           list               |               |
						#|------------------------------|		|
						#|                              |       +       |
						#|          list                |               |
						#|----------------------------------------------|
						#|                              |       ^       |
						#|           mvalue             |       -       |
						#|                              |       v       |
						#|----------------------------------------------|

						minput_rows.append(tablerow('',{}, {'obs':[
							tablecol('',{'rowspan':'2'}, {'obs': [lst_user]}),
							tablecol('',{}, {'obs': [
								# needed freespace
								htmltext("",{},{'htmltext':['&nbsp;']})
							]})
						]}))
						minput_rows.append(tablerow('',{}, {'obs':[
							tablecol('',{'rowspan':'2','type':'multi_add_top'}, {'obs': [btn_add]})
						]}))
						minput_rows.append(tablerow('',{}, {'obs':[
							tablecol('',{}, {'obs': [lst_right]})
						]}))
						minput_rows.append(tablerow('',{}, {'obs':[
							tablecol('',{}, {'obs': [self.kolabIntevationPolicyList[property.syntax.name]]}),
							tablecol('',{'type':'multi_remove_img'}, {'obs': [btn_remove]})
						]}))

						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [table("",{'type':'multi'},{"obs":minput_rows})]}))


					elif property.syntax.name == 'policyPrinterServer':

						host_choicelist=[{'name': 'localhost', 'description': 'localhost'}]

						host_choicelist_has_current=0
						if "localhost" == value:
							host_choicelist[0]['selected']='1'
							host_choicelist_has_current=1

						for dn, attr in self.lo.search('(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))', attr=['objectClass', 'aRecord', 'cn']):
							# TODO: ckeck for multiple aRecord?
							if attr.has_key('aRecord') and attr['aRecord'][0]:
								res=self.lo.search('(&(objectClass=dNSZone)(aRecord=%s)(zoneName=*)(relativeDomainName=*))' % attr['aRecord'][0])
								if not res:
									continue
								fqdn = res[0][1]['relativeDomainName'][0]+'.'+res[0][1]['zoneName'][0]
								host_choicelist.append({'name': fqdn, 'description': fqdn})
								if fqdn == value:
									host_choicelist[-1]['selected']='1'
									host_choicelist_has_current=1


						if not host_choicelist_has_current and value:
							host_choicelist.append({'name': value, 'description': value, 'selected': '1'})

						host_choicelist.sort()

						if not host_choicelist_has_current:
							host_choicelist.insert(0, {'name': "", 'description': "", 'selected': '1'})
						else:
							host_choicelist.insert(0, {'name': "", 'description': "", 'selected': '0'})


						atts=copy.deepcopy(attributes)
						host_select=question_select(property.short_description,atts,{'choicelist':host_choicelist,'helptext':_('select host')})
						minput_rows=[]
						minput_rows.append(tablerow('',{}, {'obs':[
							tablecol('',{}, {'obs': [host_select]})
						]}))
						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [table("",{'type':'multi'},{"obs":minput_rows})]}))

						self.pinput[name]=host_select

					elif property.syntax.name == 'spoolHost':
						self.minput[name]=[]
						minput_rows=[]

						atts=copy.deepcopy(attributes)

						mvaluelist=[]
						i=0
						if value:
							for v in value:
								try:
									mvaluelist.append({'name': unicode(i), 'description': syntax.tostring(v)})
								except univention.admin.uexceptions.valueInvalidSyntax, e:
									pass
								i+=1

						if name:
							host_choicelist=[]

							for dn, attr in self.lo.search('(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer)(objectClass=univentionMobileClient)(objectClass=univentionClient))', attr=['objectClass', 'aRecord', 'cn']):
								# TODO: ckeck for multiple aRecord?
								if attr.has_key('aRecord') and attr['aRecord'][0]:
									res=self.lo.search('(&(objectClass=dNSZone)(aRecord=%s)(zoneName=*)(relativeDomainName=*))' % attr['aRecord'][0])
									if not res:
										if 'univentionWindows' in attr['objectClass']:
											host_choicelist.append({'name': attr['cn'][0], 'description': attr['cn'][0]})
										else:
											host_choicelist.append({'name': attr['aRecord'][0], 'description': attr['aRecord'][0]})
										continue
									fqdn = res[0][1]['relativeDomainName'][0]+'.'+res[0][1]['zoneName'][0]
									host_choicelist.append({'name': fqdn, 'description': fqdn})
									if value and fqdn in value:
										host_choicelist[-1]['selected']='1'
										host_choicelist_has_current=1
								else:
									if 'univentionWindows' in attr['objectClass']:
										host_choicelist.append({'name': attr['cn'][0], 'description': attr['cn'][0]})
										packages.append({'name': attr['cn'][0], 'description': attr['cn'][0]})

							host_choicelist.sort()

							self.minput[name].append(question_select(property.short_description,atts,{'choicelist':host_choicelist,'helptext':_('select host')}))
							atts=copy.deepcopy(attributes)
							b_atts=copy.deepcopy(attributes)
							b2_atts=copy.deepcopy(attributes)
							# [1]: add button
							self.minput[name].append(get_addbutton(b_atts,_("Add %s") % name))
							# [2]: mselect list widget
							self.minput[name].append(question_mselect(_("Entries:"),atts,{"helptext":_("Current entries for '%s'") % name,"choicelist":mvaluelist}))
							# [3]: remove button
							self.minput[name].append(get_removebutton(b_atts,_("Remove selected '%s' entrie(s) from list") % name))

							# move buttons:
							# [4]: up button [ ^ ]
							self.minput[name].append(get_upbutton(b2_atts,_("Move upwards")))
							# [5]: down button [ v ]
							self.minput[name].append(get_downbutton(b2_atts,_("Move downwards")))

							# put the widgets/buttons from minput[name] into a table
							#----------------------------------|
							#                 |                |
							#                 |----------------|
							#  <input field>  | <add button>   |
							# ---------------------------------|
							#                 | <up button>    |
							#                 |----------------|
							#                 | <remove button>|
							#  <mselect list> |----------------|
							#                 | <down button>  |
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'rowspan':'2'}, {'obs': [\
											#input field
											self.minput[name][0]\
										]}),\
										tablecol('',{}, {'obs': [\
											# needed freespace
											htmltext("",{},{'htmltext':['&nbsp;']})
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'type':'multi_add_top'}, {'obs': [\
											#add button
											self.minput[name][1]\
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'rowspan':'3'}, {'obs': [\
											#mselect list
											self.minput[name][2]\
										]}),\
										tablecol('',{'type':'multi_remove'}, {'obs': [\
											#up button
											self.minput[name][4]\
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'type':'multi_remove'}, {'obs': [\
											#remove button
											self.minput[name][3]\
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
									tablecol('',{'type':'multi_remove_img'}, {'obs': [\
										#down button
										self.minput[name][5]\
										]})\
									]}))
						else:
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
										]}),\
										tablecol('',{}, {'obs': [\
										]})\
									]}))
						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [table("",{'type':'multi'},{"obs":minput_rows})]}))




					elif property.syntax.name == 'printerURI':

						set_uri='file:/'
						set_src=''
						if self.object.info['uri']:
							pos = self.object.info['uri'].find('/')
							if self.object.info['uri'][pos+1]=='/':
								# FIXME: The above check does not seem to work at all times,
								# self.object.info['uri'] might be s.th. like parallel://dev/zero,
								# causing minor trouble below (see next FIXME)
								set_uri=self.object.info['uri'][:pos+2]
								set_src=self.object.info['uri'][pos+2:]
							else:
								set_uri=self.object.info['uri'][:pos+1]
								set_src=self.object.info['uri'][pos+1:]

						self.minput[name]=[]
						minput_rows=[]

						mvaluelist=[]
						i=0
						if value:
							for v in value:
								try:
									mvaluelist.append({'name': unicode(i), 'description': syntax.tostring(v)})
								except univention.admin.uexceptions.valueInvalidSyntax, e:
									pass
								i+=1

						if name:

							uris=self.lo.search('(objectClass=univentionPrinterURIs)', base=position.getDomain(), scope='domain', timeout=10, sizelimit=200)
							id_choicelist_sort={}

							id_attrib='printerURI'
							dict={}
							for uri in uris:
								for id in uri[1][id_attrib]:
									dict={'name': "%s"%id, 'description': "%s"%id}
									id_choicelist_sort[id]=dict
									# FIXME: id ends with // or /, set_uri is not always set accordingly (see FIXME above)
									# workaround: trim all trailing slashes
									while(len(id)>0 and id[-1:]=="/"):
										id = id[:-1]
									set_uri_tmp = set_uri
									while(len(set_uri_tmp)>0 and set_uri_tmp[-1:]=="/"):
										set_uri_tmp = set_uri_tmp[:-1]
									if id == set_uri_tmp:
										dict['selected']='1'

							keys=id_choicelist_sort.keys()
							keys.sort()
							id_choicelist=[]
							for key in keys:
								id_choicelist.append(id_choicelist_sort[key])

							atts=copy.deepcopy(attributes)
							b_atts=copy.deepcopy(attributes)
							b2_atts=copy.deepcopy(attributes)
							if not atts.get('width'):
								atts['width']='100' # FIXME Design

							id_select=question_select(property.short_description,atts,{'choicelist':id_choicelist,'helptext':_('select attribute')})
							self.minput[name].append(id_select)
							self.minput[name].append(question_text(_("Destination"),atts,{"helptext":_("Destination"), 'usertext': unicode(set_src)}))

							#self.minput[name].append(id_select)
							# [1]: add button
							self.minput[name].insert(1,get_addbutton(b_atts,_("Add %s") % name))
							# [2]: mselect list widget
							self.minput[name].insert(2,question_mselect(_("Entries:"),atts,{"helptext":_("Current entries for '%s'") % name,"choicelist":mvaluelist}))
							# [3]: remove button
							self.minput[name].insert(3,get_removebutton(b_atts,_("Remove selected '%s' entrie(s) from list") % name))

							# move buttons:
							# [4]: up button [ ^ ]
							self.minput[name].insert(4,get_upbutton(b2_atts,_("Move upwards")))
							# [5]: down button [ v ]
							self.minput[name].insert(5,get_downbutton(b2_atts,_("Move downwards")))

							# put the widgets/buttons from minput[name] into a table
							#  <dropdown field>               |
							# --------------------------------|
							# <add button>  | <remove button> |
							# --------------------------------|
							#                                 |
							#       <mselect list>            |
							#                                 |
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
											#uri select
											self.minput[name][0]\
										]}),\
										tablecol('',{}, {'obs': [\
											#destination input
											self.minput[name][6]\
										]})\
									]}))
						else:
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
										]}),\
										tablecol('',{}, {'obs': [\
										]})\
									]}))
						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [table("",{'type':'multi'},{"obs":minput_rows})]}))
					elif property.syntax.name == 'printerShare':

						self.minput[name]=[]
						minput_rows=[]

						mvaluelist=[]
						i=0
						if value:
							for v in value:
								try:
									mvaluelist.append({'name': unicode(i), 'description': syntax.tostring(v)})
								except univention.admin.uexceptions.valueInvalidSyntax, e:
									pass
								i+=1

						if name:


							too_many_results = 0
							try:
								spoolhosts = '(|'
								for host in self.object.info[ 'spoolHost' ]:
									spoolhosts += "(univentionPrinterSpoolHost=%s)" % host
								spoolhosts += ')'
								dns=self.lo.searchDn('(&(objectClass=univentionPrinter)%s)' % spoolhosts, base=position.getDomain(), scope='domain', timeout=10, sizelimit=200)
							except: #univention.admin.uexceptions.ldapError, msg: #more than 200 results, timeout or whatever
								too_many_results = 1
								dns=[]
							if not too_many_results: # Multiselect
								id_choicelist_sort={}
								dns.sort()

								id_attrib='cn'
								dict={}
								for dn in dns:
									id=self.lo.get(dn=dn, attr=[id_attrib])[id_attrib][0]
									if id != self.object.info['name']:
										dict={'name': "%s"%id, 'description': univention.admin.uldap.explodeDn(dn, 1)[0]}
										if '%s'%id == value:
											dict['selected']='1'
										id_choicelist_sort[univention.admin.uldap.explodeDn(dn, 1)[0].lower()]=dict
								try:
									if int('0') == int(value):
										dict['selected']='1'
								except:
									dict['selected']='1'

								keys=id_choicelist_sort.keys()
								keys.sort()
								id_choicelist=[]
								for key in keys:
									id_choicelist.append(id_choicelist_sort[key])

								atts=copy.deepcopy(attributes)
								id_select=question_select(property.short_description,atts,{'choicelist':id_choicelist,'helptext':_('select attribute')})
							else: # normal field
								self.userinfo_append(_("%s: Too many entries for selectbox")%property.short_description)
								if not property.short_description[-2:] == "ID":
									property.short_description=property.short_description+" ID"
								id_select=question_property('',attributes,{'property': property, 'field': field, 'value': value, 'name': name, 'lo': self.lo})
							atts=copy.deepcopy(attributes)
							b_atts=copy.deepcopy(attributes)
							b2_atts=copy.deepcopy(attributes)

							# [0]: input field (or several input fields in case of a complex syntax property)
							self.minput[name].append(id_select)
							# [1]: add buttond
							self.minput[name].append(get_addbutton(b_atts,_("Add %s") % name))
							# [2]: mselect list widget
							self.minput[name].append(question_mselect(_("Entries:"),atts,{"helptext":_("Current entries for '%s'") % name,"choicelist":mvaluelist}))
							# [3]: remove button
							self.minput[name].append(get_removebutton(b_atts,_("Remove selected '%s' entrie(s) from list") % name))

							# move buttons:
							# [4]: up button [ ^ ]
							self.minput[name].append(get_upbutton(b2_atts,_("Move upwards")))
							# [5]: down button [ v ]
							self.minput[name].append(get_downbutton(b2_atts,_("Move downwards")))

							# put the widgets/buttons from minput[name] into a table
							#                   |                |
							#                   |----------------|
							#  <dropdown field> |  <add button>  |
							# ------------------|----------------|
							#                   | <remove button>|
							#  <mselect list>   |                |
							#                   |                |
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'rowspan':'2'}, {'obs': [\
											#input field
											self.minput[name][0]\
										]}),\
										tablecol('',{}, {'obs': [\
											# needed freespace
											htmltext("",{},{'htmltext':['&nbsp;']})
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'type':'multi_add_top'}, {'obs': [\
											#add button
											self.minput[name][1]\
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
											#mselect list
											self.minput[name][2]\
										]}),\
										tablecol('',{'type':'multi_remove_img'}, {'obs': [\
											#remove button
											self.minput[name][3]\
										]})\

									]}))
						else:
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
										]}),\
										tablecol('',{}, {'obs': [\
										]})\
									]}))
						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [table("",{'type':'multi'},{"obs":minput_rows})]}))


					elif property.syntax.name == 'printQuotaGroup' or property.syntax.name == 'printQuotaUser' or property.syntax.name == 'printQuotaGroupsPerUsers':

						self.minput[name]=[]
						minput_rows=[]

						mvaluelist=[]
						i=0
						if value:
							for v in value:
								try:
									mvaluelist.append({'name': unicode(i), 'description': syntax.tostring(v)})
								except univention.admin.uexceptions.valueInvalidSyntax, e:
									pass
								i+=1

						if name:

							too_many_results = 0
							try:
								if property.syntax.searchFilter:
									dns=self.lo.searchDn(property.syntax.searchFilter, base=position.getDomain(), scope='domain', timeout=10, sizelimit=200)
							except: #univention.admin.uexceptions.ldapError, msg: #more than 200 results, timeout or whatever
								too_many_results = 1
								dns=[]
							if not too_many_results: # Multiselect
								id_choicelist_sort={}
								dns.sort()

								id_attrib='uid'
								if property.syntax.name == 'printQuotaGroup' or property.syntax.name == 'printQuotaGroupsPerUsers':
									id_attrib='cn'
								for dn in dns:
									id=self.lo.get(dn=dn, attr=[id_attrib])[id_attrib][0]
									dict={'name': "%s"%id, 'description': "%s"%id}
									if '%s'%id == value:
										dict['selected']='1'
									id_choicelist_sort[univention.admin.uldap.explodeDn(dn, 1)[0].lower()]=dict
								dict={'name': "root", 'description': "root"}
								try:
									if int('0') == int(value):
										dict['selected']='1'
								except:
									# value is not set, can happen after updates, we assume it's root then (which will be set by the listener-modules)
									dict['selected']='1'

								id_choicelist_sort['root']=dict
								keys=id_choicelist_sort.keys()
								keys.sort()
								id_choicelist=[]
								for key in keys:
									id_choicelist.append(id_choicelist_sort[key])

								atts=copy.deepcopy(attributes)
								id_select=question_select(property.short_description,atts,{'choicelist':id_choicelist,'helptext':_('select attribute')})
								self.minput[name].append(id_select)
								self.minput[name].append(question_text(_("Soft-Limit (Pages)"),atts,{"helptext":_("Soft-Limit (Pages)")}))
								self.minput[name].append(question_text(_("Hard-Limit (Pages)"),atts,{"helptext":_("Hard-Limit (Pages)")}))


							else: # normal field
								self.userinfo_append(_("%s: Too many entries for selectbox")%property.short_description)
								self.minput[name].append(question_text(property.short_description,attributes,{"helptext":_("User")}))
								self.minput[name].append(question_text(_("Soft-Limit (Pages)"),attributes,{"helptext":_("Soft-Limit (Pages)")}))
								self.minput[name].append(question_text(_("Hard-Limit (Pages)"),attributes,{"helptext":_("Hard-Limit (Pages)")}))



							atts=copy.deepcopy(attributes)
							b_atts=copy.deepcopy(attributes)
							b2_atts=copy.deepcopy(attributes)
							# [1]: add button
							self.minput[name].insert(1, get_addbutton(b_atts,_("Add %s") % name))
							# [2]: mselect list widget
							self.minput[name].insert(2, question_mselect(_("Entries:"),atts,{"helptext":_("Current entries for '%s'") % name,"choicelist":mvaluelist}))
							# [3]: remove button
							self.minput[name].insert(3, get_removebutton(b_atts,_("Remove selected '%s' entrie(s) from list") % name))

							# move buttons:
							# [4]: up button [ ^ ]
							self.minput[name].insert(4, get_upbutton(b2_atts,_("Move upwards")))

							# [5]: down button [ v ]
							self.minput[name].insert(5, get_downbutton(b2_atts,_("Move downwards")))


							# put the widgets/buttons from minput[name] into a table
							#                 |                  |
							#                 |------------------|
							#  <input field>  |                  |
							#  <input field>  |  <add button>    |
							#  <input field>  |                  |
							#------------------------------------|
							# <mselect list>  |  <remove button> |
							#------------------------------------|


							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'rowspan':'2'}, {'obs': [\
											#input field
											self.minput[name][0]\
										]}),\
										tablecol('',{}, {'obs': [\
											# needed freespace
											#htmltext("",{},{'htmltext':['&nbsp;']})
											text('',{},{'text':['']})
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'rowspan':'3','type':'multi_add_top'}, {'obs': [\
											#add button
											self.minput[name][1]\
										]})\
									]}))

							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
											#input field
											self.minput[name][6]\
										]})\
									]}))

							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
											#input field
											self.minput[name][7]\
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
											#mselect list
											self.minput[name][2]\
										]}),\
										tablecol('',{'type':'multi_remove_img'}, {'obs': [\
											#remove button
											self.minput[name][3]\
										]})\
									]}))
						else:
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
										]}),\
										tablecol('',{}, {'obs': [\
										]})\
									]}))
						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [table("",{'type':'mutli'},{"obs":minput_rows})]}))


					elif property.syntax.name == 'service':
						self.minput[name]=[]
						minput_rows=[]

						atts=copy.deepcopy(attributes)

						mvaluelist=[]
						i=0
						if value:
							for v in value:
								try:
									mvaluelist.append({'name': unicode(i), 'description': syntax.tostring(v)})
								except univention.admin.uexceptions.valueInvalidSyntax, e:
									#self.usermessage(unicode(e))
									pass
								i+=1

						if name:
							# [0]: input field (or several input fields in case of a complex syntax property)
							packages=[]

							for dn, attr in self.lo.search('objectClass=univentionServiceObject', attr=['cn']):
									packages.append({'name': attr['cn'][0], 'description': attr['cn'][0]})

							self.minput[name].append(question_select(property.short_description,atts,{'choicelist':packages,'helptext':_('Services')}))
							atts=copy.deepcopy(attributes)
							b_atts=copy.deepcopy(attributes)
							b2_atts=copy.deepcopy(attributes)
							# [1]: add button
							self.minput[name].append(get_addbutton(b_atts,_("Add %s") % name))
							# [2]: mselect list widget
							self.minput[name].append(question_mselect(_("Entries:"),atts,{"helptext":_("Current entries for '%s'") % name,"choicelist":mvaluelist}))
							# [3]: remove button
							self.minput[name].append(get_removebutton(b_atts,_("Remove selected '%s' entrie(s) from list") % name))

							# move buttons:
							# [4]: up button [ ^ ]
							self.minput[name].append(get_upbutton(b2_atts,_("Move upwards")))
							# [5]: down button [ v ]
							self.minput[name].append(get_downbutton(b2_atts,_("Move downwards")))

							# put the widgets/buttons from minput[name] into a table
							#                 |                |
							#                 |----------------|
							#  <input field>  | <add button>   |
							# ---------------------------------|
							#                 | <up button>    |
							#                 |----------------|
							#                 | <remove button>|
							#  <mselect list> |----------------|
							#                 | <down button>  |
							#----------------------------------|
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'rowspan':'2'}, {'obs': [\
											#input field
											self.minput[name][0]\
										]}),\
										tablecol('',{}, {'obs': [\
											# needed freespace
											htmltext("",{},{'htmltext':['&nbsp;']})
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'type':'multi_add_top'}, {'obs': [\
											#add button
											self.minput[name][1]\
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablerow("",{},{"obs":[\
											tablecol('',{'rowspan':'3'}, {'obs': [\
												#mselect list
												self.minput[name][2]\
											]}),\
											tablecol('',{'type':'multi_remove'}, {'obs': [\
												#up button
												self.minput[name][4]\
											]})\
										]}),\
										tablerow("",{},{"obs":[\
											tablecol('',{'type':'multi_remove'}, {'obs': [\
												#remove button
												self.minput[name][3]\
											]})\
										]}),\
										tablerow("",{},{"obs":[\
											tablecol('',{'type':'multi_remove_img'}, {'obs': [\
												#down button
												self.minput[name][5]\
											]})\
										]})\
									]}))
						else:
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
										]}),\
										tablecol('',{}, {'obs': [\
										]})\
									]}))
						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [table("",{'type':'multi'},{"obs":minput_rows})]}))

					elif property.syntax.name == 'consoleACL':
						self.minput[name]=[]
						self.xinput[name]=[]
						minput_rows=[]

						atts=copy.deepcopy(attributes)

						mvaluelist=[]
						i=0

						if name:
							# [0]: input field (or several input fields in case of a complex syntax property)
							acllists=[]
							aclcategories=[]
							category_list = []
							global_acllist = []

							for dn, attr in self.lo.search('objectClass=univentionConsoleACL', attr=['cn', 'description', 'univentionConsoleACLCategory']):
								if attr.has_key('univentionConsoleACLCategory'):
									category = attr['univentionConsoleACLCategory'][0]
								else:
									category = 'Without Category'

								class_name=univention.admin.uldap.explodeDn(dn, 1)[0]
								if self.save.get('x_choice_value_of_%s'%name,'') == '':
									self.save.put('x_choice_value_of_%s'%name, category)

								if self.save.get('x_choice_value_of_%s'%name) == category:
									if attr.has_key('description') and attr['description'][0]:
										global_acllist.append({'name': dn, 'description': attr['description'][0]})
										acllists.append({'name': dn, 'description': attr['description'][0]})
									else:
										global_acllist.append({'name': dn, 'description': attr['cn'][0]})
										acllists.append({'name': dn, 'description': attr['cn'][0]})

									if not category in category_list:
										aclcategories.append( {'name': category, 'description': category, 'selected': class_name} )
										category_list.append( category )
								else:
									if not category in category_list:
										if category == 'Without Category':
											aclcategories.append( {'name': 'Without Category', 'description': category} )
										else:
											aclcategories.append( {'name': category, 'description': category} )
										category_list.append( category )
									global_acllist.append({'name': dn, 'description': attr['description'][0]})

							aclcategories.sort( compare_dicts_by_attr( 'description' ) )

							if value:
								for v in value:
									found=False
									for p in global_acllist:
										if p.has_key('name') and p['name'] == v:
											mvaluelist.append({'name': unicode(i), 'description': p['description']})
											found=True
											break
									i+=1

									if not found:
										mvaluelist.append({'name': syntax.tostring(v), 'description': syntax.tostring(v)})

							update_choices=button('lmanusel',{},{'helptext':_('select command category')})
							self.xinput[name].append(update_choices)
							self.xinput[name].append(question_select(_('ACL Category'),atts,
																{'choicelist':aclcategories,'helptext':_('Select ACL category'),
																'button':update_choices}))

							self.minput[name].append(question_select(property.short_description,atts,{'choicelist':acllists,'helptext':_('Select ACL')}))
							atts=copy.deepcopy(attributes)
							b_atts=copy.deepcopy(attributes)
							b2_atts=copy.deepcopy(attributes)
							# [1]: add button
							self.minput[name].append(get_addbutton(b_atts,_("Add %s") % name))
							# [2]: mselect list widget
							self.minput[name].append(question_mselect(_("Entries:"),atts,{"helptext":_("Current entries for '%s'") % name,"choicelist":mvaluelist}))
							# [3]: remove button
							self.minput[name].append(get_removebutton(b_atts,_("Remove selected '%s' entrie(s) from list") % name))

							# move buttons:
							# [4]: up button [ ^ ]
							self.minput[name].append(get_upbutton(b2_atts,_("Move upwards")))
							# [5]: down button [ v ]
							self.minput[name].append(get_downbutton(b2_atts,_("Move downwards")))

							# put the widgets/buttons from minput[name] into a table
							#                 |                |
							#                 |----------------|
							#  <input field>  | <add button>   |
							# ---------------------------------|
							#                 | <up button>    |
							#                 |----------------|
							#                 | <remove button>|
							#  <mselect list> |----------------|
							#                 | <down button>  |
							#----------------------------------|
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'rowspan':'2'}, {'obs': [\
											#input field
											self.xinput[name][1],\
											self.minput[name][0],\
										]}),\
										tablecol('',{}, {'obs': [\
											# needed freespace
											htmltext("",{},{'htmltext':['&nbsp;']})
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'type':'multi_add_top'}, {'obs': [\
											#add button
											self.minput[name][1]\
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablerow("",{},{"obs":[\
											tablecol('',{'rowspan':'3'}, {'obs': [\
												#mselect list
												self.minput[name][2]\
											]}),\
											tablecol('',{'type':'multi_remove'}, {'obs': [\
												#up button
												self.minput[name][4]\
											]})\
										]}),\
										tablerow("",{},{"obs":[\
											tablecol('',{'type':'multi_remove'}, {'obs': [\
												#remove button
												self.minput[name][3]\
											]})\
										]}),\
										tablerow("",{},{"obs":[\
											tablecol('',{'type':'multi_remove_img'}, {'obs': [\
												#down button
												self.minput[name][5]\
											]})\
										]})\
									]}))
						else:
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
										]}),\
										tablecol('',{}, {'obs': [\
										]})\
									]}))
						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [table("",{'type':'multi'},{"obs":minput_rows})]}))

					elif property.syntax.name == 'consoleOperations':
						self.minput[name]=[]
						self.xinput[name]=[]
						self.tinput[name]=[]
						minput_rows=[]

						atts=copy.deepcopy(attributes)

						mvaluelist=[]
						i=0
						if value:
							for v in value:
								try:
									mvaluelist.append({'name': unicode(i), 'description': syntax.tostring(v)})
								except univention.admin.uexceptions.valueInvalidSyntax, e:
									#self.usermessage(unicode(e))
									pass
								i+=1

						if name:
							# [0]: input field (or several input fields in case of a complex syntax property)
							operationlists=[]
							operations=[]

							searchResult=self.lo.search('objectClass=univentionConsoleOperations', base=position.getDomain(), scope='domain', attr=['cn', 'description', 'univentionConsoleOperation'])

							chosen=0
							for dn,attr in searchResult:
								if attr.has_key('univentionConsoleOperation'):
									class_name=univention.admin.uldap.explodeDn(dn, 1)[0]
									if self.save.get('x_choice_value_of_%s'%name,'') == '':
										self.save.put('x_choice_value_of_%s'%name,class_name)

									if self.save.get('x_choice_value_of_%s'%name)==class_name:
										operationlists.append({'name':class_name,'description':class_name,'selected':class_name})
										chosen=1
										for p in attr['univentionConsoleOperation']:
											operations.append({'name': "%s" %p, 'description': "%s" %p})
											if p == value:
												operationlists[-1]['selected']='1'
												operations[-1]['selected']='1'
									else:
										operationlists.append({'name':class_name,'description':class_name})

							operationlists.sort(compare_dicts_by_attr('name'))
							operations.sort(compare_dicts_by_attr('name'))

							#minput does not have all needed fields.
							update_choices=button('lmanusel',{},{'helptext':_('select command category')})
							self.xinput[name].append(update_choices)
							self.xinput[name].append(question_select(_('command category'),atts,
																{'choicelist':operationlists,'helptext':_('select operation'),
																'button':update_choices}))
							self.minput[name].append(question_select(property.short_description,atts,{'choicelist':operations,'helptext':''}))

							# [1]: add button
							atts=copy.deepcopy(attributes)
							b_atts=copy.deepcopy(attributes)
							b2_atts=copy.deepcopy(attributes)
							self.minput[name].append(get_addbutton(b_atts,_("Add %s") % name))
							# [2]: mselect list widget
							self.minput[name].append(question_mselect(_("Entries:"),atts,{"helptext":_("Current entries for '%s'") % name,"choicelist":mvaluelist}))
							# [3]: remove button
							self.minput[name].append(get_removebutton(b_atts,_("Remove selected '%s' entrie(s) from list") % name))
							self.tinput[name].append(question_text(_("Command data"),b2_atts,{"helptext":_("Parameter for the command")}))

							# put the widgets/buttons from minput[name] into a table
							#  <input field>                | <add button>
							# ------------------------------------------------
							#                 | <up button>   | <remove button>
							#  <mselect list> |---------------|
							#                 | <down button> |
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'rowspan':'2'}, {'obs': [\
											#input field
											self.xinput[name][1],\
										]}),\
										tablecol('',{}, {'obs': [\
											# needed freespace
											htmltext("",{},{'htmltext':['&nbsp;']})
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'rowspan':'2','type':'multi_add_top'}, {'obs': [\
											#add button
											self.minput[name][1]\
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
											#input field
											self.minput[name][0]\
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
											#input field
											self.tinput[name][0]\
										]})\
									]}))

							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
											#mselect list
											self.minput[name][2]\
										]}),\
										tablecol('',{'type':'multi_remove_img'}, {'obs': [\
											#remove button
											self.minput[name][3]\
										]})\
									]}))
						else:
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
										]}),\
										tablecol('',{}, {'obs': [\
										]})\
									]}))
						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [table("",{'type':'multi'},{"obs":minput_rows})]}))

					elif property.syntax.name == 'configRegistry':

						self.registryinput={}
						registryinput_rows=[]
						key_names=[]
						atts=copy.deepcopy(attributes)


						if current_module == module:
							if value:
								for v in value:
									key_names.append('%s' % v.split('=')[0])
								key_names.sort()

								found=False
								for key_name in key_names:
									for v in value:
										if v.startswith('%s=' % key_name):
											found=True
											break

									if found:

										self.registryinput[v]=question_text(_('Variable: %s' % key_name ),atts,{"helptext":_('Config Registry value for %s' % key_name), 'usertext': '%s' % string.join(v.split('=')[1:])})

										registryinput_rows.append(tablerow("",{},{"obs":[\
													tablecol('',{}, {'obs': [\
														self.registryinput[v]\
													]})\
												]}))
										registryinput_rows.append(tablerow("",{},{"obs":[\
													tablecol('',{}, {'obs': [\
														# needed freespace
														htmltext("",{},{'htmltext':['&nbsp;']})
													]})\
												]}))

							self.registryinput['new_value']=question_text(_('Name of the new Config Registry variable' ),atts,{"helptext":_('Add a new Config Registry variable' ) })
							self.registryinput['new_button']=get_addbutton(atts,_('Add the new Config Registry variable'))

							if value:
								registryinput_rows.append(tablerow("",{},{"obs":[\
											tablecol('',{}, {'obs': [\
												# needed freespace
												htmltext("",{},{'htmltext':['&nbsp;']})
											]})\
										]}))
							registryinput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
											self.registryinput['new_value']\
										]}),\
										tablecol('',{}, {'obs': [\
											self.registryinput['new_button']\
										]})\
								]}))

							cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [table("",{'type':'multi'},{"obs":registryinput_rows})]}))

							univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'registry: append to col')
							# xml objects must be placed into a colum before they can be inserted into a tablerow
							# cols.append(tablecol('',{'type':'tab_layout'}, {'obs': inputs}))


					elif property.syntax.name == 'listAttributes':
						self.xinput[name]=[]
						minput_rows=[]

						admin_modules = []
						for module_name, mod in univention.admin.modules.modules.items():
							admin_modules.append( { 'name': module_name, 'description': univention.admin.modules.short_description( mod ), 'attributes': univention.admin.modules.attributes( mod ) } )

						atts=copy.deepcopy(attributes)

						mvaluelist=[]
						i=0
						if value:
							for v in value:
								try:
									# split the entry:
									found=False
									temp_module = v.split(':')[0]
									temp_attribute = string.join(v.split(':')[1:], ':').strip(' ')
									for admin_module in admin_modules:
										if temp_module == admin_module[ 'name' ]:
											for admin_attribute in admin_module['attributes']:
												if temp_attribute == admin_attribute[ 'name' ]:
													found=True
													mvaluelist.append({'name': unicode(i), 'description': '%s: %s' % (admin_module[ 'description' ], admin_attribute[ 'description' ])})
												elif temp_attribute == 'dn':
													found = True
													mvaluelist.append( { 'name': unicode( i ), 'description': '%s: %s' % ( admin_module[ 'description' ], _( 'DN' ) ) } )
												if found:
													break
											break
									if not found:
										mvaluelist.append({'name': unicode(i), 'description': syntax.tostring(v)})
								except univention.admin.uexceptions.valueInvalidSyntax, e:
									#self.usermessage(unicode(e))
									pass
								i+=1

						if name:
							# [0]: input field (or several input fields in case of a complex syntax property)
							tablist=[]
							attrlist=[]

							_save_x_choice = 'x_choice_value_of_%s' % name
							_save_p_choice = 'p_choice_value_of_%s' % name

							if not property.multivalue and value and not self.save.get( _save_x_choice, None ):
								if not self.save.get( _save_x_choice, None ):
									self.save.put( _save_x_choice, value[ : value.find( ':' ) ] )

							_current_module = self.save.get( _save_x_choice )
							for admin_module in admin_modules:
								if _current_module == admin_module['name']:
									tablist.append( { 'name' : admin_module['name'], 'description' : admin_module['description'], 'selected' : admin_module['name'] } )
								else:
									tablist.append( { 'name' : admin_module['name'], 'description' : admin_module['description'] } )

							tablist.sort( compare_dicts_by_attr( 'description' ) )
							if self.save.get( _save_x_choice,'' ) == '':
								self.save.put( _save_x_choice, tablist[0]['name'] )
							selected = self.save.get( _save_x_choice )

							if not property.multivalue and value:
								if not self.save.get( _save_p_choice, None ):
									self.save.put( _save_p_choice, value )
							selected_attr = self.save.get( _save_p_choice, '' )
							if selected_attr:
								selected_attr = selected_attr.split( ':', 1 )[ 1 ].strip()

							for admin_module in admin_modules:
								if admin_module[ 'name' ] == selected:
									for admin_attribute in  admin_module[ 'attributes' ]:
										if admin_attribute[ 'name' ] == 'filler':
											continue
										attrlist.append( { 'name' : '%s: %s' % (admin_module['name'], admin_attribute['name']), 'description' : admin_attribute['description'] } )
										if not property.multivalue and selected_attr:
											if selected_attr == admin_attribute[ 'name' ]:
												attrlist[ -1 ][ 'selected' ] = '1'
									if not name in ( 'listAttributes', 'listNavigationAttributes' ):
										attrlist.append( { 'name' : '%s: %s' % ( admin_module[ 'name' ], 'dn' ), 'description' : _( 'DN' ) } )
										if selected_attr == 'dn':
											attrlist[ -1 ][ 'selected' ] = '1'


							attrlist.sort( compare_dicts_by_attr( 'description' ) )

							update_choices=button('lmanusel',{},{'helptext':_('select package list')})
							self.xinput[name].append(update_choices)
							self.xinput[name].append(question_select(property.short_description,atts,
																{'choicelist':tablist,'helptext':_('select tab'),
																'button':update_choices}))

							if not property.multivalue:
								self.pinput[name] = question_select(_('Self Attribute Results'),atts,{'choicelist':attrlist,'helptext':''})
								minput_rows.append(tablerow("",{},{"obs":[\
											tablecol('',{}, {'obs': [\
												#input field
												self.xinput[name][1]\
												#,self.minput[name][0]\
											]}),\
											tablecol('',{}, {'obs': [\
												# needed freespace
												htmltext("",{},{'htmltext':['&nbsp;']})
											]})\
										]}))
								minput_rows.append(tablerow("",{},{"obs":[\
											tablecol('',{}, {'obs': [\
												#input field
												self.pinput[name]\
											]})\
										]}))
							else:
								self.minput[name]=[]
								self.minput[name].append(question_select(_('Self Attribute Results'),atts,{'choicelist':attrlist,'helptext':''}))
								# [1]: add button
								atts=copy.deepcopy(attributes)
								b_atts=copy.deepcopy(attributes)
								b2_atts=copy.deepcopy(attributes)
								self.minput[name].append(get_addbutton(b_atts,_("Add %s") % name))
								# [2]: mselect list widget
								# FIXME
								self.minput[name].append(question_mselect(_("Entries:"),atts,{"helptext":_("Current entries for '%s'") % name,"choicelist":mvaluelist}))
								# [3]: remove button
								self.minput[name].append(get_removebutton(b_atts,_("Remove selected '%s' entrie(s) from list") % name))
								# move buttons:
								# [4]: up button [ ^ ]
								self.minput[name].append(get_upbutton(b2_atts,_("Move upwards")))
								# [5]: down button [ v ]
								self.minput[name].append(get_downbutton(b2_atts,_("Move downwards")))

								# put the widgets/buttons from minput[name] into a table
								#                 |                |
								#                 |----------------|
								#  <input field>  | <add button>   |
								# ---------------------------------|
								#                 | <up button>    |
								#                 |----------------|
								#                 | <remove button>|
								#  <mselect list> |----------------|
								#                 | <down button>  |
								#----------------------------------|

								minput_rows.append(tablerow("",{},{"obs":[\
											tablecol('',{'rowspan':'2'}, {'obs': [\
												#input field
												self.xinput[name][1]\
												#,self.minput[name][0]\
											]}),\
											tablecol('',{}, {'obs': [\
												# needed freespace
												htmltext("",{},{'htmltext':['&nbsp;']})
											]})\
										]}))
								minput_rows.append(tablerow("",{},{"obs":[\
											tablecol('',{'rowspan':'2','type':'multi_add_top'}, {'obs': [\
												#add button
												self.minput[name][1]\
											]})\
										]}))
								minput_rows.append(tablerow("",{},{"obs":[\
											tablecol('',{}, {'obs': [\
												#input field
												self.minput[name][0]\
											]})\
										]}))
								minput_rows.append(tablerow("",{},{"obs":[\
											tablerow("",{},{"obs":[\
												tablecol('',{'rowspan':'3'}, {'obs': [\
													#mselect list
													self.minput[name][2]\
												]}),\
												tablecol('',{'type':'multi_remove'}, {'obs': [\
													#up button
													self.minput[name][4]\
												]})\
											]}),\
											tablerow("",{},{"obs":[\
												tablecol('',{'type':'multi_remove'}, {'obs': [\
													#remove button
													self.minput[name][3]\
												]})\
											]}),\
											tablerow("",{},{"obs":[\
												tablecol('',{'type':'multi_remove_img'}, {'obs': [\
													#down button
													self.minput[name][5]\
												]})\
											]})\
										]}))
						else:
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
										]}),\
										tablecol('',{}, {'obs': [\
										]})\
									]}))
						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [table("",{'type':'multi'},{"obs":minput_rows})]}))

					################################

					elif property.syntax.name == 'ldapServer':
						self.minput[name]=[]
						minput_rows=[]

						atts=copy.deepcopy(attributes)

						mvaluelist=[]
						i=0
						if value:
							for v in value:
								try:
									mvaluelist.append({'name': unicode(i), 'description': syntax.tostring(v)})
								except univention.admin.uexceptions.valueInvalidSyntax, e:
									#self.usermessage(unicode(e))
									pass
								i+=1

						if name:
							# [0]: input field (or several input fields in case of a complex syntax property)
							packages=[]

							for dn, attr in self.lo.search('objectClass=univentionDomainController', attr=['objectClass', 'aRecord', 'cn']):
								if attr.has_key('aRecord') and attr['aRecord'][0]:
									res=self.lo.search('(&(objectClass=dNSZone)(aRecord=%s)(zoneName=*)(relativeDomainName=*))' % attr['aRecord'][0])
									if not res:
										continue
									fqdn = res[0][1]['relativeDomainName'][0]+'.'+res[0][1]['zoneName'][0]
									packages.append({'name': fqdn, 'description': fqdn})

							self.minput[name].append(question_select(property.short_description,atts,{'choicelist':packages,'helptext':_('select Server')}))
							atts=copy.deepcopy(attributes)
							b_atts=copy.deepcopy(attributes)
							b2_atts=copy.deepcopy(attributes)
							# [1]: add button
							self.minput[name].append(get_addbutton(b_atts,_("Add %s") % name))
							# [2]: mselect list widget
							self.minput[name].append(question_mselect(_("Entries:"),atts,{"helptext":_("Current entries for '%s'") % name,"choicelist":mvaluelist}))
							# [3]: remove button
							self.minput[name].append(get_removebutton(b_atts,_("Remove selected '%s' entrie(s) from list") % name))

							# move buttons:
							# [4]: up button [ ^ ]
							self.minput[name].append(get_upbutton(b2_atts,_("Move upwards")))
							# [5]: down button [ v ]
							self.minput[name].append(get_downbutton(b2_atts,_("Move downwards")))

							# put the widgets/buttons from minput[name] into a table
							#                 |                |
							#                 |----------------|
							#  <input field>  | <add button>   |
							# ---------------------------------|
							#                 | <up button>    |
							#                 |----------------|
							#                 | <remove button>|
							#  <mselect list> |----------------|
							#                 | <down button>  |
							#----------------------------------|
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'rowspan':'2'}, {'obs': [\
											#input field
											self.minput[name][0]\
										]}),\
										tablecol('',{}, {'obs': [\
											# needed freespace
											htmltext("",{},{'htmltext':['&nbsp;']})
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'type':'multi_add_top'}, {'obs': [\
											#add button
											self.minput[name][1]\
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablerow("",{},{"obs":[\
											tablecol('',{'rowspan':'3'}, {'obs': [\
												#mselect list
												self.minput[name][2]\
											]}),\
											tablecol('',{'type':'multi_remove'}, {'obs': [\
												#up button
												self.minput[name][4]\
											]})\
										]}),\
										tablerow("",{},{"obs":[\
											tablecol('',{'type':'multi_remove'}, {'obs': [\
												#remove button
												self.minput[name][3]\
											]})\
										]}),\
										tablerow("",{},{"obs":[\
											tablecol('',{'type':'multi_remove_img'}, {'obs': [\
												#down button
												self.minput[name][5]\
											]})\
										]})\
									]}))
						else:
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
										]}),\
										tablecol('',{}, {'obs': [\
										]})\
									]}))
						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [table("",{'type':'multi'},{"obs":minput_rows})]}))

					elif property.syntax.name == 'printersList':
						printer_manufs=[]
						printer_models=[]

						p_models=self.lo.search('objectClass=univentionPrinterModels', base=position.getDomain(), scope='domain')

						if not value or value == None:
							value = 'None'

						selected_manuf=self.save.get('printer_manufacturer_selected')
						selected_model=self.save.get('printer_model_selected')
						selected=0
						selected_mod=0
						for p_model in p_models:
							manuf = p_model[1]['cn'][0]
							printer_manufs.append({'name' : manuf, 'description':manuf})
							if not selected:
								printer_models=[]
								plist = p_model[1]
								if manuf==selected_manuf:
									selected=1
									printer_manufs[-1]['selected']='1'
								if plist.has_key('printerModel'):
									for i in plist['printerModel']:
										t_list=i.split('" "')
										printer_models.append({'name': t_list[0].replace('"',''), 'description': t_list[1].replace('"','')})
										if not selected_mod and selected_model == t_list[0].replace('"',''):
											selected_mod=1
											printer_models[-1]['selected']='1'

										if not selected_manuf and t_list[0].replace('"','') == value:
											printer_models[-1]['selected']='1'
											selected=1
											if not selected_manuf:
												printer_manufs[-1]['selected']='1'
												selected_mod=1

						atts=copy.deepcopy(attributes)

						printer_manufs.sort(compare_dicts_by_attr('name'))
						printer_models.sort(compare_dicts_by_attr('name'))

						self.search_property_button=button('pmanusel',{},{'helptext':_('select manufacturer')})

						printer_manufs_select=question_select(_('manufacturer'),atts,
															  {'choicelist':printer_manufs,'helptext':_('select printer-manufacturer'),
															   'button':self.search_property_button})
						printer_models_select=question_select(property.short_description,atts,{'choicelist':printer_models,'helptext':_('select printer-model')})
						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [
							 table('',{}, {'obs':[
							  tablerow('',{}, {'obs':[
							   tablecol('', {}, {'obs': [printer_manufs_select]})
							  ]}),
							  tablerow('',{}, {'obs':[
							   tablecol('', {}, {'obs': [printer_models_select]})
							  ]})
							 ]})
							]}))

						self.pinput[name]=printer_models_select
						self.printermanuf=printer_manufs_select

					elif property.syntax.name in [ 'windowsTerminalServer', 'linuxTerminalServer', 'authenticationServer', 'fileServer' ]:
						self.minput[name]=[]
						self.xinput[name]=[]
						minput_rows=[]

						atts=copy.deepcopy(attributes)

						mvaluelist=[]
						i=0
						if value:
							for v in value:
								try:
									mvaluelist.append({'name': unicode(i), 'description': syntax.tostring(v)})
								except univention.admin.uexceptions.valueInvalidSyntax, e:
									pass
								i+=1

						if name:
							packages=[]
							if property.syntax.searchFilter:
								dns=self.lo.searchDn(property.syntax.searchFilter, base=position.getDomain(), scope='domain', timeout=10, sizelimit=200)

								for dn in dns:
									vals = self.lo.get(dn=dn, attr=[ 'cn', 'aRecord' ] )
									cn = vals['cn'][0]

									# aRecord present?
									if not 'aRecord' in vals.keys():
										continue

									aRecord = vals['aRecord'][0]
									zoneDNs = self.lo.searchDn("(&(aRecord=%s)(objectClass=dNSZone))" % aRecord, base=position.getDomain(), scope='domain', timeout=10, sizelimit=200)
									zone = self.lo.get(dn=zoneDNs[0], attr=[ 'zoneName' ] )['zoneName'][0]
									fqdn="%s.%s" % (cn, zone)
									packages.append({'name': fqdn, 'description': fqdn})

							packages.sort(compare_dicts_by_attr('name'))

							#minput does not have all needed fields.
							update_choices=button('lmanusel',{},{'helptext':_('select package list')})
							self.xinput[name].append(update_choices)
							self.minput[name].append(question_select(property.short_description,atts,{'choicelist':packages,'helptext':''}))

							# [1]: add button
							atts=copy.deepcopy(attributes)
							b_atts=copy.deepcopy(attributes)
							b2_atts=copy.deepcopy(attributes)
							self.minput[name].append(get_addbutton(b_atts,_("Add %s") % name))
							# [2]: mselect list widget
							self.minput[name].append(question_mselect(_("Entries:"),atts,{"helptext":_("Current entries for '%s'") % name,"choicelist":mvaluelist}))
							# [3]: remove button
							self.minput[name].append(get_removebutton(b_atts,_("Remove selected '%s' entrie(s) from list") % name))

							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
											#input field
											self.minput[name][0]\
										]}),\
										tablecol('',{'type':'multi_add_top'}, {'obs': [\
											#add button
											self.minput[name][1]\
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
											#mselect list
											self.minput[name][2]\
										]}),\
										tablecol('',{'type':'multi_remove_img'}, {'obs': [\
											#remove button
											self.minput[name][3]\
										]})\
									]}))
						else:
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
										]}),\
										tablecol('',{}, {'obs': [\
										]})\
									]}))
						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [table("",{'type':'multi'},{"obs":minput_rows})]}))
					elif property.syntax.name == 'packageList':
						self.minput[name]=[]
						self.xinput[name]=[]
						minput_rows=[]

						atts=copy.deepcopy(attributes)

						mvaluelist=[]
						i=0
						if value:
							for v in value:
								try:
									mvaluelist.append({'name': unicode(i), 'description': syntax.tostring(v)})
								except univention.admin.uexceptions.valueInvalidSyntax, e:
									pass
								i+=1

						if name:
							# [0]: input field (or several input fields in case of a complex syntax property)
							packagelists=[]
							packages=[]

							searchResult=self.lo.search('objectClass=univentionPackageList', base=position.getDomain(), scope='domain', attr=['univentionPackageDefinition'])

							chosen=0
							for dn,attr in searchResult:
								if attr.has_key('univentionPackageDefinition'):
									class_name=univention.admin.uldap.explodeDn(dn, 1)[0]
									if self.save.get('x_choice_value_of_%s'%name,'') == '':
										self.save.put('x_choice_value_of_%s'%name,class_name)

									if self.save.get('x_choice_value_of_%s'%name)==class_name:
										packagelists.append({'name':class_name,'description':class_name,'selected':class_name})
										chosen=1
										for p in attr['univentionPackageDefinition']:
											packages.append({'name': "%s" %p, 'description': "%s" %p})
										packages.sort()
									else:
										packagelists.append({'name':class_name,'description':class_name})

							packagelists.sort(compare_dicts_by_attr('name'))
							packages.sort(compare_dicts_by_attr('name'))

							#minput does not have all needed fields.
							update_choices=button('lmanusel',{},{'helptext':_('select package list')})
							self.xinput[name].append(update_choices)
							self.xinput[name].append(question_select(_('package list'),atts,
																{'choicelist':packagelists,'helptext':_('select Packages'),
																'button':update_choices}))
							self.minput[name].append(question_select(property.short_description,atts,{'choicelist':packages,'helptext':''}))

							# [1]: add button
							atts=copy.deepcopy(attributes)
							b_atts=copy.deepcopy(attributes)
							b2_atts=copy.deepcopy(attributes)
							self.minput[name].append(get_addbutton(b_atts,_("Add %s") % name))
							# [2]: mselect list widget
							self.minput[name].append(question_mselect(_("Entries:"),atts,{"helptext":_("Current entries for '%s'") % name,"choicelist":mvaluelist}))
							# [3]: remove button
							self.minput[name].append(get_removebutton(b_atts,_("Remove selected '%s' entrie(s) from list") % name))

							# put the widgets/buttons from minput[name] into a table
							#  <input field>                | <add button>
							# ------------------------------------------------
							#                 | <up button>   | <remove button>
							#  <mselect list> |---------------|
							#                 | <down button> |
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'rowspan':'2'}, {'obs': [\
											#input field
											self.xinput[name][1]\
											#,self.minput[name][0]\
										]}),\
										tablecol('',{}, {'obs': [\
											# needed freespace
											htmltext("",{},{'htmltext':['&nbsp;']})
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'rowspan':'2','type':'multi_add_top'}, {'obs': [\
											#add button
											self.minput[name][1]\
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
											#input field
											self.minput[name][0]\
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
											#mselect list
											self.minput[name][2]\
										]}),\
										tablecol('',{'type':'multi_remove_img'}, {'obs': [\
											#remove button
											self.minput[name][3]\
										]})\
									]}))
						else:
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
										]}),\
										tablecol('',{}, {'obs': [\
										]})\
									]}))
						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [table("",{'type':'multi'},{"obs":minput_rows})]}))
					elif property.syntax.name == 'userAttributeList':
						self.minput[name]=[]
						self.xinput[name]=[]
						minput_rows=[]

						usermod = univention.admin.modules.get( 'users/user' )
						useropts = usermod.options
						userprops = usermod.property_descriptions
						userlayout = usermod.layout

						atts=copy.deepcopy(attributes)

						mvaluelist=[]
						i=0
						if value:
							for v in value:
								try:
									if userprops.has_key(v):
										mvaluelist.append({'name': unicode(i), 'description': userprops[v].short_description})
									else:
										mvaluelist.append({'name': unicode(i), 'description': syntax.tostring(v)})
								except univention.admin.uexceptions.valueInvalidSyntax, e:
									pass
								i+=1

						if name:
							# [0]: input field (or several input fields in case of a complex syntax property)
							tablist=[]
							attrlist=[]


							for tab in userlayout:
								tabname = tab.short_description
								if self.save.get( 'x_choice_value_of_%s' % name,'' ) == '':
									self.save.put( 'x_choice_value_of_%s' % name, tabname )
								if self.save.get( 'x_choice_value_of_%s' % name )== tabname:
									tablist.append( { 'name' : tabname, 'description' : tabname, 'selected' : tabname } )
								else:
									tablist.append( { 'name' : tabname, 'description' : tabname } )

							selected = self.save.get( 'x_choice_value_of_%s' % name )
							def add_valid_property( name, attrlist ):
								if name == 'filler': return False
								prop = userprops[ name ]
								descr = prop.short_description
								if not prop.options:
									attrlist.append( { 'name' : name, 'description' : descr } )
									return True
								for opt in prop.options:
									if useropts.has_key( opt ) and useropts[ opt ].disabled:
										return False
								attrlist.append( { 'name' : name, 'description' : descr } )
								return True

							for tab in userlayout:
								if tab.short_description == selected:
									for row in tab.fields:
										for cell in row:
											if isinstance( cell, univention.admin.field ):
												add_valid_property( cell.property, attrlist )
											elif isinstance( cell, ( list, tuple ) ):
												for f in cell:
													add_valid_property( f.property, attrlist )

							tablist.sort( compare_dicts_by_attr( 'name' ) )
							attrlist.sort( compare_dicts_by_attr( 'name' ) )

							#minput does not have all needed fields.
							update_choices=button('lmanusel',{},{'helptext':_('select package list')})
							self.xinput[name].append(update_choices)
							self.xinput[name].append(question_select(_('Self Tabs List'),atts,
																{'choicelist':tablist,'helptext':_('select tab'),
																'button':update_choices}))
							self.minput[name].append(question_select(property.short_description,atts,{'choicelist':attrlist,'helptext':''}))

							# [1]: add button
							atts=copy.deepcopy(attributes)
							b_atts=copy.deepcopy(attributes)
							b2_atts=copy.deepcopy(attributes)
							self.minput[name].append(get_addbutton(b_atts,_("Add %s") % name))
							# [2]: mselect list widget
							self.minput[name].append(question_mselect(_("Entries:"),atts,{"helptext":_("Current entries for '%s'") % name,"choicelist":mvaluelist}))
							# [3]: remove button
							self.minput[name].append(get_removebutton(b_atts,_("Remove selected '%s' entrie(s) from list") % name))

							# put the widgets/buttons from minput[name] into a table
							#  <input field>                | <add button>
							# ------------------------------------------------
							#                 | <up button>   | <remove button>
							#  <mselect list> |---------------|
							#                 | <down button> |
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'rowspan':'2'}, {'obs': [\
											#input field
											self.xinput[name][1]\
											#,self.minput[name][0]\
										]}),\
										tablecol('',{}, {'obs': [\
											# needed freespace
											htmltext("",{},{'htmltext':['&nbsp;']})
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'rowspan':'2','type':'multi_add_top'}, {'obs': [\
											#add button
											self.minput[name][1]\
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
											#input field
											self.minput[name][0]\
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
											#mselect list
											self.minput[name][2]\
										]}),\
										tablecol('',{'type':'multi_remove_img'}, {'obs': [\
											#remove button
											self.minput[name][3]\
										]})\
									]}))
						else:
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
										]}),\
										tablecol('',{}, {'obs': [\
										]})\
									]}))
						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [table("",{'type':'multi'},{"obs":minput_rows})]}))
					elif property.syntax.name == 'none':
							cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [ ]}))


					elif property.syntax.name == 'module':
						module_choicelist=[{'name': '', 'description': ''}]

						syntax = property.syntax
						too_many_results = 0
						try:
							mod = univention.admin.modules.get( syntax.module_type )
							if mod:
								objs = univention.admin.modules.lookup( mod, None, self.lo, syntax.filter, scope='domain',timeout=10, sizelimit=200)
							else:
								objs = []
						except univention.admin.uexceptions.ldapError, msg: #more than 1000 results
							too_many_results = 1

						atts=copy.deepcopy(attributes)

						if not too_many_results:
							for obj in objs:
								module_choicelist.append({'name': obj.dn, 'description': univention.admin.objects.description(obj)})
								if obj.dn == value:
									module_choicelist[-1]['selected']='1'

							module_select=question_select(property.short_description,atts,{'choicelist':module_choicelist,'helptext':_('select attribute')})
							self.pinput[name]=module_select
						else:
							self.userinfo_append(_("%s: Too many entries for selectbox")%property.syntax.description)
							property.syntax=univention.admin.syntax.ldapDnOrNone
							if not property.short_description[-4:] == "(DN)":
								property.short_description=property.short_description+" (DN)"
							module_select=question_property(property.short_description,attributes,{'property': property, 'field': field, 'value': value, 'name': name, 'lo': self.lo})
							self.input[name]=module_select

						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [module_select]}))


					elif property.syntax.name == 'groupDn' or property.syntax.name == 'userDn' or property.syntax.name == 'hostDn' or property.syntax.name == 'nagiosServiceDn' or property.syntax.name == 'nagiosHostsEnabledDn':

						fixedFilter=''
						if property.syntax.name == 'userDn':
							module_name = 'users/user'
							dispattr="username"
						elif property.syntax.name == 'groupDn':
							module_name = 'groups/group'
							dispattr="name"
						elif property.syntax.name == 'hostDn':
							module_name = 'computers/computer'
							dispattr="name"
						elif property.syntax.name == 'nagiosServiceDn':
							module_name = 'nagios/service'
							dispattr="name"
						elif property.syntax.name == 'nagiosHostsEnabledDn':
							module_name = 'computers/computer'
							dispattr="name"
							fixedFilter='(&(objectClass=univentionNagiosHostClass)(univentionNagiosEnabled=1)(aRecord=*))'

						search_module=univention.admin.modules.get( module_name )
						search_property_name=self.save.get('membership_search_property'+name)
						filter=None
						valid=1
						if not search_module.property_descriptions.has_key(search_property_name):
							if not search_property_name=="*":
								search_property_name="_"
						if not search_property_name=="*":
							membership_search_value=self.save.get("membership_search_value"+name)
							if not membership_search_value:
								membership_search_value="*"
							filter="(%s=%s)"%(search_property_name,membership_search_value)

						if fixedFilter:
							if filter:
								filter='(&%s%s)' % (fixedFilter, filter)
							else:
								filter=fixedFilter

						if self.save.get('membership_search_ok'+name) and not self.parent.input and search_property_name!="_": # we have no input
							self.save.put('membership_search_ok'+name,None)
							groups=[]
							if filter:
								gr=search_module.lookup(None,self.lo,filter,scope="domain",base=position.getDomain())
							elif valid:
								gr=search_module.lookup(None,self.lo,None,scope="domain",base=position.getDomain())
							else:
								gr=[]
							groups=gr
							self.save.put("membership_search_result"+name,groups)
						else:
							groups=self.save.get("membership_search_result"+name)
							if not groups:
								groups=[]
						is_in={}

						cur_group_choicelist=[]
						sort_temp = {}

						for group in value: # value may have ''-element, would crash python in the dictionary
							if group!='':
								is_in[group]=1
						for group in value:
							if group!='':
								sort_temp[group]=univention.admin.uldap.explodeDn(group, 1)[0]
						sort_keys = [(x.lower(),x) for x in sort_temp.keys()] # tupe of lower case key and keys for case insensitive sort
						sort_keys.sort()
						for unused,key in sort_keys:
							cur_group_choicelist.append({'name': key, 'description': sort_temp[key]})

						new_group_choicelist=[]
						sort_temp = {}
						for group in groups:
							if not group.dn:
								continue
							if not is_in.get(group.dn):
								additional_attrs = settings.getListAttributes( module_name )
								append_text = []
								if additional_attrs:
									obj = univention.admin.objects.get( search_module, None, self.lo,
																		group.position, group.dn )
									univention.admin.objects.open( obj )
									for attr in additional_attrs:
										if obj.has_key( attr ):
											if isinstance( obj[ attr ], list ):
												append_text.append( obj[ attr ][ 0 ] )
											else:
												append_text.append( obj[ attr ] )
								rdn = univention.admin.uldap.explodeDn( group.dn, 1 )[ 0 ]
								if append_text:
									sort_temp[ group.dn ] = '%s (%s)' % ( rdn, ', '.join( append_text ) )
								else:
									sort_temp[ group.dn ] = rdn
						# tuple of lower case key and keys for case insensitive sort
						sort_keys = [ ( x.lower(), x ) for x in sort_temp.keys() ]
						sort_keys.sort()
						for unused,key in sort_keys:
							new_group_choicelist.append( { 'name': key, 'description': sort_temp[ key ] } )

						atts=copy.deepcopy(attributes)
						#search_type=self.save.get('browse_search_type')
						searchcols=[]

						search_properties=[]
						search_properties.append({'name': '*', 'description': _('any')})
						search_properties.append({'name': '_','description':_('none')})
						if search_property_name == '_':
							search_properties[-1]['selected']='0'

						for pname, pproperty in search_module.property_descriptions.items():
							if not (hasattr(pproperty, 'dontsearch') and pproperty.dontsearch==1):
								search_properties.append({'name': pname, 'description': pproperty.short_description})

						search_properties.sort()

						for i in search_properties:
							if i['name']==search_property_name:
								i['selected']='1'

						if search_property_name not in  ('*',"_"):
							if search_property_name:
								search_property=search_module.property_descriptions[search_property_name]
							self.search_input=question_property('',{},{'property': search_property, 'value': membership_search_value, 'search': '1', 'lo': self.lo})
						if search_property_name=="*":
							search_value='*'

						if search_property_name in ("*","_"):
							self.search_input=text('',{},{'text':['']})

						self.search_property_button=button('go',{},{'helptext':_('go ahead')})
						self.search_property_select=question_select(_('property'),{},{'helptext':_('select attribute'),'choicelist':search_properties,'button':self.search_property_button})

						# make fields available in apply
						search_property_select=self.search_property_select
						search_input=self.search_input

						self.search_type_button=button('go',{},{'helptext':_('go ahead')})
						self.search_button=button(_('show'),{'icon':'/style/ok.gif'},{'helptext':_('show')})

						searchcols.append(tablecol('',{},{'obs':[search_property_select]}))
						searchcols.append(tablecol('',{},{'obs':[search_input]}))
						searchcols.append(tablecol('',{'type':'tab_layout_bottom'},{'obs':[self.search_button]}))

						atts['height']='150'
						group_new_box=question_mselect(_('All'),atts,{'choicelist':new_group_choicelist,'helptext':_('choose objects to add')})
						group_cur_box=question_mselect(_('Current'),atts,{'choicelist':cur_group_choicelist,'helptext':_('choose objects to remove')})
						group_add_button=get_rightbutton(attributes,_("Add"))
						group_remove_button=get_leftbutton(attributes,_("Remove"))

						# |------------------------------------------|
						# |             |          |                 |
						# |             |----------|                 |
						# |  list       |    >     |      list       |
						# |             |----------|                 |
						# |             |    <     |                 |
						# |------------------------------------------|

						tableobs=[tablerow("",{},{"obs":[
								tablecol("",{},
										 {"obs":[table("",{'type':'multi'},{"obs":[tablerow("",{},{"obs":searchcols})]})]}
								 )]}),
							tablerow("",{},{"obs":[
								tablecol("",{},{"obs":[table("",{'type':'multi'},{"obs":[\
									tablerow("",{},{"obs":[
										tablecol('',{'rowspan':'3'},{'obs': [group_new_box]}),
										tablecol('',{'type':'multi_spacer'}, {'obs': [\
											# needed freespace
											# htmltext("",{},{'htmltext':['&nbsp;']})
											htmltext("",{},{'htmltext':['&nbsp;']})
											]}),\
										tablecol('',{'rowspan':'3'},{'obs': [group_cur_box]})
									]}),
									tablerow("",{},{"obs":[
										tablecol('',{'type':'leftright_top'}, {'obs': [\
											#add button
											group_add_button\
										]})\
									]}),\
									tablerow("",{},{"obs":[
										tablecol('',{'type':'leftright_bottom'}, {'obs': [\
											#remove button
											group_remove_button\
										]})\
									]})\
								]})]})\
							]})\
						]

						tableobs.insert(0,tablerow("",{},{"obs":[\
							tablecol("",{"colspan":"3",'type':'description'},{"obs":[\
								text("",{},{'text':['%s'%property.short_description]})\
								]})\
							]}))
						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [table("",{'type':'multi'},{"obs":tableobs})]}))

						self.ginput[name]=(group_new_box, group_cur_box, group_add_button, group_remove_button,self.search_button,search_property_select,self.search_property_button,search_input)

					elif property.syntax.name == "sambaLogonHours":
						choices_possible=[]
						choices_current=[]
						count=0

						vals=self.object["sambaLogonHours"]
						if vals=="" or not vals: vals="1"*168

						for day in [_("Sun"), _("Mon"), _("Tue"), _("Wed"), _("Thu"), _("Fri"), _("Sat")]:
							for hour in range(0, 24):
								txt=day + " " + unicode(hour) + "-" + unicode(hour+1)
								if vals[count]=="0":
									choices_possible.append({"name": unicode(count), "description": txt})
								else:
									choices_current.append({"name": unicode(count), "description": txt})
								count+=1
						self.logonHours_possible = question_mselect(_("Disallowed at:"),{"width":"130"}, {"helptext":"", "choicelist":choices_possible})
						self.logonHours_current = question_mselect(_("Allowed at:"), {"width":"130"}, {"helptext":"", "choicelist":choices_current})
						self.logonHours_remove=get_rightbutton(attributes,_("Remove"))
						self.logonHours_add=get_leftbutton(attributes,_("Add"))

						# |------------------------------------------|
						# | Text                                     |
						# |------------------------------------------|
						# |             |          |                 |
						# |             |----------|                 |
						# |  list       |    >     |      list       |
						# |             |----------|                 |
						# |             |    <     |                 |
						# |------------------------------------------|


						minput_rows=[tablerow("",{'type':'multi'},{"obs":[\
								tablecol('',{'type':'description','colspan':'3'}, {'obs': [\
									# title
									text("",{},{"text":[_("Logon")]})
								]}),\
							]}),\
							tablerow("",{'type':'multi'},{"obs":[\
								tablecol('',{'rowspan':'3'}, {'obs': [\
									#mselect list
									self.logonHours_current\
								]}),\
								tablecol('',{'type':'multi_spacer'}, {'obs': [\
									# needed freespace
									htmltext("",{},{'htmltext':['&nbsp;']})
								]}),\
								tablecol('',{'rowspan':'3'}, {'obs': [\
									#current list
									self.logonHours_possible\
								]})\
							]}),\
							tablerow("",{},{"obs":[\
								tablecol('',{'type':'leftright_top'}, {'obs': [\
									#add button
									self.logonHours_remove\
								]})\
							]}),\
							tablerow("",{},{"obs":[\
								tablecol('',{'type':'leftright_bottom'}, {'obs': [\
									#remove button
									self.logonHours_add\
								]})\
							]})]
						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [table("",{'type':'multi'},{"obs":minput_rows})]}))

					# LDAP_Search in view-only mode
					elif property.syntax.name == 'LDAP_Search' and property.syntax.viewonly:
						property.editable = False
						minput_rows = []
						self.ldap_search_buttons = {}

						# update choices
						filter = property._replace( property.syntax.filter, self.object )
						property.syntax._prepare( self.lo, filter )

						nbhead=header(property.short_description, {'type': '4'}, {})
						col = [ tablecol("",{},{"obs":[nbhead]}) ]
						minput_rows.append(tablerow("",{},{"obs":[
							tablecol("",{'type':'policy_layout'},{"obs":[
								table("",{},{"obs":[
									tablerow("",{},{"obs":col})
								]})
							]})
						]}))

						mod = None
						object = None
						current_pos = len( minput_rows )
						headlines = {}
						for key, display in property.syntax.values:
							attrs = self.lo.get( key )
							mod = univention.admin.modules.identify( key, attrs )
							object = univention.admin.objects.get( mod[ 0 ], None, self.lo, None, key )
							univention.admin.objects.open( object )
							name = univention.admin.objects.description( object )
							iconName = ""
							if mod:
								iconName = univention.admin.modules.name( mod[ 0 ] )
							btn = button( name,
								      { 'icon' : unimodule.selectIconByName( iconName ) },
								      { 'helptext' : key } )
							
							col = [ tablecol( '', {}, { 'obs': [ btn ] } ) ]
							for entry in display:
								attr = entry.split( ':', 1 )[ 1 ].strip()
								val = u''
								if object.descriptions.has_key( attr ):
									if not headlines.has_key( attr ):
										headlines[ attr ] = object.descriptions[ attr ].short_description
								if object.info.has_key( attr ):
									val = object.info[ attr ]
									if isinstance( val, ( list, tuple ) ):
										val = '\n'.join( val )
								elif attr == 'dn':
									val = object.dn
								col.append( tablecol( '', {}, { 'obs': [ text( '', {}, { 'text' : [ unicode( val ) ] } ) ] } ) )
							self.ldap_search_buttons[ key ] = btn
							minput_rows.append( tablerow("",{},{"obs": col } ) )

						# header

						col = [ tablecol( '', {}, { 'obs': [ text( '', { 'type' : 'content_header' }, { 'text' : [ _( 'Object' ) ] } ) ] } ) ]
						if property.syntax.values:
							for entry in property.syntax.attributes:
								attr = entry.split( ':', 1 )[ 1 ].strip()
								if attr == 'dn':
									title = _( 'DN' )
								else:
									title = headlines[ attr ]
								if not title:
									title = unicode( attr )
								col.append( tablecol( '', {}, { 'obs': [ text( '', { 'type' : 'content_header' }, { 'text' : [ title ] } ) ] } ) )
							minput_rows.insert( current_pos, tablerow("",{},{"obs": col } ) )
						else:
							minput_rows.append( tablerow("",{},{"obs":[tablecol("",{'type':'wizard_layout'},{"obs":[header(_("None"),{"type":"2"},{})]})]}) )

						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [table("",{'type':'multi'},{"obs":minput_rows})]}))
					# edit multivalue property
					elif property.multivalue:
						self.minput[name]=[]
						minput_rows=[]

						mvaluelist=[]
						i=0
						if property.syntax.name == 'LDAP_Search':
							filter = property._replace( property.syntax.filter, self.object )
							property.syntax._prepare( self.lo, filter )
							for dn, val, attr in property.syntax.values:
								val = val.split( ':', 1 )[ 1 ].strip()
								attr = attr.split( ':', 1 )[ 1 ].strip()
								attrs = self.lo.get( dn )
								mod = univention.admin.modules.identify( dn, attrs )
								object = univention.admin.objects.get( mod[ 0 ], None, self.lo, None, dn )
								univention.admin.objects.open( object )
								try:
									if val == 'dn':
										val = dn
									else:
										val = object[ val ]
										if isinstance( val, ( list, tuple ) ):
											val = val[ 0 ]
										if not val:
											continue
								except:
									continue
								try:
									if attr == 'dn':
										attr = dn
									else:
										attr = object[ attr ]
										if isinstance( attr, ( list, tuple ) ):
											attr = attr[ 0 ]
								except:
									attr = ''

								property.syntax.choices.append( ( val, attr ) )
						if value:
							for v in value:
								try:
									if hasattr(property.syntax, 'choices') and property.syntax.choices:
										description = syntax.tostring(v)
										for choice in property.syntax.choices:
											if choice[0] == description:
												description = choice[1]
												continue
										mvaluelist.append({'name': unicode(i), 'description': description})
									else:
										mvaluelist.append({'name': unicode(i), 'description': syntax.tostring(v)})
								except univention.admin.uexceptions.valueInvalidSyntax, e:
									#self.usermessage(unicode(e))
									pass
								i+=1

						if name:
							atts=copy.deepcopy(attributes)
							b_atts=copy.deepcopy(attributes)
							b2_atts=copy.deepcopy(attributes)
							# [0]: input field (or several input fields in case of a complex syntax property)
							self.minput[name].append(question_property('',atts,{'property':property, 'field': field, 'name': name, 'lo': self.lo}))
							# [1]: add button
							self.minput[name].append(get_addbutton(b_atts,_("Add %s") % name))
							# [2]: mselect list widget
							self.minput[name].append(question_mselect(_("Entries:"),atts,{"helptext":_("Current entries for '%s'") % name,"choicelist":mvaluelist}))
							# [3]: remove button
							self.minput[name].append(get_removebutton(b_atts,_("Remove selected '%s' entrie(s) from list") % name))

							# move buttons:
							# [4]: up button [ ^ ]
							self.minput[name].append(get_upbutton(b2_atts,_("Move upwards")))
							# [5]: down button [ v ]
							self.minput[name].append(get_downbutton(b2_atts,_("Move downwards")))

							# put the widgets/buttons from minput[name] into a table
							#				  |				   |
							#				  |----------------|
							#  <input field>  | <add button>   |
							# ---------------------------------|
							#				  | <up button>	   |
							#				  |----------------|
							#				  | <remove button>|
							#  <mselect list> |----------------|
							#				  | <down button>  |
							#----------------------------------|
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'rowspan':'2'}, {'obs': [\
											#input field
											self.minput[name][0]\
										]}),\
										tablecol('',{}, {'obs': [\
											# needed freespace
											htmltext("",{},{'htmltext':['&nbsp;']})
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{'type':'multi_add_top'}, {'obs': [\
											#add button
											self.minput[name][1]\
										]})\
									]}))
							minput_rows.append(tablerow("",{},{"obs":[\
										tablerow("",{},{"obs":[\
											tablecol('',{'rowspan':'3'}, {'obs': [\
												#mselect list
												self.minput[name][2]\
											]}),\
											tablecol('',{'type':'multi_remove'}, {'obs': [\
												#up button
												self.minput[name][4]\
											]})\
										]}),\
										tablerow("",{},{"obs":[\
											tablecol('',{'type':'multi_remove'}, {'obs': [\
												#remove button
												self.minput[name][3]\
											]})\
										]}),\
										tablerow("",{},{"obs":[\
											tablecol('',{'type':'multi_remove_img'}, {'obs': [\
												#down button
												self.minput[name][5]\
											]})\
										]})\
									]}))
						else:
							minput_rows.append(tablerow("",{},{"obs":[\
										tablecol('',{}, {'obs': [\
										]}),\
										tablecol('',{}, {'obs': [\
										]})\
									]}))
						cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [table("",{'type':'multi'},{"obs":minput_rows})]}))

					# edit single-value property
					else:
						if property.syntax.name == 'LDAP_Search':
							filter = property._replace( property.syntax.filter, self.object )
							property.syntax._prepare( self.lo, filter )
							for dn, val, attr in property.syntax.values:
								val = val.split( ':', 1 )[ 1 ].strip()
								attr = attr.split( ':', 1 )[ 1 ].strip()
								attrs = self.lo.get( dn )
								mod = univention.admin.modules.identify( dn, attrs )
								object = univention.admin.objects.get( mod[ 0 ], None, self.lo, None, dn )
								univention.admin.objects.open( object )
								try:
									if val == 'dn':
										val = dn
									else:
										val = object[ val ]
										if isinstance( val, ( list, tuple ) ):
											val = val[ 0 ]
								except:
									val = ''
								try:
									if attr == 'dn':
										attr = dn
									else:
										attr = object[ attr ]
										if isinstance( attr, ( list, tuple ) ):
											attr = attr[ 0 ]
								except:
									attr = ''
								property.syntax.choices.append( ( val, attr ) )
						if name:
							self.input[name]=question_property('',attributes,{'property': property, 'field': field, 'value': value, 'name': name, 'lo': self.lo})

							# xml objects must be placed into a colum before they can be inserted into a tablerow
							cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [\
								self.input[name]\
							]}))
						else:
							cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [ ]}))

					if multiedit and name != 'filler':
						multiedit_overwrite = self.save.get('edit_multiedit_overwrite', [])
						if not multiedit_overwrite:
							multiedit_overwrite=[]
						if name in multiedit_overwrite:
							overwrite_checked='1'
						else:
							overwrite_checked=''
						self.input_multiedit_overwrite[name]=question_bool('',{},{'usertext':overwrite_checked,'helptext': _('overwrite value %s in all objects') % name})
						if len(cols):
							cols[-1].args['obs'].append(
								table("",{},{"obs":[
									tablerow("",{},{"obs":[
										tablecol('',{'type':'overwrite_text'}, {'obs': [
											text("",{},{"text":[_('overwrite')]}),
											]}),
										tablecol('',{'type':'overwrite_check'}, {'obs': [
											self.input_multiedit_overwrite[name]
											]})
										]})
									]}))
					if colspan:
						cols[-1].atts["colspan"]=unicode(colspan)
					if rowspan and rowspan!="1":
						cols[-1].atts["rowspan"]=unicode(rowspan)
				rows.append(tablerow("",{},{"obs":cols}))

			# create table containing one row for each 'logical' field as generated above
			main_rows.append(tablerow("",{},{"obs":[tablecol("",{'type':'content_main'},{"obs":[table("",{'type':'multi'},{"obs":rows})]})]}))


		main_rows.append(tablerow("",{},{"obs":[tablecol("",{'type':'okcancel'},{"obs":get_okcancelbuttons(self, edit_policy=edit_policy)})]}))
		self.subobjs.append(table("",
					  {'type':'content_main'},
					  {"obs":[tablerow("",{},{"obs":[tablecol("",{'type':'content_main'},{"obs":main_rows})]})]})
				    )
		self.tabbing = tabbing

	def apply(self, cancelMessage='', okMessage=''):
		if self.applyhandlemessages():
			return

		self.cancel = 0

		univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'apply ')

		return_to=self.save.get('edit_return_to')
		if not return_to:
			return_to="browse"

		if (len(self.save.get('certTempFile')) > 30) and ("/tmp/webui/univention-admin" in self.save.get('certTempFile')):
			os.unlink(self.save.get('certTempFile'))
			self.save.put('certTempFile','')

		# cancel
		if hasattr(self, 'cabut') and self.cabut.pressed():

			self.object=self.save.get('edit_object')
			if not self.object:
				# nobody should get here
				return
			univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'cancel: load object')
			if hasattr(self.object, 'cancel'):
				univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'cancel: found')
				self.object.cancel()

			self.save.put('edit_object', None)
			self.save.put('edit_object_opened', None)
			self.save.put('edit_invalid', None)
			self.save.put('edit_multiedit_overwrite', None)
			self.save.put("uc_module",return_to)
			self.save.put('tab', None)
			self.save.put('validtabs', None)
			for key in self.ginput.keys():
				self.save.put('membership_search_result'+key,None)
				self.save.put('membership_search_ok'+key,None)
				self.save.put('membership_search_value'+key,None)
				self.save.put('membership_search_property'+key,None)
			self.save.put('edit_policydn_preselect', None)
			self.save.put('edit_policy', None)
			self.save.put('edit_policy_original_reference', None)
			self.save.put('printer_manufacturer_selected',None)
			self.save.put('package_class_selected',None)
			if cancelMessage and not self.save.get("usermessages"):
				self.usermessage(cancelMessage)
			return

		# read uploaded file...
		if hasattr(self,'certLoadBtn') and self.certLoadBtn.pressed():
			univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'MODEDIT - ADD CERTIFICATE')
			self.object=self.save.get("edit_object")
			if not self.object:
				return
			if self.certBrowse.get_input():
				certFile = open(self.certBrowse.get_input())
				certContent=certFile.read()
				certFile.close()
				if "----BEGIN CERTIFICATE-----" in certContent:
					certContent = certContent.replace('----BEGIN CERTIFICATE-----','')
					certContent = certContent.replace('-----END CERTIFICATE-----','')
					self.object['userCertificate'] = [base64.decodestring(certContent)]
				else:
					self.object['userCertificate'] = [certContent]
				self.object.reload_certificate()

		#+++# DELETE CERTIFICATE #+++#
		if hasattr(self,'certDeleteBtn') and self.certDeleteBtn.pressed():
			univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'MODEDIT - DELETE CERTIFICATE')
			self.object=self.save.get("edit_object")
			if not self.object:
				return
			self.object['userCertificate'] = ['']
			self.object.reload_certificate()


		# logon hours
		if hasattr(self, "logonHours_add") and self.logonHours_add.pressed():
			moveright = self.logonHours_possible.getselected()
			self.object=self.save.get("edit_object")
			if not self.object:
				return

			vals=self.object["sambaLogonHours"]	 # vals is something like '001100111100100...'

			for num in moveright:
				vals=vals[:int(num)]+"1"+vals[int(num)+1:]

			# in case the user may now logon at any time, set attribute to ""
			# (avoids implicit change of attribute)
			if len(vals.replace("1",""))==0:
				vals=""
			self.object["sambaLogonHours"]=vals

		if hasattr(self, "logonHours_remove") and self.logonHours_remove.pressed():
			moveleft = self.logonHours_current.getselected()
			self.object=self.save.get("edit_object")
			if not self.object:
				return

			vals=self.object["sambaLogonHours"]	 # vals is something like '001100111100100...'
			if not(vals) or vals=="": vals="1"*168		 # this is the case if no attribute was available before

			for num in moveleft:
				vals=vals[:int(num)]+"0"+vals[int(num)+1:]
			self.object["sambaLogonHours"]=vals

		# Shared folder ACLs
		if hasattr(self, 'sharedFolderACLAddButton'):
			self.object=self.save.get("edit_object")
			if not self.object:
				return

			for attr in ['sharedFolderUserACL', 'sharedFolderGroupACL']:
				if self.sharedFolderACLAddButton[attr].pressed():
					# add ACL
					acl = self.sharedFolderACLRightsList[attr].getselected()

					if self.sharedFolderACLUserList[attr].__class__ == question_text:
						# no list, but simple textbox, so we have to check the format
						user = self.sharedFolderACLUserList[attr].xvars["usertext"]

						_re = self.sharedFolderACLRegEx[attr]
						if not _re.match("%s %s"%(user, acl)):
							self.save.put("sharedFolderACLUserName", user)
							self.userinfo(_("Invalid value"))
							return
					else:
						user = self.sharedFolderACLUserList[attr].getselected()

					acl_string = "%s %s"%(user, acl)
					if not acl_string in self.object[attr]:
						self.object[attr].append("%s %s"%(user, acl))
				elif self.sharedFolderACLRemoveButton[attr].pressed():
					# remove ACL
					acl = self.sharedFolderACLList[attr].getselected()
					if acl:
						for i in acl:
							self.object[attr].remove(i)

		if hasattr(self, 'kolabIntevationPolicyAddButton'):
			self.object=self.save.get("edit_object")
			if not self.object:
				return
			# univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'simpleLdap._ldap_modlist1:[%s]' % self.object["kolabInvitationPolicy"])

			if self.kolabIntevationPolicyAddButton["kolabInvitationPolicy"].pressed():
				# add ACL
				try:
					user = self.kolabIntevationPolicyUserList["kolabInvitationPolicy"].getselected()
				except:
					# no list, but simple textbox
					user = self.kolabIntevationPolicyUserList["kolabInvitationPolicy"].xvars["usertext"]
					if not user:
						return
				acl = self.kolabIntevationPolicyRightsList["kolabInvitationPolicy"].getselected()
				if user == "anyone":
					acl_string = "%s"%(acl)
				else:
					acl_string = "%s:%s"%(user, acl)
				if not acl_string in self.object["kolabInvitationPolicy"]:
					if len(self.object["kolabInvitationPolicy"]) == 1 and len(self.object["kolabInvitationPolicy"][0]) <1:
						if user == "anyone":
							self.object["kolabInvitationPolicy"]=["%s"%(acl)]
						else:
							self.object["kolabInvitationPolicy"]=["%s:%s"%(user, acl)]
					else:
						if user == "anyone":
							# if there is already an entry for 'anyone' -> replace it
							if len(self.object['kolabInvitationPolicy']) > 0:
								if self.object[ 'kolabInvitationPolicy' ][ -1 ].find( ':' ) == -1:
									self.object[ 'kolabInvitationPolicy' ][ -1 ] = "%s" % acl
								else:
									self.object["kolabInvitationPolicy"].append("%s"%(acl))
							else:
								self.object["kolabInvitationPolicy"].insert( -1, "%s"%(acl))

						else:
							# if there is already an entry for this user -> replace it ...
							for i in range( len( self.object[ 'kolabInvitationPolicy' ] ) ):
								if self.object[ 'kolabInvitationPolicy' ][ i ].find( ':' ) != -1:
									addr = self.object[ 'kolabInvitationPolicy' ][ i ].split( ':', 1 )[ 0 ]
									if user == addr:
										self.object[ 'kolabInvitationPolicy' ][ i ] = "%s:%s" % ( user, acl )
										break
							# ... otherwise insert it at the correct position
							else:
								if len(self.object[ 'kolabInvitationPolicy' ]) > 0 and  self.object[ 'kolabInvitationPolicy' ][ -1 ].find( ':' ) != -1:
									self.object["kolabInvitationPolicy"].append( "%s:%s"%(user, acl))
								else:
									self.object["kolabInvitationPolicy"].insert( -1, "%s:%s"%(user, acl))
			elif self.kolabIntevationPolicyRemoveButton["kolabInvitationPolicy"].pressed():
				# remove ACL
				acl = self.kolabIntevationPolicyList["kolabInvitationPolicy"].getselected()
				if acl:
					for acl_to_remove in acl:
						self.object["kolabInvitationPolicy"].remove(acl_to_remove)

		if hasattr(self,'positionbuttons'):
			for but in self.positionbuttons:
				if but.pressed():
					self.object=self.save.get('edit_object')
					if not self.object:
						return
					univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'cancel: load object')
					if hasattr(self.object, 'cancel'):
						univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'cancel: found')
						self.object.cancel()

					selected=but.args.get('helptext')
					if not selected:
						return

					self.save.put('browse_search_result', None)

					newpos=self.save.get('ldap_position')
					newpos.setDn(selected)
					self.save.put('ldap_position', newpos)

					self.save.put('edit_object', None)
					self.save.put('edit_object_opened', None)
					self.save.put('edit_invalid', None)
					self.save.put('edit_multiedit_overwrite', None)
					self.save.put("uc_module",return_to)
					self.save.put('tab', None)
					self.save.put('validtabs', None)
					for key in self.ginput.keys():
						self.save.put('membership_search_result'+key,None)
						self.save.put('membership_search_ok'+key,None)
						self.save.put('membership_search_value'+key,None)
						self.save.put('membership_search_property'+key,None)
					self.save.put('edit_policydn_preselect', None)
					self.save.put('edit_policy', None)
					self.save.put('edit_policy_original_reference', None)
					self.save.put('printer_manufacturer_selected',None)
					self.save.put('package_class_selected',None)

					self.userinfo(_("Position changed"))
					return

		if self.save.get('edit_dn'):
			add=0
			modify=1
			multiedit=0
		elif self.save.get('edit_dn_list'):
			add=0
			modify=0
			multiedit=1
		else:
			add=1
			modify=0
			multiedit=0

		if not hasattr(self, 'object'):
			self.object=self.save.get('edit_object')
			if not self.object:
				return

		if hasattr(self, 'edit_policy_cancel') and self.edit_policy_cancel.pressed():
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "modedit.apply: edit_policy_cancel")
			self.object.closePolicyObjects()
			original_reference=self.save.get('edit_policy_original_reference')
			if original_reference:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "modedit.apply: set original")
				univention.admin.objects.replacePolicyReference(self.object, self.save.get('edit_policy'), original_reference)
			else:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "modedit.apply: not set original")
			self.save.put('edit_object', self.object)
			self.save.put('edit_policydn_preselect', None)
			self.save.put('edit_policy', None)
			self.save.put('edit_policy_original_reference', None)
			self.save.put('tab', self.save.get('edit_policy_return_to_tab'))
			self.save.put('edit_policy_return_to_tab', None)
			return

		module=univention.admin.modules.get(self.save.get('edit_type'))
		properties=module.property_descriptions

		tab = self.save.get('tab')
		tabbing = self.tabbing
		tab = tabbing.name(tab)

		# general policy tabs (for containers only) or options tab
		if tabbing.is_policy_selection(tab) or tabbing.is_options(tab):
			if hasattr(self, 'policy_edit_buttons'):
				for policy_type, editbutton in self.policy_edit_buttons.items():
					if editbutton.pressed():
						univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "modedit.apply: edit policy of type %s" % (policy_type))
						self.save.put('edit_policy', policy_type)
						self.save.put('edit_policy_return_to_tab', tab)
						return
			if hasattr(self, 'policy_disconnect_button') and self.policy_disconnect_button.pressed() and hasattr(self, 'policy_disconnect_boxes'):
				for policy_type, checkbox in self.policy_disconnect_boxes.items():
					if checkbox.get_input():
						univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "modedit.apply: disconnect policy of type %s" % (policy_type))
						univention.admin.objects.removePolicyReference(self.object, policy_type)
						self.save.put('edit_object', self.object)
			if hasattr(self, 'option_checkboxes'):
				for name, checkbox in self.option_checkboxes.items():
					if ( not add and not module.options[ name ].editable ) or module.options[ name ].disabled:
						continue
					if checkbox.get_input() and not name in self.object.options:
						self.object.options.append(name)
					elif not checkbox.get_input() and name in self.object.options:
						self.object.options.remove(name)

		edit_policy=self.save.get('edit_policy')
		if edit_policy:
			current_module = univention.admin.modules.get(edit_policy)
		else:
			current_module = tabbing.module(tab)

		if hasattr(self, 'policydn_select_button') and self.policydn_select_button.pressed():
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'modedit.apply: selected policy dn: %s' % self.policydn_select.getselected())
			# backup of original policy reference (not neccessarily identical to that in self.object.oldpolicies)
			if not self.save.get('edit_policy_original_reference'):
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "modedit.apply: init set original")
				self.save.put('edit_policy_original_reference', univention.admin.objects.getPolicyReference(self.object, univention.admin.modules.name(current_module)))

			policy_preselect=self.save.get('edit_policydn_preselect')
			if not policy_preselect:
				policy_preselect={}
			selected=self.policydn_select.getselected()
			if selected == 'inherited':
				univention.admin.objects.removePolicyReference(self.object, univention.admin.modules.name(current_module))
			else:
				univention.admin.objects.replacePolicyReference(self.object, univention.admin.modules.name(current_module), selected)
			self.save.put('edit_object', self.object)
			policy_preselect[univention.admin.modules.name(current_module)]=selected
			self.save.put('edit_policydn_preselect', policy_preselect)
			return


		current_object=self.object
		if not current_module == module:
			current_object=self.object.loadPolicyObject(univention.admin.modules.name(current_module))

		# memorize the fields that are checked to be overwritten
		overwrite_fields=[]
		for key, checkbox in self.input_multiedit_overwrite.items():
			if checkbox.get_input():
				overwrite_fields.append(key)
		if overwrite_fields:
			self.save.put('edit_multiedit_overwrite', overwrite_fields)

		# check options of the current object
		check_options = make_options_check(current_object)

		invalid={}

		# copy single-value values to object
		for key, field in self.input.items():
			if multiedit and not key in overwrite_fields:
				continue

			property = current_module.property_descriptions[key]

			if univention.admin.objects.fixedAttribute(current_object, key) or not property.editable or \
				   check_options(property.options):
				continue
			if not add:
				if not property.may_change:
					continue
			new=None
			try:
				new=field.get_input()
				if property.syntax.name == "passwd" and not new:
					pass
				else:
					current_object[key]=new
			except univention.admin.uexceptions.valueError, e:
				invalid[key]=new
				self.userinfo_append('%s: %s' % (key, e.message))

		# copy first_only values to object
		for key, field in self.finput.items():
			property = current_module.property_descriptions[key]

			if univention.admin.objects.fixedAttribute(current_object, key) or not property.editable or \
				   check_options(property.options):
				continue

			new=None

			try:
				new_first=field.get_input()
				s=property.syntax
				try:
					p=s.parse(new_first)
				except univention.admin.uexceptions.valueError,e:
					try:
						raise univention.admin.uexceptions.valueInvalidSyntax, "%s: %s"%(property.short_description,e)
					except:
						raise univention.admin.uexceptions.valueInvalidSyntax, "%s"%property.short_description

				if not new_first and property.required and not multiedit:
					invalid[key]=""
					raise univention.admin.uexceptions.valueRequired, 'property %s required' % key
				elif not new_first:
					continue
				elif not current_object[key]:
					new=[new_first]
				else:
					new=current_object[key]
					new[0]=new_first
				current_object[key]=new
			except univention.admin.uexceptions.valueError, e:
				invalid[key]=new

		for key, mitem in self.xinput.items():
			property = current_module.property_descriptions[key]

			if univention.admin.objects.fixedAttribute(current_object, key) or \
				   check_options(property.options):
				continue
			if not key:
				continue
			new=current_object[key]
			if mitem[0].pressed():
				self.save.put("x_choice_value_of_%s"%key,mitem[1].getselected())

		for key, mitem in self.zinput.items():
			property = current_module.property_descriptions[key]

			if univention.admin.objects.fixedAttribute(current_object, key) or \
				   check_options(property.options):
				continue
			if not key:
				continue
			new=current_object[key]
			if mitem[0].pressed():
				self.save.put("z_choice_value_of_%s"%key,mitem[1].getselected())
		
		n_value=None
		n_button=False
		for key, registryitem in self.registryinput.items():
			if key == 'new_button':
				if registryitem.pressed():
					n_button=True
			elif key == 'new_value':
				n_value=registryitem.get_input()
			else:
				pos=0
				for v in current_object['registry']:
					if v.startswith('%s=' % key.split('=')[0]):
						current_object['registry'][pos]='%s=%s' %(key.split('=')[0],registryitem.get_input())
					pos=pos+1

			if n_value and n_button:

				new=current_object['registry']
				new.append( '%s=' % n_value )

				current_object['registry']=new
				n_value=None
				n_button=False

		# copy multi-value values to object
		for key, mitem in self.minput.items():

			property = current_module.property_descriptions[key]

			if univention.admin.objects.fixedAttribute(current_object, key) or \
				   check_options(property.options):
				continue
			if not key:
				continue
			new=current_object[key]

			if key == 'uri': # set printerURI
				if mitem[0].get_input() and mitem[6].get_input():
					new = mitem[0].get_input() + mitem[6].get_input()
				elif not multiedit or key in overwrite_fields:
					invalid[key]=new

			if key == 'dnsEntryZoneForward' or key == 'dnsEntryZoneReverse':
				if mitem[1].pressed():
					cpnew = copy.deepcopy( new )
					if mitem[0].get_input() and self.save.get( 'x_choice_value_of_%s' % key ):
						if self.save.get( 'x_choice_value_of_%s' % key ) + " " + mitem[0].get_input() not in cpnew:
							cpnew.append( self.save.get( 'x_choice_value_of_%s' % key ) + " " + mitem[0].get_input() )
					elif not multiedit or key in overwrite_fields:
						invalid[key]=new
					try:
						current_object[key]=cpnew
						new = cpnew
					except univention.admin.uexceptions.valueError, e:
						invalid[key]=new
			elif key == 'dhcpEntryZone':
				if mitem[1].pressed():
					cpnew = copy.deepcopy( new )
					if mitem[0].get_input() and self.save.get( 'x_choice_value_of_%s' % key ) and self.save.get( 'z_choice_value_of_%s' % key ):
						if self.save.get( 'x_choice_value_of_%s' % key ) + " " + self.save.get( 'z_choice_value_of_%s' % key ) + " " + mitem[0].get_input() not in cpnew:
							cpnew.append( self.save.get( 'x_choice_value_of_%s' % key ) + " " + mitem[0].get_input()+ " " + self.save.get( 'z_choice_value_of_%s' % key )  )
					elif not multiedit or key in overwrite_fields:
						invalid[key]=new
					try:
						current_object[key]=cpnew
						new = cpnew
					except univention.admin.uexceptions.valueError, e:
						invalid[key]=new
			else:
				if mitem[1].pressed():

					if not mitem[0].get_input() in new or (self.tinput.has_key( key) and len(self.tinput[key]) > 0 and self.tinput[key][0].get_input() ):
						cpnew=copy.deepcopy(new)
						if key == 'quotaGroups' or key == 'quotaUsers' or key == 'quotaGroupsPerUsers':
							cpnew.append([mitem[6].get_input(),mitem[7].get_input(),mitem[0].get_input()])

							if len(cpnew)>0:
								noDouble={}
								for entry in cpnew:
									if entry:
										noDouble[entry[2]]=[entry[0],entry[1]]

								cpnew=[]
								for tmpkey in noDouble.keys():
									cpnew.append([noDouble[tmpkey][0],noDouble[tmpkey][1],tmpkey])
						elif self.tinput.has_key(key) and len(self.tinput[key]) > 0 and self.tinput[key][0].get_input():
							if self.tinput[key][0].get_input():
								var = '%s:%s' % ( mitem[0].get_input(), self.tinput[key][0].get_input() )
								if not var in new:
									cpnew.append( var )
							else:
								cpnew.append('%s' % ( mitem[0].get_input() ) )
						else:
							cpnew.append(mitem[0].get_input())
						try:
							current_object[key]=cpnew
							new=cpnew
						except univention.admin.uexceptions.valueError, e:
							invalid[key]=new

			# remove
			if mitem[3].pressed():
				selected=mitem[2].getselected()
				selected.reverse()
				for value in selected:
					try:
						new.remove(current_object[key][int(value)])
					except ValueError:
						# maybe the value was not a integer, but a dn
						val = current_object[key].index( value )
						new.remove(current_object[key][val])
			# up
			elif len(mitem) > 4 and mitem[4].pressed():
				selected=mitem[2].getselected()
				for value in selected:
					if int(value)==0:
						# don't do anything if the first item is selected for moving
						break
					new.insert(new.index(current_object[key][int(value)])-1, new.pop(new.index(current_object[key][int(value)])))
			# down
			elif len(mitem) > 5 and mitem[5].pressed():
				selected=mitem[2].getselected()
				if selected:
					# start from bottom!
					selected.reverse()
				for value in selected:
					new.insert(new.index(current_object[key][int(value)])+1, new.pop(new.index(current_object[key][int(value)])))

			if key == 'listAttributes' or key == 'listNavigationAttributes': # listAttributes
				self.save.put('reload_settings', 'RELOAD')
			if multiedit and not key in overwrite_fields:
				continue

			try:
				current_object[key]=new
			except univention.admin.uexceptions.valueError, e:
				invalid[key]=new


		#primary group or other multivalues (desktop profile etc)
		for key, mitem in self.pinput.items():
			if key != 'profile':
				if univention.admin.objects.fixedAttribute(current_object, key):
					continue
				if not key:
					continue

				new = mitem.getselected()
				self.save.put( 'p_choice_value_of_%s' % key, mitem.getselected() )

				try:
					current_object[key] = new
				except univention.admin.uexceptions.valueError, e:
					invalid[key]=new

		#printer manufacturer selected
		if hasattr(self,'printermanuf') and  hasattr(self, 'search_property_button') and self.search_property_button.pressed():
			self.save.put('printer_manufacturer_selected',self.printermanuf.getselected())
		if hasattr(self,'pinput') and self.pinput.has_key('model'):
			self.save.put('printer_model_selected',self.pinput['model'].getselected())

		if hasattr(self,'packageclass'):
			self.save.put('package_class_selected',self.packageclass.getselected())


		#dns reverse entry
		for key, ritem in self.rinput.items():
			if univention.admin.objects.fixedAttribute(current_object, key):
				continue
			if not key:
				continue

			new = ritem.getselected()

			try:
				current_object[key] = new
			except univention.admin.uexceptions.valueError, e:
				invalid[key]=new

		# group membership
		for key, mitem in self.ginput.items():
			if univention.admin.objects.fixedAttribute(current_object, key):
				continue
			if not key:
				continue
			new=current_object[key]
			# group_add_button
			if mitem[2].pressed():
				for value in mitem[0].getselected():
					if new and new[0]:
						new.append(value)
					else:
						new=[value]
			# group_remove_button
			elif mitem[3].pressed():
				for value in mitem[1].getselected():
					new.remove(value)
			# search_property_select
			elif mitem[6].pressed():
				self.save.put("membership_search_property"+key,mitem[5].get_input())
				self.save.put("membership_search_ok"+key,None)
				self.save.put("membership_search_result"+key,None)
			elif mitem[4].pressed():
				try:
					self.save.put("membership_search_value"+key,mitem[7].get_input())
					if self.save.get("membership_search_property"+key)=="_":
						self.save.put("membership_search_result"+key,None)
				except:
					self.save.put("membership_search_value"+key,None)
				self.save.put("membership_search_ok"+key,1)	
			try:
				current_object[key]=new
			except univention.admin.uexceptions.valueError, e:
				invalid[key]=new

		self.save.put('edit_object', self.object)
		self.save.put('edit_invalid', invalid)

		if hasattr( self, 'ldap_search_buttons' ):
			for key, button in self.ldap_search_buttons.items():
				if button.pressed():
					attrs = self.lo.get( key )
					module = univention.admin.modules.identify( key, attrs )
					if module:
						obj = univention.admin.objects.get( module[ 0 ], None, self.lo, univention.admin.uldap.position( self.position.getBase() ), dn = key )
						self.save.put( 'edit_object', obj )
						self.save.put( 'edit_type', univention.admin.modules.name( module[ 0 ] ) )
						self.save.put( 'edit_dn', key )
						self.save.put( 'edit_object_opened', 0 )
						return
		if not invalid:
			if hasattr(self, 'edit_policy_ok') and self.edit_policy_ok.pressed():
				self.object.savePolicyObjects()
				self.save.put('edit_object', self.object)
				self.save.put('edit_policydn_preselect', None)
				self.save.put('edit_policy', None)
				self.save.put('edit_policy_original_reference', None)
				self.save.put('tab', self.save.get('edit_policy_return_to_tab'))
				self.save.put('edit_policy_return_to_tab', None)
				return

			if not edit_policy:
				validtabs=self.save.get("validtabs")
				if not validtabs:
					validtabs=[]
				if not tab in validtabs:
					validtabs.append(tab)
				self.save.put("validtabs", validtabs)

				if tab != self.save.get('tab') or tab != tabbing.at(self.nbook.getselected()):
					for key in self.ginput.keys():
						self.save.put('membership_search_result'+key,None)
						self.save.put('membership_search_ok'+key,None)
						self.save.put('membership_search_value'+key,None)
						self.save.put('membership_search_property'+key,None)			

				# change to selected tab
				if tab != self.save.get('tab'):
					self.save.put('tab', tab)
				else:
					self.save.put('tab', tabbing.at(self.nbook.getselected()))

			if hasattr(self, 'okbut') and self.okbut.pressed():
				nextrequired = self.get_nextrequired(current_module, current_object, tabbing.module_tabs(), validtabs, multiedit, check_options, tabbing.previoustabs, invalid)
				if nextrequired and nextrequired != tab:
					self.save.put('tab', nextrequired)
					return
				# catch exceptions
				try:
					if multiedit:

						self.multiedit_modify_status=[0, len(self.save.get('edit_dn_list')), 0]
						self.multiedit_errors = []
						position = self.object.position
						for dn, arg in self.save.get('edit_dn_list'):
							if self.cancel:
								raise SystemExit
							try:
								object=univention.admin.objects.get(module, None, self.lo, position, dn=dn, arg=arg)
								univention.admin.objects.open(object)
								for name in overwrite_fields:
									object[name]=self.object[name]
								object.modify()
							except univention.admin.uexceptions.base, ex:
								self.multiedit_modify_status[2] += 1
								self.multiedit_errors.append('%s: %s %s' % (dn,ex.message,unicode(ex)))
							self.multiedit_modify_status[0] += 1
						if self.multiedit_errors:
							self.usermessage(_("Modifying %d/%d objects failed: %s") % (self.multiedit_modify_status[2], self.multiedit_modify_status[1], string.join(self.multiedit_errors, '<br>')))
						else:
							self.userinfo(_("Modified %d/%d objects successfully.") % (self.multiedit_modify_status[0], self.multiedit_modify_status[1]))
					elif add:
						self.object.create()
					else:
						self.object.modify()

				except univention.admin.uexceptions.base, ex:
					self.usermessage(_("error while modifying: %s %s") % (ex.message,unicode(ex)))
					self.save.put('edit_object', self.object)
				except Exception, ex:
					self.object=self.save.get('edit_object')
					if self.object:
						univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'cancel_modify: load object')
						if hasattr(self.object, 'cancel'):
							univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'cancel_modify: found')
							self.object.cancel()
					try:
						if hasattr(ex,'message'):
							import traceback
							info = sys.exc_info()
							lines = traceback.format_exception(*info)
							univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'CAUGHT EXCEPTION!\n%s %s\n%s' %
												(ex.message,unicode(ex),''.join(lines)))
							self.usermessage(_("error while modifying: %s %s") % (ex.message,ex))
						else:
							import traceback
							info = sys.exc_info()
							lines = traceback.format_exception(*info)
							univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'CAUGHT EXCEPTION!\n%s\n%s' %
												(unicode(ex),''.join(lines)))
							self.usermessage(_("error while modifying: %s %s") % ("",ex))
					except UnicodeEncodeError, e: # raise fails if uid contains umlauts or other non-ASCII-characters
						self.usermessage(_("internal error: %s") % unicode( e ) )

					self.save.put('edit_object', None)
					self.save.put('edit_object_opened', None)
					self.save.put('edit_invalid', None)
					self.save.put('edit_multiedit_overwrite', None)
					self.save.put("uc_module",return_to)
					self.save.put('tab', None)
					self.save.put('validtabs', None)
					for key in self.ginput.keys():
						self.save.put('membership_search_result'+key,None)
						self.save.put('membership_search_ok'+key,None)
						self.save.put('membership_search_value'+key,None)
						self.save.put('membership_search_property'+key,None)
					self.save.put('printer_manufacturer_selected',None)
					self.save.put('package_class_selected',None)
				else:
					message_string = ''
					for obj, cmd, exception in self.object.exceptions:
						#FIXME: remove HTML code
						if exception:
							message_string+=_('While %s %s: %s<br>')% (cmd,obj, unicode(exception))
					if message_string:
						self.usermessage(message_string)

					if add:
						self.userinfo(_("Object created."))
					elif multiedit:
						self.userinfo(_("Objects modified."))
					else:
						self.userinfo(_("Object modified."))
					self.save.put('edit_object', None)
					self.save.put('edit_object_opened', None)
					self.save.put('edit_invalid', None)
					self.save.put('edit_multiedit_overwrite', None)
					self.save.put("uc_module",return_to)
					self.save.put('tab', None)
					self.save.put('validtabs', None)
					for key in self.ginput.keys():
						self.save.put('membership_search_result'+key,None)
						self.save.put('membership_search_ok'+key,None)
						self.save.put('membership_search_value'+key,None)
						self.save.put('membership_search_property'+key,None)
					self.save.put('printer_manufacturer_selected',None)
					self.save.put('package_class_selected',None)
				if okMessage and not self.save.get("usermessages"):
					self.usermessage(okMessage)




	def waitmessage(self):
		if hasattr(self, 'multiedit_modify_status'):
			return _('Modified %d/%d objects (%d errors).' % (self.multiedit_modify_status[0], self.multiedit_modify_status[1], self.multiedit_modify_status[2]))
		elif hasattr(self, 'save') and self.save.get('modedit_wait_message','') != '': # there seems to be a case where self.save isn't initialized, maybe if the process just finished
			waitMessage = self.save.get('modedit_wait_message','')
			self.save.put('modedit_wait_message', '')
			return waitMessage
		else:
			return _('The operation is in progress. Please wait.')

	def waitcancel(self):
		self.cancel = 1

		return_to=self.save.get('edit_return_to')
		if not return_to:
			return_to="browse"

		self.save.put('edit_object', None)
		self.save.put('edit_object_opened', None)
		self.save.put('edit_invalid', None)
		self.save.put('edit_multiedit_overwrite', None)
		self.save.put("uc_module",return_to)
		self.save.put('tab', None)
		self.save.put('validtabs', None)
		for key in self.ginput.keys():
			self.save.put('membership_search_result'+key,None)
			self.save.put('membership_search_ok'+key,None)
			self.save.put('membership_search_value'+key,None)
			self.save.put('membership_search_property'+key,None)
		self.save.put('printer_manufacturer_selected',None)
		self.save.put('package_class_selected',None)

	def get_nextrequired(self, module, object, layout, validtabs, multiedit, check_options, previous, invalid):
		for tab in layout:
			description = tab.short_description
			if description in validtabs:
				continue
			for line in tab.fields:
				for row in line:
					if isinstance(row, univention.admin.field):
						row = [row]
					for field in row:
						name = field.property
						if module.property_descriptions.has_key(name):
							property = module.property_descriptions[name]
							if property.required and not multiedit:
								if not object.has_key(name) or not object[name]:
									if check_options(property.options):
										continue
									return self.get_previous_nextrequired(description, name, validtabs, previous(description))
							else:
								try:
									property.check_default(object)
								except univention.admin.uexceptions.templateSyntaxError, ex:
									invalid[name] = property.safe_default(object)
									self.userinfo(ex.message % string.join(ex.templates, ', '))
									return description
		return None

	def get_previous_nextrequired(self, default, name, validtabs, layout):
		# check for required fields that are displayed more than once
		# should not be neccessary but still...
		for tab in reversed(list(layout)):
			if tab.short_description in validtabs:
				continue
			for line in tab.fields:
				for row in line:
					if isinstance(row, univention.admin.field):
						row = [row]
					for field in row:
						if field.property == name:
							return tab.short_description
		return default
