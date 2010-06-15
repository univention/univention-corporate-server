#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Kolab2 Tools
#
# Copyright (C) 2008-2009 Univention GmbH
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

import email
import email.MIMEMultipart
import email.MIMEText
import email.Charset
import email.Utils
import time

import univention.config_registry as ucr

cfgRegistry = ucr.ConfigRegistry()
cfgRegistry.load()

import event
import contact

class Kolab2Message( object ):
	_counter = 0

	def __init__( self ):
		self._message = None

	def parse( self, data ):
		self._message = email.message_from_string( data )

	def create( self ):
		self._message = email.MIMEMultipart.MIMEMultipart()
		self._add_infotext()

	def __getitem__( self, key ):
		return self._message.__getitem__( self, key )

	def __setitem__( self, key, value ):
		return self._message.__setitem__( self, key, value )

	def get_addresses( self, header ):
		addrs = self._message.get_all( header, [] )

		# replace linefeeds, otherwise the parser (email.Uitls.parseaddr) will fail
		fixed_addrs = []
		for addr in addrs:
			fixed_addrs.append( addr.replace( '\r\n\t', '' ) )

		return email.Utils.getaddresses( fixed_addrs )

	def set_addresses( self, header, addresses ):
		value = []
		for addr in addresses:
			value.append( email.Utils.formataddr( addr ) )

		del self._message[ header ]
		self._message[ header ] = ', '.join( value )

	def as_string( self ):
		return self._message.as_string()

	def _add_infotext( self ):
		'''creates the information part of the message, explaining the content'''

		info = '''
Dies ist ein Kolab-Groupware-Objekt. Um dieses Objekt anzuzeigen, benötigen
Sie ein E-Mail-Programm, das das Kolab-Groupware-Format unterstützt. Eine
Liste solcher Programme finden Sie unter
http://www.kolab.org/kolab2-clients.html
'''
		charset = email.Charset.Charset( 'utf-8' )
		charset.body_encoding = email.Charset.QP
		info_text = email.MIMEText.MIMEText( charset.body_encode( info ), 'plain', 'utf-8' )
		info_text.set_charset( charset )
		info_text.set_payload( charset.body_encode( info ) )
		info_text.add_header( 'Content-Disposition', 'inline' )
		del info_text[ 'Content-Transfer-Encoding' ]
		info_text[ 'Content-Transfer-Encoding' ] = charset.get_body_encoding()
		self._message.attach( info_text )

	def replace_kolab_part( self, kolab_object ):
		if not self._message.is_multipart():
			return None

		for msg in self._message.get_payload():
			if msg.get_content_type().startswith( 'application/x-vnd.kolab.' ):

				charset = msg.get_charset()
				if not charset:
					charset = email.Charset.Charset( 'utf-8' )
					transfer = msg.get( 'Content-Transfer-Encoding', '' ).lower()
					if transfer == 'base64':
						charset.body_encoding = email.Charset.BASE64
					elif transfer == 'quoted-printable':
						charset.body_encoding = email.Charset.QP
					else:
						charset.body_encoding = email.Charset.BASE64
						del msg[ 'Content-Transfer-Encoding' ]
						msg[ 'Content-Transfer-Encoding' ] = charset.get_body_encoding()
					msg.set_charset( charset )
				xml = kolab_object.as_string()
				msg.set_payload( charset.body_encode( xml ) )
				break

	def get_kolab_part( self ):
		if not self._message.is_multipart():
			return None

		for msg in self._message.get_payload():
			if msg.get_content_type() == 'application/x-vnd.kolab.event':
				ev = event.Kolab2Event()
				ev.parse( msg.get_payload( decode = True ) )
				return ev
			if msg.get_content_type() == 'application/x-vnd.kolab.contact':
				co = contact.Kolab2Contact()
				co.parse( msg.get_payload( decode = True ) )
				return co

	def add_kolab_part( self, kolab_object ):
		charset = email.Charset.Charset( 'utf-8' )
 		charset.body_encoding = email.Charset.BASE64
		if kolab_object.is_contact():
			app = email.MIMEText.MIMEText( '', 'x-vnd.kolab.contact', 'utf-8' )
		else:
			app = email.MIMEText.MIMEText( '', 'x-vnd.kolab.event', 'utf-8' )
		app.set_charset( charset )
		xml = self._doc.toxml( encoding = 'utf-8' )
		app.set_payload( charset.body_encode( xml ) )
		if kolab_object.is_contact():
			app.set_type( 'application/x-vnd.kolab.contact' )
		else:
			app.set_type( 'application/x-vnd.kolab.event' )
		app.add_header( 'Content-Disposition', 'attachment', filename = 'event.xml' )
		self.attach( app )

	def remove_ical_part( self ):
		if not self._message.is_multipart():
			return None

		new_parts = []
		for msg in self._message.get_payload():
			if msg.get_content_type() != 'text/calendar':
				new_parts.append( msg )
		self._message.set_payload( new_parts )

	def remove_winmail_part( self ):
		if not self._message.is_multipart():
			return None

		new_parts = []
		for msg in self._message.get_payload():
			if msg.get_content_type() != 'application/ms-tnef':
				new_parts.append( msg )
		self._message.set_payload( new_parts )

	def create_message_id( self ):
		del self._message[ 'Message-ID' ]
		self._message[ 'Message-ID' ] = '%s-%d@%s' % ( str( time.time() ), Kolab2Message._counter, cfgRegistry.get( 'domainname', 'localhost' ) )
		Kolab2Message._counter += 1
