#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  web interface daemon
#
# Copyright (C) 2006 Univention GmbH
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

import sys, locale, os, getopt, string, copy, socket, select, fcntl
from optparse import OptionParser

sys.path.append('/usr/share/univention-webui/modules/')
ldir = '/usr/share/univention-management-console/frontend/'
sys.path.append(ldir)
os.chdir(ldir)

import univention.debug as ud

import univention.baseconfig

baseConfig = univention.baseconfig.baseConfig()
baseConfig.load()

def daemonize():
	pid = os.fork()
	if pid > 0:
		os._exit(0)

	null = os.open('/dev/null', os.O_RDWR)
	os.dup2(null, sys.stdin.fileno())
	os.dup2(null, sys.stdout.fileno())
	os.dup2(null, sys.stderr.fileno())
	os.setsid()

def main(argv):
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

	# parse command line arguments
	( options, arguments ) = parser.parse_args()

	if options.debug > 0:
		ud.init('/var/log/univention/management-console-web.log', 1, 1)
		ud.set_level( ud.LDAP, options.debug )
		ud.set_level( ud.ADMIN, options.debug )
	else:
		ud.init('/dev/null', 0, 0)
	
	os.environ["HTTPS"] = "%s" % options.https

	if options.socket == '-':
		filename = sys.stdin.read()
		if filename[ -1 ] == '\n':
			options.socket = filename[ : -1 ]
		else:
			options.socket = filename

	localeok = False
	try:
		locale.setlocale( locale.LC_MESSAGES, locale.normalize( options.language ) )
		localeok = True
	except:
		ud.debug(ud.ADMIN, ud.ERROR, 'univention-console-frontend.py: specified locale is not available (cmdline: %s)' % options.language)
	if not localeok:
		if baseConfig.has_key('umc/web/language') and baseConfig['umc/web/language']:
			try:
				locale.setlocale( locale.LC_MESSAGES, locale.normalize( baseConfig['umc/web/language'] ) )
				localeok = True
			except:
				ud.debug(ud.ADMIN, ud.ERROR, 'univention-console-frontend.py: specified locale is not available (baseconfig: %s)' % baseConfig['umc/web/language'])


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
	try:
		sock.listen(1)

		if options.daemon_mode:
			daemonize()

		# initialize UMCP client
		print 'CLIENT', client.run()

		while 1:
			rfds, wfds, xfds = \
				  select.select( [ sock ], [], [], options.timeout )
			if not rfds:
				ud.debug(ud.ADMIN, ud.INFO, 'TIMED OUT! EXIT!')
				raise Exception( 'timeout' ) # timeout
			conn, addr = sock.accept()

			# receive input
			input = ''
			while 1:
				buf = conn.recv( 1024 )

# 				if not buf: continue
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

			number = int(meta.get('Number', '-1'))

			if options.debug >= 2:
				open('/tmp/xmlin', 'w').write(xmlin)
			xmlout = session.startRequest( xmlin, number, ignore_ldap_connection=True, timeout = None )
			if options.debug >= 2:
				open('/tmp/xmlout', 'w').write( xmlout )

			# send output
			conn.send( xmlout + '\0' )
			conn.close()

			# Do cleanup work after the connection has been closed,
			# so that the response will not be delayed
			session.finishRequest(number)
	except Exception, e:
		import traceback
		ud.debug( ud.ADMIN, ud.ERROR, "EXCEPTION: %s" % str( e ) )
		ud.debug( ud.ADMIN, ud.ERROR, traceback.format_exc() )

	os.unlink(options.socket)
	# kill process, because the UMCP client thread keeps it alive
	client.stop()
	sys.exit( 0 )

if __name__ == '__main__':
	main(sys.argv)
