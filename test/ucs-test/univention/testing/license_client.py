#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright 2014-2022 Univention GmbH
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

"""
A tool to obtain licenses for the UCS test environments.
"""
import cgi
import logging
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from datetime import datetime
from os import path
from sys import exit
from typing import Any, Dict, Iterable, Optional, Tuple  # noqa: F401

from six.moves.html_parser import HTMLParser
from six.moves.http_client import HTTPSConnection, HTTPException, HTTPResponse  # noqa: F401
from six.moves.urllib.parse import urlencode


class CredentialsMissing(Exception):

	"""
	A custom exception to be raised when a 'license.secret' file is not found
	"""


class ShopParser(HTMLParser):

	def __init__(self, log):
		# type: (logging.Logger) -> None
		HTMLParser.__init__(self)  # old style class
		self.log = log
		self.link_to_license = None  # type: Optional[str]

	def error(self, message):
		self.log.error("Failed parsing HTML: %s", message)

	def handle_starttag(self, tag, attrs):
		# type: (str, Iterable[Tuple[str, Optional[str]]]) -> None
		"""
		Method is called every time a new start tag is found in the
		html feed. When the link tag with 'orders/' attribute is
		found, the attribute is saved to 'self.link_to_license'
		"""
		self.log.debug("In 'handle_starttag' method: tag='%s', attrs='%s'", tag, attrs)
		if tag != 'a':
			return
		for (name, value) in attrs:
			if name != 'href':
				continue
			if not value:
				continue
			if not value.startswith('orders/'):
				continue
			self.link_to_license = value
			break


class TestLicenseClient(object):

	def __init__(self, parser=None):
		# type: (Optional[ArgumentParser]) -> None
		"""
		Class constructor for the test license client and HTMLParser
		"""
		self.log = logging.getLogger("License_Client")
		self.setup_logging()

		self.parser = parser
		self.license_server_url = 'license.univention.de'
		self.license_filename = 'ValidTest.license'

		self.connection = None  # type: Optional[HTTPSConnection]
		self.server_username = 'ucs-test'
		self.server_password = ''
		self.secret_file = '/etc/license.secret'
		self.cookie = ''
		self.license_shop = 'testing'

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
		}  # type: Dict[str, Any]

	def setup_logging(self):
		# type: () -> None
		"""
		Creates and configures the logger with an INFO level
		"""
		self.log.setLevel(logging.INFO)
		ch = logging.StreamHandler()
		ch.setLevel(logging.DEBUG)
		ch.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
		self.log.addHandler(ch)

	def create_connection(self):
		# type: () -> None
		"""
		Creates a HTTPS connection instance on a default port (443)
		to the 'self.license_server_url'
		"""
		self.log.debug("In 'create_connection'")
		self.connection = HTTPSConnection(self.license_server_url, timeout=60)

	def close_connection(self):
		# type: () -> None
		"""
		Closes the license server connection if the connection instance
		was created
		"""
		self.log.debug("In 'close_connection'")
		if self.connection:
			try:
				self.connection.close()
			except HTTPException as exc:
				self.log.exception("An HTTP Exception occurred while closing the connection: '%s'", exc)
			finally:
				self.connection = None

	def get_server_password(self, secret_file='/etc/license.secret'):
		# type: (str) -> None
		"""
		Opens and reads the 'secret_file'. Saves the result to a
		'self.server_password'
		"""
		self.log.debug("In 'get_server_password': secret_file='%s'", secret_file)
		if not path.exists(secret_file):
			self.log.critical("The '%s' secret file does not exist, cannot proceed without password", secret_file)
			raise CredentialsMissing("The '%s' secret file does not exist" % secret_file)
		try:
			with open(secret_file, 'r') as password:
				self.server_password = password.read()
		except (IOError, ValueError) as exc:
			self.log.exception("Failed to get the password from the '%s', an error occurred: %r", secret_file, exc)
			exit(1)
		if not self.server_password:
			self.log.critical("The password to access the license service cannot be empty")
			exit(1)

	def get_cookie(self):
		# type: () -> None
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

		response = self.make_post_request('/shop/%s/' % (self.license_shop,), urlencode(body), headers)
		self.log.debug("The response status is '%s', reason is '%s', headers are '%s'", response.status, response.reason, response.getheaders())

		self.cookie = response.getheader('set-cookie')
		if 'sessionid' not in self.cookie:
			self.log.critical("The 'sessionid' field was not found in the received cookie: '%s'", self.cookie)
			exit(1)
		# extracting only the 'sessionid' part of the cookie:
		self.cookie = self.cookie[:self.cookie.find(';')]
		self.log.debug("The cookie is: '%s'", self.cookie)
		# reading the response to avoid 'ResponseNotReady' exception later:
		response.read()

	def make_post_request(self, url, body, headers):
		# type: (str, str, Dict[str, str]) -> HTTPResponse
		"""
		Makes a POST request with the given 'url', 'body', 'headers' and
		returns the response
		"""
		self.log.debug("In 'make_post_request' method: url='%s', body='%s', headers='%s'", url, body, headers)
		assert self.connection
		try:
			self.connection.request("POST", url, body, headers)
			return self.connection.getresponse()
		except HTTPException as exc:
			self.log.exception("An HTTP Exception occurred while making '%s' POST request: '%s'", url, exc)
			exit(1)

	def make_get_request(self, url, headers):
		# type: (str, Dict[str, str]) -> HTTPResponse
		"""
		Makes a GET request with the given 'url', 'headers' and
		returns the response
		"""
		self.log.debug("In 'make_get_request' method: url='%s', headers='%s'", url, headers)
		assert self.connection
		try:
			self.connection.request("GET", url, headers=headers)
			return self.connection.getresponse()
		except HTTPException as exc:
			self.log.exception("An HTTP Exception occurred while making '%s' GET request: '%s'", url, exc)
			exit(1)

	def get_the_license(self, body):
		# type: (str) -> None
		"""
		Processes the given 'body' with HTMLParser to find the link
		to a created license file and downloads the license after.
		"""
		self.log.debug("In 'get_the_license' method: body='%s'", body)
		parser = ShopParser(self.log)
		parser.feed(body)  # process the response 'body' for license link
		if not parser.link_to_license:
			self.log.critical("The link to the license file was not found in the body from server: '%s'", body)
			exit(1)
		self.download_license_file(parser.link_to_license)

	def order_a_license(self):
		# type: () -> str
		"""
		Makes a POST request with encoded 'self.license_params' as a body to
		order a new license. Returns the response body.
		"""
		self.log.debug("In 'order_a_license' method")
		body = self.license_params
		headers = {
			"Cookie": self.cookie,
			"Content-type": "application/x-www-form-urlencoded",
		}

		response = self.make_post_request('/shop/%s/order' % (self.license_shop,), urlencode(body), headers)
		assert response.status == 202
		return self.get_body(response)

	def get_body(self, response):
		# type: (HTTPResponse) -> str
		self.log.debug("The response status is '%s', reason is '%s', headers are '%s'", response.status, response.reason, response.getheaders())
		content_type = response.getheader('Content-Type')
		mimetype, options = cgi.parse_header(content_type)
		encoding = options.get("charset", "ascii")
		return response.read().decode(encoding, "replace")

	def download_license_file(self, link_to_license):
		# type: (str) -> None
		"""
		Downloads the license located at `filename` and saves it
		to the file 'self.license_filename'
		"""
		self.log.debug("In 'download_license_file' method")
		headers = {
			"Cookie": self.cookie,
			"Accept": "text/plain",
		}
		response = self.make_get_request('/shop/%s/%s' % (self.license_shop, link_to_license), headers)
		try:
			body = self.get_body(response)
			with open(self.license_filename, 'w') as license_file:
				license_file.write(body)
			self.log.info("The license was written to file '%s'", self.license_filename)
		except (IOError, ValueError) as exc:
			self.log.exception("An error happened while writing the downloaded license to a file '%s': '%s'", self.license_filename, exc)
			exit(1)

	def check_date_format(self):
		# type: () -> None
		"""
		Checks if the 'EndDate' format is correct.
		"""
		try:
			if self.license_params['EndDate'] != 'unlimited':
				datetime.strptime(self.license_params['EndDate'], '%d.%m.%Y')
		except ValueError as exc:
			self.log.exception("The 'EndDate' for the license has a wrong format, supported format is 'dd.mm.yyyy': %r", exc)
			exit(1)

	def update_with_parsed_args(self, args):
		# type: (Dict[str, Any]) -> None
		"""
		Updates the loglevel and license filename settings if given
		among the parsed arguments. Merges parsed data with default
		license parameters.
		"""
		log_level = args.pop('LogLevel')
		if log_level:
			numeric_level = getattr(logging, log_level.upper(), None)
			if isinstance(numeric_level, int):
				self.log.setLevel(numeric_level)
			else:
				self.log.info("The LogLevel was not changed, unknown '%s' log level given", log_level)

		self.license_shop = args.pop('shop')
		self.server_username = args.pop('username')
		self.secret_file = args.pop('secret_file')
		license_file = args.pop('FileName')
		if license_file:
			self.license_filename = license_file
		self.log.debug("The filename for the license will be '%s'", self.license_filename)

		# merging parsed args with the default values:
		self.license_params.update((key, val) for key, val in args.items() if val is not None)
		self.log.info("Requested license parameters are: '%s'", self.license_params)

	def process_cmd_arguments(self):
		# type: () -> None
		"""
		Populates self.parser class with positional and optional arguments and
		processes the user input, checks the date format and than merges it
		with the default values in the 'self.license_params' dictionary
		"""
		self.log.debug("In 'process_cmd_arguments' method")
		assert self.parser
		self.parser.add_argument("BaseDN", help="A base DN for the license")
		self.parser.add_argument("EndDate", help="The date till which the license will be valid (max 1 year from now)")
		self.parser.add_argument("-f", "--FileName", help="The filename to be used for the issued license", default="ValidTest.license")
		self.parser.add_argument("-s", "--Servers", type=int, help="Max amount of servers allowed with the license", default=50)
		self.parser.add_argument("-u", "--Users", type=int, help="Max amount of users allowed with the license", default=50)
		self.parser.add_argument("-mc", "--ManagedClients", type=int, help="Max amount of managed clients allowed with the license", default=50)
		self.parser.add_argument("-cc", "--CorporateClients", type=int, help="Max amount of corporate clients allowed with the license", default=50)
		self.parser.add_argument("-ll", "--LogLevel", help="Logging level", choices=("INFO", "DEBUG", "ERROR", "CRITICAL"), default="INFO")
		self.parser.add_argument("--shop", help="The shop", default=self.license_shop)
		self.parser.add_argument("--username", help="username", default=self.server_username)
		self.parser.add_argument("--secret-file", help="password file", default=self.secret_file)

		opts = self.parser.parse_args()
		args = vars(opts)  # converting Namespace to a dictionary
		self.log.debug("Parsed arguments are: '%s'", args)
		self.update_with_parsed_args(args)

	def main(self, base_dn="", end_date="", server_url="", license_file=""):
		# type: (str, str, str, str) -> None
		"""
		A method to order and download a test license from the license server.
		'base_dn' and 'end_date' should be provided if argument parser is
		not used.
		'server_url' is an optional argument for the license shop server.
		'license_file' is an optional argument for the license filename.
		"""
		self.log.debug("In 'main' method: server_url='%s', license_file='%s', base_dn='%s', end_date='%s'", server_url, license_file, base_dn, end_date)
		if self.parser:
			self.process_cmd_arguments()
		elif base_dn and end_date:
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
		self.get_server_password(self.secret_file)
		try:
			self.create_connection()
			self.get_cookie()
			self.get_the_license(self.order_a_license())
		finally:
			self.close_connection()


if __name__ == '__main__':
	Client = TestLicenseClient(ArgumentParser(description=__doc__, formatter_class=ArgumentDefaultsHelpFormatter))
	Client.main()
