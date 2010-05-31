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

import httplib
import socket
import sys
import time
from cherrypy import wsgiserver
from cgi import parse_qs, escape
import univention_baseconfig
import univention.uldap, ldap
import locale
from optparse import OptionParser
import logging
import logging.config

# test with
# curl -v http://localhost:8080/connect
# echo -e "GET /connect HTTP/1.1\n\rHost: localhost:8080\n\r\n\r" | nc -q1 localhost 8080
    
baseConfig = univention_baseconfig.baseConfig()
baseConfig.load()

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
	clientid = escape(d.get('clientid', [''])[0]) # Returns the first age value.
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

def auth_ldap(username, password):
	"""LDAP bind test."""

	ldap_base = baseConfig.get('ldap/base')
	if not ldap_base:
		raise "No key ldap/base in UCR."
	ldap_server = baseConfig.get('ldap/server/name')
	if not ldap_server:
		raise "No key ldap/server/name in UCR."

	# Anon search to map uid to binddn
	try:
		ldap_conn = univention.uldap.access(host=ldap_server, base=ldap_base)
	except ldap.LDAPError, msg:
		logger.error("Could not connect '%s' for '%s'" % (ldap_server, ldap_base))
		return False
	res = ldap_conn.searchDn('(uid=%s)' % username )
	if len(res) != 1:
		logger.error("Multiple DNs found for uid=%s." % (username,))
		return False
	binddn=res[0]

	# Simple bind
	try:
		ldap_conn = univention.uldap.access(host=ldap_server, base=ldap_base, binddn=binddn, bindpw=password, start_tls=2)
		ldap_conn.lo.unbind()
		return True
	except ldap.LDAPError, msg:
		logger.info("Authentication failure for uid=%s, binddn= %s" % (username, binddn))
		return False

class HTTP_basic_auth_ldap(object):
	'''Authentication middleware'''

	def __init__(self, app, realm='OpenDVDI'):
		self.app = app
		self.realm = realm
	
	def __call__(self, environ, start_response):
		def repl_start_response(status, headers, exc_info=None):
			if status.startswith('401'):
				remove_header(headers, 'WWW-Authenticate')
				headers.append(('WWW-Authenticate', 'Basic realm="%s"' % self.realm))
			return start_response(status, headers)
		auth = environ.get('HTTP_AUTHORIZATION')
		if auth:
		    scheme, data = auth.split(None, 1)
		    assert scheme.lower() == 'basic'
		    username, password = map(escape, data.decode('base64').split(':', 1))
		    if auth_ldap(username, password):
		    	environ['REMOTE_USER'] = username
		    	del environ['HTTP_AUTHORIZATION']
		if not 'REMOTE_USER' in environ:
				return self.bad_auth(environ, start_response)
		return self.app(environ, repl_start_response)	# move on
	
	def bad_auth(self, environ, start_response):
		body = 'Please authenticate'
		headers = [
		    ('content-type', 'text/plain'),
		    ('content-length', str(len(body))),
		    ('WWW-Authenticate', 'Basic realm="%s"' % self.realm)]
		start_response('401 Unauthorized', headers)
    	return [body]

wsgi_apps = wsgiserver.WSGIPathInfoDispatcher({'/connect': HTTP_basic_auth_ldap(connect), '/alive': alive})
    
if __name__ == '__main__':
	locale.setlocale(locale.LC_ALL, '')

	progname = os.path.basename(sys.argv[0])

	parser = OptionParser( usage=usage )
	parser.add_option( '-c', '--config',
			action='store', dest='conffile', default="/etc/univention/opendvdi/sessionbroker.ini",
			help='Path to the ini-file' )
	parser.add_option( '-l', '--log',
			action='store', dest='logfile', default='/var/log/univention/opendvdi-sessionbroker.log',
			help='Path to the log file' )
	parser.add_option( '-p', '--port',
			action='store', dest='port', default='8080',
			help='Session Broker Port' )
	parser.add_option( '-v', '--verbose',
			action='store_true', dest='verbose', default=False,
			help='Print additional information' )

	(options, arguments) = parser.parse_args()

	PORT=options.port

	# Logging
	config = ConfigParser.ConfigParser()
	config.read(options.conffile)
	logging.basicConfig(filename=options.logfile)
	logging.config.fileConfig(options.conffile)

	logger = logging.getLogger("SessionBroker")

	if options.verbose:
		logger.setLevel(logging.DEBUG)

	# WSGI server
	server = wsgiserver.CherryPyWSGIServer(('localhost', PORT), wsgi_apps,
											   server_name='localhost')
	# SSL support
	ssl_basedir='/etc/univention/ssl'
	fqdn = "%s.%s" (baseConfig.get('hostname'), baseConfig.get('domainname'))
	server.ssl_certificate = '%s/%s/cert.pem' % (ssl_basedir, fqdn)
	server.ssl_private_key = '%s/%s/private.key' % (ssl_basedir, fqdn)

	try:
		server.start()
	except KeyboardInterrupt:
		server.stop()
