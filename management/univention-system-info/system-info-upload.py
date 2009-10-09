#!/usr/bin/python2.4
#
# Univention System Info
#  Stores files uploaded via HTTP POST
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

import univention.config_registry as ucr

import cgi
from email.MIMEText import MIMEText
import os
import subprocess
import smtplib
import sys
import time

configRegistry = ucr.ConfigRegistry()
configRegistry.load()

def save_uploaded_file( form_field, upload_dir, max_size ):
	form = cgi.FieldStorage()
	if not form.has_key( form_field ):
		return ( False, None )
	fileitem = form[ form_field ]
	if not fileitem.filename.endswith( '.tar.gz' ):
		return ( False, fileitem.filename )
	filename = os.path.join( upload_dir, fileitem.filename )
	if os.path.exists( filename ):
		filename += '.%s' % str( time.time() * 100 )
	fout = file( filename , 'wb' )
	size = 0
	while True:
		chunk = fileitem.file.read( 100000 )
		if not chunk:
			break
		size += len( chunk )
		if size > max_size:
			fout.close()
			os.unlink( fout.name )
			return ( False, fileitem.filename )
		fout.write( chunk )
	fout.close()

	return ( True, fileitem.filename )

# make HTTP happy
print 'Content-Type: text/plain\n'

path = configRegistry.get( 'umc/sysinfo/upload/path', '/var/lib/univention-system-info/archives/' )

ok, filename = save_uploaded_file( 'filename', path, configRegistry.get( 'umc/sysinfo/upload/size', '2000000' ) )

if not ok:
	print 'ERROR: wrong file type or file to big'
else:
	msg = MIMEText('''
A new Univention system info archive has been uploaded.

Archive: %s
''' % os.path.join( path, filename ) )
	msg[ 'Subject' ] = 'Univention System Info Upload'
	sender = configRegistry.get( 'umc/sysinfo/upload/sender', 'root' )
	recipient = configRegistry.get( 'umc/sysinfo/upload/recipient', sender )
	
	msg[ 'From' ] = sender
	msg[ 'To' ] = recipient
	
	s = smtplib.SMTP()
	s.connect()
	s.sendmail( sender, [ recipient ], msg.as_string() )
	s.close()
	print 'OK: file saved successfully'

