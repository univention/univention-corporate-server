#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  maps dynamic elements
#
# Copyright 2007-2010 Univention GmbH
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
mapper.add( umcd.YesNoQuestion, structural.frame_map )
