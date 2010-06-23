#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  web interface daemon
#
# Copyright 2006-2010 Univention GmbH
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

import sys, locale, os, socket, select, fcntl, time, cPickle, threading, struct
from optparse import OptionParser

sys.path.append('/usr/share/univention-webui/modules/')
ldir = '/usr/share/univention-management-console/frontend/'
sys.path.append(ldir)
os.chdir(ldir)

import univention.debug as ud
import univention.management.console.protocol as umcp

import univention.config_registry

configRegistry = univention.config_registry.ConfigRegistry()
configRegistry.load()

watchdog = time.time()
watchdog_timeout = 60 * 5

THREAD_ERRORS = []

def daemonize():
	pid = os.fork()
	if pid > 0:
		os._exit(0)

	null = os.open('/dev/null', os.O_RDWR)
	os.dup2(null, sys.stdin.fileno())
	os.dup2(null, sys.stdout.fileno())
	os.dup2(null, sys.stderr.fileno())
	os.setsid()


def reset_watchdog():
	global watchdog
	watchdog = time.time()


def watchdog_timed_out():
	return watchdog + watchdog_timeout < time.time()


def rawsock_send_error( conn, msg ):
	ud.debug(ud.ADMIN, ud.ERROR, 'univention-console-frontend.py: rawsock_error: msg=%s' % msg)
	response = { 'Content-Type': 'text/plain',
				 'data': msg }
	data = cPickle.dumps( response )
	conn.send( struct.pack( '!I', len(data) ) )
	conn.send( data )
	conn.close()

def handle_rawsock( conn ):
	global THREAD_ERRORS
	try:
		ud.debug( ud.ADMIN, ud.INFO, 'univention-console-frontend.py: rawsock: loading request' )

		# receive input
		data = ''
		while len(data) < 4:
			buf = conn.recv( 4 )
			if not buf:
				ud.debug( ud.ADMIN, ud.ERROR, 'univention-console-frontend.py: rawsock: client connection closed unexpectedly' )
				conn.close()
				return
			data = data + buf
		datalen = struct.unpack('!I', data[0:4])[0]
		data = data[4:]
		while len(data) < datalen:
			buf = conn.recv( 8192 )
			if not buf:
				ud.debug( ud.ADMIN, ud.ERROR, 'univention-console-frontend.py: rawsock: client connection closed unexpectedly' )
				conn.close()
				return
			data = data + buf
			ud.debug( ud.ADMIN, ud.INFO, 'univention-console-frontend.py: rawsock: got chunk of %s bytes - %s of %s bytes received' % ( len(buf), len(data), datalen ) )
		ud.debug( ud.ADMIN, ud.INFO, 'univention-console-frontend.py: rawsock: request complete' )

		sockdata = cPickle.loads( data )

		# enable output only during debugging session: contains sessionid ==> possible security hole
		# ud.debug( ud.ADMIN, ud.INFO, 'univention-console-frontend.py: rawsock: request=%s' % sockdata )

		if type(sockdata) != type( {} ) or not sockdata.get('UMCP-CMD'):
			rawsock_send_error( conn, '<h1>no UMCP-CMD given</h1>' )
			return

		req = umcp.Command( [ sockdata.get('UMCP-CMD') ], opts = sockdata.get('UMCP-DATA', {}) )

		import client
		reqid = client.request_send( req )
		ud.debug( ud.ADMIN, ud.INFO, 'univention-console-frontend.py: rawsock: request id = %s' % reqid )
		response = client.response_wait( reqid, timeout = int(configRegistry.get('umc/raw/request/timeout', 30)) )
		if not response:
			rawsock_send_error( conn, '<h1>cmd not successful: no response yet</h1>' )
			return
		elif response.status() != 200:
			rawsock_send_error( conn,
								'<h1>cmd not successful: status=%s msg=%s</h1>' % (response.status(),
																					umcp.status_information( response.status() )))
			return

		if type(response.dialog) == type({}) and \
			   ( ( 'Content-Type' in response.dialog.keys() and 'Content' in response.dialog.keys() ) or \
				 'Location' in response.dialog.keys() ):
			sockresponse = response.dialog
		else:
			sockresponse = { 'Content-Type': 'application/binary',
							 'Content': response.dialog }

		data = cPickle.dumps( sockresponse )
		conn.send( struct.pack( '!I', len(data) ) )
		conn.send( data )

		conn.close()

		ud.debug( ud.ADMIN, ud.INFO, 'univention-console-frontend.py: rawsock: response sent - socket closed')

		reset_watchdog()

	except Exception, e:
		import traceback
		THREAD_ERRORS.append( traceback.format_exc() )


def handle_sock( conn, session, options ):
	# receive input
	input = ''
	while 1:
		buf = conn.recv( 1024 )

		#				if not buf: continue
		if buf[ -1 ] == '\0':
			buf = buf[ : -1 ]
			input += buf
			break
		else:
			input += buf

	# split into meta text and xml text
	pos = input.find('\n\n')
	if pos >= 0:
		metatext = input[:pos]
		xmlin = input[pos+2:]
	else:
		metatext = ''
		xmlin = input

	# parse metatext
	meta = {}
	for line in metatext.split('\n'):
		pos = line.find(': ')
		if pos < 1:
			continue
		meta[line[:pos]] = line[pos+2:]

	# get session id from index.php and pass it to UMCP client wrapper
	import client
	if not client._sessionId:
		client.set_sessionid( meta.get('SessionId', 'NO-SESSION-ID') )
		ud.debug(ud.ADMIN, ud.INFO, 'univention-console-frontend.py: sessionId = %s' % client._sessionId)

	number = int(meta.get('Number', '-1'))

	if options.debug >= 2:
		open('/tmp/xmlin', 'w').write(xmlin)
	xmlout = session.startRequest( xmlin, number, ignore_ldap_connection=True, timeout = None, meta=meta )
	if options.debug >= 2:
		open('/tmp/xmlout', 'w').write( xmlout )

	# send output
	conn.send( xmlout + '\0' )
	conn.close()

	# Do cleanup work after the connection has been closed,
	# so that the response will not be delayed
	session.finishRequest(number)

	reset_watchdog()



def log_errors():
	global THREAD_ERRORS
	if THREAD_ERRORS:
		for msg in THREAD_ERRORS:
			ud.debug( ud.ADMIN, ud.ERROR, 'univention-console-frontend.py: thread error=\n%s' % msg )
	THREAD_ERRORS = []



def main(argv):
	global watchdog_timeout

	parser = OptionParser( usage = "usage: %prog [options]" )
	parser.add_option( '-s', '--socket', type = 'string', action = 'store',
					   dest = 'socket', help = 'defines the socket to bind to',
					   default = '' )
	parser.add_option( '-l', '--language', type = 'string', action = 'store',
					   dest = 'language', default = 'de_DE.utf8',
					   help = 'defines the language to use' )
	parser.add_option( '-n', '--no-daemon', action = 'store_false',
					   dest = 'daemon_mode', default = True,
					   help = 'if set the process will not fork into the background' )
	parser.add_option( '-t', '--timeout', type = 'int', default = 60 * 5,
					   action = 'store', dest = 'timeout',
					   help = 'defines the timeout for inactivity' )
	parser.add_option( '-d', '--debug', action = 'store', type = 'int',
					   dest = 'debug', default = 0,
					   help = 'if given than debugging is activated and set to the specified level' )
	parser.add_option( '-e', '--https', action = 'store', type = 'int',
					   dest = 'https', default = 0,
					   help = 'if set to 1 HTTPS is used' )
	parser.add_option( '-x', '--http_host', action = 'store', type = 'string',
					   dest = 'http_host', default = None,
					   help = 'add the $_SERVER[HTTP_HOST] variable from PHP to Python' )

	# parse command line arguments
	( options, arguments ) = parser.parse_args()

	if options.debug > 0:
		ud.init('/var/log/univention/management-console-web.log', 1, 1)
		ud.set_level( ud.LDAP, options.debug )
		ud.set_level( ud.ADMIN, options.debug )
	else:
		ud.init('/dev/null', 0, 0)

	os.environ["HTTPS"] = "%s" % options.https
	os.environ["HTTP_HOST"] = "%s" % options.http_host

	if options.socket == '-':
		filename = sys.stdin.read()
		if filename[ -1 ] == '\n':
			options.socket = filename[ : -1 ]
		else:
			options.socket = filename
#		filename = sys.stdin.read().rstrip('\n')

	watchdog_timeout = options.timeout

	localeok = False
	try:
		locale.setlocale( locale.LC_MESSAGES, locale.normalize( options.language ) )
		localeok = True
	except:
		ud.debug(ud.ADMIN, ud.ERROR, 'univention-console-frontend.py: specified locale is not available (cmdline: %s)' % options.language)
	if not localeok:
		if configRegistry.get('umc/web/language'):
			try:
				locale.setlocale( locale.LC_MESSAGES, locale.normalize( configRegistry.get('umc/web/language') ) )
				localeok = True
			except:
				ud.debug(ud.ADMIN, ud.ERROR, 'univention-console-frontend.py: specified locale is not available (baseconfig: %s)' % configRegistry.get('umc/web/language'))

	import client
	from uniparts import *
	import requests

	if not options.socket:
		ud.debug(ud.ADMIN, ud.ERROR, 'Socket filename missing.')

	# initialize global structures
	try:
		uaccess = requests.new_uaccess()
		uaccess.requireLicense()
	except:
		uaccess=None
	session=requests.session(uaccess)

	sock = socket.socket( socket.AF_UNIX, socket.SOCK_STREAM )
	fcntl.fcntl(sock.fileno(), fcntl.F_SETFD, 1)
	sock.bind( options.socket )

	rawsockfn = '%s.raw' % options.socket
	rawsock = socket.socket( socket.AF_UNIX, socket.SOCK_STREAM )
	rawsock.bind( rawsockfn )
	ud.debug(ud.ADMIN, ud.INFO, 'univention-console-frontend.py: opened raw sock: %s' % rawsockfn)

	threadlist = []

	try:
		sock.listen(1)
		rawsock.listen( int( configRegistry.get('umc/raw/backlog', '5') ) )

		if options.daemon_mode:
			daemonize()

		# initialize UMCP client
		print 'CLIENT', client.run()

		reset_watchdog()

		while 1:
			rfds, wfds, xfds = select.select( [ sock, rawsock ], [], [], 60 )
			log_errors()
			if not rfds and not wfds and not xfds:
				# select timeout occurred - check if watchdog is overdue
				if not watchdog_timed_out():
					# watchdog is NOT overdue ==> continue
					continue

				ud.debug(ud.ADMIN, ud.INFO, 'TIMED OUT! EXIT!')
				raise Exception( 'timeout' ) # timeout

			reset_watchdog()

			if sock in rfds:
				conn, addr = sock.accept()
				ud.debug( ud.ADMIN, ud.WARN, 'univention-console-frontend.py: sock: new connection' )
				thr = threading.Thread( target = handle_sock, args = (conn, session, options) )
				thr.start()
				threadlist.append(thr)

			if rawsock in rfds:
				conn, addr = rawsock.accept()
				ud.debug( ud.ADMIN, ud.WARN, 'univention-console-frontend.py: rawsock: new connection' )
				thr = threading.Thread( target = handle_rawsock, args = (conn,) )
				thr.start()
				threadlist.append(thr)

			newlist = []
			for th in threadlist:
				if th.isAlive():
					newlist.append( th )
			threadlist = newlist

			log_errors()

	except Exception, e:
		import traceback
		ud.debug( ud.ADMIN, ud.ERROR, "EXCEPTION: %s" % str( e ) )
		ud.debug( ud.ADMIN, ud.ERROR, traceback.format_exc() )

	os.unlink(options.socket)
	os.unlink(rawsockfn)
	# kill process, because the UMCP client thread keeps it alive
	client.stop()
	sys.exit( 0 )

if __name__ == '__main__':
	main(sys.argv)


