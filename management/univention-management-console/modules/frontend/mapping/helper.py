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
import structural

import univention.management.console.dialog as umcd

from uniparts import *

def infobox_map( storage, umcp_part ):
	rows = []
	ico = icon( '', { 'url' : umcp_part.get_image() }, {} )
	icon_col = tablecol( '', { 'type' : 'umc_infobox_col' }, { 'obs' : [ ico ] } )
	txt = text( '', utils.attributes( umcp_part ), { 'text' : [ unicode( umcp_part ) ] } )
	text_col = tablecol( '', { 'type' : 'umc_infobox_col' }, { 'obs' : [ txt ] } )
	row = tablerow( '', { 'type' : 'umc_infobox_row' }, { 'obs' : [ icon_col, text_col ] } )

	return table( '', { 'type' : 'umc_infobox' }, { 'obs' : [ row ] } )

mapper.add( umcd.InfoBox, infobox_map )
mapper.add( umcd.Question, structural.list_map )
