#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# UCS test connections to remote UMC Servers
#
# Copyright 2016-2022 Univention GmbH
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

from __future__ import print_function
import sys
import pprint

from six.moves.html_parser import HTMLParser
from six.moves.http_cookies import SimpleCookie
import requests

from univention.lib.umc import Client as _Client
from univention.config_registry import ConfigRegistry


class Client(_Client):

	print_response = True
	print_request_data = True

	@classmethod
	def get_test_connection(cls, hostname=None, *args, **kwargs):
		ucr = ConfigRegistry()
		ucr.load()
		username = ucr.get('tests/domainadmin/account')
		username = username.split(',')[0][len('uid='):]
		password = ucr.get('tests/domainadmin/pwd')
		return cls(hostname, username, password, *args, **kwargs)

	def umc_command(self, *args, **kwargs):
		self.print_request_data = kwargs.pop('print_request_data', True)
		self.print_response = kwargs.pop('print_response', True)
		try:
			return super(Client, self).umc_command(*args, **kwargs)
		finally:
			self.print_request_data = True
			self.print_response = True

	def request(self, method, path, data=None, headers=None):
		print('')
		print('*** UMC request: "%s %s" %s' % (method, path, '(%s)' % (data.get('flavor'),) if isinstance(data, dict) else ''))
		if self.print_request_data:
			print('UMC request payload: \n%s' % (pprint.pformat(data), ))
		try:
			response = super(Client, self).request(method, path, data, headers)
		except Exception:
			print('UMC request failed: %s' % (sys.exc_info()[1],))
			print('')
			raise
		if self.print_response:
			print('*** UMC response: \n%s\n***' % (pprint.pformat(response.data),))
		else:
			print('*** UMC response received')
		print('')
		return response


class SamlLoginError(Exception):
	pass


class GetHtmlTagValue(HTMLParser, object):
	def __init__(self, tag, condition, value_name):
		self.tag = tag
		self.condition = condition
		self.value_name = value_name
		self.value = None
		super(GetHtmlTagValue, self).__init__()

	def handle_starttag(self, tag, attrs):
		if tag == self.tag and self.condition in attrs:
			for attr in attrs:
				if attr[0] == self.value_name:
					self.value = attr[1]


def get_html_tag_value(page, tag, condition, value_name):
	htmlParser = GetHtmlTagValue(tag, condition, value_name)
	htmlParser.feed(page)
	htmlParser.close()
	return htmlParser.value


class ClientSaml(Client):

	def authenticate(self, *args):
		self.authenticate_saml(*args)

	def authenticate_saml(self, *args):
		self.__samlSession = requests.Session()

		saml_login_url = "https://%s/univention/saml/" % self.hostname
		print('GET SAML login form at: %s' % saml_login_url)
		saml_login_page = self.__samlSession.get(saml_login_url)
		saml_login_page.raise_for_status()
		saml_idp_login_ans = self._login_at_idp_with_credentials(saml_login_page)

		print('SAML message received from %s' % saml_idp_login_ans.url)
		self._send_saml_response_to_sp(saml_idp_login_ans)
		self.cookies = SimpleCookie()
		self.cookies.update(self.__samlSession.cookies.get_dict(domain=self.hostname))

	def _login_at_idp_with_credentials(self, saml_login_page):
		"""Send login form to IdP"""
		auth_state = get_html_tag_value(saml_login_page.text, 'input', ('name', 'AuthState', ), 'value')
		data = {'username': self.username, 'password': self.password, 'AuthState': auth_state}
		print('Post SAML login form to: %s' % saml_login_page.url)
		saml_idp_login_ans = self.__samlSession.post(saml_login_page.url, data=data)
		saml_idp_login_ans.raise_for_status()
		if 'umcLoginWarning' in saml_idp_login_ans.text:
			raise SamlLoginError('Login failed?:\n{}'.format(saml_idp_login_ans.text))
		return saml_idp_login_ans

	def _send_saml_response_to_sp(self, saml_idp_login_ans):
		sp_login_url = get_html_tag_value(saml_idp_login_ans.text, 'form', ('method', 'post', ), 'action')
		saml_msg = get_html_tag_value(saml_idp_login_ans.text, 'input', ('name', 'SAMLResponse', ), 'value')
		relay_state = get_html_tag_value(saml_idp_login_ans.text, 'input', ('name', 'RelayState', ), 'value')
		print('Post SAML msg to: %s' % sp_login_url)
		self.__samlSession.post(sp_login_url, data={'SAMLResponse': saml_msg, 'RelayState': relay_state}).raise_for_status()
