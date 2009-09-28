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

import mapper
import utils

import univention.management.console.tools as umc_tools

import univention.management.console.dialog as umcd
import univention.management.console as umc

from uniparts import *

_ = umc.Translation( 'univention.management.console.frontend' ).translate

def text_map( storage, umcp_part ):
	return text( '', utils.layout_attrs( storage, umcp_part ),
				 { 'text' : [ umcp_part.get_text() ] } )

for t in umcd.TextTypes:
	mapper.add( t, text_map )

def html_map( storage, umcp_part ):
	return htmltext( '', utils.layout_attrs( storage, umcp_part ),
					 { 'htmltext' : [ umcp_part.get_text() ] } )

mapper.add( umcd.HTML, html_map )

def icon_map( storage, umcp_part ):
	# FIXME: the following try-except-block is rather hacky but currently the best solution.
	# umcp_part.has_attributes() sometimes throws an exception if umcp_part.__attributes
	# does not exist. Fixing has_attributes() by adding a safety check, changes the behaviour
	# of the whole UMC.
	try:
		attrs = utils.layout_attrs( storage, umcp_part )
	except:
		attrs = {}
	attrs.update ({ 'url' : umcp_part.get_image() })
	return icon( '', attrs, {} )

mapper.add( umcd.Image, icon_map )
mapper.add( umcd.ImageURL, icon_map )

def link_map( storage, umcp_part ):
	try:
		attrs = utils.layout_attrs( storage, umcp_part )
	except:
		attrs = {}
	attributes = utils.attributes( umcp_part )

	attrstr = ''
	for key in ['onmouseover', 'onmouseout']:
		if attributes.has_key(key):
			attrstr += ' %s="%s"' % (key, attributes[key])

	html =  ' <table class="button"><tr>\n'
	if umcp_part.get_icon():
		html += '<td class="button_icon"><a href="%s" target="_blank" class="nounderline"><img class="button_icon" src="%s" alt="%s" %s></a></td>\n' % ( umcp_part.get_link(),
																																						 umc_tools.image_get( umcp_part.get_icon(), umc_tools.SIZE_MEDIUM ),
																																						 umcp_part.get_text(),
																																						 attrstr)
	if not umcp_part.get_icon() or umcp_part.show_icon_and_text():
		html += '<td class="button_link"><a href="%s" target="_blank" class="nounderline" %s><span class="content">%s</span></a></td>\n' % ( umcp_part.get_link(),
																																			 attrstr,
																																			 umcp_part )
	html += '</tr></table>\n'

	text = htmltext( '', attributes, { 'htmltext' : [ html ] } )
	storage[ umcp_part.id() ] = ( text, umcp_part )

	return text

mapper.add( umcd.Link, link_map )

def _input_map( storage, umcp_part, attributes ):
	default = utils.default( umcp_part )
	quest = question_text( unicode( umcp_part ), attributes,
						   { 'usertext' : default,
							 'helptext' : '' } )
	storage[ umcp_part.id() ] = ( quest, umcp_part )

	return quest

def textinput_map( storage, umcp_part ):
	return _input_map( storage, umcp_part, utils.layout_attrs( storage, umcp_part ) )

def readonlyinput_map( storage, umcp_part ):
	attributes = utils.attributes( umcp_part )
	attributes.update( { 'passive' : 'true' } )

	return _input_map( storage, umcp_part, attributes )

mapper.add( umcd.TextInput, textinput_map )
mapper.add( umcd.ReadOnlyInput, readonlyinput_map )

def dateinput_map( storage, umcp_part ):
	default = utils.default( umcp_part )
	quest = question_dojo_date_widget( unicode( umcp_part ), utils.layout_attrs( storage, umcp_part ),
						   { 'usertext' : default,
							 'helptext' : '' } )
	storage[ umcp_part.id() ] = ( quest, umcp_part )

	return quest

mapper.add( umcd.DateInput, dateinput_map )

def password_map( storage, umcp_part ):
	quest = question_secure( unicode( umcp_part ), utils.layout_attrs( storage, umcp_part ),
							{ 'usertext' : '' } )
	storage[ umcp_part.id() ] = ( quest, umcp_part )

	return quest

mapper.add( umcd.SecretInput, password_map )

def longtext_map( storage, umcp_part ):
	default = utils.default( umcp_part )
	attributes = utils.layout_attrs( storage, umcp_part )
	quest = question_ltext( unicode( umcp_part ), attributes,
						   { 'usertext' : default, 'helptext' : '' } )
	storage[ umcp_part.id() ] = ( quest, umcp_part )

	return quest

mapper.add( umcd.MultiLineInput, longtext_map )

def checkbox_map( storage, umcp_part ):
	attributes = utils.attributes( umcp_part )
	if utils.default( umcp_part ):
		value = '1'
	else:
		value = ''

	attributes.update( { 'usertext' : value, 'helptext' : '' } )
	quest = question_bool( unicode( umcp_part ), utils.layout_attrs( storage, umcp_part ),
						   attributes )
	storage[ umcp_part.id() ] = ( quest, umcp_part )

	return quest

mapper.add( umcd.Checkbox, checkbox_map )

def selection_map( storage, umcp_part ):
	default = utils.default( umcp_part )
	attributes = utils.attributes( umcp_part )
	choices = []
	for key, name in umcp_part.choices():
		if default and key == default:
			choices.append( { 'name' : key, 'description' : name, 'selected' : '1' } )
		else:
			choices.append( { 'name' : key, 'description' : name } )
	attributes.update( { 'choicelist' : choices } )
	quest = question_select( str( umcp_part ), utils.layout_attrs( storage, umcp_part ), attributes )
	storage[ umcp_part.id() ] = ( quest, umcp_part )

	return quest

mapper.add( umcd.Selection, selection_map )

