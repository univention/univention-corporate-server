#!/usr/bin/env python3

from html.parser import HTMLParser

from bs4 import BeautifulSoup
import univention.testing.utils as utils
from locust import HttpUser, task, between

html = HTMLParser()

account = utils.UCSTestDomainAdminCredentials()

WAIT_MIN = 1
WAIT_MAX = 1


def logout_at_idp(self, client):
	"""Logout from session"""
	with client.get("/univention/logout", allow_redirects=True, timeout=10, catch_response=True) as req3:
		if not (200 <= req3.status_code <= 399):
			return None


def login_at_idp_with_credentials(self, client):
	"""Send form with login data"""
	data = {'username': "Administrator", 'password': "univention"}
	with client.post(self.login_link, name="/realms/ucs/login-actions/authenticate", allow_redirects=True, timeout=10, catch_response=True, data=data) as req2:
		soup = BeautifulSoup(req2.content, features="lxml")
		saml_response = soup.find("input", {"name": "SAMLResponse"}).get("value")
		if not saml_response:
			return None
		if not (200 <= req2.status_code <= 399):
			return None


def entry(self, client):
	"""Use Identity Provider to log in to a Service Provider.
	The IdP doesn't know the session and has to ask for username and password"""

	# Open login prompt. Redirects to IdP. IdP answers with login prompt
	entry = "/univention/saml/"
	with client.get(entry, allow_redirects=True, timeout=10, catch_response=True) as req1:
		if not (200 <= req1.status_code <= 399):
			return None
		if req1.content is None or len(req1.content) == 0:
			return None
	soup = BeautifulSoup(req1.content, features="lxml")
	login_link = soup.find("form", {"id": "kc-form-login"}).get("action")
	self.login_link = html.unescape(login_link)
	self.login_at_idp_with_credentials(client)
	self.logout_at_idp(client)
	client.cookies.clear()


class QuickstartUser(HttpUser):
	wait_time = between(WAIT_MIN, WAIT_MAX)

	@task
	def get_samlSession(self):
		entry(self.client)
