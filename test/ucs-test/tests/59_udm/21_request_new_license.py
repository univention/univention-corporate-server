#!/usr/share/ucs-test/runner /usr/bin/py.test
# -*- coding: utf-8 -*-
## desc: Test UDM umc call to request a new license
## exposure: dangerous
## roles: [domaincontroller_master]
## tags: [udm_api, skip_admember]
## packages: [univention-management-console-module-udm]
## bugs: [49384]

from __future__ import print_function

import subprocess
import shutil
import ssl
from socket import gethostname
from multiprocessing import Process
import BaseHTTPServer
from unittest import main, TestCase
from univention.config_registry import handler_set, handler_unset
import univention.testing.utils as utils
from univention.testing.network import NetworkRedirector


class HTTPHandlerClass(BaseHTTPServer.BaseHTTPRequestHandler):

	def do_POST(self):
		self.send_response(200)
		self.end_headers()


class LicenseServer(object):

	cert_basedir = '/etc/univention/ssl/license.univention.de/'

	def __init__(self, host, port):
		self.host = host
		self.port = port
		server = Process(target=self.startHttpServer)
		self.server = server

	def __enter__(self):
		handler_set(['hosts/static/127.0.100.101=license.univention.de'])
		subprocess.check_call([
			'univention-certificate',
			'new',
			'-name', 'license.univention.de',
			'-days', '1',
		])
		self.server.start()
		return self

	def __exit__(self, *args):
		# Terminating Http server
		self.server.terminate()
		self.server.join(5)
		print('Http server is terminated...\n%r' % self.server.is_alive())
		handler_unset(['hosts/static/127.0.100.101'])
		shutil.rmtree(self.cert_basedir)

	def startHttpServer(self):
		"""Start a simple Http server in the working directory
		"""
		ServerClass = BaseHTTPServer.HTTPServer
		Protocol = 'HTTP/1.1'
		server_address = (self.host, self.port)

		HTTPHandlerClass.protocol_version = Protocol
		httpd = ServerClass(server_address, HTTPHandlerClass)
		httpd.socket = ssl.wrap_socket(
			httpd.socket,
			keyfile='{}private.key'.format(self.cert_basedir),
			certfile='{}cert.pem'.format(self.cert_basedir),
			server_side=True,
		)

		sa = httpd.socket.getsockname()
		print('Serving HTTP on "{}:{}"'.format(sa[0], sa[1]))
		httpd.serve_forever()


class TestRequestLicense(TestCase):

	@classmethod
	def setUpClass(cls):
		test_server_port = 60026
		cls._licenseServer = LicenseServer('localhost', test_server_port).__enter__()
		cls._nethelper = NetworkRedirector().__enter__()
		cls._nethelper.add_redirection('127.0.100.101', 443, test_server_port)

	@classmethod
	def tearDownClass(cls):
		cls._licenseServer.__exit__(None, None, None)
		cls._nethelper.__exit__(None, None, None)

	def test_request_license_admin(self):
		account = utils.UCSTestDomainAdminCredentials()
		ans = subprocess.check_output([
			'/usr/sbin/umc-command',
			'--pretty-print',
			'--username', account.username,
			'--password', account.bindpw,
			'udm/request_new_license',
			'--flavor', 'license-request',
			'--option', 'email=brodersen@univention.de',
		])
		print(ans)
		assert 'STATUS   : 200' in ans

	def test_request_license_machine(self):
		username = '{}$'.format(gethostname())
		with open('/etc/machine.secret', 'r') as secret:
			password = secret.read().strip()
		ans = subprocess.check_output([
			'/usr/sbin/umc-command',
			'--pretty-print',
			'--username', username,
			'--password', password,
			'udm/request_new_license',
			'--flavor', 'license-request',
			'--option', 'email=brodersen@univention.de',
		])
		print(ans)
		assert 'STATUS   : 200' in ans


if __name__ == '__main__':
	main(verbosity=2)
