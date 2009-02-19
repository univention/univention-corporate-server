#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  mail server wizard
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

import univention.management.console as umc
import univention.management.console.dialog as umcd
import univention.management.console.protocol as umcp
import univention.management.console.tools as umct

_ = umc.Translation( 'univention.management.console.wizards.mailserver' ).translate

class Web( object ):
	def _web_mailserver_show( self, object, res ):
		options = res.dialog
		items = []
		wiz = umcd.Wizard( _( "Mail server configuration" ) )
		image = umcd.Image( 'wizards/mailserver/mail', umct.SIZE_LARGE )
		wiz.set_image( image )
		spam = umcd.make( self[ 'wizard/mailserver/set' ][ 'spam' ], default = options[ 'spam' ] )
		wiz.add_option( _( 'The mail server has the possibility to provide filtering of SPAM e-mails. It is recommended to activate this option.' ), spam )
		items.append( spam.id() )

		virus = umcd.make( self[ 'wizard/mailserver/set' ][ 'virus' ], default = options[ 'virus' ] )
		wiz.add_option( _( 'To avoid the delivery of virus infected e-mails the mail server can check incoming and outgoing e-mails for known virus signatures. This increases the security and it is highly recommanded to activate this option.' ), virus )
		items.append( virus.id() )

		imap = umcd.make( self[ 'wizard/mailserver/set' ][ 'imap' ], default = options[ 'imap' ] )
		wiz.add_option( _( 'IMAP is the most common protocol to access mail servers. It is recommended to activate this option.' ), imap )
		items.append( imap.id() )

		imap_quota = umcd.make( self[ 'wizard/mailserver/set' ][ 'imap_quota' ],
								default = options[ 'imap_quota' ] )
		wiz.add_option( _( 'To restrict the amount of e-mails that a user can store on the mail server it is required to activate this option. Via Univention Directory Manager it is possible to define the amount of e-mails that can be stored by a user (policy "mail quota").' ), imap_quota )
		items.append( imap_quota.id() )

		pop = umcd.make( self[ 'wizard/mailserver/set' ][ 'pop' ], default = options[ 'pop' ] )
		wiz.add_option( _( 'POP3 is another protocol that can be used to access mail servers. When Outlook is used as client for UGS, this option must be activated.' ), pop )
		items.append( pop.id() )

		size = umcd.make( self[ 'wizard/mailserver/set' ][ 'messagesizelimit' ],
						  default = options[ 'messagesizelimit' ] )
		size[ 'width' ] = '200'
		wiz.add_option( _( 'The following option provides the possibility to set a maximum size of incoming and outgoing e-mails. Very large e-mails may cause a high load on the mail server and thereby may increase respone times. The default value should work well in most scenarios.' ), size )
		items.append( size.id() )

		root = umcd.make( self[ 'wizard/mailserver/set' ][ 'root' ], default = options[ 'root' ] )
		root[ 'width' ] = '200'
		wiz.add_option( _( 'Any kind of information regarding problems or warnings on a system are send to the local e-mail account of the root user. These e-mails can be redirected to another global account by setting this option to a valid e-mail address.' ), root )
		items.append( root.id() )

		req = umcp.Command( args = [ 'wizard/mailserver/set' ] )
		req_show = umcp.Command( args = [ 'wizard/mailserver/show' ] )

		actions = ( umcd.Action( req, items ), umcd.Action( req_show ) )
		button = umcd.SetButton( actions )
		wiz.add_buttons( button, umcd.ResetButton( items ) )

		res.dialog = wiz

		self.revamped( object.id(), res )
