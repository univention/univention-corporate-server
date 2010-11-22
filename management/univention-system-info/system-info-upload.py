#!/usr/bin/python2.4
#
# Univention System Info
#  Stores files uploaded via HTTP POST
#
# Copyright 2009-2010 Univention GmbH
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

import univention.config_registry as ucr

import cgi
from email.MIMEText import MIMEText
import os
import socket
import subprocess
import smtplib
import sys
import time
import tarfile

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
	infoTable = ''
	# get contents of info file
	try:
		tarFile = tarfile.open( os.path.join(path, filename), 'r' )
		infoTable = '<table>\n'
		for line in tarFile.extractfile( tarFile.getmember('%s/info' % filename[:-7]) ).readlines():
			key, val = line.strip().split(':')
			infoTable += '<tr><td>%s:</td><td>%s</td></tr>\n' % (key.strip(), val.strip())
		infoTable += '</table>'
	except:
		pass

	msg = MIMEText('''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html>
<head/>
<body>
<p>A new Univention system info archive has been uploaded.</p>
%s

<p>
Archive: <a href="https://%s/univention-system-info-upload/archives/%s">%s</a>
</p>
</body>
</html>
''' % ( infoTable, socket.getfqdn(), filename, filename ), 'html' )
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

