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

import univention.kolab2 as uk2
import univention.config_registry as ucr
import univention.debug as ud

from optparse import OptionParser
import shlex
import sys

configRegistry = ucr.ConfigRegistry()
configRegistry.load()

_ignored = None
_mapping = None

def change_contacts( imap4, options ):
	imap4.select( options.folder )
	type = imap4.get_folder_type()
	print >>sys.stderr, 'Checking imap folder: %s' % options.folder
	ud.debug( ud.ADMIN, ud.INFO, 'Checking imap folder: %s' % options.folder)

	_to_be_removed = []
	_to_be_added = []

	if not type or not type.startswith( 'contact.' ):
		ud.debug( ud.ADMIN, ud.INFO, 'Ignore imap folder: %s' % options.folder)
		return

	mails = imap4.get_mails()
	for id, msg in mails:
		message = uk2.Kolab2Message()
		message.parse( msg )

		addr = message.get_kolab_part()
		modified = False
		if isinstance( addr, uk2.Kolab2Contact ):
			ud.debug( ud.ADMIN, ud.INFO, 'Check mail with Kolab uid %s' % addr.uid )
			home1=None
			home2=None
			business1=None
			business2=None
			for i in range(1,addr.n_phones):
				type = getattr(addr, 'phone%d_type' %i)
				if type == 'home1':
					home1 = i
				if type == 'home2':
					home2 = i
				if type == 'business1':
					business1 = i
				if type == 'business2':
					business2 = i

			if home2 and not home1:
				ud.debug( ud.ADMIN, ud.INFO, 'change home2 to home1 for %s' % addr.uid)
				addr.__setattr__( 'phone%d_type' % home2, 'home1')
				modified = True

			if business2 and not business1:
				ud.debug( ud.ADMIN, ud.INFO, 'change business2 to business1 for %s' % addr.uid)
				addr.__setattr__( 'phone%d_type' % business2, 'business1')
				modified = True

			if modified:
				addr.modified() # set last modification date
				message.replace_kolab_part( addr )
				print >>sys.stderr, 'Replace Message with Kolab uid: %s' % addr.uid
				ud.debug( ud.ADMIN, ud.INFO, 'Replace Message with Kolab uid: %s' % addr.uid)
				if not options.simulate:
					_to_be_added.append( message )
					_to_be_removed.append( id )

	for id in _to_be_removed:
		imap4.remove( id, expunge = False )
	for msg in _to_be_added:
		msg.create_message_id()
		imap4.add( msg.as_string() )

	imap4.expunge()

def main():
	debug_level = int( configRegistry.get( 'kolab2/tools/debug/level','0' ) )

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

	( options, args ) = parser.parse_args()


	if not options.folder:
		print >>sys.stderr, 'error: no email folder specified.'
		parser.print_help()
		sys.exit( 1 )

	# open logging
	ud.init( '/var/log/univention/kolab2-tools.log', 1, 1 )
	ud.set_level( ud.ADMIN, options.debug )
	ud.debug( ud.ADMIN, ud.ERROR, 'START: %s' % str( sys.argv ) )

	# open IMAP connection
	imap4 = uk2.IMAP_Client()

	ud.debug( ud.ADMIN, ud.INFO, 'change attribute in folder: %s' % options.folder )
	change_contacts( imap4, options )

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
			ud.debug( ud.ADMIN, ud.INFO, 'change attribute in folder: %s' % options.folder )
			change_contacts( imap4, options )

if __name__ == "__main__":
	main()
