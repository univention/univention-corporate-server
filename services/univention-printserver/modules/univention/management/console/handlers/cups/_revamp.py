#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  cups module: revamp module command result for the specific user interface
#
# Copyright 2007-2012 Univention GmbH
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

import notifier.popen

import univention.management.console as umc
import univention.management.console.dialog as umcd
import univention.management.console.protocol as umcp

import univention.debug as ud

import tools

_ = umc.Translation( 'univention.management.console.handlers.cups' ).translate

class Web( object ):
	def _web_cups_list( self, object, res ):
		if object.incomplete:
			res.dialog = [ self.__printer_search_form() ]
			self.revamped( object.id(), res )
			return

		lst = umcd.List()
		boxes = []
		filter, key, printers = res.dialog
		if printers:
			lst.set_header( [ _( 'Server' ), _( 'Printer' ), _( 'Status' ), _( 'Quota' ),
							  _( 'Location' ), _( 'Description' ), '' ] )
			for printer, attributes in printers.items():
				req = umcp.Command( args = [ 'cups/printer/show' ], opts = { 'printer' : printer } )
				req.set_flag( 'web:startup', True )
				req.set_flag( 'web:startup_reload', True )
				req.set_flag( 'web:startup_format', '%(name)s: %(printer)s' )
				chk = umcd.Checkbox( static_options = { 'printers' : printer } )
				boxes.append( chk.id() )

				quotastate = _( 'inactive' )
				if attributes['quotastate']:
					reqquota = umcp.Command( args = [ 'cups/printer/quota/list' ], opts = { 'printer' : printer } )
					reqquota.set_flag( 'web:startup', True )
					reqquota.set_flag( 'web:startup_reload', True )
					reqquota.set_flag( 'web:startup_format', '%(name)s: %(printer)s' )
					quotastate = umcd.Button( _( 'active' ), 'cups/quota', umcd.Action( reqquota ) )

				row = [ umc.registry[ 'hostname' ],
						umcd.Button( printer, 'cups/printer', umcd.Action( req ) ),
						attributes[ 'state' ], quotastate,
						attributes[ 'location' ], attributes[ 'description' ],
						chk ]
				lst.add_row( row )
			req = umcp.Command( args = [], opts= { 'printers' : [] } )
			req_list = umcp.Command( args = [ 'cups/list' ],
									 opts = { 'filter' : filter, 'key' : key } )
			actions = ( umcd.Action( req, boxes, True ), umcd.Action( req_list ) )
			choices = [ ( 'cups/printer/enable', _( 'Activate printers' ) ),
						( 'cups/printer/disable', _( 'Deactivate printers' ) ) ]
			select = umcd.SelectionButton( _( 'Select the operation' ), choices, actions )

			lst.add_row( [ umcd.Fill( 6 ), select ] )
		else:
			lst.add_row( [ _( 'No printers could be found.' ) ] )

		res.dialog = [ self.__printer_search_form( filter, key ),
					   umcd.Frame( [ lst ], _( 'Search result' ) ) ]

		self.revamped( object.id(), res )

	def __printer_search_form( self, filter = '*', key = 'printer' ):
		select = umcd.make( self[ 'cups/list' ][ 'key' ], default = key,
							attributes = { 'width' : '200' } )
		text = umcd.make( self[ 'cups/list' ][ 'filter' ], default = filter,
						  attributes = { 'width' : '250' } )
		form = umcd.SearchForm( 'cups/list', [ [ ( select, 'printer' ), ( text, '*' ) ] ] )
		return form

	def _web_cups_printer_show( self, object, res ):
		joblist, printer = res.dialog

		info = umcd.List()
		attributes = printer[ object.options[ 'printer' ] ]
		headline = _( 'Printer: %s' ) % object.options[ 'printer' ]
		info.add_row( [ _( 'Server' ) + ':', umc.registry[ 'hostname' ] ] )
		info.add_row( [ _( 'Status' ) + ':', attributes[ 'state' ] ] )
		info.add_row( [ _( 'Location' ) + ':', attributes[ 'location' ] ] )
		info.add_row( [ _( 'Description' ) + ':', attributes[ 'description' ] ] )

		lst = umcd.List()
		boxes = []
		if joblist:
			lst.set_header( [ _( 'Job ID' ), _( 'Owner' ), _( 'Size' ), _( 'Date' ), '' ] )
			for job_id, owner, size, date in joblist:
				static_options = { 'jobs' : job_id, 'printer' : object.options[ 'printer' ] }
				chk_button = umcd.Checkbox( static_options = static_options )
				boxes.append( chk_button.id() )
				lst.add_row(  [ job_id, owner, umcd.Number(size), date, chk_button ] )

			req = umcp.Command( args = [], opts= { 'jobs' : [] } )
			req_show = umcp.Command( args = [ 'cups/printer/show' ],
									 opts= { 'printer' : object.options[ 'printer' ] } )
			actions = ( umcd.Action( req, boxes, True ), umcd.Action( req_show ) )
			choices = [ ( 'cups/job/cancel', _( 'Cancel print job' ) ), ]
			select = umcd.SelectionButton( _( 'Select the operation' ), choices, actions )
			lst.add_row( [ umcd.Fill( 4 ), select ] )
		else:
			lst.add_row( [ _( 'No jobs in the queue' ) ] )

		res.dialog = [ umcd.Frame( [ info, ], _( 'Information' ) ),
					   umcd.Frame( [ lst, ], _( 'Print job list' ) ) ]

		self.revamped( object.id(), res )


	def _web_cups_printer_quota_list( self, object, res ):
		printerdata, quotadata = res.dialog

		info = umcd.List()
		printer = tools.parse_lpstat_l( printerdata )
		attributes = printer[ object.options[ 'printer' ] ]
		headline = _( 'Printer: %s' ) % object.options[ 'printer' ]
		info.add_row( [ _( 'Server' ) + ':', umc.registry[ 'hostname' ] ] )
		info.add_row( [ _( 'Status' ) + ':', attributes[ 'state' ] ] )
		info.add_row( [ _( 'Location' ) + ':', attributes[ 'location' ] ] )
		info.add_row( [ _( 'Description' ) + ':', attributes[ 'description' ] ] )

		# find correct printer
		prnQuota = None
		for x in quotadata:
			if x.printername == object.options[ 'printer' ]:
				prnQuota = x

		lstQ = umcd.List()
		boxes = []
		if prnQuota:
			lstQ.set_header( [ _( 'User' ), _( 'Pages used' ), _( 'Soft limit' ), _( 'Hard limit' ),
							   _( 'Lifetime page counter' ), '' ] )
			for uquota in prnQuota.userlist:
				static_options = { 'user' : uquota.user, 'printer' : object.options[ 'printer' ] }
				chk_button = umcd.Checkbox( static_options = static_options )
				boxes.append( chk_button.id() )

				softlimit = uquota.softlimit
				hardlimit = uquota.hardlimit
				if not softlimit.isdigit():
					if softlimit == 'None':
						softlimit = ''
				if not hardlimit.isdigit():
					if hardlimit == 'None':
						hardlimit = ''

				req = umcp.Command( args = [ 'cups/quota/user/show' ],
									opts =  { 'user' : uquota.user,
												'printer' : object.options[ 'printer' ],
												'pagesoftlimit' : softlimit,
												'pagehardlimit' : hardlimit } )
				req.set_flag( 'web:startup', True )
				req.set_flag( 'web:startup_reload', True )
				req.set_flag( 'web:startup_dialog', True )
				req.set_flag( 'web:startup_format', _( 'Edit print quota for %(user)s' ) )
				lstQ.add_row(  [ umcd.Button( uquota.user, 'cups/user', umcd.Action( req ) ),
								 umcd.Number(uquota.pagecounter), umcd.Number(softlimit),
								 umcd.Number(hardlimit), umcd.Number(uquota.lifetimepagecounter),
								 chk_button ] )

			req = umcp.Command( args = [ ], opts= { 'printer' : object.options[ 'printer' ],
													'user': [] } )
			req_show = umcp.Command( args = [ 'cups/printer/quota/list' ],
									 opts= { 'printer' : object.options[ 'printer' ] } )
			actions = ( umcd.Action( req, boxes, True ), umcd.Action( req_show ) )
			choices = [ ( 'cups/quota/user/reset', _( 'Reset user quota' ) ) ]
			select = umcd.SelectionButton( _( 'Select the operation' ), choices, actions )
			lstQ.add_row( [ umcd.Fill( 5 ), select ] )
		else:
			lstQ.add_row( [ _( 'No quota settings available' ) ] )

		req = umcp.Command( args = [ 'cups/quota/user/show' ],
							opts = { 'printer' : object.options[ 'printer' ] } )
		req.set_flag( 'web:startup', True )
		req.set_flag( 'web:startup_reload', True )
		req.set_flag( 'web:startup_dialog', True )
		req.set_flag( 'web:startup_format', _( 'User quota on %(printer)s' ) )
		lstQ.add_row( [ umcd.Button( _( 'Add quota entry' ), 'actions/add', umcd.Action( req ),
									attributes = { 'colspan' : '3' } ), umcd.Fill( 3 ) ] )
		res.dialog = [ umcd.Frame( [ info, ], _( 'Information' ) ),
						umcd.Frame( [ lstQ ], _( 'Print quota' ) ) ]

		self.revamped( object.id(), res )

	def _web_cups_quota_user_show( self, object, res ):
		lst = umcd.List()

		quota = res.dialog
		if quota[ 'user' ]:
			headline = _( "Modify print quota setting for user '%(user)s' on printer %(printer)s" ) % quota
		else:
			headline = _( "Add print quota entry on printer %(printer)s" ) % quota

		# user and partition
		if not quota['user']:
			user = umcd.make( self[ 'cups/quota/user/set' ][ 'user' ] )
		else:
			if type(quota['user']) == type([]):
				user = umcd.make_readonly( self[ 'cups/quota/user/set' ][ 'user' ], default = ','.join(quota['user']) )
			else:
				user = umcd.make_readonly( self[ 'cups/quota/user/set' ][ 'user' ], default = quota['user'] )
		items = [ user.id() ]

		if not quota['printer']:
			printer = umcd.make( self[ 'cups/quota/user/set' ][ 'printer' ] )
		else:
			printer = umcd.make_readonly( self[ 'cups/quota/user/set' ][ 'printer' ],
											default = quota['printer'] )
		items += [ printer.id() ]
		lst.add_row( [ user, printer ] )

		soft = umcd.make( self[ 'cups/quota/user/set' ][ 'softlimit' ], default = quota['softlimit'] )
		hard = umcd.make( self[ 'cups/quota/user/set' ][ 'hardlimit' ], default = quota['hardlimit'] )
		items += [ soft.id(), hard.id() ]
		lst.add_row( [ soft, hard ] )

		opts = { 'softlimit' : quota['softlimit'],
				 'hardlimit' : quota['hardlimit']}
		if quota['printer']:
			opts['printer'] = quota['printer']
		if quota['user']:
			opts['user'] = quota['user']

		req = umcp.Command( args = [ 'cups/quota/user/set' ], opts = opts )
		if quota['printer']:
			req_show = umcp.Command( args = [ 'cups/quota/user/show' ],
									 opts = { 'printer' : quota['printer'] } )
			items_show = []
		else:
			req_show = umcp.Command( args = [ 'cups/quota/user/show' ] )
			items_show = [ printer.id(), ]

		actions = ( umcd.Action( req, items ), umcd.Action( req_show, items_show ) )
		button = umcd.SetButton( actions )
		cancel = umcd.CancelButton( attributes = { 'align' : 'right' } )
		lst.add_row( [ button, cancel ] )

		res.dialog = umcd.Frame( [ lst ], headline )
		self.revamped( object.id(), res )
