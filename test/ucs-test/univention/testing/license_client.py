#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# UCS test
"""
A tool to obtain licenses for the UCS test environments.
"""
#
# Copyright 2014-2019 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

import sys
from sys import modules, exit
from os import path
import logging

from argparse import ArgumentParser
from datetime import datetime

if sys.version_info >= (3,):
	from urllib.parse import urlencode
	from http.client import HTTPSConnection
	from http.client import HTTPException
	from html.parser import HTMLParser

	class HTMLParseError(Exception):
		"""
		Backwards compatability as exception removed in python 3.5
        """
else:
	from urllib import urlencode
	from httplib import HTTPSConnection
	from httplib import HTTPException
	from HTMLParser import HTMLParser
	from HTMLParser import HTMLParseError


class CredentialsMissing(Exception):

	"""
	A custom exception to be raised when a 'license.secret' file is not found
	"""


class TestLicenseClient(HTMLParser):

	def __init__(self, ArgParser=None):
		"""
		Class constructor for the test license client and HTMLParser
		"""
		self.reset()  # to reset the HTML Parser
		self.setup_logging()

		self.Parser = ArgParser
		self.license_server_url = 'license.univention.de'
		self.license_filename = 'ValidTest.license'

		self.Connection = None
		self.server_username = 'ucs-test'
		self.server_password = ''
		self.cookie = ''
		self.link_to_license = None

		self.license_params = {
			"kundeUnternehmen": "Univention",
			"kundeEmail": "umc-test@univention.de",
			"BaseDN": "",
			"EndDate": "",
			"Servers": 50,
			"Support": 0,
			"PremiumSupport": 0,
			"Users": 50,
			"ManagedClients": 50,
			"CorporateClients": 50,
			"VirtualDesktopUsers": 0,
			"VirtualDesktopClients": 0,
			"Type": "UCS",
		}

	def setup_logging(self):
		"""
		Creates and configrues the logger with an INFO level
		"""
		self.log = logging.getLogger("Test_License_Client_Log")
		self.log.setLevel(logging.INFO)
		ch = logging.StreamHandler()
		ch.setLevel(logging.DEBUG)
		ch.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
		self.log.addHandler(ch)

	def create_connection(self):
		"""
		Creates a HTTPS Connection instance on a default port (443)
		to the 'self.license_server_url'
		"""
		self.log.debug("In 'create_connection'")
		self.Connection = HTTPSConnection(self.license_server_url)

	def close_connection(self):
		"""
		Closes the license server connection if the connection instance
		was created
		"""
		self.log.debug("In 'close_connection'")
		if self.Connection:
			try:
				self.Connection.close()
			except HTTPException as exc:
				self.log.exception("An HTTP Exception occurred while closing the connection: '%s'" % exc)

	def get_server_password(self, secret_file='/etc/license.secret'):
		"""
		Opens and reads the 'secret_file'. Saves the result to a
		'self.server_password'
		"""
		self.log.debug("In 'get_server_password': secret_file='%s'" % secret_file)
		if not path.exists(secret_file):
			self.log.critical("The '%s' secret file does not exist, cannot proceed without password" % secret_file)
			raise CredentialsMissing("The '%s' secret file does not exist" % secret_file)
		try:
			with open(secret_file, 'r') as password:
				self.server_password = password.read()
		except (IOError, ValueError) as exc:
			self.log.exception("Failed to get the password from the '%s', an error occurred: %r" % (secret_file, exc))
			exit(1)
		if not self.server_password:
			self.log.critical("The password to access the license service cannot be empty")
			exit(1)

	def get_cookie(self):
		"""
		Makes a POST request with 'self.server_username' and
		'self.server_password' into login forms and saves the
		cookie from the response received.
		"""
		self.log.debug("In 'get_cookie' method")
		body = {
			"username": self.server_username,
			"password": self.server_password,
		}
		headers = {
			"Content-type": "application/x-www-form-urlencoded",
			"Accept": "text/plain",
		}

		response = self.make_post_request('/shop/testing/', urlencode(body), headers)
		self.log.debug("The response status is '%s', reason is '%s', headers are '%s'" % (response.status, response.reason, response.getheaders()))

		self.cookie = response.getheader('set-cookie')
		if not ('sessionid' in self.cookie):
			self.log.critical("The 'sessionid' field was not found in the received cookie: '%s'" % self.cookie)
			exit(1)
		# extracting only the 'sessionid' part of the cookie:
		self.cookie = self.cookie[:self.cookie.find(';')]
		self.log.debug("The cookie is: '%s'" % self.cookie)
		# reading the response to avoid 'ResponseNotReady' exception later:
		response.read()

	def make_post_request(self, url, body, headers):
		"""
		Makes a POST request with the given 'url', 'body', 'headers' and
		returns the response
		"""
		self.log.debug("In 'make_post_request' method: url='%s', body='%s', headers='%s'" % (url, body, headers))
		try:
			self.Connection.request("POST", url, body, headers)
			response = self.Connection.getresponse()
		except HTTPException as exc:
			self.log.exception("An HTTP Exception occurred while making '%s' POST request: '%s'" % (url, exc))
			exit(1)
		return response

	def make_get_request(self, url, headers):
		"""
		Makes a GET request with the given 'url', 'headers' and
		returns the response
		"""
		self.log.debug("In 'make_get_request' method: url='%s', headers='%s'" % (url, headers))
		try:
			self.Connection.request("GET", url, headers=headers)
			response = self.Connection.getresponse()
		except HTTPException as exc:
			self.log.exception("An HTTP Exception occurred while making '%s' GET request: '%s'" % (url, exc))
			exit(1)
		return response

	def handle_starttag(self, tag, attrs):
		"""
		Method is called every time a new start tag is found in the
		html feed. When the link tag with 'orders/' attribute is
		found, the attribute is saved to 'self.link_to_license'
		"""
		self.log.debug("In 'handle_starttag' method: tag='%s', attrs='%s'" % (tag, attrs))
		if attrs:
			if (tag == 'a' and 'href' in attrs[0]):
				for attribute in attrs[0]:
					if attribute.startswith('orders/'):
						# link to the license is found:
						self.link_to_license = attribute
						return

	def get_the_license(self, body):
		"""
		Processes the given 'body' with HTMLParser to find the link
		to a created license file and downloads the license after.
		"""
		self.log.debug("In 'get_the_license' method: body='%s'" % body)
		try:
			self.feed(body)  # process the response 'body' for license link
		except HTMLParseError as exc:
			self.log.exception("An exception occurred while parsing the response body for a link to a license file: '%s'" % exc)
		if not self.link_to_license:
			self.log.critical("The link to the license file was not found in the body from server: '%s'" % body)
			exit(1)
		self.download_license_file()

	def order_a_license(self):
		"""
		Makes a POST request with encoded 'self.license_params' as a body to
		oreder a new license. Returns the response body.
		"""
		self.log.debug("In 'order_a_license' method")
		body = self.license_params
		headers = {
			"Cookie": self.cookie,
			"Content-type": "application/x-www-form-urlencoded",
		}

		response = self.make_post_request('/shop/testing/order', urlencode(body), headers)
		self.log.debug("The response status is '%s', reason is '%s', headers are '%s'" % (response.status, response.reason, response.getheaders()))
		return response.read()

	def download_license_file(self):
		"""
		Downloads the license located at 'self.link_to_license' and saves it
		to the file with a 'self.license_filename'
		"""
		self.log.debug("In 'download_license_file' method")
		headers = {
			"Cookie": self.cookie,
			"Accept": "text/plain",
		}
		response = self.make_get_request('/shop/testing/' + self.link_to_license, headers)
		self.log.debug("The response status is '%s', reason is '%s', headers are '%s'" % (response.status, response.reason, response.getheaders()))
		try:
			with open(self.license_filename, 'w') as license_file:
				license_file.write(response.read())
				self.log.info("The license was written to file '%s'" % self.license_filename)
		except (IOError, ValueError) as exc:
			self.log.exception("An error happened while writing the downloaded license to a file '%s': '%s'" % (self.license_filename, exc))
			exit(1)

	def check_date_format(self):
		"""
		Checks if the 'EndDate' format is correct.
		"""
		try:
			datetime.strptime(self.license_params['EndDate'], '%d.%m.%Y')
		except ValueError as exc:
			self.log.exception("The 'EndDate' for the license has a wrong format, supported format is 'dd.mm.yyyy': %r" % exc)
			exit(1)

	def update_with_parsed_args(self, args):
		"""
		Updates the loglevel and license filename settings if given
		among the parsed arguments. Merges parsed data with default
		license parameters.
		"""
		log_level = args.get('LogLevel')
		if log_level:
			numeric_level = getattr(logging, log_level.upper(), None)
			if isinstance(numeric_level, int):
				self.log.setLevel(numeric_level)
			else:
				self.log.info("The LogLevel was not changed, unknown '%s' log level given" % log_level)
		del args['LogLevel']  # should not be in self.license_params

		license_file = args.get('FileName')
		if license_file:
			self.license_filename = license_file
		del args['FileName']  # should not be in self.license_params
		self.log.debug("The filename for the license will be '%s'" % self.license_filename)

		# merging parsed args with the default values:
		self.license_params.update((key, val) for key, val in args.iteritems() if val is not None)
		self.log.info("Requested license parameters are: '%s'" % self.license_params)

	def process_cmd_arguments(self):
		"""
		Populates self.Parser class with positional and optional arguments and
		processes the user input, checks the date format and than merges it
		with the default values in the 'self.license_params' dictionary
		"""
		self.log.debug("In 'process_cmd_arguments' method")
		self.Parser.add_argument("BaseDN", help="A base DN for the license")
		self.Parser.add_argument("EndDate", help="The date till which the license will be valid (max 1 year from now)")
		self.Parser.add_argument("-f", "--FileName", help="The filename to be used for the issued license (default=ValidTest.license)")
		self.Parser.add_argument("-s", "--Servers", type=int, help="Max amount of servers allowed with the license (default=50)")
		self.Parser.add_argument("-u", "--Users", type=int, help="Max amount of users allowed with the license (default=50)")
		self.Parser.add_argument("-mc", "--ManagedClients", type=int, help="Max amount of managed clients allowed with the license (default=50)")
		self.Parser.add_argument("-cc", "--CorporateClients", type=int, help="Max amount of corporate clients allowed with the license (default=50)")
		self.Parser.add_argument("-ll", "--LogLevel", help="Logging level: INFO|DEBUG|ERROR|CRITICAL (default=INFO)")

		args = self.Parser.parse_args()
		args = vars(args)  # converting Namespace to a dictionary
		self.log.debug("Parsed arguments are: '%s'" % args)
		self.update_with_parsed_args(args)

	def main(self, base_dn="", end_date="", server_url="", license_file=""):
		"""
		A method to order and download a test license from the license server.
		'base_dn' and 'end_date' should be provided if argument parser is
		not used.
		'server_url' is an optional argument for the license shop server.
		'license_file' is an optional argument for the license filename.
		"""
		self.log.debug("In 'main' method: server_url='%s', license_file='%s', base_dn='%s', end_date='%s'" % (server_url, license_file, base_dn, end_date))
		if self.Parser:
			self.process_cmd_arguments()
		elif (base_dn and end_date):
			self.license_params['BaseDN'] = base_dn
			self.license_params['EndDate'] = end_date
		else:
			self.log.error("The 'BaseDN' or/and 'EndDate' were not provided for the license to create")
			exit(1)

		self.check_date_format()

		if server_url:
			self.license_server_url = server_url
		if license_file:
			self.license_filename = license_file
		self.get_server_password()
		try:
			self.create_connection()
			self.get_cookie()
			self.get_the_license(self.order_a_license())
		finally:
			self.close_connection()


if __name__ == '__main__':
	description = modules[__name__].__doc__
	Client = TestLicenseClient(ArgumentParser(description=description))
	Client.main()
