#!/usr/bin/env python
import re
import requests
import cookielib

import univention.testing.utils as utils
import univention.config_registry as configRegistry
ucr=configRegistry.ConfigRegistry()
ucr.load()

# TODO: Verify ceritficate. SNI problem? Wait for python 2.7.9 or later.
# Verify certificate by changeing:
# verify=False
# to:
# verify='/etc/univention/ssl/ucsCA/CAcert.pem'

HOSTNAME = '%s.%s' % (ucr['hostname'], ucr['domainname'])


class SamlError(Exception):
	"""Custom error for everything SAML related"""
	def __init__(self, msg):
		self.message = msg

	def __str__(self):
		return repr(self.message)


def _change_IdP_url_to_IdP_IP(IdP_IP, cookies, url):
	sso_fqdn = 'ucs-sso.%(domainname)s' % ucr
	if sso_fqdn in url:
		headers = {'host': sso_fqdn}
		url = url.replace(sso_fqdn, IdP_IP)
		for cookie in cookies:
			if cookie.domain == sso_fqdn:
				cookie.domain = IdP_IP
				cookies.set_cookie(cookie)
	else:
		headers = None
	return headers, cookies


def _request(method, url, status_code, position, data=None, cookies=None, IdP_IP=None):
	"""does POST or GET requests and raises SamlError which encodes the login step
	through position parameter."""

	if IdP_IP:
		headers, cookies = _change_IdP_url_to_IdP_IP(IdP_IP, cookies, url)
	else:
		headers = None

	_requests = {
			'GET': requests.get,
			'POST': requests.post
			}
	try:
		response = _requests[method](url, cookies=cookies, data=data, verify=False, allow_redirects=True, headers=headers)
	except requests.exceptions.SSLError as E:
		raise SamlError("Problem while %s\nSSL error: %s" % (position, E.message))
	except requests.ConnectionError as E:
		raise SamlError("Problem while %s\nNo connection to server: %s" % (position, E.message))
	
	if response.status_code in range(300,400) and 'Location' in response.headers:
		# manually execute HTTP redirect
		response = _request('GET', response.headers['Location'], 200, position, data=data,
					cookies=response.cookies, IdP_IP=IdP_IP)
	
	# check for an expected status_code as a different would indicate an error
	# in the current login step.
	if response.status_code != status_code:
			raise SamlError("Problem while %s\nWrong status code: %s, expected: %s" % (position, response.status_code, status_code))
	return response


def _login_at_idp_with_credentials(username, password, response):
	"""Send form with login data"""
	response = _request('POST', response.url, 200, "posting login form",
				data={'username': username,
					  'password': password
					  },
				cookies = response.cookies
				)
	return response


def _extract_value_from_saml_response(response_text, attribute_name):
	try:
		return re.search('name="%s" value="([^"]+)"' % attribute_name, bytes(response_text)).group(1)
	except AttributeError:
		raise SamlError('No attribute with name %s found in response' % attribute_name)

def _extract_sp_url_from_response(response_text):
	try:
		return re.search('method="post" action="([^"]+)"', bytes(response_text)).group(1)
	# Incase the answer doesn't contain a url to POST to several failure cases
	# are handeled.
	except AttributeError:
		if re.search('<p>An LDAP password change is required before login is possible</p>', bytes(response_text)):
			raise SamlError("Got password expired notice")
		elif re.search('<p>The LDAP account is expired, login is denied</p>', bytes(response_text)):
			raise SamlError("Got account expired notice")
		elif re.search('<h1>Incorrect username or password</h1>', bytes(response_text)):
			raise SamlError("Got incorrect username or password notice")
		else:
			raise SamlError("No url to post SAML message found")


def _send_saml_response_to_sp(response):
	
	url = _extract_sp_url_from_response(response.text)
	saml_msg = _extract_value_from_saml_response(response.text, 'SAMLResponse')

	# POST the SAML message to SP, thus logging in.
	return _request('POST', url, 200, "posting SAML message",
			data={'SAMLResponse': saml_msg},
			cookies=response.cookies)


def test_login(cookies, hostname=HOSTNAME):
	"""Test login at umc"""
	_request('GET', "https://%s/univention-management-console/get/modules/list" % hostname, 200, "testing login",
			cookies=cookies)


def test_logout(cookies, hostname=HOSTNAME):
	"""Test logout at umc"""
	_request('GET', "https://%s/univention-management-console/get/modules/list" % hostname, 401, "testing logout", cookies=cookies)


def login_with_existing_session_at_IdP(cookies, hostname=HOSTNAME, IdP_IP=None):
	"""Use Identity Provider to log in to a Service Provider.
	If the IdP already knows the session and doesn't ask for username and password"""

	# Open login prompt. Redirects to IdP. IdP answers with SAML message
	url = "https://%s/univention-management-console/saml/" % hostname
	response = _request('GET', url, 200, "requesting SAML message", cookies=cookies, IdP_IP=IdP_IP)

	return _send_saml_response_to_sp(response).cookies

def login_with_new_session_at_IdP(username, password, hostname=HOSTNAME, IdP_IP=None):
	"""Use Identity Provider to log in to a Service Provider.
	The IdP doesn't know the session and has to ask for username and password"""

	# Open login prompt. Redirects to IdP. IdP answers with login prompt
	url = "https://%s/univention-management-console/saml/" % hostname
	response = _request('GET', url, 200, "reaching login dialog", IdP_IP=IdP_IP)

	# Login at IdP. IdP answers with SAML message
	response = _login_at_idp_with_credentials(username, password, response)

	return _send_saml_response_to_sp(response).cookies


def logout_at_IdP(cookies, hostname=HOSTNAME):
	"""Logout from session"""
	url = "https://%s/univention-management-console/logout" % hostname
	return _request('GET', url, 200, "trying to logout", cookies=cookies).cookies
