#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention System Info
#  module: ceollecting system information
#
# Copyright (C) 2009 Univention GmbH
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
import univention.management.console.handlers as umch
import univention.management.console.dialog as umcd
import univention.management.console.tools as umct
import univention.management.console.protocol as umcp

import notifier.popen

import univention.config_registry as ucr
import univention.service_info as usi

import os
import re
from urllib import quote, urlencode
from urlparse import urlunparse

# locale module that overrides functions in urllib2
import upload
import urllib2

_ = umc.Translation('univention.management.console.handlers.sysinfo').translate

name = 'sysinfo'
icon = 'sysinfo/module'
short_description = _('System Information')
long_description = _('Collecting System Information')
categories = [ 'system', 'all' ]

command_description = {
	'sysinfo/show': umch.command(
		short_description = _('System Information'),
		long_description = _('System Information'),
		method = 'sysinfo_show',
		values = { 
				   },
		startup = True,
		),
	'sysinfo/upload': umch.command(
		short_description = _('Store System Information'),
		long_description = _('System Information'),
		method = 'sysinfo_show',
		values = { 'manufacturer' : umc.String( _( 'Manufacturer' ) ),
				   'model' : umc.String( _( 'Model' ) ),
				   'comment' : umc.String( _( 'Descriptive comment' ), required = False ),
				   'support' : umc.Boolean( _( 'This is related to a support case' ) ),
				   'ticket' : umc.String( _( 'This is related to a support case' ) ),
				   'cpu' : umc.String( _( 'CPU' ), required = False, may_change = False ),
				   'num_cpu' : umc.String( _( 'Number of CPUs' ), required = False, may_change = False ),
				   'mem' : umc.String( _( 'Memory' ), required = False, may_change = False ),
				   'net_dev' : umc.String( _( 'Network Device' ), required = False, may_change = False ),
				   'gfx_dev' : umc.String( _( 'Graphics Device' ), required = False, may_change = False ),
				   },
		),	
}
class handler( umch.simpleHandler ):
	def __init__( self ):
		global command_description
		umch.simpleHandler.__init__( self, command_description )
		self.current_page = 0
		self._current_page = None
		self._pages = {}
		self.sysinfo = {}
		self._create_wizard_pages()
		self.mem_reg = re.compile( '([0-9]*) kB' )
		
	def sysinfo_show( self, object ):
		if 'action' in object.options:
			action = object.options[ 'action' ]
			del object.options[ 'action' ]
		else:
			action = None
		res = umcp.Response( object )
		if not action or action == 'next':
			if self._current_page == None:
				m, p = self._call_dmidecode()
				object.options[ 'manufacturer' ] = m
				object.options[ 'model' ] = p
				res.dialog = self._get_page( 'general', object )
				self.finished( object.id(), res )
			elif self._current_page == 'general':
				if object.options[ 'support' ]:
					res.dialog = self._get_page( 'support', object )
					self.finished( object.id(), res )
				else:
					ret = self.collect_data( object )
					if ret == None:
						res.dialog = self._get_page( 'summary', object )
						self.finished( object.id(), res )
					else:
						self.finished( object.id(), res, ret, False )
			elif self._current_page == 'support':
				ret = self.collect_data( object )
				if ret == None:
					res.dialog = self._get_page( 'summary', object )
					self.finished( object.id(), res )
				else:
					self.finished( object.id(), res, ret, False )
			elif self._current_page == 'summary':
				res.dialog = self._get_page( 'choice', object )
				self.finished( object.id(), res )
		elif action == 'prev':
			if self._current_page == 'support':
				res.dialog = self._get_page( 'general', object )
				self.finished( object.id(), res )
			elif self._current_page == 'summary':
				if object.options[ 'support' ]:
					res.dialog = self._get_page( 'support', object )
				else:
					res.dialog = self._get_page( 'general', object )
				self.finished( object.id(), res )
			elif self._current_page == 'choice':
				res.dialog = self._get_page( 'summary', object )
				self.finished( object.id(), res )
			elif self._current_page == 'sendmail':
				res.dialog = self._get_page( 'choice', object )
				self.finished( object.id(), res )
		elif action == 'mail':
			if self._current_page == 'choice':
				res.dialog = self._get_page( 'sendmail', object )
				self.finished( object.id(), res )
		elif action == 'upload':
			fd = open( os.path.join( '/var/www/univention-management-console/system-info/', object.options[ 'archive' ] ), 'r' )
			url = umc.registry.get( 'umc/sysinfo/upload/url', 'https://forge.univention.de/cgi-bin/system-info-upload.py' )
			data = { 'filename' : fd, }
			req = urllib2.Request( url, data, {} )
			try:
				u = urllib2.urlopen( req )
				answer = u.read()
				success = True
			except:
				success = False
			if not success or answer.startswith( 'ERROR:' ):
				res.dialog = self._get_page( 'uploadfailed', object )
				self.finished( object.id(), res )
				return
			res.dialog = self._get_page( 'uploadok', object )
			self.finished( object.id(), res )
		elif action == 'finish':
			os.unlink( os.path.join( '/var/www/univention-management-console/system-info/', object.options[ 'archive' ] ) )
			res.dialog = None
			res.status( 250 )
			self.finished( object.id(), res )

	def collect_data( self, object ):
		# call usi in UMC mode (-u)
		if not object.options[ 'comment' ]:
			comment = ''
		else:
			comment = object.options[ 'comment' ]
		cmd = '/usr/bin/univention-system-info -m "%s" -t "%s" -c "%s" -s "%s" -u' % ( object.options[ 'manufacturer' ], object.options[ 'model' ], comment, object.options[ 'support' ] )
		ret = umct.run_process( cmd, timeout = 10000 )
		# usi exited successfully
		if ret[ 'exit' ] == 0:
			for line in ret[ 'stdout' ].readlines():
				info, value = line.split( ':' )
				object.options[ info ] = value[ : -1 ]
			# adjust memory value
			if object.options[ 'mem' ]:
				match = self.mem_reg.match( object.options[ 'mem' ] )
				if match:
					try:
						object.options[ 'mem' ] = '%.2f GB' % ( float( match.groups()[ 0 ] ) / 1024 )
					except:
						pass
					
			return None
		else:
			return _( 'Execution of univention-system-info failed: %s' ) % ret[ 'stderr' ].read()

	def _get_page( self, page, object ):
		self._current_page = page
		wiz, buttons, inputs = self._pages[ page ]
		for btn in buttons:
			btn.actions[ 0 ].command.options.update( object.options )

		for item in inputs:
			if type( item ) == umcd.Link:
				item.set_link( 'http://%s/univention-management-console/system-info/%s' % ( umc.registry.get( 'hostname' ), object.options[ 'archive' ] ) )
			elif item.option in object.options:
				item.default = object.options[ item.option ]
		return wiz.setup()

	def __mail_sysinfo( self ):
		url = urlunparse( ( 'mailto', '', umc.registry.get( 'umc/sysinfo/mail/address', 'feedback@univention.de' ), '',
							urlencode( { 'subject' : unicode( umc.registry.get( 'umc/sysinfo/mail/subject', 'Univention System Info' ) ), } ), '' ) )
		return url.replace( '+', '%20' )

	def _call_dmidecode( self ):
		manu = None
		ret = umct.run_process( 'dmidecode -s system-manufacturer', timeout = 3000 )
		if ret[ 'exit' ] == 0:
			manu = ret[ 'stdout' ].read()
		product = None
		ret = umct.run_process( 'dmidecode -s system-product-name', timeout = 3000 )
		if ret[ 'exit' ] == 0:
			product = ret[ 'stdout' ].read()

		return ( manu, product )

	def _create_wizard_pages( self ):
		# first page
		items = []
		wiz = umcd.Wizard( _( "General Information" ) )
		image = umcd.Image( 'sysinfo/module', umct.SIZE_LARGE )
		wiz.set_image( image )

		description = _( '''
This modul collects information about the hardware of your system. These might be helpful in connection with a support case. By transmitting the data to Univention you provide the information on which platforms UCS is currently used and therefore should be supported by newer versions. All information gathered by this modul will be made anonymous before the transfer to Univention. In the following procedure you will be informed in detail about the each step.
''' )
		wiz._content.add_row( [ umcd.Fill( 2, description ), ] )
		wiz._content.add_row( [ umcd.Fill( 2 ), ] )
		wiz._content.add_row( [ umcd.Fill( 2, _( 'No information is transmitted without your acceptance!' ) ), ] )
		wiz._content.add_row( [ umcd.Fill( 2 ), ] )

		manu = umcd.make( self[ 'sysinfo/upload' ][ 'manufacturer' ] )
		items.append( manu.id() )
		model = umcd.make( self[ 'sysinfo/upload' ][ 'model' ] )
		items.append( model.id() )

		wiz._content.add_row( [ manu, model ] )
		
		comment = umcd.make( self[ 'sysinfo/upload' ][ 'comment' ] )
		items.append( comment.id() )
		support = umcd.make( self[ 'sysinfo/upload' ][ 'support' ] )
		items.append( support.id() )

		wiz._content.add_row( [ comment, support ] )
		
		description = _( '''
If this is related to a support case the next step will be to enter the ticket number. if not than the information about your system will be collected and a summary is shown.
''' )
		wiz._content.add_row( [ umcd.Fill( 2 ), ] )
		wiz._content.add_row( [ umcd.Fill( 2, description ), ] )

		req = umcp.SimpleCommand('sysinfo/show', { 'action' : 'next' } )

		button = umcd.NextButton( ( umcd.Action( req, items ), ), { 'class' : 'button_right' } )
		wiz._content.add_row( [ '', button ] )

		self._pages[ 'general' ] = ( wiz, ( button, ), ( manu, model, comment, support ) )

		# second page
		items = []
		wiz = umcd.Wizard( _( "Support Information" ) )
		image = umcd.Image( 'sysinfo/module', umct.SIZE_LARGE )
		wiz.set_image( image )

		description = _( '''
If a Univention Support Engeenier has aksed you to provide these information, than please insert the ticket number of the related support ticket into the following text field. The ticket number can be found in the subject of a support mail of the ticket. This information will speed up the processing of the ticket.
''' )
		wiz._content.add_row( [ umcd.Fill( 2, description ), ] )
		wiz._content.add_row( [ umcd.Fill( 2 ), ] )

		ticket = umcd.make( self[ 'sysinfo/upload' ][ 'ticket' ] )
		items.append( ticket.id() )

		wiz._content.add_row( [ ticket, ] )

		wiz._content.add_row( [ umcd.Fill( 2 ), ] )
		wiz._content.add_row( [ umcd.Fill( 2, _( 'In the next step the information aobut the hardware of your system will be collect and a summary will be shown. No information will be send to Univention.' ) ), ] )
		wiz._content.add_row( [ umcd.Fill( 2 ), ] )

		
		next = umcp.SimpleCommand( 'sysinfo/show', { 'action' : 'next' } )
		prev = umcp.SimpleCommand( 'sysinfo/show', { 'action' : 'prev' } )
		prev.verify_options = False

		bnext = umcd.NextButton( ( umcd.Action( next, items ), ), { 'class' : 'button_right' } )
		bprev = umcd.PrevButton( ( umcd.Action( prev, items ), ) )
		wiz._content.add_row( [ bprev, bnext ] )

		self._pages[ 'support' ] = ( wiz, ( bprev, bnext ), ( ticket, ) )

		# third page
		items = []
		wiz = umcd.Wizard( _( "Collected Data" ) )
		image = umcd.Image( 'sysinfo/module', umct.SIZE_LARGE )
		wiz.set_image( image )

		description = _( '''
The following information has been collected and will be transfered to Univention with your acceptance.
''' )
		wiz._content.add_row( [ umcd.Fill( 2, description ), ] )
		wiz._content.add_row( [ umcd.Fill( 2 ), ] )

		cpu = umcd.make( self[ 'sysinfo/upload' ][ 'cpu' ] )
		cpu[ 'width' ] = '400'
		items.append( cpu.id() )
		num_cpu = umcd.make( self[ 'sysinfo/upload' ][ 'num_cpu' ] )
		num_cpu[ 'width' ] = '50'
		items.append( num_cpu.id() )
		mem = umcd.make( self[ 'sysinfo/upload' ][ 'mem' ] )
		mem[ 'width' ] = '50'
		items.append( mem.id() )
		wiz._content.add_row( [ cpu, ] )
		wiz._content.add_row( [ num_cpu, ] )
		wiz._content.add_row( [ mem, ] )
		net_dev = umcd.make( self[ 'sysinfo/upload' ][ 'net_dev' ] )
		net_dev[ 'width' ] = '400'
		items.append( net_dev.id() )
		wiz._content.add_row( [ net_dev, ] )
		gfx_dev = umcd.make( self[ 'sysinfo/upload' ][ 'gfx_dev' ] )
		gfx_dev[ 'width' ] = '400'
		items.append( gfx_dev.id() )
		wiz._content.add_row( [ gfx_dev, ] )

		infos = _( '''
Additionally to the information listed above some more details about your system hsa been collected. The hole set of collected data that willb e transmitted to Univention can be downlaoded at the following URL:
''' )
		wiz._content.add_row( [ umcd.Fill( 2 ), ] )
		wiz._content.add_row( [ umcd.Fill( 2, infos ), ] )
		wiz._content.add_row( [ umcd.Fill( 2 ), ] )

		link = umcd.Link( _( 'Archive with system information' ), '', 'sysinfo/download', icon_and_text = True )
		wiz._content.add_row( [ link, ] )
		wiz._content.add_row( [ umcd.Fill( 2 ), ] )

		wiz._content.add_row( [ umcd.Fill( 2, _( 'In the following step two possiblities to transmit the information to Nnivention will be described.' ) ), ] )
		wiz._content.add_row( [ umcd.Fill( 2 ), ] )

		
		next = umcp.SimpleCommand('sysinfo/show', { 'action' : 'next' } )
		prev = umcp.SimpleCommand('sysinfo/show', { 'action' : 'prev' } )

		bnext = umcd.NextButton( ( umcd.Action( next, items ), ), { 'class' : 'button_right' } )
		bprev = umcd.PrevButton( ( umcd.Action( prev, items ), ) )
		wiz._content.add_row( [ bprev, bnext ] )

		self._pages[ 'summary' ] = ( wiz, ( bprev, bnext ), ( cpu, num_cpu, mem, net_dev, gfx_dev, link ) )

		# forth page
		items = []
		wiz = umcd.Wizard( _( "Transfer the information" ) )
		image = umcd.Image( 'sysinfo/module', umct.SIZE_LARGE )
		wiz.set_image( image )

		description = _( '''
The collected information can be transfered to Univention by uploading the data or be sending the data via mail. Please selected the corresponding button for the technique of your choice.
''' )
		wiz._content.add_row( [ umcd.Fill( 3, description ), ] )
		wiz._content.add_row( [ umcd.Fill( 3 ), ] )
		wiz._content.add_row( [ umcd.Fill( 3 ), ] )
		wiz._content.add_row( [ umcd.Fill( 3 ), ] )
		
		upload = umcp.SimpleCommand('sysinfo/show', { 'action' : 'upload' } )
		mail = umcp.SimpleCommand('sysinfo/show', { 'action' : 'mail' } )
		prev = umcp.SimpleCommand('sysinfo/show', { 'action' : 'prev' } )

		bupload = umcd.Button( _( 'Upload' ), 'actions/upload', umcd.Action( upload, items ), { 'class' : 'button_right' } )
		bmail = umcd.Button( _( 'Send mail (optional)' ), 'actions/mail', umcd.Action( mail, items ), { 'class' : 'button_center' } )
		bprev = umcd.PrevButton( ( umcd.Action( prev, items ), ) )
		wiz._content.add_row( [ bprev, umcd.Cell( bmail, { 'align' : 'center' } ), bupload ] )

		self._pages[ 'choice' ] = ( wiz, ( bprev, bupload, bmail ), () )

		# fifth page
		items = []
		wiz = umcd.Wizard( _( "Transfer via mail" ) )
		image = umcd.Image( 'sysinfo/module', umct.SIZE_LARGE )
		wiz.set_image( image )

		description = _( '''
To transfer the information via mail please follow these steps:
''' )
		instruction = _( '''
<ol>
<li>Download the archive with the collected information and save it on your local system (find the link below)</li>
<li>Click on link <i>Send mail</i> to open your mail program</li>
<li>Attach the downloaded archive to the mail and send it to Univention</li>
<li>End this assistent by clicking on the button <i>Finish</i></li>
</ol>
''' )
		wiz._content.add_row( [ description, ] )
		wiz._content.add_row( [ umcd.HTML( instruction ), ] )
		
		finish = umcp.SimpleCommand('sysinfo/show', { 'action' : 'finish' } )
		prev = umcp.SimpleCommand('sysinfo/show', { 'action' : 'prev' } )

		link = umcd.Link( _( 'Archive with system information' ), '', 'sysinfo/download', icon_and_text = True )
		wiz._content.add_row( [ link, ] )
		wiz._content.add_row( [ umcd.Link( _( 'Send mail' ), self.__mail_sysinfo(), 'sysinfo/mail-send', icon_and_text = True ) ] )
		wiz._content.add_row( [ '', ] )
		
		bfinish = umcd.Button( _( 'Finish' ), 'actions/finish', umcd.Action( finish, items ), { 'class' : 'button_right' } )
		bprev = umcd.PrevButton( ( umcd.Action( prev, items ), ) )
		wiz._content.add_row( [ '', ] )
		wiz._content.add_row( [ bprev, bfinish ] )

		self._pages[ 'sendmail' ] = ( wiz, ( bprev, bfinish ), ( link, ) )

		# sixth page
		items = []
		wiz = umcd.Wizard( _( "Transfered successfully" ) )
		image = umcd.Image( 'sysinfo/module', umct.SIZE_LARGE )
		wiz.set_image( image )

		description = _( '''
The information were tranfered to Univention successfully.
<br>
Thank you very much for your support!
''' )
		wiz._content.add_row( [ umcd.HTML( description ), ] )
		wiz._content.add_row( [ '', ] )
		finish = umcp.SimpleCommand('sysinfo/show', { 'action' : 'finish' } )

		bfinish = umcd.Button( _( 'Finish' ), 'actions/finish', umcd.Action( finish, items ), { 'class' : 'button_right' } )
		wiz._content.add_row( [ '', ] )
		wiz._content.add_row( [ '', bfinish ] )

		self._pages[ 'uploadok' ] = ( wiz, ( bfinish, ), () )

		# seventh page
		items = []
		wiz = umcd.Wizard( _( "Transfered successfully" ) )
		image = umcd.Image( 'sysinfo/module', umct.SIZE_LARGE )
		wiz.set_image( image )

		description = _( '''
The information could not be tranfered to Univention successfully. Therefor we would like you to ask to send the information via mail to Univention. Please follow the steps:
<br><br>
Thank you very much for your support!
''' )
		wiz._content.add_row( [ umcd.HTML( description ), ] )
		wiz._content.add_row( [ umcd.HTML( instruction ), ] )
		
		finish = umcp.SimpleCommand('sysinfo/show', { 'action' : 'finish' } )

		link = umcd.Link( _( 'Archive with system information' ), '', 'sysinfo/download', icon_and_text = True )
		wiz._content.add_row( [ link, ] )
		wiz._content.add_row( [ umcd.Link( _( 'Send mail' ), self.__mail_sysinfo(), 'sysinfo/mail-send', icon_and_text = True ) ] )
		wiz._content.add_row( [ '', ] )
		
		bfinish = umcd.Button( _( 'Finish' ), 'actions/finish', umcd.Action( finish, items ), { 'class' : 'button_right' } )
		wiz._content.add_row( [ '', ] )
		wiz._content.add_row( [ '', bfinish ] )

		self._pages[ 'uploadfailed' ] = ( wiz, ( bfinish, ), ( link, ) )
