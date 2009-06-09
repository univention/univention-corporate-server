#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  maps dynamic elements
#
# Copyright (C) 2007-2009 Univention GmbH
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

import copy, tempfile, os

import mapper
import buttons
import utils

import univention.admin.modules
import univention.admin.objects
import univention.management.console as umc
import univention.management.console.tools as umc_tools

import univention.management.console.dialog as umcd

import univention.debug as ud

from uniparts import *

_ = umc.Translation( 'univention.management.console.frontend' ).translate

class DynamicListMap( mapper.IMapper ):
	def __init__( self ):
		mapper.IMapper.__init__( self )

	def layout( self, storage, umcp_part ):
		headers = []

		for col in umcp_part.get_header():
			head = header( str( col ), { 'type' : '4' }, {} )
			headers.append( tablecol( '', { 'type' : 'umc_list_head' }, { 'obs' : [ head ] } ) )
		rows = [ tablerow( '', { 'type' : 'umc_list_head' }, { 'obs' : headers } ) ]

		remove_btns = []
		select_btns = []
		for row in umcp_part.get_content():
			up = storage.to_uniparts( row )
			if umcp_part.modifier:

				#
				# FIXME: find a better way to get unipart objects
				# FIXME: currently first object is always "modifier"
				# FIXME: and last object is always "modified"
				# FIXME: (see also dialog/dynamic.py in methon DynamicList.set_row()
				#
				modifier_obj = up.args['obs'][0].args['obs'][0]
				modified_obj = up.args['obs'][-1].args['obs'][0]

				if not modifier_obj.args.has_key('button') or not modifier_obj.args['button']:
					commit_button = button( '', {}, { 'helptext' : '' } )
					modifier_obj.args['button'] = commit_button
				select_btns.append( modifier_obj.args['button'] )

			icon = { 'icon' : umc_tools.image_get( 'actions/remove', umc_tools.SIZE_SMALL ) }
			but = button( '', icon, { 'helptext' : '' } )
			remove_btns.append( but )
			btn_col = tablecol( '', { 'type' : 'umc_list_element' },
								{ 'obs' : [ but ] } )
			up.args[ 'obs' ].append( btn_col )
			rows.append( up )

		fill_col = tablecol( '', { 'colspan' : str( umcp_part.num_columns() ) ,
								   'type' : 'umc_list_element' },
							 { 'obs' : [ text( '', {}, { 'text' : [ '' ] } ) ] } )
		icon = { 'icon' : umc_tools.image_get( 'actions/add', umc_tools.SIZE_MEDIUM ) }
		but = button( _( 'Add' ), icon, { 'helptext' : _( 'Add' ) } )
		storage[  umcp_part.id() ] = ( ( but, remove_btns, select_btns ), umcp_part )
		btn_col = tablecol( '', { 'type' : 'umc_list_element' },
							{ 'obs' : [ but ] } )
		rows.append( tablerow( '', {}, { 'obs': [ fill_col, btn_col ] } ) )

		return table( '', { 'type' : 'umc_list' }, { 'obs' : rows } )


	def apply( self, storage, dyn, params ):
		btn, rm_btns, select_btns = params
		# cache current values
		for rows in dyn.get_items():
			for item_id in rows:
				uni_item, umcp_item = storage.find_by_umcp_id( item_id )
				umcp_item.cached = uni_item.get_input()
		# add new row?
		if btn.pressed():
			dyn.append_row()
			return True
		else:
			# remove a row?
			i = 0
			for btn in rm_btns:
				if btn.pressed():
					dyn.remove_row( i )
					return True
				i += 1
			# change a row?
			i = 0
			for btn in select_btns:
				if btn.pressed():
					modifier_id = dyn.get_items()[i][0]
					uni_item, umcp_item = storage.find_by_umcp_id( modifier_id )
					value = uni_item.get_input()

					dyn.modify_row( i, value )
					return True
				i += 1
		return False

	def parse( self, storage, dyn, params ):
		btn, rm_btns, select_btns = params
		# retrieve information from lines
		items = []
		for rows in dyn.get_items():
			line = {}
			for item_id in rows:
				uni_item, umcp_item = storage.find_by_umcp_id( item_id )
				value = uni_item.get_input()
				if not utils.check_syntax( umcp_item, value ):
					raise umc.SyntaxError( umcp_item )
				line[ umcp_item.option ] = value
			items.append( line )
		return items

mapper.add( umcd.DynamicList, DynamicListMap() )

class MultiValueMap( mapper.IMapper ):
	def __init__( self ):
		mapper.IMapper.__init__( self )

	def layout( self, storage, umcp_part ):
		items = []
		input_fields = []
		attributes = utils.attributes( umcp_part )
		for field in umcp_part.fields:
			items.append( storage.to_uniparts( field ) )
		field_tables = []
		for item in items:
			field_tables.append( table( '', { 'border' : '0' }, { 'obs' : [
				tablerow( '', {}, { 'obs' : [
					tablecol( '', {}, { 'obs' : [
						item
						] } )
					] } )
				] } )
			)

		input_fields.append( tablerow( '', {}, { 'obs' : [
			tablecol( '', { 'rowspan' : '2' }, { 'obs' :
				field_tables
				} ),
			tablecol( '', {}, { 'obs' : [
				htmltext( '', {}, { 'htmltext' : [ '&nbsp;' ] } )
				] } ),
			] }
		) )

		btn_add = utils.button_add()
		input_fields.append( tablerow( '', {}, { 'obs' : [
			tablecol( '', { 'type' : 'multi_add_top' }, { 'obs' : [ btn_add ] } ) ] } ) )

		btn_up = utils.button_up()
		up = tablecol( '', { 'type' : 'multi_remove' }, { 'obs' : [ btn_up ] } )
		btn_remove = utils.button_remove()
		remove = tablerow( '', {}, { 'obs' : [ tablecol( '', { 'type' : 'multi_remove' },
														 { 'obs' : [ btn_remove ] } ) ] } )
		btn_down = utils.button_down()
		down = tablerow( '', {}, { 'obs' : [ tablecol( '', { 'type' : 'multi_remove_img' },
													   { 'obs' : [ btn_down ] } ) ] } )
		# current values
		default = utils.default( umcp_part )
		umcp_part.cached = default
		mvaluelist = []
		if default:
			for key, descr in default:
				mvaluelist.append( { 'name' : key, 'description' : descr } )

		mselect = question_mselect( _( 'Entries:' ), utils.attributes( umcp_part ),
									{ 'helptext' : _( "Current entries for '%s'" ) % unicode( umcp_part ),
									  'choicelist' : mvaluelist } )

		tmselect = tablerow( '', {}, { 'obs' : [ tablecol( '', { 'rowspan' : '3' },
														   { 'obs' : [ mselect ] } ), up ] } )

		input_fields.append( tablerow( '', {}, { 'obs' : [ tmselect, remove, down ] } ) )

		storage[ umcp_part.id() ] = ( ( mselect, btn_add, btn_remove, btn_up, btn_down ), umcp_part )

		return table( '', { 'border' : '0' }, { 'obs' : input_fields } )

	def apply( self, storage, dyn, params ):
		mselect, btn_add, btn_remove, btn_up, btn_down = params

		# add item
		if btn_add.pressed():
			values = []
			for field in dyn.field_ids:
				uni_item, umcp_item = storage.find_by_umcp_id( field )
				value = uni_item.get_input()
				labelID = getattr(umcp_item, 'labelID', None)
				if labelID and value == labelID:
					return True
				if not utils.check_syntax( umcp_item, value ):
					raise umc.SyntaxError( field )
				values.append( umcp_item.item( value ) )
			key = dyn.separator.join( map( lambda x: x[ 0 ], values ) )
			value = dyn.separator.join( map( lambda x: x[ 1 ], values ) )
			if not dyn.cached:
				if dyn.default:
					dyn.cached = list( dyn.default )
				else:
					dyn.cached = []
			dyn.cached.append( ( key, value ) )
			return True
		# remove item
		elif btn_remove.pressed():
			dynamic_action = True
			selected = mselect.getselected()
			newvalue = []
			if selected:
				selected = selected[ 0 ]
				for key, descr in dyn.cached:
					if key != selected:
						newvalue.append( ( key, descr ) )
				dyn.cached = newvalue
			return True

		return False

	def parse( self, storage, dyn, params ):
		if dyn.cached:
			mapped = map( lambda x: x[ 0 ], dyn.cached )
		else:
			mapped = tuple()
		if utils.check_syntax( dyn, mapped ):
			return mapped

		raise umc.SyntaxError( dyn )

mapper.add( umcd.MultiValue, MultiValueMap() )


class ObjectSelectMap( mapper.IMapper ):
	def __init__( self ):
		mapper.IMapper.__init__( self )
		self.lo = umc.LdapConnection()

	def layout( self, storage, umcp_part ):

		filter = None
		save = umcp_part.save

		search_module = univention.admin.modules.get( umcp_part.modulename )

		# load current values from saver dict (use default if not set)
		current_value = save.get('objectselect_current_value', None)
		if current_value == None:
			if umcp_part.default:
				current_value = umcp_part.default
			else:
				current_value = []
			save['objectselect_current_value'] = current_value

		# search_property_name
		# '*' ==> ALL
		# '_' ==> NONE

		# get selected property name from saver-dict (default = '_' ==> None)
		search_property_name = save.get('search_property_name', '_')

		# check if property name is valid otherwise set to '_'
		if not search_module.property_descriptions.has_key(search_property_name) and not search_property_name == '*':
			search_property_name = '_'

		# get search value entered by user
		if not search_property_name == '*':
			objectselect_search_value = save.get('objectselect_search_value', '')
			if not objectselect_search_value:
				objectselect_search_value = '*'
			# set user defined filter
			filter = '(%s=%s)' % (search_property_name, objectselect_search_value)



		# build property dropdown list
		search_properties=[]
		for pname, pproperty in search_module.property_descriptions.items():
			if not umcp_part.search_properties or pname in umcp_part.search_properties:
				if not (hasattr(pproperty, 'dontsearch') and pproperty.dontsearch==1):
					search_properties.append({'name': pname, 'description': pproperty.short_description})
		search_properties.sort()
		# insert ANY and NONE at beginning of select list
		search_properties.insert(0, {'name': '*', 'description': _('any')})
		search_properties.insert(0, {'name': '_','description':_('none')})

		# select currently active property in dropdownbox
		for i in search_properties:
			if i['name']==search_property_name:
				i['selected']='1'

		# build input widget if search_property_name is not ALL or NONE
		if search_property_name not in  ('*',"_"):
			description = ''
			if search_property_name:
				search_property = search_module.property_descriptions[search_property_name]
				description = search_property.short_description
			search_input = question_text(description,{},{'usertext': objectselect_search_value, 'helptext': _('Enter search filter')})
		else:
			# do not create input widget if ALL or NONE is selected
			search_input = text('',{},{'text':['']})

			if search_property_name == '*':
				search_value='*'

		search_property_button = button('go',{},{'helptext':_('Display')})
		search_property_select = question_select(_('Property'),{},{'helptext':_('Select attribute'),
																   'choicelist':search_properties,
																   'button':search_property_button})
		search_button = utils.button_search()

		# add widgets to table if search is enabled
		if not umcp_part.search_disabled:
			searchcols=[]
			searchcols.append(tablecol('',{},{'obs':[search_property_select]}))
			searchcols.append(tablecol('',{},{'obs':[search_input]}))
			searchcols.append(tablecol('',{'type':'tab_layout_bottom'},{'obs':[search_button]}))
		else:
			# otherwise set search property to '*'
			search_property_name = '*'
			save['objectselect_search_ok'] = True
			save['objectselect_search_value'] = '*'
			save['search_property_name'] = '*'
			filter = ''


		# if additional filter is present, combine filters
		if umcp_part.filter:
			if filter:
				filter = '(&%s%s)' % (umcp_part.filter, filter)
			else:
				filter = umcp_part.filter

		ud.debug( ud.ADMIN, ud.INFO, 'ObjectSearch: search filter="%s"' % filter )

		# if search is ok and search property is not NONE then start ldap search
		if save.get('objectselect_search_ok', False) and search_property_name != '_':
			del save['objectselect_search_ok']
			# use given basedn
			if umcp_part.basedn:
				basedn = umcp_part.basedn
			else:
				basedn = self.lo.get_basedn()
			search_result = search_module.lookup(None, self.lo, filter, scope = umcp_part.scope, base = basedn)
			save['objectselect_search_result'] = search_result
		else:
			search_result = save.get('objectselect_search_result', [])

		# get all attributes
		available_attributes = search_module.property_descriptions.keys()

		# build choicelist with current items and remember their dn
		is_in={}
		cur_group_choicelist=[]
		sort_temp = {}
		for dn in current_value: # value may have ''-element, would crash python in the dictionary
			if dn != '':
				is_in[dn]=1

				obj = univention.admin.objects.get( search_module, None, self.lo, '', dn )
				univention.admin.objects.open( obj )

				txt = ''
				for attr in umcp_part.attr_display:
					if attr in available_attributes:
						if obj.has_key(attr):
							if isinstance( obj[ attr ], list ):
								txt += ', '.join( obj[ attr ] )
							else:
								txt += obj[ attr ]
					elif attr == 'dn':
						txt += dn
					else:
						txt += attr
				if txt:
					sort_temp[ dn ] = txt
				else:
					sort_temp[ dn ] = dn

		# tuple of lower case key and keys for case insensitive sort
		sort_keys = [ ( x.lower(), x ) for x in sort_temp.keys() ]
		sort_keys.sort()
		for unused, key in sort_keys:
			cur_group_choicelist.append( { 'name': key, 'description': sort_temp[ key ] } )


		# build choicelist with new items
		new_group_choicelist=[]
		sort_temp = {}
		# check for each result item...
		for item in search_result:
			if not item.dn:
				continue
			# ...if item is not in "current" list...
			if not is_in.get(item.dn):
				append_text = []

				obj = univention.admin.objects.get( search_module, None, self.lo, item.position, item.dn )
				univention.admin.objects.open( obj )

				txt = ''
				for attr in umcp_part.attr_display:
					if attr in available_attributes:
						if obj.has_key(attr):
							if isinstance( obj[ attr ], list ):
								txt += ', '.join( obj[ attr ] )
							else:
								txt += obj[ attr ]
					elif attr == 'dn':
						txt += item.dn
					else:
						txt += attr
				if txt:
					sort_temp[ item.dn ] = txt
				else:
					sort_temp[ item.dn ] = item.dn


		# tuple of lower case key and keys for case insensitive sort
		sort_keys = [ ( x.lower(), x ) for x in sort_temp.keys() ]
		sort_keys.sort()
		for unused, key in sort_keys:
			new_group_choicelist.append( { 'name': key, 'description': sort_temp[ key ] } )


		atts = { 'height' : '150' }
		value_list_new = question_mselect(_('All'),atts,{'choicelist':new_group_choicelist,'helptext':_('Select objects to add')})
		value_list_cur = question_mselect(_('Current'),atts,{'choicelist':cur_group_choicelist,'helptext':_('Select objects to remove')})
		button_add = utils.button_right('Add items')
		button_remove = utils.button_left('Remove items')

		#
		# label
		#
		# [select property] [property filter] [searchbtn]
		#
		# |---------------------------------------------|
		# |                |          |                 |
		# |                |----------|                 |
		# |  list          |    >     |      list       |
		# |                |----------|                 |
		# |                |    <     |                 |
		# |---------------------------------------------|
		#


		tableobs =[ tablerow("",{},{"obs":[
			tablecol("",{},
					 {"obs":[ header( umcp_part.get_text(), {'type':'4'}, {} ) ] }
					 )]})
		]

		if not umcp_part.search_disabled:
			tableobs.append( tablerow("",{},{"obs":[
				tablecol("",{},
						 {"obs":[table("",{'type':'multi'},{"obs":[tablerow("",{},{"obs":searchcols})]})]}
						 )]}) )

		tableobs.append(
			tablerow("",{},{"obs":[
				tablecol("",{},{"obs":[table("",{'type':'multi'},{"obs":[\
					tablerow("",{},{"obs":[
						tablecol('',{'rowspan':'3'},{'obs': [value_list_new]}),
						tablecol('',{'type':'multi_spacer'}, {'obs': [\
							# needed freespace
							# htmltext("",{},{'htmltext':['&nbsp;']})
							htmltext("",{},{'htmltext':['&nbsp;']})
							]}),\
						tablecol('',{'rowspan':'3'},{'obs': [value_list_cur]})
					]}),
					tablerow("",{},{"obs":[
						tablecol('',{'type':'leftright_top'}, {'obs': [\
							#add button
							button_add\
						]})\
					]}),\
					tablerow("",{},{"obs":[
						tablecol('',{'type':'leftright_bottom'}, {'obs': [\
							#remove button
							button_remove\
						]})\
					]})\
				]})]})\
			]})\
		)

		cols = []
		cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [table("",{'type':'multi'},{"obs":tableobs})]}))

		storage[ umcp_part.id() ] = ( ( umcp_part.save, search_property_select, search_property_button, search_button, search_input,
										value_list_new, value_list_cur, button_add, button_remove ), umcp_part )

		return table( '', { 'border' : '0' }, { 'obs' : cols } )


	def apply( self, storage, dyn, params ):
		( save, search_property_select, search_property_button, search_button, search_input,
		  value_list_new, value_list_cur, button_add, button_remove ) = params

		if search_property_button.pressed():
			selected = search_property_select.getselected()
			save[ 'search_property_name' ] = selected
			if save.has_key('objectselect_search_result'):
				del save['objectselect_search_result']
#			ud.debug( ud.ADMIN, ud.INFO, 'ObjectselectMap: cleared search_result; search_property_select = "%s"' % selected )
			return True

		elif search_button.pressed():
#			ud.debug( ud.ADMIN, ud.INFO, 'ObjectselectMap: search_button pressed' )

			save[ 'objectselect_search_value' ] = search_input.get_input()
			if save.get('objectselect_search_property','_') == '_':
				if save.has_key('objectselect_search_result'):
					del save['objectselect_search_result']
			save[ 'objectselect_search_ok' ] = True
			return True

		elif button_add.pressed():
#			ud.debug( ud.ADMIN, ud.INFO, 'ObjectselectMap: button_add pressed' )
			selected = value_list_new.getselected()
			current = save.get('objectselect_current_value',[])
			current.extend(selected)
			save['objectselect_current_value'] = current
			return True

		elif button_remove.pressed():
#			ud.debug( ud.ADMIN, ud.INFO, 'ObjectselectMap: button_remove pressed' )
			selected = value_list_cur.getselected()
			current = save.get('objectselect_current_value',[])
			current = filter(lambda x: not x in selected, current)
			save['objectselect_current_value'] = current
			return True

		return False


	def parse( self, storage, dyn, params ):
		( save, search_property_select, search_property_button, search_button, search_input,
		  value_list_new, value_list_cur, button_add, button_remove ) = params

		mapped = save.get('objectselect_current_value', [])
		if utils.check_syntax( dyn, mapped ):
			return mapped

		raise umc.SyntaxError( dyn )

mapper.add( umcd.ObjectSelect, ObjectSelectMap() )



class FileUploadMap( mapper.IMapper ):
	def __init__( self ):
		mapper.IMapper.__init__( self )

	def layout( self, storage, umcp_part ):
		# |----------------------------------------------------------|
		# | File 1    (X) Remove                                     |
		# | File 2    (X) Remove                                     |
		# | File ...  (X) Remove                                     |
		# | File n    (X) Remove                                     |
		# |----------------------------------------------------------|
		# | <uploadfield with searchbutton>                          |
		# |----------------------------------------------------------|
		# | <upload-button>                                          |
		# |----------------------------------------------------------|

		save = umcp_part.save
		cols = []

		fileDeleteBtnList = []
		fileBrowseBtn = question_file( _('Select a file'), {} , {"helptext":_("Select a file")})
		fileLoadBtn = button(_("Upload file"),{'icon':'/style/ok.gif'},{"helptext":_("Upload selected file")})

		filelist = save.get('uploadFilelist',[])
		rows = []
		for entry in filelist:
			btn = button(_("Remove"),{'icon':'/style/cancel.gif'},{"helptext":_("Delete file")})
			fileDeleteBtnList.append( btn )
			rows.append( tablerow("",{},{"obs":[
									tablecol('',{}, {'obs': [
										htmltext("",{},{'htmltext':[ entry['filename']]})
									]}),
									tablecol('',{}, {'obs': [
										htmltext("",{},{'htmltext':['&nbsp;']})
									]}),
									tablecol('',{}, {'obs': [
										btn
									]}),
								]})
						)
		if umcp_part.maxfiles == 0 or len(filelist) < umcp_part.maxfiles:
			rows.extend( [tablerow("",{},{"obs":[
										tablecol('',{}, {'obs': [
											fileBrowseBtn
										]}),
									]}),
							tablerow("",{},{"obs":[
										tablecol('',{}, {'obs': [
											#upload button
											fileLoadBtn
										]}),
									]})] )
		if rows:
			cols.append(tablecol('',{'type':'tab_layout'}, {'obs': [table("",{'type':'multi'},{"obs":   rows,   })]}))

		storage[ umcp_part.id() ] = ( ( save, fileBrowseBtn, fileLoadBtn, fileDeleteBtnList ), umcp_part )

		return table( '', { 'border' : '0' }, { 'obs' : cols } )


	def apply( self, storage, dyn, params ):
		( save, fileBrowseBtn, fileLoadBtn, fileDeleteBtnList ) = params

		ud.debug(ud.ADMIN, ud.INFO, 'FileUploadMap:apply: fileBrowseBtn=%s' % fileBrowseBtn.__dict__)
		ud.debug(ud.ADMIN, ud.INFO, 'FileUploadMap:apply: fileLoadBtn=%s' % fileLoadBtn.__dict__)
		if fileLoadBtn.pressed():
			if fileBrowseBtn.get_input() and fileBrowseBtn.get_filename():
				tmpUploadFn=tempfile.mkstemp('.uploadFile.tmp', 'univention-management-console.', '/tmp/webui')[1]
				os.rename(fileBrowseBtn.get_input(), tmpUploadFn)

				filelist = save.get('uploadFilelist',[])
				filelist.append( { 'filename': fileBrowseBtn.get_filename(),
								   'tmpfname': tmpUploadFn } )
				save['uploadFilelist'] = filelist
			else:
				ud.debug(ud.ADMIN, ud.ERROR, 'dynamics.py:FileUploadMap:apply: no (temporary) filename given')
			return True

		for i in range(len(fileDeleteBtnList)):
			if fileDeleteBtnList[i].pressed():
				filelist = save.get('uploadFilelist',[])
				tmpfname = filelist[i].get('tmpfname')
				if tmpfname:
					try:
						os.remove( tmpfname )
					except:
						ud.debug(ud.ADMIN, ud.ERROR, 'dynamics.py:FileUploadMap:apply: error while os.remove(%s)' % (tmpfname) )
				del filelist[i]
				save['uploadFilelist'] = filelist
				return True

		return False


	def parse( self, storage, dyn, params ):
		( save, fileBrowseBtn, fileLoadBtn, fileDeleteBtnList ) = params
		return save.get('uploadFilelist', [])


mapper.add( umcd.FileUpload, FileUploadMap() )
