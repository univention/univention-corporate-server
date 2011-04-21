#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  wizard table for UMCP dialogs
#
# Copyright 2006-2010 Univention GmbH
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

import univention.management.console.protocol as umcp
import univention.management.console.locales as locales

from base import *
from button import *
from image import *

import copy as copy_module


_ = locales.Translation( 'univention.management.console.dialog' ).translate

class Wizard( Element ):
	"""Low-level graphical representation for a Wizard page."""
	def __init__( self, title = '' ):
		Element.__init__( self )
		self._title = title
		self._content = List( attributes = { 'width' : '100%' } )
		self._image = None

	def set_image( self, image ):
		"""Set top-left image to instance of umcd.Image."""
		self._image = image

	def add_option( self, text, option ):
		"""Add widget to this Wizard page."""
		self._content.add_row( [ option, text ] )

	def add_buttons( self, *args ):
		"""Add buttons to this Wizard page."""
		if self._image:
			self._content.add_row( [ Fill( 2 ) ] )
			self._content.add_row( [ '', args ] )
		else:
			self._content.add_row( [ '' ] )
			self._content.add_row( [ args ] )

	def setup( self ):
		"""Convert Wizard to dialog element."""
		if self._image:
			self._image[ 'width' ] = '100'
			return Frame( [ List( content = [ [ Cell( self._image, { 'valign' : 'top' } ), self._content ] ], attributes = { 'width' : '100%' } ) ], self._title )
		else:
			return Section( self._title, self._content, attributes = { 'width' : '100%' } )

WizardTypes = (Wizard,)

# the following classes help to setup a wizard based on the Wizard
# dialog class above. An example can be found in the UVMM UMC module

class Page( object ):
	"""High-level implementation of a wizard page."""
	def __init__( self, title = '', description = '' ):
		self.title = title
		self.description = description
		self.options = []
		self.actions = []
		self.buttons = []
		self.hint = None

	def setup( self, command, options, prev = True, next = True, finish = False, cancel = True ):
		"""Convert this page into graphical representation. Returns a Wizard instance containing description, hint, options and buttons."""
		wizard = Wizard( self.title )
		# add description
		if self.description:
			if isinstance( self.description, HTML ):
				self.description[ 'colspan' ] = '2'
				wizard._content.add_row( [ self.description, ] )
			else:
				wizard._content.add_row( [ Fill( 2, self.description ), ] )
			wizard._content.add_row( [ Fill( 2, '' ), ] )
		items = []

		# add hint
		if self.hint:
			attrs = { 'valign' : 'top', 'type' : 'umc_mini_padding', 'width' : '100%' }
			table = List( attributes = attrs )
			hint = HTML( self.hint, attributes = attrs )
			table.add_row( [ Cell( hint, attributes = attrs ) ] )

			wizard._content.add_row( [ Cell( table, attributes = { 'colspan' : '2' } ) ] )
			wizard._content.add_row( [ Fill( 2, '' ), ] )

		# add options
		for option in self.options:
			if hasattr( option, 'option' ):
				items.append( option.id() )
				if option.option in options:
					option.default = options[ option.option ]
			option[ 'colspan' ] = '2'
			wizard._content.add_row( [ option, ] )

		wizard._content.add_row( [ Fill( 2, '' ), ] )
		if self.actions:
			# add already collected options to actions
			for button in self.actions:
				for action in button.actions:
					action.command.options.update( options )
			wizard._content.add_row( [ List( content = [ self.actions, ], attributes = { 'colspan' : '2' } ), ] )
			wizard._content.add_row( [ Fill( 2, '' ), ] )

		if not self.buttons:
			if next:
				opts = copy_module.copy( options )
				opts[ 'action' ] = 'next'
				next_btn = Button( _( 'Next' ), actions = ( Action( umcp.SimpleCommand( command, opts ), items ), ), attributes = { 'class' : 'button_right' }, default = True, close_dialog = False )
			elif finish:
				opts = copy_module.copy( options )
				opts[ 'action' ] = 'finish'
				if isinstance( finish, basestring ):
					text = finish
				else:
					text = _( 'Finish' )
				next_btn = Button( text, actions = ( Action( umcp.SimpleCommand( command, opts ), items ), ), attributes = { 'class' : 'button_right' }, default = True )
			else:
				next_btn = ''
			if cancel:
				opts = copy_module.copy( options )
				opts[ 'action' ] = 'cancel'
				cmd = umcp.SimpleCommand( command, opts )
				cmd.verify_options = False
				cancel_btn = Cell( Button( _( 'Cancel' ), actions = ( Action( cmd, items ) ) ), attributes = { 'type' : 'button_padding' } )
			else:
				cancel_btn = ''
			if prev:
				opts = copy_module.copy( options )
				opts[ 'action' ] = 'prev'
				prev = umcp.SimpleCommand( command, opts )
				prev.verify_options = False
				prev_btn = Cell( Button( _( 'Previous' ), actions = ( Action( prev, items ), ), attributes = { 'class' : 'cancel' }, close_dialog = False ), attributes = { 'type' : 'button_padding' } )
			else:
				prev_btn = ''

			lst = List()
			lst.add_row( [ prev_btn, next_btn ] )
			wizard._content.add_row( [ cancel_btn, Cell( lst, attributes = { 'type' : 'umc_list_element_right' } ) ] )
		else:
			wizard._content.add_row( self.buttons )

		return wizard.setup()

class WizardResult( object ):
	"""Encapsulate result of a Wizard page. value=True to continue to next page, value=False & text to stay on the current page."""
	def __init__( self, value =True, text = '' ):
		self.value = value
		self.text = text

	def __nonzero__( self ):
		"""Return True, if the Wizard page in complete and the next Wizard should switch to the next page."""
		return self.value

class IWizard( list ):
	"""High-level implementation of a wizard containing a list of wizard pages, stacked on top of each other in card layout fashion."""
	def __init__( self, command = '' ):
		list.__init__( self )
		self.current = None
		self.command = command
		self.actions = { 'next' : self.next, 'prev' : self.prev, 'cancel' : self.cancel, 'finish' : self.finish }
		self._result = None

	def replace_title( self, title ):
		"""Set title of all pages."""
		for page in self:
			page.title = title

	def result( self ):
		"""Return the result storged by the last Wizard page."""
		return self._result

	def action( self, object ):
		"""Call the function responsible for handling the action (object.options['action']), falling back to 'next'."""
		if 'action' in object.options:
			action = object.options[ 'action' ]
			del object.options[ 'action' ]
		else:
			action = 'next'

		if action in self.actions:
			return self.actions[ action ]( object )

		return WizardResult( False, 'Unknown wizard action: %s' % action )

	def setup( self, object, prev = None, next = None, finish = None, cancel = None ):
		"""Create graphical representation for the current Wizard page."""
		if prev == True:
			force_prev = True
		else:
			force_prev = False
		if prev is None:
			prev = True
		if next is None:
			next = True
		if finish is None:
			finish = False
		if cancel is None:
			cancel = True
		if self.current == ( len( self ) - 1 ): # last page
			next = False
			if not finish:
				finish = True
		elif not self.current:
			prev = force_prev

		page = self[self.current]
		return page.setup(self.command, object.options, prev=prev, next=next, finish=finish, cancel=cancel)

	def finish( self, object ):
		"""Convert the internally collected data of this Wizard into the external representation."""
		return WizardResult( False, 'finish is not implemented!' )

	def next( self, object ):
		"""Transition to the next Wizard page."""
		if self.current == None:
			self.current = 0
		elif self.current == ( len( self ) - 1 ):
			return None
		else:
			self.current += 1

		return WizardResult()

	def prev( self, object ):
		"""Transition to the previous Wizard page."""
		if self.current == 0:
			return None
		else:
			self.current -= 1

		return WizardResult()

	def cancel( self, object ):
		"""Cancel the complete Wizard."""
		return WizardResult( False, 'cancel is not implemented!' )

	def reset( self ):
		"""Reset Wizard back to initial values."""
		self.current = None
		self._result = None
