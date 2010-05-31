#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention OpenDVDI Sessionbroker Client
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
"""Univention OpenDVDI Sessionbroker Client."""

import locale
from optparse import OptionParser
import sys
import httplib
import urllib
import threading
import time

id=''
drop_connection=False

# test with
# curl -v http://localhost:8080/connect
# echo -e "GET /connect HTTP/1.1\n\rHost: localhost:8080\n\r\n\r" | nc -q1 localhost 8080

def iter_chunked(response, amt = None):
        chunk_left = None
        value = ''

        # XXX This accumulates chunks by repeated string concatenation,
        # which is not efficient as the number or size of chunks gets big.
        while True:
            if chunk_left is None:
                line = response.fp.readline()
                i = line.find(';')
                if i >= 0:
                    line = line[:i] # strip chunk-extensions
                chunk_left = int(line, 16)
                if chunk_left == 0:
                    break
            if amt is None:
                value = response._safe_read(chunk_left)
            elif amt < chunk_left:
                value = response._safe_read(amt)
                chunk_left = chunk_left - amt
            elif amt == chunk_left:
                value = response._safe_read(amt)
                response._safe_read(2)  # toss the CRLF at the end of the chunk
                chunk_left = None
            else:
                value = response._safe_read(chunk_left)
                amt -= chunk_left
            yield value

            # we read the whole chunk, get another
            response._safe_read(2)      # toss the CRLF at the end of the chunk
            chunk_left = None

        # read and discard trailer up to the CRLF terminator
        ### note: we shouldn't have any trailers!
        while True:
            line = response.fp.readline()
            if not line:
                # a vanishingly small number of sites EOF without
                # sending the trailer
                break
            if line == '\r\n':
                break

def HTTP11_streaming_client(HOST, PORT):
	global id
	global drop_connection
	conn1 =  httplib.HTTPSConnection(HOST, int(PORT))
	# conn1 =  httplib.HTTPConnection(HOST, PORT)
	conn1.auto_open =  False
	conn1.connect()
	conn1.request("GET", "/connect")
	r1 = conn1.getresponse()
	# print r1.status, r1.reason
        if r1.chunked != httplib._UNKNOWN:
		for chunk in iter_chunked(r1):
			if drop_connection:
				break
			print "GOT SERVER COMMAND"
			for line in chunk.splitlines():
				if line.startswith("id: "):
					id=line[4:]
					print "SERVER SENT ID=%s" % id
        else: # not r1.chunked
		raise httplib.UnknownTransferEncoding()

def HTTP11_client(HOST, PORT):
	global id
	conn2 =  httplib.HTTPSConnection(HOST, int(PORT))
	# conn2 =  httplib.HTTPConnection(HOST, PORT)
	conn2.auto_open =  False
	conn2.connect()
	
	while not id:
		time.sleep(0.1)
	
	for trial in xrange(5):
		# Send next alive
		conn2.request("GET", "/alive?clientid=%s"  % id)
		time.sleep(1)
		print 'aliveevent %s\n' % (trial+1)
		
		# Retrieve response
		response = conn2.getresponse()
		body = response.read()
		print 'aliveevent server response: %s\n' % body
	
	conn2.close()
	global drop_connection
	drop_connection=True

if __name__ == '__main__':
	locale.setlocale(locale.LC_ALL, '')

	progname = os.path.basename(sys.argv[0])

	parser = OptionParser( usage=usage )
		parser.add_option( '-s', '--server',
				action='store', dest='sessionbrokerhost', default='localhost',
				help='Session Broker' )
		parser.add_option( '-p', '--port',
				action='store', dest='port', default='8080',
				help='Session Broker Port' )
		parser.add_option( '-v', '--verbose',
				action='store_true', dest='verbose', default=False,
				help='Print additional information' )

	(options, arguments) = parser.parse_args()

	HOST=options.sessionbrokerhost
	PORT=options.port

	t_funktion1 = threading.Thread(target = HTTP11_streaming_client, args = (HOST, PORT))
	# t_funktion1.daemon=True
	t_funktion1.start()
	t_funktion2 = threading.Thread(target = HTTP11_client, args = (HOST, PORT))
	t_funktion2.start()
	t_funktion2.join()

