# -*- coding: utf-8 -*-
#
# Univention Admin
#  the navigation module
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
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
from uniparts import *
from local import _
from syntax import *

import univention.debug
import univention.admin.uldap
import univention.admin.modules
import univention.admin.objects
import unimodule

import string
import ldap
import types
import re

def create(a,b,c):
	return modbrowse(a,b,c)

def myinfo(settings):
	if settings.listAdminModule('modbrowse'):
		return unimodule.realmodule("browse", _("Browse"), _("Browse LDAP directory"))
	else:
		return unimodule.realmodule("browse", "", "")

def myrgroup():
	return _("Account Operators")
def mywgroup():
	return _("Account Operators")
def mymenunum():
	return 100
def mysubmodules():
	return []
def mymenuicon():
	return '/icon/browse.gif'

class modbrowse(unimodule.unimodule):
	def mytype(self):
		return "dialog"

	def mydescription(self):
		return mydescription()

	def mysubmodules(self):
		return mysubmodules()

	# This method displays the dialog that asks the user to confirm the
	# list of objects to remove. It is called if "removelist" is set.
	def delmode(self, removelist):
		position=self.position

		self.subobjs.append(table("",
					  {'type':'content_header'},
					  {"obs":[tablerow("",{},{"obs":[tablecol("",{'type':'browse_layout'},{"obs":[]})]})]}))

		self.nbook=notebook('', {}, {'buttons': [(_('delete'), _('delete'))], 'selected': 0})
		self.subobjs.append(self.nbook)

		#begin table:
		rows=[tablerow("",{},{"obs":[tablecol("",{'type':'browse_layout'},{"obs":[header(_("%d Object(s) Selected for Removal") % len(removelist),{"type":"3"},{})]})]})]
		cols=[]
		cols.append(tablecol("",{'type':'browse_layout'},{"obs":[header(_("Object"),{"type":"6"},{})]}))
		cols.append(tablecol("",{'type':'browse_layout'},{"obs":[header(_("Location"),{"type":"6"},{})]}))
		cols.append(tablecol("",{'type':'browse_layout'},{"obs":[header(_("Delete?"),{"type":"6"},{})]}))
		cols.append(tablecol("",{'type':'browse_layout'},{"obs":[header(_("Delete referring objects?"),{"type":"6"},{})]}))
		rows.append(tablerow("",{'type':'browse_layout'},{"obs": cols}))

		rows.append(tablerow("",{},{"obs": [
			tablecol("",{'type':'browse_layout'},{"obs":[space('',{'size':'1'},{})]}),
			tablecol("",{'type':'browse_layout'},{"obs":[space('',{'size':'1'},{})]}),
			tablecol("",{'type':'browse_layout'},{"obs":[space('',{'size':'1'},{})]}),
			tablecol("",{'type':'browse_layout'},{"obs":[space('',{'size':'1'},{})]}),
		]}))

		removelist_withcleanup=[]

		self.ignore_buttons=[]
		self.final_delboxes=[]
		self.cleanup_delboxes=[]
		for i in removelist:
			cols=[]
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "creating object handler")
			object_module=univention.admin.modules.get(i[1])
			object=univention.admin.objects.get(object_module, None, self.lo, self.position, dn=i[0], arg=i[2])
			object_type=univention.admin.objects.module(object)

			# We need to verify that the objects still exist. When a multidelete operation
			# is canceled, for example, there will be objects that don't exist anymore.
			if not object.dn:
				removelist.remove(i)
				continue

			icon_path='/icon/'+object_type+'.gif'
			if not os.path.exists('/usr/share/univention-admin/www'+icon_path):
				icon_path='/icon/'+object_type+'.png'
				if not os.path.exists('/usr/share/univention-admin/www'+icon_path):
					icon_path='/icon/generic.gif'

			name=univention.admin.objects.description(object)
			description=univention.admin.modules.short_description(object_module)

			object_button=button(name,{'icon':icon_path, 'passive':"1"},{'helptext':_('%s object') % description})
			self.ignore_buttons.append(object_button)
			cols.append(tablecol("",{'type':'browse_layout'},{"obs":[object_button]}))

			locationpos=univention.admin.uldap.position(self.position.getBase())
			locationpos.setDn(object.dn)
			if not hasattr(object, 'superordinate') or not object.superordinate or not object.dn == object.superordinate.dn:
				locationpos.switchToParent()
			location=text('',{},{'text':[locationpos.getPrintable(long=1)]})
			cols.append(tablecol("",{'type':'browse_layout'},{"obs":[location]}))

			final_delete=question_bool('',{},{'usertext':"1",'helptext':_('select %s') % name})
			self.final_delboxes.append((final_delete, object.dn, object_type, univention.admin.objects.arg(object)))
			cols.append(tablecol("",{'type':'browse_layout'},{"obs":[final_delete]}))

			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "check if cleanup neccessary: %s" % i[0])
			if univention.admin.objects.wantsCleanup(object):
				removelist_withcleanup.append(i)
				cleanup_delete=question_bool('',{},{'helptext':_('select %s') % name})
				self.cleanup_delboxes.append((cleanup_delete, object.dn, object_type, univention.admin.objects.arg(object)))
				cols.append(tablecol("",{'type':'browse_layout'},{"obs":[cleanup_delete]}))
			else:
				cols.append(tablecol("",{'type':'browse_layout'},{"obs":[text('',{},{'text':[""]})]}))
			rows.append(tablerow("",{},{"obs":cols}))

		if removelist_withcleanup:
			self.save.put('removelist_withcleanup', removelist_withcleanup)

		# generate table
		main_rows = []
		main_rows.append(
			tablerow("",{},{"obs":[tablecol("",{'type':'content_main'},{"obs":[table("",{"type":"content_list"},{"obs":rows})]})]})
		)
		#end table
		self.final_delbut=button(_('OK'),{'icon':'/style/ok.gif'},{'helptext':_('Really delete selected objects and referring objects if enabled.')})
		self.cancel_delbut=button(_("Cancel"),{'icon':'/style/cancel.gif'},{"helptext":_("Cancel")})

		main_rows.append(
			tablerow("",{},{"obs":[tablecol("",{'type':'content_main'},{"obs":[self.final_delbut, self.cancel_delbut]})]})
		)
		# main table
		self.subobjs.append(table("",
					  {'type':'content_main'},
					  {"obs":[tablerow("",{},{"obs":[tablecol("",{'type':'content_main'},{"obs":main_rows})]})]})
				    )



	def myinit(self):
		self.save=self.parent.save
		if self.inithandlemessages():
			return
		settings=self.save.get('settings')

		self.lo=self.args["uaccess"]
		position=self.save.get('ldap_position')
		self.position=position

		# removelist is a list of DNs the user has selected to be removed.
		# We ask the user to confirm the selected list of DNs.
		if self.save.get("removelist"):
			self.delmode(self.save.get("removelist"))
			return

		# move_dn_list is a list of DNs that are being moved. If it is set,
		# we are in "select target" mode. That means, the user browses to
		# the location to move the objects to and presses the "Move here"
		# button. We don't allow objects to be edited or the like. If the
		# cancel button is pressed, we leave the "select target" mode and
		# return to the previous location
		move_dn_list=self.save.get('browse_move_dn_list')

		if not position.getDn().endswith(settings.base_dn):
			position.setDn(settings.base_dn)

		###########################################################################
		# current object
		###########################################################################

		module=univention.admin.modules.identifyOne(position.getDn(), self.lo.get(position.getDn()))
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'module: %s' % univention.admin.modules.name(module))
		object=univention.admin.objects.get(module, None, self.lo, position, dn=position.getDn())

		shadow_module, shadow_object=univention.admin.objects.shadow(self.lo, module, object, position)
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'shadow module: %s' % univention.admin.modules.name(shadow_module))
		if shadow_object:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'shadow object: %s' % str(shadow_object.items()))
			pass
		else:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'shadow object: none')
			pass

		sub_types=[]
		sub_modules=[]
		for m in univention.admin.modules.subordinates(shadow_module):
			sub_modules.append(m)
			sub_types.append(univention.admin.modules.name(m))
		for m in univention.admin.modules.containers:
			if univention.admin.modules.name(m) == 'container/dc':
				continue
			sub_modules.append(m)
			sub_types.append(univention.admin.modules.name(m))

		cols=[]

		###########################################################################
		# position
		###########################################################################

		# If base dn is "dc=foo,dc=bar" and settings.base_dn is "cn=users,dc=foo,dc=bar",
		# create string root_label "foo.bar/users/"

		domain_components=univention.admin.uldap.explodeDn(position.getBase(), 1)
		root_components=univention.admin.uldap.explodeDn(settings.base_dn, 1)[0:-len(domain_components)]
		root_label=string.join(domain_components, '.')
		if root_components:
			root_label = root_label+'/'+string.join(root_components, '/')

		# Create list of "buttons" (label, dn). The last entry is the current DN and
		# will hence be displayed as a label rather than a button
		current_dn = settings.base_dn
		buttons = [(root_label, current_dn)]

		self.positionbuttons = []
		positioncolcontent = []

		path_components=univention.admin.uldap.explodeDn(position.getDn(), 0)[0:-len(domain_components)-len(root_components)]
		path_components.reverse()
		for p in path_components:
			label = p[p.find('=')+1:]
			current_dn = p+','+current_dn
			buttons.append((label, current_dn))

		for label, dn in buttons[:-1]:
			positionbutton = button("%s" % label, {"link": "1"}, {"helptext": dn})
			self.positionbuttons.append(positionbutton)
			positioncolcontent.append(positionbutton)
			positioncolcontent.append(text("",{},{"text":["/"]}))

		positioncolcontent.append(text("",{},{"text":[buttons[-1][0]]}))

		header_rows = []
		main_rows = []

		header_rows.append(tablerow("",{},{"obs":[tablecol("",{'colspan':'4','type':'content_position'},{"obs":[text("",{},{"text":["%s /" % _("Position:")]})] + positioncolcontent})]}))

		###########################################################################
		# add select
		###########################################################################

		self.add_button = button(_('add'),{},{'helptext':_('add new object of selected type at current position')})
		add_types = []

		list_types = []
		try:
			policies=self.lo.getPolicies(position.getDn())
			list_types=policies['univentionPolicyAdminContainerSettings']['univentionAdminListModules']['value']
		except KeyError:
			pass
		for m in sub_modules:
			if not univention.admin.modules.supports(m, 'add') or list_types and\
					not univention.admin.modules.name(m) in list_types:
				continue
			add_types.append({'name': univention.admin.modules.name(m), 'description': univention.admin.modules.short_description(m)})
		add_types.sort()
		add_types.insert(0, {'name': "uidummy098", 'description': _("Make your choice...")})
		self.add_select=question_select(_('add new object at current position'),{},{"helptext":_("select type of object to add"),"choicelist":add_types,"button":self.add_button})

		cols.append(tablecol('',{'colspan':'2','type':'browse_layout'},{'obs':[self.add_select]}))

		###########################################################################
		# first table: position + add
		###########################################################################

		tobs2=[table("",{},{"obs":[tablerow("",{},{"obs":cols})]})]

		if move_dn_list:
			header_rows.append(tablerow("",{},{"obs":[tablecol("",{'colspan':'4','type':'content_header'},{"obs":[header(_("Select target to move %d object(s) to") % len(move_dn_list), {"type": "1"}, {})]})]}))
			self.nbook=notebook('', {}, {'buttons': [(_('move'), _('move selected objects'))], 'selected': 0})
		else:
			main_rows.append(tablerow("",{},{"obs":[tablecol("",{'type':'content_header'},{"obs":tobs2})]}))
			self.nbook=notebook('', {}, {'buttons': [(_('browse'), _('browse LDAP'))], 'selected': 0})

		# build header-table
		self.subobjs.append(table("",{'type':'content_header'},{"obs":header_rows}))
		self.subobjs.append(self.nbook)


		###########################################################################
		# search select
		###########################################################################

		visible=self.save.get('browse_search_visible', 20)
		if visible > 1000:
			visible=1000
		start=self.save.get('browse_table_start', 0)

		search_type=self.save.get('browse_search_type')
		if not search_type or (not search_type == 'none' and not search_type == 'any' and not search_type in sub_types):
			search_type='any'

		searchcols=[]

		search_types=[]
		search_types.append({'name': 'any', 'description': _('any')})
		search_types.append({'name': 'none', 'description': _('none')})

		for m in sub_modules:
			if univention.admin.modules.childs(m) or not univention.admin.modules.supports(m, 'search'):
				continue
			name=univention.admin.modules.name(m)
			search_types.append({'name': name, 'description': univention.admin.modules.short_description(m)})
			if not search_type or search_type == name:
				search_type=name
		search_types.sort()
		for i in search_types:
			if search_type == i['name']:
				i['selected']='1'

		if search_type == 'any' or search_type == 'none':
			search_property_select=text('',{},{'text':['']})
			search_input=text('',{},{'text':['']})
		else:
			search_module=univention.admin.modules.get(search_type)

			search_property_name=self.save.get('browse_search_property')
			if not search_module.property_descriptions.has_key(search_property_name):
				search_property_name='*'

			search_properties=[]
			search_properties.append({'name': '*', 'description': _('any')})

			for name, property in search_module.property_descriptions.items():
				if not (hasattr(property, 'dontsearch') and property.dontsearch==1):
					search_properties.append({'name': name, 'description': property.short_description})

			search_properties.sort()

			for i in search_properties:
				if i['name']==search_property_name:
					i['selected']='1'

			if search_property_name != '*':
				search_property=search_module.property_descriptions[search_property_name]
				search_value=self.save.get('browse_search_value')
				self.search_input=question_property('',{},{'property': search_property, 'value': search_value, 'search': '1', 'lo': self.lo})
			else:
				search_value='*'
				self.search_input=text('',{},{'text':['']})

			self.search_property_button=button('go',{},{'helptext':'go'})# TODO helptext
			self.search_property_select=question_select(_('property'),{'width':'200'},{'helptext':_('property'),'choicelist':search_properties,'button':self.search_property_button}) # TODO helptext

			# make fields available in apply
			search_property_select=self.search_property_select
			search_input=self.search_input

		self.search_type_button=button(_('go'),{},{'helptext':_('go')})# TODO helptexs
		self.search_type_select=question_select(_('type'),{'width':'200'},{"helptext":_('type'),"choicelist":search_types,'button':self.search_type_button})# TODO helptext
		self.search_button=button(_('show'),{'icon':'/style/ok.gif'},{'helptext':_('show')})# TODO helptext
		self.search_visible=question_text(_('results per page'), {'width':'100'}, {'usertext': str(visible)})

		searchcols.append(tablecol('',{'type':'browse_layout'},{'obs':[self.search_type_select]}))
		searchcols.append(tablecol('',{'type':'browse_layout'},{'obs':[search_property_select]}))
		searchcols.append(tablecol('',{'type':'browse_layout'},{'obs':[search_input]}))
		main_rows.append(tablerow("",{},{"obs":[tablecol("",{},{"obs":[table("",{},{"obs":[tablerow('',{},{'obs':searchcols})]})]})]}))

		searchcols=[]
		searchcols.append(tablecol('',{'type':'browse_layout'},{'obs':[self.search_visible]}))
		searchcols.append(tablecol('',{'type':'browse_layout_bottom'},{'obs':[self.search_button]}))
		main_rows.append(tablerow("",{},{"obs":[tablecol("",{},{"obs":[table("",{},{"obs":[tablerow('',{},{'obs':searchcols})]})]})]}))

		main_rows.append(tablerow("",{},{"obs":[tablecol("",{},{"obs":[space('',{'size':'1'},{})]})]}))

		###########################################################################
		# lookup objects
		###########################################################################

		max_results=1000 # maximum number of results searched, should be configurable. This is more than the number of results that can be displayed !
		size_limit_reached = 0

		cached = 1
		result=self.save.get('browse_search_result')
		if not result:
			cached = 0
			result=[]

		if self.save.get('reload_settings'):
			self.save.put('reload_settings', None)
			settings.reload(self.lo)
		navigation_attributes = settings.getListNavigationAttributes( )
		for i in range(0, len(navigation_attributes)):
			m=univention.admin.modules.get(navigation_attributes[i][1])
			key=navigation_attributes[i][0]
			if m.property_descriptions.has_key(key) and m.property_descriptions[key].short_description:
				navigation_attributes[i][2] =  m.property_descriptions[key].short_description
		nresults = len(result)
		if not result:
			try:
				# recompute nresult after each search so that we can pass a sensible size-limit
				nresults=0
				if object and settings.listObject(object):
					result.append(object)

				# container
				for sub_module in sub_modules:
					if not univention.admin.modules.childs(sub_module):
						continue
					for o in univention.admin.modules.lookup(sub_module, None, self.lo, base=position.getDn(), scope='base', superordinate=shadow_object, timeout=-1, sizelimit=max_results-nresults):
						if univention.admin.objects.module(o) == univention.admin.objects.module(object):
							continue
						result.append(o)
						nresults+=1
					tmpresult=settings.filterObjects(univention.admin.modules.lookup(sub_module, None, self.lo, base=position.getDn(), scope='one', superordinate=shadow_object, timeout=-1, sizelimit=max_results-nresults))
					already_open=False
					for i in range(0, len(navigation_attributes)):
						key=navigation_attributes[i][0]
						if sub_module.property_descriptions.has_key(key) and sub_module.property_descriptions[key].short_description:
							for i in tmpresult:
								univention.admin.objects.open(i)
								already_open=True
						if already_open:
							break
					result+=tmpresult
					nresults=len(result)


				# search module(s)
				if search_type == 'any':
					for m in sub_modules:
						if univention.admin.modules.childs(m) or univention.admin.modules.virtual(m):
							continue
						tmpresult=settings.filterObjects(univention.admin.modules.lookup(m, None, self.lo, base=position.getDn(), filter='', scope='base+one', superordinate=shadow_object, timeout=-1, sizelimit=max_results-nresults))
						already_open=False
						for i in range(0, len(navigation_attributes)):
							key=navigation_attributes[i][0]
							if m.property_descriptions.has_key(key) and m.property_descriptions[key].short_description:
								for i in tmpresult:
									univention.admin.objects.open(i)
									already_open=True
							if already_open:
								break
						result+=tmpresult
						nresults=len(result)
				elif search_type == 'none':
					pass
				else:
					if search_property_name != '*':
						filter=univention.admin.filter.expression(search_property_name, search_value)
					else:
						filter=''
					tmpresult=settings.filterObjects(univention.admin.modules.lookup(search_module, None, self.lo, base=position.getDn(), filter=filter, scope='base+one', superordinate=shadow_object, timeout=-1, sizelimit=max_results-nresults))
					already_open=False
					for i in range(0, len(navigation_attributes)):
						key=navigation_attributes[i][0]
						if m.property_descriptions.has_key(key) and m.property_descriptions[key].short_description:
							for i in tmpresult:
								univention.admin.objects.open(i)
								already_open=True
					if not already_open:
						if search_property_name != '*':
							for i in tmpresult:
								if not i.has_key(search_property_name) or not i[search_property_name]:
									univention.admin.objects.open(i)
					result.extend(tmpresult)
					nresults=len(result)
			except univention.admin.uexceptions.ldapError, msg:
				size_limit_reached = 1
				result = []

			sorted=[]
			# sort items
			sorting_helper_list=[]
			sorting_helper_dict={}
			for nx in range(len(result)):
				sorting_helper_name=univention.admin.objects.description(result[nx])
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'modbrowse: sorting: sorting-helper-name=%s' % sorting_helper_name)
				if not sorting_helper_list.count(sorting_helper_name):
					sorting_helper_list.append(sorting_helper_name)
				if not sorting_helper_dict.has_key(sorting_helper_name):
					sorting_helper_dict[sorting_helper_name]=[]
				sorting_helper_dict[sorting_helper_name].append(nx)
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'modbrowse: sorting: helper_dict=%s' % sorting_helper_dict)
			def caseigncompare(a, b):
				a2=a.upper()
				b2=b.upper()
				if a2 == b2:
					# fallback to casecompare
					if a == b:
						return 0
					l=[a, b]
					l.sort()
					if l.index(a) < l.index(b):
						return -1
					else:
						return 1

				l=[a2, b2]
				l.sort()

				if l.index(a2) < l.index(b2):
					return -1
				else:
					return 1
			sorting_helper_list.sort(caseigncompare)
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'modbrowse: sorting: helper_list=%s' % sorting_helper_list)

			# add current first...
			for helper in sorting_helper_list:
				for nx in sorting_helper_dict[helper]:
					if result[nx] == object:
						univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'modbrowse: sorting: appending %s' % result[nx])
						sorted.append(result[nx])
			# then add containers...
			childs=['container/dc', 'container/cn', 'container/ou', 'dhcp/service', 'dhcp/shared', 'dhcp/subnet', 'dhcp/sharedsubnet', 'dns/forward_zone', 'dns/reverse_zone', 'settings/cn', 'settings/admin']
			for child in range(len(childs)):
				for helper in sorting_helper_list:
					for nx in sorting_helper_dict[helper]:
						sorting_helper_sub_object_type=univention.admin.objects.module(result[nx])
						sorting_helper_sub_object_module=univention.admin.modules.get(sorting_helper_sub_object_type)
						if univention.admin.modules.childs(sorting_helper_sub_object_module) and sorting_helper_sub_object_type == childs[child] and not result[nx] == object:
							univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'modbrowse: sorting: appending %s' % result[nx])
							sorted.append(result[nx])

			# then add other objects
			for helper in sorting_helper_list:
				for nx in sorting_helper_dict[helper]:
					sorting_helper_sub_object_type=univention.admin.objects.module(result[nx])
					sorting_helper_sub_object_module=univention.admin.modules.get(sorting_helper_sub_object_type)
					if not univention.admin.modules.childs(sorting_helper_sub_object_module) and not result[nx] == object:
						univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'modbrowse: sorting: appending %s' % result[nx])
						sorted.append(result[nx])

			result=sorted

			self.save.put('browse_search_result', result)
			self.save.put('browse_search_do', None)


		###########################################################################
		# listing head
		###########################################################################

		# list
		self.dirbuts=[]
		self.editbuts=[]
		self.delboxes=[]

		dirrows=[]
		cols=[]
		cols.append(tablecol("",{'type':'browse_layout'},{"obs":[header(_("Object"),{"type":"6"},{})]}))
		cols.append(tablecol("",{'type':'browse_layout'},{"obs":[header(_("Type"),{"type":"6"},{})]}))
		old_search_property_name=self.save.get('browse_old_search_property')
		old_search_type=self.save.get('browse_old_search_type')
		for i in range(0, len(navigation_attributes)):
			cols.append(tablecol("",{'type':'browse_layout'},{"obs":[header(navigation_attributes[i][2],{"type":"6"},{})]}))
		if old_search_type and old_search_type != 'any' and old_search_property_name and old_search_property_name != '*':
			search_module=univention.admin.modules.get(old_search_type)
			old_search_property=search_module.property_descriptions[old_search_property_name]
			cols.append(tablecol("",{'type':'browse_layout'},{"obs":[header(old_search_property.short_description,{"type":"6"},{})]}))
		if not move_dn_list:
			cols.append(tablecol("",{'type':'browse_layout'},{"obs":[header(_("Select"),{"type":"6"},{})]}))
		dirrows.append(tablerow("",{'type': 'header'},{"obs": cols}))

		# switch to parent directory
		if not position.isBase():
			t=button(_('up'),{'icon':'/icon/up.gif'},{"helptext":_("switch to parent directory")}) # ICON
			self.dirbuts.append((t,self.lo.parentDn(position.getDn()), ''))
			iconcols=[
				tablecol("",{'type':'browse_layout'},{"obs":[t]}),
				tablecol("",{'type':'browse_layout'},{"obs":[]}),
				]
			if not move_dn_list:
				iconcols.append(tablecol("",{'type':'browse_layout'},{"obs":[]}))
			if old_search_type and old_search_type != 'any' and old_search_property_name and old_search_property_name != '*':
				iconcols.append(tablecol("",{'type':'browse_layout'},{"obs":[]}))
			dirrows.append(tablerow("",{},{"obs":iconcols}))

		###########################################################################
		# listing objects
		###########################################################################

		if nresults > 0:
			if cached:
				main_rows.append(tablerow("",{},{"obs":[tablecol("",{'type':'browse_layout'},{"obs":[header(_("%d search result(s) (cached):") % nresults,{"type":"2"},{})]})]}))
			else:
				main_rows.append(tablerow("",{},{"obs":[tablecol("",{'type':'browse_layout'},{"obs":[header(_("%d search result(s):") % nresults,{"type":"2"},{})]})]}))

		for sub_object in result[start:start+visible]:
			valid=1
			if not hasattr(sub_object, 'dn') or not sub_object.dn:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'object does not seem valid, skipping')
				continue

			cols=[]

			sub_object_type=univention.admin.objects.module(sub_object)
			sub_object_module=univention.admin.modules.get(sub_object_type)

			rdn=univention.admin.uldap.explodeDn(sub_object.dn, 1)[0]

			domain=univention.admin.uldap.explodeDn(sub_object.dn, 0)[0]
			domainContainer, ign = string.split(domain,"=")
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "rdn = "+domainContainer)

			icon_path='/icon/'+sub_object_type+'.gif'
			if os.path.exists('/usr/share/univention-admin/www'+icon_path):
				pass
			elif os.path.exists('/usr/share/univention-admin/www'+'/icon/'+sub_object_type+'.png'):
				icon_path='/icon/'+sub_object_type+'.png'
			elif univention.admin.modules.childs(sub_object_module):
				icon_path='/icon/folder.gif'
			else:
				icon_path='/icon/generic.gif'


			if position.isDomain() and not rdn in ['dhcp', 'dns', 'policies'] and not domainContainer in ['dc','ou','cn','uid','l','o','c','sambaDomainName']:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "Ignore rdn = "+rdn)
				valid=0

			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'processing object: %s' % sub_object.dn)

			if not object:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'object was deleted: %s' % sub_object.dn)
				continue
			else:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'object was not deleted: %s' % sub_object.dn)
				pass

			if sub_object.dn == object.dn and sub_object.module == object.module:
				name=_('(current)')
			else:
				name=univention.admin.objects.description(sub_object)
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'object %s name = %s ' % (sub_object.dn,name))

			open_button=icon('',{'url':'/icon/empty.gif'},{}) # ICON

			if valid:
				if univention.admin.modules.childs(sub_object_module) and not object.dn == sub_object.dn:
					atts={'icon':icon_path}
					if move_dn_list:
						for dn, arg, _type in move_dn_list:
							if dn == sub_object.dn:
								atts['passive']='1'
								break
					edit_button=button(name,atts,{'helptext':_('open "%s"') % univention.admin.objects.description(sub_object)})
				else:
					atts={'icon':icon_path}
					if move_dn_list:
						atts['passive']='1'
					edit_button=button(name,atts,{'helptext':_('edit "%s"') % univention.admin.objects.description(sub_object)})
				self.editbuts.append((edit_button, sub_object.dn, sub_object_type, univention.admin.objects.arg(sub_object)))
			else:
				edit_button=button(name,{'icon':icon_path,'passive':'1'},{'helptext':_('edit "%s"') % univention.admin.objects.description(sub_object)})
			cols.append(tablecol("",{'type':'browse_layout'},{"obs":[open_button, edit_button]}))

			objecttype=text('',{},{'text':[univention.admin.modules.short_description(sub_object_module)]})
			cols.append(tablecol("",{'type':'browse_layout'},{"obs":[objecttype]}))

			for i in range(0, len(navigation_attributes)):
				key=navigation_attributes[i][0]
				displayvalue=''
				if sub_object.has_key(key):
					tmpvalue=sub_object[key]
					if type(tmpvalue) is not types.ListType:
						displayvalue=[tmpvalue]
					else:
						displayvalue=tmpvalue
				property_text=text('',{},{'text':displayvalue})
				cols.append(tablecol("",{'type':'browse_layout'},{"obs":[property_text]}))
			if old_search_property_name and old_search_property_name != '*' and sub_object.has_key(old_search_property_name) and sub_object[old_search_property_name]:
				tmpvalue=sub_object[old_search_property_name]
				if type(tmpvalue) is not types.ListType:
					displayvalue=[tmpvalue]
				else:
					stop=0
					old_search_value=self.save.get('browse_old_search_value')
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 're search_value: %s' % old_search_value)
					if not old_search_value:
						stop=1
					try:
						_re=re.compile(old_search_value)
					except Exception, e:
						try:
							_re=re.compile(re.sub("\\*", ".*", old_search_value))
						except Exception, e:
							stop=1
					if not stop:
						displayvalue=[]
						for i in tmpvalue:
							if _re.search(i):
								displayvalue.append(i)
					else:
						displayvalue=tmpvalue
				property_text=text('',{},{'text':displayvalue})
				cols.append(tablecol("",{'type':'browse_layout'},{"obs":[property_text]}))
			elif old_search_property_name and old_search_property_name != '*':
				cols.append(tablecol("",{'type':'browse_layout'},{"obs":[text('',{},{'text':''})]}))

			# not current
			if not move_dn_list and not (sub_object.dn == object.dn and sub_object.module == object.module) and not (hasattr(univention.admin.modules.get(sub_object.module),'operations') and not 'remove' in univention.admin.modules.get(sub_object.module).operations):

				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'allowed to delete object %s / module %s'%(name,sub_object.module))
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'sub_object: %s'%(sub_object))


				if hasattr(sub_object, 'arg'):
					arg=sub_object.arg
				else:
					arg=None
				selected_dns=self.save.get('browse_selected_dns', {})
				if selected_dns.get((sub_object.dn, univention.admin.modules.name(sub_object_type), arg)):
					selected = '1'
				else:
					selected = ''
				delete=question_bool('',{},{'usertext': selected, 'helptext':_('select %s') % univention.admin.objects.description(sub_object)})
				self.delboxes.append((delete, sub_object.dn, sub_object_type, univention.admin.objects.arg(sub_object)))

				cols.append(tablecol("",{'type':'browse_layout'},{"obs":[delete]}))
			elif not move_dn_list:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'not allowed to delete object %s / module %s'%(name,sub_object.module))
				cols.append(tablecol("",{'type':'browse_layout'},{"obs":[]}))
			dirrows.append(tablerow("",{},{"obs":cols}))

		###########################################################################
		# delete, move, edit buttons
		###########################################################################

		colspan=2+len(navigation_attributes)
		if old_search_property_name and old_search_property_name != '*':
			colspan+=1
		colspan=str(colspan)

		self.selection_commit_button=button(_("Do"),{},{"helptext":_("Do action with selected objects.")})
		self.selection_select=question_select(_('Do with selected objects...'),{'width':'200'},{"helptext":_("Do with selected objects..."),"choicelist":[
			{'name': "uidummy098", 'description': "---"},
			{'name': "invert", 'description': _("Invert selection")},
			{'name': "edit", 'description': _("Edit")},
			{'name': "delete", 'description': _("Delete")},
			{'name': "recursive_delete", 'description': _("Delete recursively")},
			{'name': "move", 'description': _("Move")},
		],"button":self.selection_commit_button})
		if not move_dn_list:
			dirrows.append(tablerow("",{'type':'footer'},{"obs":[
				tablecol("",{"colspan":colspan, 'type':'browse_layout'},{"obs":[]}),
				tablecol("",{'type':'browse_layout'},{"obs":[self.selection_select]}),
			]}))

		self.dirstab=longtable("",{'total': str(len(result)), 'start': str(start), 'visible': str(visible)},{"obs":dirrows})
		main_rows.append(tablerow("",{},{"obs":[tablecol("",{},{"obs":[self.dirstab]})]}))

		if move_dn_list:
			self.move_here_button=button(_("Move here"),{'icon':'/style/ok.gif'},{"helptext":_("move selected objects here")})
			self.cancel_move_button=button(_("Cancel"),{'icon':'/style/cancel.gif'},{"helptext":_("cancel moving object")})
			main_rows.append(tablerow("",{},{"obs":[tablecol("",{'type':'browse_layout'},{"obs":[self.move_here_button,self.cancel_move_button]})]}))

		if size_limit_reached:
			main_rows.append(tablerow("",{},{"obs":[tablecol("",{'type':'browse_layout'},{"obs":[header(_("More than %d results, please refine search filter.") % max_results, {"type":"2"},{})]})]}))

		self.subobjs.append(table("",
					  {'type':'content_main'},
					  {"obs":main_rows})
				    )

	def apply(self):
		if self.applyhandlemessages():
			return

		self.cancel = 0

		self.save.put('validtabs', None)

		position=self.save.get('ldap_position')
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'position is: %s' % position.getDn())

		old_start=self.save.get('browse_table_start', 0)
		if hasattr(self, 'dirstab'):
			self.save.put('browse_table_start', self.dirstab.getcontent())

		#delmode
		if hasattr(self, 'ignore_buttons'):
			for i in self.ignore_buttons:
				if i.pressed():
					return

		if hasattr(self, 'cancel_delbut') and self.cancel_delbut.pressed():
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "cancel delete")
			self.save.put('removelist', None)
			self.save.put('browse_table_start', old_start)
			return

		if hasattr(self, 'final_delbut') and self.final_delbut.pressed():
			self.save.put('browse_table_start', old_start)
			removelist=self.save.get("removelist")
			if not removelist or not type(removelist) is types.ListType:
				return

			removelist_withcleanup=self.save.get("removelist_withcleanup")
			if not removelist_withcleanup or not type(removelist_withcleanup) is types.ListType:
				removelist_withcleanup=[]

			remove_childs=self.save.get("remove_children")
			self.multidelete_status=[0,len(removelist),0]
			multidelete_errors=[]
			for i in removelist:
				if self.cancel:
					raise SystemExit
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "modbrowse.apply: delmode: processing %s" % i[0])
				dontdel=0
				dontcleanup=0
				for final in self.final_delboxes:
					if final[1]==i[0] and not final[0].get_input():
						univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "modbrowse.apply: delmode: found item in self.final_delboxes: %s" % final[1])
						dontdel=1
						break
				if dontdel:
					continue
				for cleanup in self.cleanup_delboxes:
					if cleanup[1]==i[0] and not cleanup[0].get_input():
						dontcleanup=1
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "modbrowse.apply: creating object handler")
				module=univention.admin.modules.get(i[1])
				object=univention.admin.objects.get(module, None, self.lo, position, dn=i[0], arg=i[2])
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "modbrowse.apply: delete: %s" % i[0])
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "setting child_removal")
				if i in removelist_withcleanup and not dontcleanup:
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "modbrowse.apply: perform cleanup for: %s" % i[0])
					univention.admin.objects.performCleanup(object)
				try:
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "modbrowse.apply: try to remove: %s" % i[0])

					if remove_childs:
						object.remove(remove_childs)
					else:
						object.remove()
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "modbrowse.apply: object removed: %s" % i[0])
				except univention.admin.uexceptions.base, ex:
					message=str(ex)
					if message=="Operation not allowed on non-leaf":
						message="Object is a non-empty container"

					multidelete_errors.append("%s: %s %s" % (univention.admin.uldap.explodeDn(i[0], 1)[0], message, ex.message))
					self.multidelete_status[2] += 1
				self.multidelete_status[0] += 1
			self.save.put("remove_children", None)
			if multidelete_errors:
				self.usermessage(_("Removing %d/%d selected objects failed: %s") % (self.multidelete_status[2], self.multidelete_status[1], string.join(multidelete_errors, '<br>'))) # XXX
			else:
				self.userinfo(_("Removed %d/%d objects successfully.") % (self.multidelete_status[0], self.multidelete_status[1]))
			self.save.put("removelist", None)
			self.save.put("removelist_withcleanup", None)
			self.save.put('browse_search_result', None) ### reload after delete
			self.save.put('browse_selected_dns', {})
			self.save.put('browse_search_do', '1')
			return

		# search
		if hasattr(self, 'search_visible'):
			visible=self.search_visible.get_input()
			if visible:
				try:
					self.save.put('browse_search_visible', int(visible))
				except:
					self.save.put('browse_search_visible', 20)
		if hasattr(self, 'search_type_button') and self.search_type_button.pressed():
			self.save.put('browse_search_type', self.search_type_select.getselected())
			self.save.put('browse_search_property', None)
			self.save.put('browse_search_value', None)
		elif hasattr(self, 'search_property_button') and self.search_property_button.pressed():
			self.save.put('browse_search_property', self.search_property_select.getselected())
			self.save.put('browse_search_value', None)
		elif hasattr(self, 'search_input'):
			self.save.put('browse_search_value', self.search_input.get_input())

		if hasattr(self, 'search_button') and self.search_button.pressed():
			self.save.put('browse_search_result', None)
			self.save.put('browse_selected_dns', {})

			if hasattr(self, 'search_type_select') and self.search_type_select.getselected():
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "saving old_search_type_name: %s" % self.search_type_select.getselected())
				self.save.put('browse_old_search_type', self.search_type_select.getselected())
			else:
				self.save.put('browse_old_search_type', None)
			if hasattr(self, 'search_property_select') and self.search_property_select.getselected():
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "saving old_search_property_name: %s" % self.search_property_select.getselected())
				self.save.put('browse_old_search_property', self.search_property_select.getselected())
			else:
				self.save.put('browse_old_search_property', None)
			if hasattr(self, 'search_input') and self.search_input.get_input():
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "saving old_search_value: %s" % self.search_input.get_input())
				self.save.put('browse_old_search_value', self.search_input.get_input())
			else:
				self.save.put('browse_old_search_value', None)
			self.save.put('browse_search_do', '1')


		if hasattr(self, 'dirbuts'):
			for i in self.dirbuts:
				if i[0].pressed():
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "dirbut[1]: %s"% i[1])
					if not i[1]:
						position.switchToParent()
					else:
						position.setDn(i[1])
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "position.getDn(): %s" % position.getDn())
					self.save.put('ldap_position', position)
					self.save.put('browse_search_result', None)
					self.save.put('browse_selected_dns', {})
					self.userinfo(_("Position changed."))
					return

		if hasattr(self, 'add_button') and self.add_button.pressed():
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'add type: %s' % self.add_select.getselected())
			if not self.add_select.getselected() == "uidummy098":
				self.save.put('edit_dn', None)
				self.save.put('edit_type', self.add_select.getselected())
				self.save.put('browse_search_result', None) ### reload after add
				self.save.put('browse_selected_dns', {})
				self.save.put('uc_module', 'edit')
				self.save.put('browse_table_start', old_start)
			return

		if hasattr(self, 'editbuts'):
			for i in self.editbuts:
				if i[0].pressed():
					sub_object_module=univention.admin.modules.get(i[2])
					if univention.admin.modules.childs(sub_object_module) and not position.getDn() == i[1]:
						univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "open editbut[1]: %s"% i[1])
						if not i[1]:
							position.switchToParent()
						else:
							position.setDn(i[1])
							self.userinfo(_("Position changed."))
						univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "position.getDn(): %s" % position.getDn())
						self.save.put('ldap_position', position)
						self.save.put('browse_search_result', None)
						self.save.put('browse_selected_dns', {})
						return
					else:
						univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "edit editbut[1]: %s"% i[1])
						self.save.put('edit_dn', i[1])
						self.save.put('edit_type', i[2])
						self.save.put('edit_arg', i[3])
						temp_sub_object_module=univention.admin.modules.get(sub_object_module)
						if hasattr(temp_sub_object_module,"superordinate") and temp_sub_object_module.superordinate: #at the moment only needed with virtual objects
							self.save.put('browse_search_result', None) ### reload after changes
							self.save.put('browse_selected_dns', {})
						self.save.put('uc_module', 'edit')
						self.save.put('browse_table_start', old_start)
						return

		if hasattr(self, 'delboxes') and hasattr(self, 'selection_commit_button'):
			selected_dns=self.save.get('browse_selected_dns', {})

			invert_selection=self.selection_select.getselected() == "invert" and self.selection_commit_button.pressed()

			# For whatever reason, this seems to be necessary.
			if invert_selection:
				self.save.put('browse_table_start', old_start)

			for i in self.delboxes:
				if (not i[0].get_input() and not invert_selection) or (i[0].get_input() and invert_selection):
					selected_dns[(i[1],i[2],i[3])]=0
				else:
					selected_dns[(i[1],i[2],i[3])]=1

			self.save.put('browse_selected_dns', selected_dns)
			self.userinfo(_('%d object(s) are selected.') % selected_dns.values().count(1))

			if not self.selection_commit_button.pressed() or invert_selection:
				pass

			elif self.selection_select.getselected() == "delete":
				removelist=[]
				for i, val in selected_dns.items():
					if val:
						removelist.append((i[0], i[1], i[2]))
				if removelist:
					self.save.put("removelist", removelist)
				return

			elif self.selection_select.getselected() == "recursive_delete":
				removelist=[]
				for i, val in selected_dns.items():
					if val:
						removelist.append((i[0], i[1], i[2]))
				if removelist:
					self.save.put("removelist", removelist)
				self.save.put("remove_children", 1)
				return

			elif self.selection_select.getselected() == "edit":
				edit_dn_list=[]
				edit_type=''
				for i, val in selected_dns.items():
					if val:
						if not edit_type:
							edit_type=i[1]
						elif edit_type != i[1]:
							# objects with different types have been selected
							edit_dn_list=[]
							self.usermessage(_('Cannot edit multiple objects with different types.'))
							return
						edit_dn_list.append((i[0], i[2]))
				if edit_dn_list:
					if len( edit_dn_list ) > 1:
						self.save.put('edit_dn', '')
						self.save.put('edit_dn_list', edit_dn_list)
					else:
						self.save.put('edit_dn_list', '')
						self.save.put('edit_dn', edit_dn_list[ 0 ][ 0 ] )
					self.save.put('edit_type', edit_type)
					self.save.put('uc_module', 'edit')
					self.save.put('browse_table_start', old_start)
				return

			elif self.selection_select.getselected() == "move":
				move_dn_list=[]
				for i, val in selected_dns.items():
					if val:
						move_dn_list.append((i[0], i[1], i[2]))
				if move_dn_list:
					self.save.put('browse_move_dn_list', move_dn_list)
					self.save.put('browse_before_move_position', position.getDn())
				return

		if hasattr(self, "cancel_move_button") and self.cancel_move_button.pressed():
			position.setDn(self.save.get('browse_before_move_position'))
			self.save.put('ldap_position', position)
			self.save.put('browse_search_result', [])
			self.save.put('browse_selected_dns', {})
			self.save.put('browse_move_dn_list', [])
			self.save.put('browse_before_move_position', '')

		if hasattr(self, "move_here_button") and self.move_here_button.pressed():
			if self.save.get('browse_before_move_position') == position.getDn():
				self.userinfo(_('Position has not changed. Not moving objects.'))
				self.save.put('browse_move_dn_list', [])
				self.save.put('browse_before_move_position', '')
				return

			move_dn_list=self.save.get('browse_move_dn_list')
			move_errors=[]
			self.move_status=[0,len(move_dn_list),0]
			for dn, module_type, arg in move_dn_list:
				if self.cancel:
					raise SystemExit
				try:
					module=univention.admin.modules.get(module_type)
					object=univention.admin.objects.get(module, None, self.lo, position, dn=dn, arg=arg)
					univention.admin.objects.open(object)
					rdn=dn[:string.find(dn,',')]
					newdn='%s,%s' % (rdn,position.getDn())
					object.move(newdn)
				except univention.admin.uexceptions.base, ex:
					self.move_status[2] += 1
					move_errors.append('%s: %s %s' % (dn,ex.message,str(ex)))
				self.move_status[0] += 1
			if move_errors:
				self.usermessage(_("Moving %d/%d objects failed: %s") % (self.move_status[2], self.move_status[1], string.join(move_errors, '<br>'))) # XXX
			else:
				self.userinfo(_("Moved %d/%d objects successfully.") % (self.move_status[0], self.move_status[1]))
			self.save.put('browse_move_dn_list', [])
			self.save.put('browse_search_result', [])
			self.save.put('browse_selected_dns', {})

		if hasattr(self,"positionbuttons"):
			for but in self.positionbuttons:
				if but.pressed():
					newpos=self.save.get('ldap_position')
					newpos.setDn(but.args.get("helptext",""))
					self.save.put('ldap_position', newpos)
					self.save.put('browse_search_result', None)
					self.save.put('browse_selected_dns', {})
					self.save.put('browse_search_property', None)
					self.save.put('browse_search_type', None)
					self.userinfo(_("Position changed."))
					self.save.put('browse_old_search_value', None)
					self.save.put('browse_old_search_property', None)
					self.save.put('browse_old_search_type', None)

	def waitmessage(self):
		if hasattr(self, 'multidelete_status'):
			return _('Removed %d/%d objects (%d errors).' % (self.multidelete_status[0], self.multidelete_status[1], self.multidelete_status[2]))
		if hasattr(self, 'move_status'):
			return _('Moved %d/%d objects (%d errors).' % (self.move_status[0], self.move_status[1], self.move_status[2]))

	def waitcancel(self):
		self.cancel = 1
