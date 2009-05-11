#!/usr/bin/python
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

import univention.kolab2 as uk2
import univention.config_registry as ucr
import univention.debug as ud

from optparse import OptionParser
import shlex
import sys

cfgRegistry = ucr.ConfigRegistry()
cfgRegistry.load()

_ignored = None
_mapping = None

def _read_ignored_addresses( filename ):
	global _ignored

	if _ignored:
		return _ignored
	addrs = []
	fd = open( filename )
	for line in fd.readlines():
		addrs.append( line[ : -1 ].lower() )

	ud.debug( ud.ADMIN, ud.INFO, 'found %d known email addresses that will be ignored' % len( addrs ) )
	_ignored = addrs

	return addrs

def _read_address_mapping( filename ):
	global _mapping
	if _mapping:
		return _mapping
	mapping = {}
	fd = open( filename )
	mail = None
	uid = None
	for line in fd.readlines():
		if line[ 0 ] == '#':
			continue
		uid, mail = line.split( ':', 1 )
		mapping[ uid.lower() ] = mail[ : -1 ].lower()

	ud.debug( ud.ADMIN, ud.INFO, 'found %d mapping entries' % len( mapping ) )
	_mapping = mapping

	return mapping

def _adjust_events( imap4, mails, options, ignore, mapping ):
	_to_be_removed = []
	_to_be_added = []
	for id, msg in mails:
		message = uk2.Kolab2Message()
		message.parse( msg )
		modified = False
		modified, message = _adjust_headers( imap4, message, options, ignore, mapping )
		event = message.get_kolab_part()
		if isinstance( event, uk2.Kolab2Event ):
			# adjust organizer
			user, domain = event.organizer_smtp_address.split( '@', 1 )
			if not event.organizer_smtp_address in ignore and domain in options.domains:
				if mapping.has_key( user ):
					ud.debug( ud.ADMIN, ud.INFO, 'replace organizer email address: %s -> %s' % \
							  ( event.organizer_smtp_address, mapping[ user ] ) )
					event.organizer_smtp_address = mapping[ user ]
					modified = True
			# adjust attendees
			for i in range( 1, event.n_attendees ):
				addr = event.get_attendee_email( i )
				try:
	 				user, domain = addr.split( '@', 1 )
				except:
					# invalid email address
					continue
				if addr in ignore or not domain in options.domains:
					continue
				if mapping.has_key( user ):
					event.set_attendee_email( i, mapping[ user ] )
					modified = True
					ud.debug( ud.ADMIN, ud.INFO, 'replace recipient email address: %s -> %s' % \
							  ( addr, mapping[ user ] ) )
			if modified:
				event.modified() # set last modification date
				message.replace_kolab_part( event )
# 				message.remove_ical_part() # otherwise the attendee lists will be merged by Bynari
# 				message.remove_winmail_part() # otherwise the attendee lists will be merged by Bynari
				_to_be_added.append( message )
				_to_be_removed.append( id )
		else:
			ud.debug( ud.ADMIN, ud.WARN, 'found invalid object in event folder: %s' % type( event ) )

	for id in _to_be_removed:
		imap4.remove( id, expunge = False )
	for msg in _to_be_added:
		msg.create_message_id()
		imap4.add( msg.as_string() )

	imap4.expunge()

def _adjust_headers( imap4, message, options, ignore, mapping ):
	changed = False
	for header in ( 'To', 'CC', 'BCC', 'From', 'Sender' ):
		addrs = message.get_addresses( header )
		modified = False
		new_addrs = []
		for name, addr in addrs:
			try:
				user, domain = addr.split( '@', 1 )
			except:
				continue
			user = user.lower()
			addr = addr.lower()
			domain = domain.lower()
			if addr in ignore or not domain in options.domains:
				new_addrs.append( ( name, addr ) )
			elif mapping.has_key( user ):
				new_addrs.append( ( name, mapping[ user ] ) )
				ud.debug( ud.ADMIN, ud.INFO, 'replace email address (%s): %s -> %s' % ( header, addr, mapping[ user ] ) )
				modified = True
			else:
				new_addrs.append( ( name, addr ) )
		if modified:
			changed = True
			message.set_addresses( header, new_addrs )

	return ( changed, message )

def _adjust_mails( imap4, mails, options, ignore, mapping ):
	_to_be_removed = []
	_to_be_added = []
	for id, msg in mails:
		if imap4.is_deleted( id ):
			continue
		message = uk2.Kolab2Message()
		message.parse( msg )
		modified, message = _adjust_headers( imap4, message, options, ignore, mapping )
		if modified:
			_to_be_removed.append( id )
			_to_be_added.append( message )

	for id in _to_be_removed:
		imap4.remove( id, expunge = False )
	for msg in _to_be_added:
		msg.create_message_id()
		imap4.add( msg.as_string() )

	imap4.expunge()

def adjust_addresses_in_folder( imap4, options ):
	imap4.select( options.folder )
	type = imap4.get_folder_type()
	mails = imap4.get_mails()
	ignore = _read_ignored_addresses( options.ignored_addresses )
	mapping = _read_address_mapping( options.address_mapping )
	if not type or type == 'mail':
		ud.debug( ud.ADMIN, ud.INFO, 'adjusting mails ...' )
		_adjust_mails( imap4, mails, options, ignore, mapping )
	elif type.startswith( 'event.' ):
		ud.debug( ud.ADMIN, ud.INFO, 'adjusting events ...' )
		_adjust_events( imap4, mails, options, ignore, mapping )
	elif type.startswith( 'contact.' ):
		ud.debug( ud.ADMIN, ud.INFO, 'unsupported folder type for adjustment: %s' % type )
		pass # TODO: not yet supported

def main():
	debug_level = int( cfgRegistry.get( 'kolab2/tools/debug/level','0' ) )

	parser = OptionParser()
	parser.add_option( '-d', '--debug', action = 'store', type = 'int',
					   dest = 'debug', default = debug_level,
					   help = 'if given than debugging is activated and set to the specified level' )
	parser.add_option( '-s', '--simulate', action = 'store_true',
					   dest = 'simulate', default = False,
					   help = 'if given the synchronisation is just simulated, no modifications are done' )
	parser.add_option( '-r', '--recursive', action = 'store_true',
					   dest = 'recursive', default = False,
					   help = 'if given the adjustment is done in all sub folders too' )
	parser.add_option( '-f', '--folder', action = 'store', dest = 'folder',
					   help = 'mailbox to search for invalid email addresses' )
	parser.add_option( '-i', '--ignored', action = 'store', dest = 'ignored_addresses',
					   help = 'do not convert addresses found in this list', default = None )
	parser.add_option( '-m', '--mapping', action = 'store', dest = 'address_mapping',
					   help = 'mapping of username and valid email addresses', default = None )
	parser.add_option( '-D', '--domain', action = 'append', dest = 'domains', default = [],
					   help = 'list of domains to consider when adjusting email addresses' )

	( options, args ) = parser.parse_args()

	if not options.address_mapping:
		print >>sys.stderr, 'error: no list of valid email addresses specified.'
		parser.print_help()
		sys.exit( 1 )

	if not options.folder:
		print >>sys.stderr, 'error: no email folder specified.'
		parser.print_help()
		sys.exit( 1 )

	if not options.domains:
		print >>sys.stderr, 'error: no email domains specified.'
		parser.print_help()
		sys.exit( 1 )

	if not options.ignored_addresses:
		print >>sys.stderr, 'warning: no list of email addresses that should be ignored is specified.'

	# open logging
	ud.init( '/var/log/univention/kolab2-adjust-addresses.log', 1, 1 )
	ud.set_level( ud.ADMIN, options.debug )
	ud.debug( ud.ADMIN, ud.ERROR, 'START: %s' % str( sys.argv ) )

	# open IMAP connection
	imap4 = uk2.IMAP_Client()

	# adjust addresses
	ud.debug( ud.ADMIN, ud.INFO, 'adjust address in folder: %s' % options.folder )
	adjust_addresses_in_folder( imap4, options )

	if options.recursive:
		base = options.folder
		imap4.select( options.folder )
		name, domain = options.folder.split( '@' )
		typ, data = imap4.list( '""', '*%s*@%s' % ( name, domain ) )
		if typ != 'OK':
			print >>sys.stderr, 'error: could not get list of sub folders'
			sys.exit( 1 )
		for box in data:
			children, dir, mailbox = shlex.split( box )
			if mailbox == base:
				continue
			options.folder = mailbox
			ud.debug( ud.ADMIN, ud.INFO, 'adjust address in folder: %s' % options.folder )
			adjust_addresses_in_folder( imap4, options )


if __name__ == "__main__":
	main()
