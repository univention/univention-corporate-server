#!/usr/bin/python3
#
# Univention Portal
#
# Copyright 2019-2021 Univention GmbH
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

import json

import jwt
from jwt.algorithms import RSAAlgorithm
from six import with_metaclass
from six.moves.urllib_parse import urlencode
from tornado import escape, web
from tornado.auth import OAuth2Mixin
from tornado.httpclient import AsyncHTTPClient, HTTPClientError, HTTPError, HTTPRequest

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

	This base class does nothing...
	"""

	def get_auth_mode(self, request):  # pragma: no cover
		return "ucs"

	async def login_request(self, request):  # pragma: no cover
		pass

	async def login_user(self, request):  # pragma: no cover
		pass

	async def logout_user(self, request):  # pragma: no cover
		pass

	async def get_user(self, request):  # pragma: no cover
		return User(username=None, display_name=None, groups=[], headers={})

	def refresh(self, reason=None):  # pragma: no cover
		pass


class UMCAuthenticator(Authenticator):
	"""
	Specialized Authenticator that relies on a UMC that actually holds any session.
	Asks UMC for every request if this session is known.

	auth_mode:
		The preferred mode for auth. The portal hands it over to the frontend.
	umc_session_url:
		The URL where to go to with the cookie. Expects a json answer with the username.
	group_cache:
		As UMC does not return groups, we need a cache object that gets us the groups for the username.
	"""

	def __init__(self, auth_mode, umc_session_url, group_cache):
		self.auth_mode = auth_mode
		self.umc_session_url = umc_session_url
		self.group_cache = group_cache

	def get_auth_mode(self, request):
		return self.auth_mode

	def refresh(self, reason=None):
		return self.group_cache.refresh(reason=reason)

	async def get_user(self, request):
		cookies = dict((key, morsel.value) for key, morsel in request.cookies.items())
		username, display_name = await self._get_username(cookies)
		groups = self.group_cache.get().get(username, [])
		return User(username, display_name=display_name, groups=groups, headers=dict(request.request.headers))

	async def _get_username(self, cookies):
		for cookie in cookies:
			if cookie.startswith("UMCSessionId"):
				# UMCSessionId-1234 -> Host: localhost:1234
				host_port = cookie[13:]
				if host_port:
					host_port = ":{}".format(host_port)
				break
		else:
			get_logger("user").debug("no user given")
			return None, None
		headers = {"Host": "localhost" + host_port}
		get_logger("user").debug("searching user for cookies=%r" % cookies)
		username = await self._ask_umc(cookies, headers)
		if username is None:
			get_logger("user").debug("no user found")
			return None, None
		else:
			get_logger("user").debug("found %s" % (username,))
			return username.lower(), username

	async def _ask_umc(self, cookies, headers):
		try:
			headers['Cookie'] = '; '.join('='.join(c) for c in cookies.items())
			req = HTTPRequest(self.umc_session_url, method="GET", headers=headers)
			http_client = AsyncHTTPClient()
			response = await http_client.fetch(req)
			data = json.loads(response.body.decode('UTF-8'))
			username = data["result"]["username"]
		except HTTPError as exc:
			get_logger("user").error("request failed: %s" % exc)
		except EnvironmentError as exc:
			get_logger("user").error("connection failed: %s" % exc)
		except ValueError:
			get_logger("user").error("malformed answer!")
		except KeyError:
			get_logger("user").warning("session unknown!")
		else:
			return username


class OpenIDConnectAuthenticator(Authenticator, OAuth2Mixin):

	sessions = {}

	def prepare(self, request):
		self.op = request.get_query_argument('state', request.get_query_argument('op', request.get_cookie('oidc-op', request.application.settings['oidc_default_op'])))
		try:
			settings = request.application.settings['oidc'][self.op]
		except KeyError:
			raise HTTPError(404, 'OP not available')
		self.cookie_name_token = settings['oidc_cookie_token']
		self.cookie_name_user = settings['oidc_cookie_user']
		self.cookie_name_refresh_token = settings['oidc_cookie_refresh_token']
		# oidc_server = settings['oidc_server']
		# oidc_client_realm = settings['oidc_client_realm']
		self.oidc_client_id = settings['oidc_client_id']
		self.oidc_secret = settings['oidc_secret']
		self._OAUTH_AUTHORIZE_URL = settings["oidc_authorize_url"]
		self._OAUTH_ACCESS_TOKEN_URL = settings["oidc_access_token_url"]
		self._OAUTH_LOGOUT_URL = settings["oidc_logout_url"]
		self._OAUTH_USERINFO_URL = settings["oidc_userinfo_url"]
		self._OAUTH_CERT_URL = settings["oidc_cert_url"]
		self.extra_parameters = [x.strip() for x in settings.get('extra_parameters', '').split(',') if x.strip()]

	def get_auth_mode(self, request):
		return "oidc"

	async def get_authenticated_user(self, redirect_uri, code):
		http = self.get_auth_http_client()
		body = urlencode({
			"redirect_uri": redirect_uri,
			"code": code,
			"client_id": self.oidc_client_id,
			"client_secret": self.oidc_secret,
			"grant_type": "authorization_code",
		})
		response = await http.fetch(
			self._OAUTH_ACCESS_TOKEN_URL,
			method="POST",
			headers={"Content-Type": "application/x-www-form-urlencoded"},
			body=body,
		)
		return escape.json_decode(response.body)

	async def login_request(self, request):
		self.prepare(request)
		code = request.get_argument('code', False)
		if code:
			try:
				access = await self.get_authenticated_user(
					redirect_uri=request.reverse_abs_url('login'),
					code=request.get_argument('code'),
				)
			except HTTPClientError as exc:
				raise web.HTTPError(400, 'Could not authenticate user: %s' % (json.loads(exc.response.body),))

			access_token = access['access_token']
			if not access_token:
				raise web.HTTPError(400, "Could no receive access token")

			refresh_token = access['refresh_token']

			user_info_req = HTTPRequest(
				self._OAUTH_USERINFO_URL,
				method="GET",
				headers={
					"Accept": "application/json",
					"Authorization": "Bearer {}".format(access_token)
				},
			)
			http_client = self.get_auth_http_client()
			user_info_res = await http_client.fetch(user_info_req)
			user_info_res_json = json.loads(user_info_res.body.decode('utf-8'))
			request.set_secure_cookie(self.cookie_name_user, user_info_res_json['preferred_username'])
			request.set_secure_cookie(self.cookie_name_token, access_token)
			request.set_secure_cookie(self.cookie_name_refresh_token, refresh_token)
			get_logger("user").info('OIDC-Login: User-Info: %r' % (user_info_res_json,))
			self.sessions[access_token.encode('ASCII')] = user_info_res_json
			# currently not required, all infos are in the first userinfo request
			# user = await self.oauth2_request(
			# 	url=self._OAUTH_USERINFO_URL,
			# 	access_token=access['access_token'],
			# 	post_args={},
			# )
			request.redirect(request.reverse_abs_url('index'))
		else:
			self.redirect = request.redirect
			extra_parameters = {'approval_prompt': 'auto'}
			for extra_parameter in self.extra_parameters:
				value = request.get_query_argument(extra_parameter, None)
				if value:
					extra_parameters[extra_parameter] = value
			extra_parameters['state'] = self.op

			self.authorize_redirect(
				redirect_uri=request.reverse_abs_url('login'),
				client_id=self.oidc_client_id,
				scope=['profile', 'email'],
				response_type='code',
				extra_params=extra_parameters,
			)

	async def logout_user(self, request):
		self.prepare(request)
		access_token = request.get_secure_cookie(self.cookie_name_token)
		if not access_token:
			raise web.HTTPError(400, "Not logged in")
		access_token = access_token.decode('UTF-8')
		refresh_token = request.get_secure_cookie(self.cookie_name_refresh_token)
		if refresh_token:
			refresh_token = refresh_token.decode("UTF-8")

		body = urlencode({
			"client_id": self.oidc_client_id,
			"client_secret": self.oidc_secret,
			"refresh_token": refresh_token,
		})

		logout_req = HTTPRequest(
			self._OAUTH_LOGOUT_URL,
			method="POST",
			headers={
				"Authorization": "Bearer {}".format(access_token),
			},
			body=body,
		)

		http_client = self.get_auth_http_client()
		logout_res = await http_client.fetch(logout_req)
		assert 200 <= logout_res.code < 300, "Logout failed"  # actually 204
		self.sessions.pop(access_token.encode('ASCII'), None)
		request.clear_cookie('oidc-op')
		request.clear_cookie(self.cookie_name_user)
		request.clear_cookie(self.cookie_name_token)
		request.clear_cookie(self.cookie_name_refresh_token)
		request.redirect(request.reverse_abs_url('index'))

	async def get_user(self, request):
		self.prepare(request)
		user = self.sessions.get(request.get_secure_cookie(self.cookie_name_token))
		# user = await self.get_current_user(request)
		if user:
			try:
				user['groups']
			except KeyError:
				get_logger("user").error('No groups were delivered')

			return User(username=user.get('preferred_username', ''), display_name=user.get('name', ''), groups=user.get('groups', []), headers=dict(request.request.headers), args=user)
		return User(None, display_name=None, groups=[], headers=dict(request.request.headers))

	async def get_current_user(self, request):
		# user = request.get_secure_cookie(self.cookie_name_user)
		bearer = request.get_secure_cookie(self.cookie_name_token)
		request = HTTPRequest(self._OAUTH_CERT_URL, method='GET')
		http_client = AsyncHTTPClient()

		response = await http_client.fetch(request, raise_error=False)

		if response.code != 200:
			get_logger("user").warning("Fetching certificate failed")
			raise web.HTTPError(500)

		jwk = json.loads(response.body.decode('utf-8'))
		try:
			public_key = RSAAlgorithm.from_jwk(json.dumps(jwk['keys'][0]))
			payload = jwt.decode(bearer, public_key, algorithms='RS256', options={'verify_aud': False})
		except jwt.ExpiredSignatureError:
			get_logger("user").warning("Signature expired")
			raise web.HTTPError(401, reason='Unauthorized')
		except jwt.InvalidSignatureError:
			get_logger("user").error("Invalid signature")
			raise web.HTTPError(401, reason='Unauthorized')

		get_logger("user").info('OIDC JWK-Payload: %r' % (payload,))
		return payload


class MultiAuthenticator(Authenticator):

	def get_auth_mode(self, request):
		return "ucs"

	async def login_request(self, request):
		pass

	async def login_user(self, request):
		pass

	async def logout_user(self, request):
		pass

	async def get_user(self, request):
		return User(username=None, display_name=None, groups=[], headers={})

	def refresh(self, reason=None):
		pass
