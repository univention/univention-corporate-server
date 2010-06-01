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
import os
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
from univention.opendvdi.sessionbroker import uuid	# backport from python2.5
import MySQLdb

# test with
# curl -v http://localhost:8080/connect
# echo -e "GET /connect HTTP/1.1\n\rHost: localhost:8080\n\r\n\r" | nc -q1 localhost 8080
    
baseConfig = univention_baseconfig.baseConfig()
baseConfig.load()

sessionbroker_dir='/etc/univention/opendvdi/sessionbroker'
session_db_password=''
update_interval=5
SESSION_STATUS_CONNECTING='connecting'
SESSION_STATUS_ACTIVE='active'
SESSION_STATUS_SILENT='silent'
SESSION_STATUS_TERMINATED_CLIENT='clientterm'
SESSION_STATUS_TERMINATED_SERVER='serverterm'

class session_db_connector:
	def __init__(self, session_db_password) :
		self.PASSWORD=session_db_password
		self.HOST	= 'localhost'
		self.PORT	= 3306
		self.USER	= 'opendvdi-sessionbroker'
		self.DB		= 'opendvdi-sessionbroker'
		self.CONNECTION = None

	def dbcursor (self):
		if not self.CONNECTION:
			self.CONNECTION = self.dbconnect (host=self.HOST, port=self.PORT, user=self.USER, passwd=self.PASSWORD, db=self.DB)
		try:
			return self.CONNECTION.cursor()
		except (AttributeError, MySQLdb.OperationalError):
			self.dbdisconnect()
			self.CONNECTION = self.dbconnect (host=self.HOST, port=self.PORT, user=self.USER, passwd=self.PASSWORD, db=self.DB)
			return self.CONNECTION.cursor()

	def dbconnect (self, *args, **kwargs):
		if not self.CONNECTION:
			self.CONNECTION = MySQLdb.connect(*args, **kwargs)
			if self.CONNECTION.get_server_info() >= '4.1' and not self.CONNECTION.character_set_name().startswith('utf8'):
				self.CONNECTION.set_character_set('utf8')
		return self.CONNECTION

	def dbdisconnect (self):
		self.CONNECTION.close ()
		self.CONNECTION = None

	def get_alive_timestamp(self, session_id):
		cursor = self.dbcursor()

		# dictionary for the mysql commands
		request_dict={
		'session_table': 'sessions',
		'session_id': session_id,
		}

		cursor.execute("SELECT alive_timestamp FROM `%(session_table)s` WHERE session_id='%(session_id)s'" % request_dict)
		res = cursor.fetchone()
		return res[0]

		cursor.close()

	def update_alive_timestamp(self, session_id):
		cursor = self.dbcursor()

		# dictionary for the mysql commands
		request_dict={
		'session_table': 'sessions',
		'session_id': session_id,
		'alive_timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
		'status': SESSION_STATUS_ACTIVE,
		}

		cursor.execute("UPDATE `%(session_table)s` SET alive_timestamp='%(alive_timestamp)s' WHERE session_id=%(session_id)d" % request_dict)

		cursor.close()
		watchdog = threading.Timer(update_interval, self.check_session, [session_id])
		return watchdog

	def newsession(self, username, client_ip):
		cursor = self.dbcursor()

		timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
		# dictionary for the mysql commands
		request_dict={
		'session_table': 'sessions',
		'session_id': uuid.uuid5(uuid.uuid1(), username),
		'username': username,
		'client_ip': client_ip,
		'desktop_host': desktop_host,
		'session_protocol': session_protocol,
		'session_start': timestamp,
		'alive_timestamp': timestamp,
		'update_interval': update_interval,
		'status': SESSION_STATUS_CONNECTING,
		}

		cursor.execute("INSERT INTO `%(session_table)s` VALUES ('%(session_id)s', '%(username)s', '%(client_ip)s', '%(desktop_host)s', '%(session_protocol)s', '%(session_start)s', '%(alive_timestamp)s', '%(update_interval)s, %(status)s')" % request_dict)

		cursor.close()
		watchdog = threading.Timer(update_interval, self.check_session, [session_id])
		return (session_id, desktop_host, watchdog)

	def check_session(self, session_id):
		now=time.time()
		cursor = self.dbcursor()

		# dictionary for the mysql commands
		request_dict={
		'session_table': 'sessions',
		'session_id': session_id,
		}

		cursor.execute("SELECT alive_timestamp FROM `%(session_table)s` WHERE session_id='%(session_id)s'" % request_dict)
		res = cursor.fetchone()
		last_alive_time=time.strptime(res[0], "%Y-%m-%d %H:%M:%S")
		if now-time.mktime(last_alive_time) > update_interval:
			request_dict['status']=SESSION_STATUS_SILENT
			cursor.execute("UPDATE `%(session_table)s` SET status='%(status)s' WHERE session_id=%(session_id)d" % request_dict)

		cursor.close()

def get_session_db_password():
	global session_db_password
	file="opendvdi-sessionbroker.secret" % ou
	try:
		f = open (os.path.join(sessionbroker_dir, file), 'r')
		session_db_password = f.read ()
		if len (session_db_password) > 0 and session_db_password[-1] == '\n':
			session_db_password = session_db_password[:-1]
		f.close ()
	except IOError:
		logger.error("IOError reading %s" % (file, ))

class connection_server_response:
	def __init__(self, username):
		self.session_db=session_db_connector(session_db_password)
		self.session_id, self.desktop_host, self.watchdog = self.session_db.newsession(username, client_ip)

    def __iter__(self):
        return self

    def next(self):
        #if self.session_db.session_terminated():
        #    raise StopIteration
		if self.watchdog:
			msg="--newdivider\n\rContent-Type: application/xml; charset=utf-8\n\r\n\r<?xml version="1.0" ?><body><session id=%s/></body>\n"  % self.id
			self.watchdog.start()
			self.watchdog=None
        	return msg

		# TODO: wait on session.command_queue, e.g. via threading.Condition().wait()
		while 1:
			time.sleep(1)
		
		msg="--newdivider\n\rContent-Type: application/xml; charset=utf-8\n\r\n\r<?xml version="1.0" ?><body><command>%s</command></body>\n" % self.command_queue.pop(0)
		return msg

##### Exceptions
#class DBSelectFaild (Exception):
#	def __init__ (self, msg):
#		self.msg = msg

def connect(environ, start_response):
	# streaming HTTP server response
	status = '200 OK'
	response_headers = [('Content-type','multipart/x-mixed-replace; boundary=newdivider')]
	start_response(status, response_headers)
	return connection_server_response(environ['REMOTE_USER'])

def alive(environ, start_response):
	d = parse_qs(environ['QUERY_STRING'])
	session_id = escape(d.get('session_id', [''])[0])

	# normal HTTP server response
	status = '200 OK'
	response_headers = [('Content-type','text/plain')]
	start_response(status, response_headers)
	# NOTE: check connection1? No, let the client monitor it, he must initiate reconnect
	# TODO: check if id is valid

	session_db=session_db_connector(session_db_password)
	watchdog = session_db.update_alive_timestamp(session_id)
	watchdog.start()

	return [ "ack session_id: %s" % (session_id, ) ]

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
		    username, password = data.decode('base64').split(':', 1)
			username = escape(username)
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

	# Database backend connection
	get_session_db_password()

	if os.getuid() == 0:	# drop privileges
		os.setuid(65534)

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
