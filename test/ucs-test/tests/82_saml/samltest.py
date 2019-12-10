#!/usr/bin/env python
import re
import requests
from requests_kerberos import HTTPKerberosAuth, OPTIONAL
import subprocess
import socket
import json
import shutil
import os

import univention.testing.utils as utils
import univention.config_registry as configRegistry

import defusedxml.ElementTree as ET
import xml.etree.ElementTree

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
			if re.search('<b>Your password is expired.</b>', bytes(self.page.text)):
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


class SPCertificate(object):

	@staticmethod
	def get_server_cert_folder():
		ucr = configRegistry.ConfigRegistry()
		ucr.load()
		hostname = '%s.%s' % (ucr['hostname'], ucr['domainname'])
		return os.path.join('/etc/univention/ssl', hostname)

	def __init__(self, certificate, update_metadata=True):
		self.certificate = certificate
		cert_folder = self.get_server_cert_folder()
		self.cert_path = os.path.join(cert_folder, 'cert.pem')
		self.cert_path_backup = os.path.join(cert_folder, 'cert.pem.backup')
		self.update_metadata = update_metadata

	def __enter__(self):
		shutil.move(self.cert_path, self.cert_path_backup)
		with open(self.cert_path, 'w') as cert_file:
			cert_file.write(self.certificate)
		if self.update_metadata:
			subprocess.check_call('/usr/share/univention-management-console/saml/update_metadata')

	def __exit__(self, exc_type, exc_value, traceback):
		shutil.move(self.cert_path_backup, self.cert_path)
		if self.update_metadata:
			subprocess.check_call('/usr/share/univention-management-console/saml/update_metadata')


class SamlTest(object):
	def __init__(self, username, password, use_kerberos=False):
		self.ucr = configRegistry.ConfigRegistry()
		self.ucr.load()
		self.use_kerberos = use_kerberos
		self.target_sp_hostname = '%s.%s' % (self.ucr['hostname'], self.ucr['domainname'])
		self.username = username
		self.password = password
		self.session = requests.Session()
		if use_kerberos:
			self.session.auth = HTTPKerberosAuth(mutual_authentication=OPTIONAL)
		self.page = None
		self.parsed_page = None
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
		umc_session_id = self.session.cookies.get("UMCSessionId", domain=self.target_sp_hostname.lower())
		if umc_session_id:
			headers["X-Xsrf-Protection"] = umc_session_id
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
		try:
			self.parsed_page = ET.fromstring(bytes(self.page.text))
		except xml.etree.ElementTree.ParseError as exc:
			print('WARN: could not parse XML/HTML: %s' % (exc,))
			self.parsed_page = xml.etree.ElementTree.Element('html')
		self._check_status_code(status_code)

	def _login_at_idp_with_credentials(self):
		"""Send form with login data"""
		auth_state = self._extract_auth_state()
		self.position = "posting login form"
		print("Post SAML login form to: %s" % self.page.url)
		data = {'username': self.username, 'password': self.password, 'AuthState': auth_state}
		self._request('POST', self.page.url, 200, data=data)

	def xpath(self, xpath):
		elem = self.parsed_page.find(xpath)
		if elem is None:
			elem = {}
		return elem

	def _extract_relay_state(self):
		print("Extract relay state from SAML response")
		relay_state = self.xpath('.//{http://www.w3.org/1999/xhtml}input[@name="RelayState"]').get('value', '')
		if relay_state is None:
			print("No relay state found")
			raise SamlLoginError(self.page)
		print("The relay state is:\n%s" % relay_state)
		return relay_state

	def _extract_saml_msg(self):
		print("Extract SAML message from SAML response")
		saml_message = self.xpath('.//{http://www.w3.org/1999/xhtml}input[@name="SAMLResponse"]').get('value')
		if saml_message is None:
			raise SamlLoginError(self.page)
		print("The SAML message is:\n%s" % saml_message)
		return saml_message

	def _extract_sp_url(self):
		print("Extract url to post SAML message to")
		url = self.xpath('.//{http://www.w3.org/1999/xhtml}form[@method="post"]').get('action')
		if url is None:
			print("No url to post SAML message to found")
			raise SamlLoginError(self.page)
		print("The url to post SAML message to is: %s" % url)
		return url

	def _extract_auth_state(self):
		print("Extract AuthState")
		auth_state = self.xpath('.//{http://www.w3.org/1999/xhtml}input[@name="AuthState"]').get('value')
		if auth_state is None:
			try:
				auth_state = re.search('name="AuthState" value="([^"]+)"', bytes(self.page.text)).group(1)
				auth_state = html.unescape(auth_state)
			except AttributeError:
				pass
		if not auth_state:
			raise SamlError("No AuthState field found.\nSAML response:\n%s" % self.page.text)
		print("The SAML AuthState is:\n%s" % auth_state)
		return auth_state

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
		except SamlError:
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
		print('SAML message received from %s' % self.page.url)
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
		# Login at IdP. IdP answers with SAML message and url to SP in body
		if self.use_kerberos:
			self._request('GET', url, 200)
		else:
			try:
				self._request('GET', url, 200)
			except SamlError:
				# The kerberos backend adds a manual redirect
				if not self.page or self.page.status_code != 401:
					raise
				login_link = re.search('<a href="([^"]+)">', bytes(self.page.text)).group(1)
				self._request('GET', login_link, 200)
			self._login_at_idp_with_credentials()

		print('SAML message received from %s' % self.page.url)
		url = self._extract_sp_url()
		saml_msg = self._extract_saml_msg()
		relay_state = self._extract_relay_state()
		self._send_saml_response_to_sp(url, saml_msg, relay_state)

	def logout_at_IdP(self):
		"""Logout from session"""
		url = "https://%s/univention/logout" % self.target_sp_hostname
		print("Logging out at url: %s" % url)
		self.position = "trying to logout"
		self._request('GET', url, 200)
