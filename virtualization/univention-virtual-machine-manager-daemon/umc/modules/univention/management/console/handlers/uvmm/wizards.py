#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Virtual Machine Manager
#  module: wizards for devices and virtual instances
#
# Copyright (C) 2010 Univention GmbH
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

import univention.management.console.dialog as umcd

class Page( object ):
	def __init__( self, title = '', description = '' ):
		self.title = title
		self.description = description
		self.options = []
		self.buttons = []

	def setup( self, command, prev = True, next = True ):
		wizard = umcd.Wizard( self.title )
		wizard._content.add_row( [ umcd.Fill( 2, description ), ] )
		wizard._content.add_row( [ umcd.Fill( 2, umcd.Text( '' ) ), ] )
		items = []
		for option in self.options:
			items.append( option.id() )
			wizard._content.add_row( [ option, ] )
		wizard._content.add_row( [ umcd.Fill( 2, umcd.Text( '' ) ), ] )
		if not self.buttons:
			if next:
				next_btn = umcd.NextButton( ( umcd.Action( umcp.SimpleCommand( command, { 'action' : 'next' } ), items ), ) )
			else:
				next_btn = ''
			if pref:
				prev_btn = umcd.PrevButton( ( umcd.Action( umcp.SimpleCommand( command, { 'action' : 'prev' } ), items ), ) )
			else:
				prev_btn = ''

			wizard._content.add_row( [ prev_btn, next_btn ] )

		return wizard.setup()

class IWizard( list ):
	def __init__( self ):
		list.__init__( self )
		self.current = None
		self.actions = { 'next' : self.next, 'prev' : self.prev }

	def action( self, object ):
		if 'action' in object.options:
			action = object.options[ 'action' ]
			del object.options[ 'action' ]
		else:
			action = 'next'

		if action in self.actions:
			return self.actions[ action ]( object )

	def next( self, object ):
		if self.current == None:
			self.current = 0
		elif self.current == ( len( self ) - 1 ):
			return None
		else:
			self.current += 1

		return self[ self.current ]

	def prev( self, object ):
		if self.current == 0:
			return None
		else:
			self.current -= 1

		return self[ self.current ]

class DeviceWizard( IWizard ):
	def __init__( self ):
		IWizard.__init__( self )

class InstanceWizard( IWizard ):
	def __init__( self ):
		IWizard.__init__( self )
