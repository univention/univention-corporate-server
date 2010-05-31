#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention OpenDVDI Sessionbroker
#
# Copyright (C) 2010 Univention GmbH
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA	 02110-1301	 USA
"""Univention OpenDVDI Sessionbroker."""

import locale
from optparse import OptionParser
import httplib
import socket
import sys
import time
from cherrypy import wsgiserver
from cgi import parse_qs, escape

# test with
# curl -v http://localhost:8080/connect
# echo -e "GET /connect HTTP/1.1\n\rHost: localhost:8080\n\r\n\r" | nc -q1 localhost 8080
    
timeout=2

id=0
n1=0

def multipart_answer():
	#try:
		global id
		part0="--newdevider\n\rContent-Type: application/xml; charset=utf-8\n\r\n\rid: %s\n"  % id
		part1="--newdevider\n\rContent-Type: application/xml; charset=utf-8\n\r\n\r"
		yield part0
		# TODO: wait on message queue, e.g. via threading.Condition().wait()
		while 1:
			time.sleep(timeout)
			yield part1
	#except ('error', (32, 'Broken pipe') ):
	#	pass

def connect(environ, start_response):
	# streaming HTTP server response
	global id
	global n1
	status = '200 OK'
	response_headers = [('Content-type','multipart/x-mixed-replace; boundary=newdivider')]
	start_response(status, response_headers)
	id+=1
	n1=0
	return multipart_answer()

def alive(environ, start_response):
	d = parse_qs(environ['QUERY_STRING'])
	clientid = d.get('clientid', [''])[0] # Returns the first age value.
	# normal HTTP server response
	global n1
	global id
	status = '200 OK'
	response_headers = [('Content-type','text/plain')]
	start_response(status, response_headers)
	n1+=1
	# NOTE: check connection1? No, let the client monitor it, he must initiate reconnect
	# TODO: reset connection status timer
	return [ "ack (clientid: %s - req: %s)" % (id, n1) ]

wsgi_apps = wsgiserver.WSGIPathInfoDispatcher({'/connect': connect, '/alive': alive})
    
if __name__ == '__main__':
	locale.setlocale(locale.LC_ALL, '')

	progname = os.path.basename(sys.argv[0])

	parser = OptionParser( usage=usage )
		parser.add_option( '-p', '--port',
				action='store', dest='port', default='8080',
				help='Session Broker Port' )
		parser.add_option( '-v', '--verbose',
				action='store_true', dest='verbose', default=False,
				help='Print additional information' )

	(options, arguments) = parser.parse_args()

	PORT=options.port

	server = wsgiserver.CherryPyWSGIServer(('localhost', PORT), wsgi_apps,
											   server_name='localhost')
	# SSL support
	server.ssl_certificate = '/etc/univention/ssl/qamaster.univention.qa/cert.pem'
	server.ssl_private_key = '/etc/univention/ssl/qamaster.univention.qa/private.key'

	try:
		server.start()
	except KeyboardInterrupt:
		server.stop()
