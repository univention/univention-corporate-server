#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Simple HTTP Proxy for ucs-test."""
# Inspired by <http://effbot.org/librarybook/simplehttpserver.htm>
from __future__ import print_function
from six.moves import BaseHTTPServer
import urllib2
import urlparse
import httplib
import shutil
from optparse import OptionParser
import base64
import os

PORT = 3128


class Proxy(BaseHTTPServer.BaseHTTPRequestHandler):
	server_version = "UCSTestProxy/1.0"

	def do_GET(self):
		self.common(data=True)

	def do_HEAD(self):
		self.common(data=False)

	def common(self, data=True):
		if options.authorization:
			try:
				auth = self.headers['Proxy-Authorization']
				if not auth.startswith('Basic '):
					raise KeyError("Only Basic authentication: %s" % auth)
				auth = auth[len('Basic '):]
				auth = base64.decodestring(auth)
				username, password = auth.split(':', 1)
				username, password = urllib2.unquote(username), urllib2.unquote(password)
				if username != options.username:
					msg = "Username: %s != %s" % (username, options.username)
					if options.verbose:
						self.log_error(msg)
					raise KeyError(msg)
				if password != options.password:
					msg = "Password: %s != %s" % (password, options.password)
					if options.verbose:
						self.log_error(msg)
					raise KeyError(msg)
			except KeyError as exc:
				self.send_response(httplib.PROXY_AUTHENTICATION_REQUIRED)
				self.send_header('WWW-Authenticate', 'Basic realm="%s"' % (options.realm,))
				self.send_header('Content-type', 'text/html')
				self.end_headers()
				self.wfile.write('<html><body><h1>Error: Proxy authorization needed</h1>%s</body></html>' % (exc,))
				return
		# rewrite url
		url = urlparse.urlsplit(self.path)
		u = list(url)
		# The proxy gets a verbatim copy of the URL, which might contain the
		# target site credentials. urllib doesn't handle this, strip it.
		if '@' in u[1]:
			u[1] = u[1].split('@', 1)[1]
		# Fake DNS resolve of configured hostname to localhost
		if options.translate:
			if url.hostname == options.translate:
				u[1] = u[1].replace(options.translate, 'localhost')
		url = urlparse.urlunsplit(u)
		try:
			req = urllib2.Request(url=url, headers=self.headers)
			if options.verbose:
				for k, v in self.headers.items():
					self.log_message("> %s: %s" % (k, v))
			fp = urllib2.urlopen(req)
		except urllib2.HTTPError as fp:
			if options.verbose:
				self.log_error("%d %s" % (fp.code, fp.msg))

		self.send_response(fp.code)
		via = '1.0 %s' % (httpd.server_name,)
		for k, v in fp.headers.items():
			if k.lower() == 'via':
				via = "%s, %s" % (via, v)
			elif k.lower() in ('server', 'date'):  # Std-Hrds by BaseHTTPReqHand
				continue
			elif k.lower() == 'transfer-encoding':
				continue
			else:
				if options.verbose:
					self.log_message("< %s: %s" % (k, v))
				self.send_header(k, v)
		self.send_header('Via', via)
		self.end_headers()
		if data:
			shutil.copyfileobj(fp, self.wfile)
		fp.close()


if __name__ == '__main__':
	parser = OptionParser()
	parser.add_option('-p', '--port', action='store', dest='port', type='int',
			default=PORT, help='TCP port number')
	parser.add_option('-a', '--authorization', action='store_true',
			dest='authorization', default=False, help='Require authorization')
	parser.add_option('-u', '--username', action='store', dest='username',
			default='username', help='User name for HTTP Proxy authorization, unquoted')
	parser.add_option('-w', '--password', action='store', dest='password',
			default='password', help='Password for HTTP Proxy authorization, unquoted')
	parser.add_option('-r', '--realm', action='store', dest='realm',
			default='realm', help='Realm for HTTP Proxy authorization')
	parser.add_option('-t', '--translate', action='store', dest='translate',
			metavar='HOSTNAME',
			help='Translate requests for this host name to localhost')
	parser.add_option('-f', '--fork', action='store_true',
			dest='fork', default=False, help='Fork daemon process')
	parser.add_option('-v', '--verbose', action='store_true',
			dest='verbose', default=False, help='Output verbose informations')
	(options, arguments) = parser.parse_args()

	httpd = BaseHTTPServer.HTTPServer(('', int(options.port)), Proxy)
	if options.fork:
		pid = os.fork()
		if pid == 0:
			for fd in range(3):
				os.close(fd)
				fd2 = os.open(os.devnull, fd == 0 and os.O_RDONLY or os.O_WRONLY)
				if fd2 != fd:
					os.dup2(fd2, fd)
					os.close(fd2)
			httpd.serve_forever()
		else:
			print("proxy_pid=%d proxy_port=%d" % (pid, httpd.server_port))
	else:
		try:
			print("proxy_pid=%d proxy_port=%d" % (os.getpid(), httpd.server_port))
			httpd.serve_forever()
		except KeyboardInterrupt:
			pass
