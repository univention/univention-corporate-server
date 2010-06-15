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

import imaplib
import re

import univention.debug as ud
import univention.uldap

import mail

# support for annotations is included with python 2.5
imaplib.Commands.update(
       {
        'GETANNOTATION':     ('AUTH', 'SELECTED'),
        'SETANNOTATION':     ('AUTH', 'SELECTED'),
        })

class IMAP_Client( object ):
	ANNOTATION_RESPONSE = re.compile( '"[^"]*" "[^"]*" \("[^"]*" "([^"]*)"\)' )

	def __init__( self ):
		self._folder = None
		try:
			fd = open( '/etc/cyrus.secret', 'r' )
		except:
			raise RuntimeError( 'Failed to read password for user cyrus. Is there a IMAP server installed?' )

		password = fd.readline()
		fd.close()
		if password[ -1 ] == '\n':
			password = password[ : -1 ]

		# try to connect
		try:
			self.imap4 = imaplib.IMAP4( 'localhost' )
		except Exception, e:
			raise RuntimeError( 'Connection to local IMAP server failed!' )

		# try to log in
		try:
			self.imap4.login( 'cyrus', password )
		except:
			raise RuntimeError( 'Login to IMAP server failed!' )

	def select( self, folder ):
		# remove ACLs from previously selected folder
		if self._folder:
			self.imap4.deleteacl( self._folder, 'cyrus' )

		self._folder = folder

		# set ACLs (required!)
		self.imap4.setacl( self._folder, 'cyrus', 'lrswipcda' )

		# select mailbox (checks existance)
		self.imap4.select( self._folder )

	def get_mails( self ):
		mails = []
		typ, data = self.imap4.search( None, 'ALL' )

		if not typ == 'OK' or not data:
			return mails

		for  i in data[ 0 ].split():
			typ, data = self.imap4.fetch( i, '(FLAGS BODY[])' )
			if typ == 'OK' and data:
				mails.append( ( i, data[ 0 ][ 1 ] ) )

		return mails

	def replace( self, id, message ):
		self.remove( id )
		self.add( message )

	def remove_all( self ):
		typ, data = self.imap4.search( None, 'ALL' )
		if not data:
			return

		# mark as deleted
		for i in data[ 0 ].split():
			self.imap4.store( i, '+FLAGS', '\\Deleted' )

		# expunge
		self.imap4.expunge()

	def is_deleted( self, id ):
		type, data = self.imap4.fetch( id, '(FLAGS)' )
		return data and data[ 0 ].find( '\\Deleted' ) > -1

	def remove( self, id, expunge = True ):
		# mark as deleted
		self.imap4.store( id, '+FLAGS', '\\Deleted' )

		# expunge
		if expunge:
			self.imap4.expunge()

	def expunge( self ):
		self.imap4.expunge()

	def list( self, directory = '""', pattern = '*' ):
		return self.imap4.list( directory, pattern )

	def add( self, message ):
		if not self._folder:
			raise RuntimeError( 'No folder select' )
		# add new message
		self.imap4.append( self._folder, None, None, message )

	def getannotation(self, root, entry, attrib):
		"""Get annotation

		(typ, [data]) = <instance>.getannotation(self, root, entry, attrib)
		"""
		typ, dat = self.imap4._simple_command('GETANNOTATION', root, entry, attrib)
		return self.imap4._untagged_response(typ, dat, 'ANNOTATION')

	def setannotation(self, root, entry, value):
		"""Set annotation value.

		(typ, [data]) = <instance>.setannotation(root, limits)
		"""
		typ, dat = self.imap4._simple_command('SETANNOTATION', root, entry, value)
		return self.imap4._untagged_response(typ, dat, 'ANNOTATION')

	def get_folder_type( self ):
		if not self._folder:
			raise RuntimeError( 'No folder select' )

		typ, dat = self.getannotation( self._folder, '/vendor/kolab/folder-type', '("value.shared")' )

		if typ != 'OK' or not dat or not dat[ 0 ] :
			return None

		match = IMAP_Client.ANNOTATION_RESPONSE.match( dat[ 0 ] )
		if not match:
			return None

		return match.groups()[ 0 ]
