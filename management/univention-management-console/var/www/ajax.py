#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  web interface daemon
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

import cgi, re, sys, socket, cPickle, struct
import univention.debug as ud

import univention.config_registry

REsessionid = re.compile('^[a-f0-9]+$')
REcommand = re.compile('^[-_/a-zA-Z0-9]+$')

def main(argv):

	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()

	if configRegistry.get('umc/ajax/debug/traceback', '').lower() in [ 'yes', '1', 'true' ]:
		import cgitb; cgitb.enable()

	try:
		debug = int(configRegistry.get('umc/raw/debug/level', '1'))
	except:
		debug = 1

	if debug > 0:
		ud.init('/var/log/univention/management-console-web.log', 1, 1)
		ud.set_level( ud.ADMIN, debug )
	else:
		ud.init('/dev/null', 0, 0)


	# get formular data
	form = cgi.FieldStorage()

	# check session id
	session_id = form.getfirst('session_id','0').split('_')[-1]
	if not REsessionid.match(session_id):
		print 'Content-Type: text/html\n\n'
		print '<h1>INVALID SESSION-ID</h1>\n'
		print 'session_id = %s<br>\n' % form.getfirst('session_id')
		sys.exit(1)

	# check command
	umcpcmd = form.getfirst('umcpcmd','')
	if not REcommand.match(umcpcmd):
		print 'Content-Type: text/html\n\n'
		print '<h1>INVALID UMCP COMMAND</h1>\n'
		print 'umcpcmd = %s<br>\n' % form.getfirst('umcpcmd')
		sys.exit(1)

	ud.debug( ud.ADMIN, ud.INFO, 'AJAX: session id is ok')

	# connect to socket
	try:
		rawsock = socket.socket( socket.AF_UNIX, socket.SOCK_STREAM )

		fn = open('/tmp/webui/%s/socket_filename' % session_id).read()
		rawsockfn = '%s.raw' % fn
		rawsock.connect( rawsockfn )

		ud.debug( ud.ADMIN, ud.INFO, 'AJAX: connection to socket %s established' % rawsockfn )

		umcpdata = {}
		for key in form:
			if not key in [ 'umcpcmd' ]:
				umcpdata[ key ] = form.getfirst(key)

		request = { 'UMCP-CMD': umcpcmd,
					'UMCP-DATA': umcpdata,
					}

		data = cPickle.dumps( request )
		rawsock.send( struct.pack( '!I', len(data) ) )
		rawsock.send( data )

		ud.debug( ud.ADMIN, ud.INFO, 'AJAX: data sent to UMCP client')

		data = ''
		while len(data) < 4:
			buf = rawsock.recv( 4 )
			if not buf:
				rawsock.close()
				ud.debug( ud.ADMIN, ud.ERROR, 'AJAX: Connection to UMCP client closed unexpectedly' )
				raise Exception('Connection to UMCP client closed unexpectedly')
			data = data + buf
		datalen = struct.unpack('!I', data[0:4])[0]
		data = data[4:]
		while len(data) < datalen:
			buf = rawsock.recv( 8192 )
			if not buf:
				rawsock.close()
				ud.debug( ud.ADMIN, ud.ERROR, 'AJAX: Connection to UMCP client closed unexpectedly' )
				raise Exception('Connection to UMCP client closed unexpectedly')
			data = data + buf
			ud.debug( ud.ADMIN, ud.INFO, 'AJAX: got chunk of %s bytes - %s of %s bytes received' % ( len(buf), len(data), datalen ) )
		ud.debug( ud.ADMIN, ud.INFO, 'AJAX: response from UMCP client complete' )

		response = cPickle.loads( data )

		ud.debug( ud.ADMIN, ud.INFO, 'AJAX: got data (content-type: %s)' % response.get('Content-Type','<NO CONTENT TYPE SET>'))

		if 'Location' in response:
			print 'Location: %s\n' % response.get('Location')
			ud.debug( ud.ADMIN, ud.INFO, 'AJAX: redirect sent to browser')
		else:
			# get content before sending any header
			output = str(response.get('Content'))

			# print in any case Content-Type as first header and fall back to application/octet-stream if C-T is not set
			print 'Content-Type: %s' % response.get('Content-Type','application/octet-stream')

			# calculate Content-Length on our own if not set by response
			if not 'Content-Length' in response:
				print 'Content-Length: %d\n' % len(output)

			# send remaining headers (except the ones above)
			for key,val in response.items():
				if key in [ 'Location', 'Content-Type', 'Content' ]:
					continue
				print '%s: %s' % (key, val)

			# send data
			print output

			ud.debug( ud.ADMIN, ud.INFO, 'AJAX: data response sent to browser')


	except Exception, e:
		print 'Content-Type: text/html\n'
		print '<h1>An error occurred.</h1>\n'
		print 'Error: %s<br>\n' % str( e )
		print 'Please try again later. If the error reoccurs, please notify your local administrator.'
		import traceback
		ud.debug( ud.ADMIN, ud.ERROR, "AJAX: EXCEPTION: %s" % str( e ) )
		ud.debug( ud.ADMIN, ud.ERROR, 'AJAX: DATA = %s' % str(form) )
		ud.debug( ud.ADMIN, ud.ERROR, str(traceback.format_exc()) )


if __name__ == '__main__':
	main(sys.argv)
