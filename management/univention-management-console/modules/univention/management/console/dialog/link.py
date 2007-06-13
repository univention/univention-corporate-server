# -*- coding: utf-8 -*-
#
# Univention Management Console
#  class representing a link object within a UMCP dialog
#
# Copyright (C) 2006 Univention GmbH
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

import base

class Link( base.Text ):
	def __init__( self, description = '', link = '', icon = None ):
		base.Text.__init__( self, description )
		self._link = link
		self._icon = icon

	def get_icon( self ):
		return self._icon

	def get_link( self ):
		return self._link

	def set_link( self, link ):
		'''
		A given link may be the next request or just a string.
		The latter needs to be parseable as a href-uri in html.
		'''
		self._link = link

LinkTypes = ( type( Link() ), )
