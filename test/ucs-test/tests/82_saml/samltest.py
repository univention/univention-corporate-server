#!/usr/bin/env python
import re
import requests

import univention.testing.utils as utils
import univention.config_registry as configRegistry


class SamlError(Exception):
	"""Custom error for everything SAML related"""

	def __init__(self, msg):
		self.message = msg

	def __str__(self):
		return repr(self.message)


class SamlTest(object):

	def __init__(self, username, password):
		self.ucr = configRegistry.ConfigRegistry()
		self.ucr.load()
		self.hostname = '%s.%s' % (self.ucr['hostname'], self.ucr['domainname'])
		self.username = username
		self.password = password
		self.session = requests.Session()
		self.page = None

	def _change_IdP_url_to_IdP_IP(self, IdP_IP, url):
		sso_fqdn = 'ucs-sso.%(domainname)s' % self.ucr
		if sso_fqdn in url:
			headers = {'host': sso_fqdn}
			url = url.replace(sso_fqdn, IdP_IP)
			for cookie in self.session.cookies:
				if cookie.domain == sso_fqdn:
					cookie.domain = IdP_IP
					self.session.cookies.set_cookie(cookie)
		else:
			headers = None
		return headers, url

	def _request(self, method, url, status_code, position, data=None, IdP_IP=None):
		"""does POST or GET requests and raises SamlError which encodes the login step
		through position parameter."""

		if IdP_IP:
			print("Change IdP url to custom IdP IP")
			headers, url = self._change_IdP_url_to_IdP_IP(IdP_IP, url)
		else:
			headers = None

		_requests = {
			'GET': self.session.get,
			'POST': self.session.post}

		try:
			self.page = _requests[method](url, data=data, verify='/etc/univention/ssl/ucsCA/CAcert.pem', allow_redirects=True, headers=headers)		
		except requests.exceptions.SSLError as E:
			# Bug: https://github.com/shazow/urllib3/issues/556
			# raise SamlError("Problem while %s\nSSL error: %s" % (position, E.message))
			raise SamlError("Problem while %s\nSSL error: %s" % (position, 'Some ssl error'))
		except requests.ConnectionError as E:
			raise SamlError("Problem while %s\nNo connection to server: %s" % (position, E.message))

		if self.page.status_code in range(300, 400) and 'Location' in self.page.headers:
			# manually execute HTTP redirect
			print("Follow redirect to: %s" % self.page.headers['Location'])
			self.page = self._request('GET', self.page.headers['Location'], 200, position, data=data, IdP_IP=IdP_IP)

		# check for an expected status_code as a different would indicate an error
		# in the current login step.
		if self.page.status_code != status_code:
			raise SamlError("Problem while %s\nWrong status code: %s, expected: %s\nServer response was: %s" % (position, self.page.status_code, status_code, self.page.text))


	def _login_at_idp_with_credentials(self):
		"""Send form with login data"""

		auth_state = self._extract_auth_state_from()

		print("POST form with username and password to: %s" % self.page.url)
		self._request(
			'POST',
			self.page.url,
			200,
			"posting login form",
			data={'username': self.username, 'password': self.password, 'AuthState': auth_state}
			)

	def _extract_saml_msg_from(self):
		print("Extract SAML message from SAML response")
		try:
			return re.search('name="SAMLResponse" value="([^"]+)"', bytes(self.page.text)).group(1)
		except AttributeError:
			return None

	def _extract_sp_url_from(self):
		print("Extract url to post SAML message to")
		try:
			return re.search('method="post" action="([^"]+)"', bytes(self.page.text)).group(1)
		except AttributeError:
			return None

	def _extract_auth_state_from(self):
		print("Extract url to post SAML message to")
		try:
			return re.search('name="AuthState" value="([^"]+)"', bytes(self.page.text)).group(1)
		except AttributeError:
			raise SamlError("No AuthState field found.\nSAML response:\n%s" % self.page.text)

	def _send_saml_response_to_sp(self, url, saml_msg):
		# POST the SAML message to SP, thus logging in.
		print("POST SAML message to: %s" % url)
		self._request('POST', url, 200, "posting SAML message", data={'SAMLResponse': saml_msg})

	def test_login(self):
		"""Test login at umc"""
		print("Test login...")
		self._request('GET', "https://%s/univention/get/hosts" % self.hostname, 200, "testing login")
		print("Login success")

	def test_logout(self):
		"""Test logout at umc"""
		print("Test logout at SP...")
		self._request('GET', "https://%s/univention/get/hosts" % self.hostname, 405, "testing logout")
		print("Logout success at SP")

	def test_logout_at_IdP(self, IdP_IP=None):
		"""Test that passwordless login is not possible after logout"""
		print("Test logout at IdP...")
		try:
			self.login_with_existing_session_at_IdP(IdP_IP=None)
		except SamlError:
			print("Logout success at IdP")
		else:
			utils.fail("Session not closed at IdP after logout")

	def _error_evaluation(self):
			if re.search('<h1>Password change required</h1>', bytes(self.page.text)):
				raise SamlError("Got password expired notice")
			elif re.search('<h1>Account expired</h1>', bytes(self.page.text)):
				raise SamlError("Got account expired notice")
			elif re.search('<h1>Incorrect username or password</h1>', bytes(self.page.text)):
				raise SamlError("Got incorrect username or password notice")
			else:
				raise SamlError("Unknown error in SAML response.\nSAML response:\n%s" % self.page.text)

	def _evaluate_idp_response(self):
		"""Make sure the Identity Provider has returned a SAML message and a url at the Service Provider,
		if not evaluate the response body for common error cases"""
		url = self._extract_sp_url_from()
		saml_msg = self._extract_saml_msg_from()

		if url and saml_msg:
			return url, saml_msg
		else:
			self._error_evaluation()

	def login_with_existing_session_at_IdP(self, IdP_IP=None):
		"""Use Identity Provider to log in to a Service Provider.
		If the IdP already knows the session and doesn't ask for username and password"""

		# Open login prompt. Redirects to IdP. IdP answers with SAML message
		url = "https://%s/univention/saml/" % self.hostname
		print("GET SAML login form at: %s" % url)
		self._request('GET', url, 200, "requesting SAML message", IdP_IP=IdP_IP)

		url, saml_msg = self._evaluate_idp_response()

		self._send_saml_response_to_sp(url, saml_msg)


	def login_with_new_session_at_IdP(self, IdP_IP=None):
		"""Use Identity Provider to log in to a Service Provider.
		The IdP doesn't know the session and has to ask for username and password"""

		# Open login prompt. Redirects to IdP. IdP answers with login prompt
		url = "https://%s/univention/saml/" % self.hostname
		print("GET SAML login form at: %s" % url)
		self._request('GET', url, 200, "reaching login dialog", IdP_IP=IdP_IP)

		# Login at IdP. IdP answers with SAML message and url to SP in body
		self._login_at_idp_with_credentials()

		url, saml_msg = self._evaluate_idp_response()

		self._send_saml_response_to_sp(url, saml_msg)


	def logout_at_IdP(self):
		"""Logout from session"""
		url = "https://%s/univention/logout" % self.hostname
		print("Loging out at url: %s" % url)
		self._request('GET', url, 200, "trying to logout")
