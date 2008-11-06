#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  quota module: revamp module command result for the specific user interface
#
# Copyright (C) 2007 Univention GmbH
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

import univention.management.console as umc
import univention.management.console.dialog as umcd
import univention.management.console.protocol as umcp
import univention.management.console.tools as umct

import univention.debug as ud

import mtab
import tools

_ = umc.Translation( 'univention.management.console.handlers.quota' ).translate

class Web( object ):
	def _web_quota_list( self, object, res ):
		lst = umcd.List()
		part_cell = umcd.Text( _( 'Partition' ) )
		part_cell[ 'colspan' ] = '2'

		lst.set_header( [ part_cell, _( 'Mount-Point' ), _( 'Quota' ), _( 'Size' ),
						  _( 'Free' ), _( 'Select' ) ] )
		boxes = []

		for part in res.dialog:
			if part.params.mount_point == '/':
				chk = umcd.Text( '' )
			else:
				chk = umcd.Checkbox( static_options =
									 { 'partition' : part.params.spec } )
				boxes.append( chk.id() )
			req = umcp.Command( args = [ 'quota/partition/show' ],
								opts =  { 'partition' : part.params.spec } )
			req.set_flag( 'web:startup', True )
			req.set_flag( 'web:startup_reload', True )
			req.set_flag( 'web:startup_format', _( 'Partition: %(partition)s' ) )
			row_args = {}
			info = ''
			status = _( 'unknown' )
			if part.mounted and part.quota_written and part.quota_used:
				btn = umcd.Button( part.params.spec, 'quota/partition', umcd.Action( req ) )
				btn[ 'colspan' ] = '2'
				part_cell = [ btn, ]
				status = _( 'activated' )
			else:
				if not part.mounted:
					info = _( 'This partition is currently not mounted' )
				elif not part.quota_written and part.quota_used:
					info = _( 'The quota support is deactivated in the configuration, but the partition is still mounted with quota support activated.' )
				elif part.quota_written and not part.quota_used:
					info = _( 'The quota support is activated in the configuration, but the partition is still mounted without quota support.' )
				elif not part.quota_written and not part.quota_used:
					status = _( 'deactivated' )

				btn = umcd.Image( 'quota/partition_inactive',
								  attributes = { 'type' : 'umc_list_element_part_left' } )
				txt = umcd.Text( part.params.spec,
								 attributes = { 'type' : 'umc_list_element_part_right' } )
				part_cell = [ btn, txt ]
				row_args[ 'type' ] = 'umc_list_inactive'

			lst.add_row( part_cell + [ part.params.mount_point, status,
									   umcd.Number( part.size ), umcd.Number( part.free ), chk ],
						 attributes = row_args )
			if info:
				infobox = umcd.InfoBox( info, columns = 5 )
				lst.add_row( [ '', infobox, '' ] )

		req = umcp.Command( args = [], opts= { 'partition' : [] } )
		req_list = umcp.Command( args = [ 'quota/list' ] )
		actions = ( umcd.Action( req, boxes, True ), umcd.Action( req_list ) )
		choices = [ ( 'quota/partition/activate', _( 'activate' ) ),
					( 'quota/partition/deactivate', _( 'deactivate' ) ) ]
		select = umcd.SelectionButton( _( 'Select the Operation' ), choices, actions )
		lst.add_row( [ umcd.Fill( 6 ), select ] )

		res.dialog = umcd.Frame( [ lst ], _( 'Partition Overview' ) )
		self.revamped( object.id(), res )

	def _web_quota_partition_show( self, object, res ):
		partition, quotas = res.dialog

		if object.incomplete or not partition:
			res.dialog = []
			self.revamped( object.id(), res )
			return

		info = umcd.List()
		info.add_row( [ _( 'Mount-Point:' ), partition.mount_point ] )
		info.add_row( [ _( 'Filesystem:' ), partition.type ] )
		info.add_row( [ _( 'Options:' ), ', '.join( partition.options ) ] )

		lst = umcd.List()
		if quotas:
			# parse repquota output
			blocks = umcd.Text( _( 'Limit: Size' ), attributes = { 'colspan' : '4' } )
			files = umcd.Text( _( 'Limit: Files' ), attributes = { 'colspan' : '4' } )
			lst.set_header( [ _( 'User' ), blocks, files, _( 'Select' ) ] )
			lst.set_second_header( [ '', _( 'Used' ), _( 'Soft' ), _( 'Hard' ), _( 'Grace' ),
									 _( 'Used' ), _( 'Soft' ), _( 'Hard' ), _( 'Grace' ), '' ] )

			boxes = []
			for user in quotas:
				if user.user == 'root':
					continue
				chk = umcd.Checkbox( static_options = { 'user' : user.user } )
				boxes.append( chk.id() )
				req = umcp.Command( args = [ 'quota/user/show' ],
									opts =  { 'user' : user.user, 'partition' : partition.spec } )
				req.set_flag( 'web:startup', True )
				req.set_flag( 'web:startup_reload', True )
				req.set_flag( 'web:startup_dialog', True )
				req.set_flag( 'web:startup_format', _( 'Edit Quota for %(user)s' ) )
				lst.add_row( [ umcd.Button( user.user, 'quota/user', umcd.Action( req ) ),
								 umcd.Number( tools.block2byte( user.bused ) ),
								 umcd.Number( tools.block2byte( user.bsoft ) ),
								 umcd.Number( tools.block2byte( user.bhard ) ),
								 umcd.Text( user.btime ),
								 umcd.Number( user.fused ), umcd.Number( user.fsoft ),
								 umcd.Number( user.fhard ), umcd.Text( user.ftime ), chk ] )

			req = umcp.Command( args = [], opts = { 'partition' : partition.spec, 'user' : [] } )
			req_show = umcp.Command( args = [ 'quota/partition/show' ],
									 opts =	{ 'partition' : partition.spec } )
			actions = ( umcd.Action( req, boxes, True ), umcd.Action( req_show ) )
			choices = [ ( 'quota/user/remove', _( 'Remove Quota Settings' ) ), ]
			select = umcd.SelectionButton( _( 'Select the Operation' ), choices, actions )
			lst.add_row( [ umcd.Fill( 9 ), select ] )
		else:
			lst.add_row( [ umcd.Fill( 9, _( 'Currently there are no quota settings for this partition' ) ) ] )

		req = umcp.Command( args = [ 'quota/user/show' ], opts = { 'partition' : partition.spec } )
		req.set_flag( 'web:startup', True )
		req.set_flag( 'web:startup_reload', True )
		req.set_flag( 'web:startup_dialog', True )
		req.set_flag( 'web:startup_format', _( 'Add Quota Settings on %(partition)s' ) )
		lst.add_row( [ umcd.Button( _( 'Add User' ), 'actions/add', umcd.Action( req ),
									attributes = { 'colspan' : '3' } ), umcd.Fill( 7 ) ] )
		info_frame = umcd.Frame( [ info ], _( 'Configuration' ) )
		if not lst:
			res.dialog = [ info_frame ]
		else:
			res.dialog = [ info_frame, umcd.Frame( [ lst ], _( 'Quota Settings' ) ) ]
		self.revamped( object.id(), res )

	def _web_quota_user_show( self, object, res ):
		lst = umcd.List()

		quota = res.dialog
		if quota.user and quota.partition:
			headline = _( "Modify Quota Setting for User '%(user)s' on Partition %(partition)s" ) \
					   % { 'user' : quota.user, 'partition' : quota.partition.spec }
		elif quota.partition:
			headline = _( "Add Quota Setting for a User on Partition %s" ) % \
					   quota.partition.spec
		else:
			headline = _( "Add Quota Setting for a User" )

		# user and partition
		if not quota.user:
			user = umcd.make( self[ 'quota/user/set' ][ 'user' ] )
		else:
			user = umcd.make_readonly( self[ 'quota/user/set' ][ 'user' ], default = quota.user )
		items = [ user.id() ]

		if not quota.partition or not quota.partition.spec:
			partition = umcd.make( self[ 'quota/user/set' ][ 'partition' ] )
		else:
			partition = umcd.make_readonly( self[ 'quota/user/set' ][ 'partition' ],
											default = quota.partition.spec )
		items += [ partition.id() ]
		lst.add_row( [ user, partition ] )

		soft = umcd.make( self[ 'quota/user/set' ][ 'block_soft' ],
						  default = tools.block2byte( quota.bsoft ) )
		hard = umcd.make( self[ 'quota/user/set' ][ 'block_hard' ],
						  default = tools.block2byte( quota.bhard ) )
		items += [ soft.id(), hard.id() ]
		lst.add_row( [ _( 'Amount of Data' ), ] )
		lst.add_row( [ soft, hard ] )
		lst.add_row( [ _( 'Number of Files' ), ] )
		soft = umcd.make( self[ 'quota/user/set' ][ 'file_soft' ], default = quota.fsoft )
		hard = umcd.make( self[ 'quota/user/set' ][ 'file_hard' ], default = quota.fhard )
		lst.add_row( [ soft, hard ] )
		items += [ soft.id(), hard.id() ]

		opts = { 'block_soft' : tools.block2byte( quota.bsoft ),
				 'block_hard' : tools.block2byte( quota.bhard ),
				 'file_soft'  : quota.fsoft, 'file_hard'  : quota.fhard }
		if quota.partition:
			opts[ 'partition' ] = quota.partition.spec
		if quota.user:
			opts[ 'user' ] = quota.user

		req = umcp.Command( args = [ 'quota/user/set' ], opts = opts )
		if quota.partition:
			req_show = umcp.Command( args = [ 'quota/user/show' ],
									 opts = { 'partition' : quota.partition.spec } )
			items_show = []
		else:
			req_show = umcp.Command( args = [ 'quota/user/show' ] )
			items_show = [ partition.id(), ]

		actions = ( umcd.Action( req, items ), umcd.Action( req_show, items_show ) )
		button = umcd.SetButton( actions )
		cancel = umcd.CancelButton( attributes = { 'align' : 'right' } )
		lst.add_row( [ button, cancel ] )

		res.dialog = umcd.Frame( [ lst ], headline )
		self.revamped( object.id(), res )
