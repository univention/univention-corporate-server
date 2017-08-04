#!/usr/bin/env python
import re
import requests
import subprocess
import socket
import json

import univention.testing.utils as utils
import univention.config_registry as configRegistry

from HTMLParser import HTMLParser
html = HTMLParser()


class SamlError(Exception):
	"""Custom error for everything SAML related"""
	def __init__(self, msg):
		self.message = msg

	def __str__(self):
		return repr(self.message)


class SamlLoginError(SamlError):
	def __init__(self, page):
		self.page = page
		self.message = ''
		self._error_evaluation()

	def _error_evaluation(self):
			if re.search('<b>Password change required.</b>', bytes(self.page.text)):
				self.message = "Got password expired notice"
			elif re.search('<b>Account expired.</b>', bytes(self.page.text)):
				self.message = "Got account expired notice"
			elif re.search('<b>Incorrect username or password.</b>', bytes(self.page.text)):
				self.message = "Got incorrect username or password notice"
			else:
				self.message = "Unknown error in SAML response.\nSAML response:\n%s" % self.page.text


class GuaranteedIdP(object):
	def __init__(self, ip):
		self.ip = ip

	def __enter__(self):
		subprocess.call(['ucr', 'set', 'hosts/static/%s=ucs-sso.univention.intranet' % self.ip])
		subprocess.call(['invoke-rc.d', 'nscd', 'restart'])
		IdP_IP = socket.gethostbyname('ucs-sso.univention.intranet')
		if IdP_IP != self.ip:
			utils.fail("Couldn't set guaranteed IdP")
		print('Set IdP to: %s' % self.ip)

	def __exit__(self, exc_type, exc_value, traceback):
		subprocess.call(['ucr', 'unset', 'hosts/static/%s' % self.ip])
		subprocess.call(['invoke-rc.d', 'nscd', 'restart'])


class SamlTest(object):
	def __init__(self, username, password):
		self.ucr = configRegistry.ConfigRegistry()
		self.ucr.load()
		self.target_sp_hostname = '%s.%s' % (self.ucr['hostname'], self.ucr['domainname'])
		self.username = username
		self.password = password
		self.session = requests.Session()
		self.page = None
		self.position = 'Init...'

	def _check_status_code(self, status_code):
		# check for an expected status_code as a different would indicate an error
		# in the current login step.
		if self.page.status_code != status_code:
			raise SamlError("Problem while %s\nWrong status code: %s, expected: %s\nServer response was: %s" % (self.position, self.page.status_code, status_code, self.page.text))

	def _request(self, method, url, status_code, data=None):
		"""does POST or GET requests and raises SamlError which encodes the login step
		through position parameter."""
		headers = {'Accept-Language': 'en-US;q=0.6,en;q=0.4', 'Referer': ''}
		if "UMCSessionId" in self.session.cookies:
			headers["X-Xsrf-Protection"] = self.session.cookies["UMCSessionId"]
		_requests = {
			'GET': self.session.get,
			'POST': self.session.post}
		try:
			self.page = _requests[method](url, data=data, verify='/etc/univention/ssl/ucsCA/CAcert.pem', headers=headers)
		except requests.exceptions.SSLError as E:
			# Bug: https://github.com/shazow/urllib3/issues/556
			# raise SamlError("Problem while %s\nSSL error: %s" % (self.position, E.message))
			raise SamlError("Problem while %s\nSSL error: %s" % (self.position, 'Some ssl error'))
		except requests.ConnectionError as E:
			raise SamlError("Problem while %s\nNo connection to server: %s" % (self.position, E.message))
		self._check_status_code(status_code)

	def _login_at_idp_with_credentials(self):
		"""Send form with login data"""
		auth_state = self._extract_auth_state()
		self.position = "posting login form"
		print("Post SAML login form to: %s" % self.page.url)
		data = {'username': self.username, 'password': self.password, 'AuthState': auth_state}
		self._request('POST', self.page.url, 200, data=data)

	def _extract_relay_state(self):
		print("Extract relay state from SAML response")
		try:
			relay_state = re.search('name="RelayState" value="([^"]+)"', bytes(self.page.text)).group(1)
			relay_state = html.unescape(relay_state)
			print("The relay state is:\n%s" % relay_state)
			return relay_state
		except AttributeError:
			print("No relay state found")
			raise SamlLoginError(self.page)

	def _extract_saml_msg(self):
		print("Extract SAML message from SAML response")
		try:
			saml_message = re.search('name="SAMLResponse" value="([^"]+)"', bytes(self.page.text)).group(1)
			saml_message = html.unescape(saml_message)
			print("The SAML message is:\n%s" % saml_message)
			return saml_message
		except AttributeError:
			print("No SAML message found")
			raise SamlLoginError(self.page)

	def _extract_sp_url(self):
		print("Extract url to post SAML message to")
		try:
			url = re.search('method="post" action="([^"]+)"', bytes(self.page.text)).group(1)
			url = html.unescape(url)
			print("The url to post SAML message to is: %s" % url)
			return url
		except AttributeError:
			print("No url to post SAML message to found")
			raise SamlLoginError(self.page)

	def _extract_auth_state(self):
		print("Extract AuthState")
		try:
			auth_state = re.search('name="AuthState" value="([^"]+)"', bytes(self.page.text)).group(1)
			auth_state = html.unescape(auth_state)
			print("The SAML AuthState is:\n%s" % auth_state)
			return auth_state
		except AttributeError:
			raise SamlError("No AuthState field found.\nSAML response:\n%s" % self.page.text)

	def _send_saml_response_to_sp(self, url, saml_msg, relay_state):
		# POST the SAML message to SP, thus logging in.
		print("POST SAML message to: %s" % url)
		self.position = "posting SAML message"
		self._request('POST', url, 200, data={'SAMLResponse': saml_msg, 'RelayState': relay_state})

	def test_login(self):
		"""Test login on umc"""
		url = "https://%s/univention/get/session-info" % self.target_sp_hostname
		print("Test login @ %s" % url)
		self.position = "testing login"
		self._request('GET', url, 200)
		auth_type = json.loads(self.page.text)['result']['auth_type']
		if auth_type != 'SAML':
			utils.fail("SAML wasn't used for login?")
		print("Login success")

	def test_slapd(self):
		"""Test ldap login with saml"""
		url = "https://%s/univention/command/udm/meta_info" % self.target_sp_hostname
		print("Test ldap login @ %s" % url)
		self.position = "testing ldap login"
		self._request('POST', url, 200, data={"objectType": "dns/dns"})
		print("LDAP login success")

	def test_logout(self):
		"""Test logout on umc"""
		url = "https://%s/univention/get/session-info" % self.target_sp_hostname
		print("Test logout @ %s" % url)
		self.position = "testing logout"
		self._request('GET', url, 401)
		print("Logout success at SP")

	def test_logout_at_IdP(self):
		"""Test that passwordless login is not possible after logout"""
		print("Test logout at IdP...")
		try:
			self.login_with_existing_session_at_IdP()
		except SamlLoginError:
			print("Logout success at IdP")
		else:
			utils.fail("Session not closed at IdP after logout")

	def login_with_existing_session_at_IdP(self):
		"""Use Identity Provider to log in to a Service Provider.
		If the IdP already knows the session and doesn't ask for username and password"""

		# Open login prompt. Redirects to IdP. IdP answers with SAML message
		url = "https://%s/univention/saml/" % self.target_sp_hostname
		print("GET SAML login form at: %s" % url)
		self.position = "requesting SAML message"
		self._request('GET', url, 200)
		print('SAML message recieved from %s' % self.page.url)
		url = self._extract_sp_url()
		saml_msg = self._extract_saml_msg()
		relay_state = self._extract_relay_state()
		self._send_saml_response_to_sp(url, saml_msg, relay_state)

	def login_with_new_session_at_IdP(self):
		"""Use Identity Provider to log in to a Service Provider.
		The IdP doesn't know the session and has to ask for username and password"""

		# Open login prompt. Redirects to IdP. IdP answers with login prompt
		url = "https://%s/univention/saml/" % self.target_sp_hostname
		print("GET SAML login form at: %s" % url)
		self.position = "reaching login dialog"
		self._request('GET', url, 200)
		print('SAML message recieved from %s' % self.page.url)

		# Login at IdP. IdP answers with SAML message and url to SP in body
		self._login_at_idp_with_credentials()
		url = self._extract_sp_url()
		saml_msg = self._extract_saml_msg()
		relay_state = self._extract_relay_state()
		self._send_saml_response_to_sp(url, saml_msg, relay_state)

	def logout_at_IdP(self):
		"""Logout from session"""
		url = "https://%s/univention/logout" % self.target_sp_hostname
		print("Loging out at url: %s" % url)
		self.position = "trying to logout"
		self._request('GET', url, 200)
