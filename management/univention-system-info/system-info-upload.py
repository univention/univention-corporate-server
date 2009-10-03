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
import os
import sys
import time

configRegistry = ucr.ConfigRegistry()
configRegistry.load()

def save_uploaded_file( form_field, upload_dir, max_size ):
	form = cgi.FieldStorage()
	if not form.has_key( form_field ):
		return
	fileitem = form[ form_field ]
	if not fileitem.filename.endswith( '.tar.gz' ):
		return False
	filename = os.path.join( upload_dir, fileitem.filename )
	if os.path.exists( filename ):
		filename += '%s' % str( time.time() * 100 )
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
			return False
		fout.write( chunk )
	fout.close()

	return True

# make HTTP happy
print 'Content-Type: text/plain\n'

if not save_uploaded_file( 'filename', configRegistry.get( 'umc/sysinfo/upload/path', '/var/lib/univention-system-info/archives/' ), configRegistry.get( 'umc/sysinfo/upload/size', '2000000' ) ):
	print 'ERROR: wrong file type or file to big'
else:
	print 'OK: file saved successfully'

