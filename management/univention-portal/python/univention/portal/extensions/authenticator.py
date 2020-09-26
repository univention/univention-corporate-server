#!/usr/bin/python2.7
#
# Univention Portal
#
# Copyright 2019-2020 Univention GmbH
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

import base64
import uuid

import requests
import tornado
from six import with_metaclass
from univention.portal import Plugin
from univention.portal.log import get_logger
from univention.portal.user import User


class Session(object):
	def __init__(self, nonce):
		self.nonce = nonce
		self.user = None

	def is_valid(self):
		return True


class Authenticator(with_metaclass(Plugin)):
	"""
	Our base class for authentication
	May hold all the sessions, set cookies, etc.

	The idea is that this class handles the following
	methods from the Portal:
	`login_request`: A user GETs to the login action
	`login_user`: Credentials are POSTed to this action
	`get_user`: While gathering the portal data, the caller wants
	to get a `User` object

	This base class does nothing...
	"""

	def login_request(self, request): pass

	def login_user(self, request): pass

	def get_user(self, request): pass

	def refresh(self, reason=None):	pass


class OpenIDAuthenticator(Authenticator):
	"""
	Specialized Authenticator that implements the OpenID Connect login flow.

	authorization_endpoint:
		URI for the endpoint of your OpenID Connect provider (e.g. "https://keycloak.mydomain.com/auth/realms/test/protocol/openid-connect/auth")
	client_id:
		Name of the client of the Portal as configured at your endpoint
	portal_cookie_name:
		Name of the Cookie the Authenticator sets and retrieves for the logged in user, default: "UniventionPortalSessionId"
	"""
	def __init__(self, authorization_endpoint, client_id, portal_cookie_name="UniventionPortalSessionId"):
		self.authorization_endpoint = authorization_endpoint
		self.client_id = client_id
		self.portal_cookie_name = portal_cookie_name
		self.sessions = {}

	def _redirect_to_authorization_endpoint(self, request, session_id, nonce):
		redirect_uri = "https://{}/univention/portal/portal/login/".format(request.request.host)  # FIXME
		get_logger("auth").info("Nonce used: {}".format(nonce))
		url = "{}?client_id={}&redirect_uri={}&scope=openid&kc_idp_hint=ucsoidc&response_mode=form_post&response_type=id_token&state={}&nonce={}".format(self.authorization_endpoint, self.client_id, redirect_uri, session_id, nonce)
		request.set_status(302)
		request.set_header("Location", url)
		raise tornado.web.Finish()

	def _verify_token(self, token, session):
		# TODO: we need a lib... python-jwt? alg was RS256 here...
		header, payload, sig = token.split(".")
		remainder = len(payload) % 4
		if remainder:
			payload = payload + "=" * (4 - remainder)
		token = base64.urlsafe_b64decode(payload)
		assert token["nonce"] == session.nonce
		return token

	def login_user(self, request):
		state = request.get_argument("state")
		session = self.sessions[state]
		token = request.get_argument("id_token")
		token = self._verify_token(token, session)
		session.user = User(token["preferred_username"], [])
		get_logger("auth").info("Successfully logged in...")
		request.set_cookie(self.portal_cookie_name, state)
		url = "https://{}/univention/portal/".format(request.request.host)  # FIXME
		request.set_status(302)
		request.set_header("Location", url)
		raise tornado.web.Finish()

	def login_request(self, request):
		session_id = uuid.uuid4()
		nonce = uuid.uuid4()
		self.sessions[session_id] = Session(nonce)
		get_logger("auth").info("Requested login! Created session_id {}".format(session_id))
		self._redirect_to_authorization_endpoint(request, session_id, nonce)

	def get_user(self, request):
		get_logger("auth").info("Checking for {}".format(self.portal_cookie_name))
		session_id = request.get_cookie(self.portal_cookie_name)
		if session_id is None:
			get_logger("auth").info("No cookie set")
			return None
		session = self.sessions.get(session_id)
		if session:
			get_logger("auth").info("Found session {}".format(session_id))
			if session.is_valid():
				return session.user
			else:
				get_logger("auth").info("Session no longer valid. Removing...")
				self.sessions.pop(session_id, None)
				request.clear_cookie(self.portal_cookie_name)
				return None
		else:
			get_logger("auth").info("Unknown session {}".format(session_id))
			request.clear_cookie(self.portal_cookie_name)
			return None


class UMCAuthenticator(Authenticator):
	"""
	Specialized Authenticator that relies on a UMC that actually holds any session.
	Asks UMC for every request if this session is known.

	umc_session_url:
		The URL where to go to with the cookie. Expects a json answer with the username.
	group_cache:
		As UMC does not return groups, we need a cache object that gets us the groups for the username.
	portal_cookie_name:
		Name of the Cookie the Authenticator retrieves for the logged in user, default: "UMCSessionId"
	umc_cookie_name:
		Name of the Cookie in UMC. Defaults to the `portal_cookie_name`.
	"""
	def __init__(self, umc_session_url, group_cache, portal_cookie_name="UMCSessionId", umc_cookie_name=None):
		self.umc_session_url = umc_session_url
		self.group_cache = group_cache
		self.portal_cookie_name = portal_cookie_name
		self.umc_cookie_name = umc_cookie_name or portal_cookie_name

	def refresh(self, reason=None):
		return self.group_cache.refresh(reason=reason)

	def get_user(self, request):
		session = request.get_cookie(self.portal_cookie_name)
		username = self._get_username(session)
		groups = self.group_cache.get().get(username, [])
		return User(username, groups=groups)

	def _get_username(self, session):
		if session is None:
			get_logger("user").debug("no user given")
			return None
		get_logger("user").debug("searching user for %s" % session)
		username = self._ask_umc(session)
		if username is None:
			get_logger("user").debug("no user found")
		else:
			get_logger("user").debug("found %s" % username)
			return username.lower()

	def _ask_umc(self, session):
		try:
			response = requests.get(self.umc_session_url, cookies={self.umc_cookie_name: session})
			data = response.json()
			username = data["result"]["username"]
		except requests.ConnectionError as exc:
			get_logger("user").error("connection failed: %s" % exc)
		except ValueError:
			get_logger("user").error("malformed answer!")
		except KeyError:
			get_logger("user").warn("session unknown!")
		else:
			return username
