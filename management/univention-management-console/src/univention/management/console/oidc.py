#!/usr/bin/python3
#
# Univention Management Console
#  OpenID Connect implementation for the UMC
#
# Copyright 2022 Univention GmbH
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
import json
import time

import jwt
from jwt.algorithms import RSAAlgorithm
from six.moves.urllib_parse import urlencode, urlparse, urlunsplit, parse_qsl
from tornado import escape, gen
from tornado.auth import OAuth2Mixin
from tornado.httpclient import AsyncHTTPClient, HTTPClientError, HTTPRequest

from univention.management.console.error import UMC_Error
from univention.management.console.resource import Resource
from univention.management.console.log import CORE
from univention.management.console.error import BadRequest, NotFound, Unauthorized, ServerError

try:
	from time import monotonic
except ImportError:
	from monotonic import monotonic


class OIDCUser(object):

	def __init__(self, access_token, claims, refresh_token=None):
		self.jwt = base64.b64encode(json.dumps(access_token).encode('ASCII')).decode('ASCII')
		self.claims = claims
		self.username = claims['preferred_username']
		#self.session_end_time = int(monotonic() + (time.time() - claims['exp']))
		self.session_end_time = int(monotonic() + (time.time() - access_token['expires_in']))


class OIDCResource(OAuth2Mixin, Resource):
	"""Base class for all OIDC resources."""

	def prepare(self):
		super(OIDCResource, self).prepare()
		state = dict(parse_qsl(self.get_query_argument('state', '')))
		self.op = state.get('op', self.get_query_argument('op', self.get_cookie('oidc-op', self.application.settings['oidc_default_op'])))
		try:
			settings = self.application.settings['oidc'][self.op]
		except KeyError:
			raise NotFound('OP not available')
		self.client_id = settings['client_id']
		self.client_secret = settings['client_secret']
		self._OAUTH_AUTHORIZE_URL = settings["authorization_endpoint"]
		self._OAUTH_ACCESS_TOKEN_URL = settings["token_endpoint"]
		self._OAUTH_LOGOUT_URL = settings["end_session_endpoint"]
		self._OAUTH_USERINFO_URL = settings["userinfo_endpoint"]
		self._OAUTH_CERT_URL = settings["jwks_uri"]
		self.extra_parameters = [x.strip() for x in settings.get('extra_parameters', '').split(',') if x.strip()]

	@gen.coroutine
	def bearer_authorization(self, access):
		access_token = access['access_token']
		if not access_token:
			raise BadRequest(self._("Could not receive access token."))

		user_info_req = HTTPRequest(
			self._OAUTH_USERINFO_URL,
			method="GET",
			headers={
				"Accept": "application/json",
				"Authorization": "Bearer %s" % (access_token,)
			},
		)
		http_client = self.get_auth_http_client()
		user_info_res = yield http_client.fetch(user_info_req)
		user_info = json.loads(user_info_res.body.decode('utf-8'))
		CORE.info('OIDC User-Info: %r' % (user_info,))

		oidc = OIDCUser(access, user_info, refresh_token=access.get('refresh_token'))

		# TODO/FIXME: do PAM auth here?!
		#result = yield self.current_user.authenticate({
		#	'locale': self.locale.code,
		#	'username': oidc.username,
		#	'password': oidc.jwt,
		#	'auth_type': 'OIDC',
		#})
		#if not self.current_user.authenticated:
		#	raise UMC_Error(result.message, result.status, result.result)

		self.set_session(self.create_sessionid(), oidc.username, oidc=oidc)
		self.current_user.authenticated = True
		self.current_user.user.set_credentials(oidc.username, oidc.jwt, 'OIDC')

	@gen.coroutine
	def verify_jwt(self, access_token):
		self = HTTPRequest(self._OAUTH_CERT_URL, method='GET')
		http_client = AsyncHTTPClient()

		response = yield http_client.fetch(self, raise_error=False)

		if response.code != 200:
			CORE.warn("Fetching certificate failed")
			raise ServerError(self._("Could not receive certificate from OP."))

		jwk = json.loads(response.body.decode('utf-8'))
		try:
			public_key = RSAAlgorithm.from_jwk(json.dumps(jwk['keys'][0]))
			payload = jwt.decode(access_token, public_key, algorithms='RS256', options={'verify_aud': False})
		except jwt.ExpiredSignatureError:
			CORE.warn("Signature expired")
			raise Unauthorized(self._("The OIDC response signature is expired."))
		except jwt.InvalidSignatureError as exc:
			CORE.error("Invalid signature: %s" % (exc,))
			raise Unauthorized(self._('The OIDC response contained an invalid signature: %s') % (exc,))

		CORE.info('OIDC JWK-Payload: %r' % (payload,))
		raise gen.Return(payload)


class OIDCLogin(OIDCResource):

	@gen.coroutine
	def get_access_token(self, redirect_uri, code):
		http = self.get_auth_http_client()
		body = urlencode({
			"redirect_uri": redirect_uri,
			"code": code,
			"client_id": self.client_id,
			"client_secret": self.client_secret,
			"grant_type": "authorization_code",
		})
		response = yield http.fetch(
			self._OAUTH_ACCESS_TOKEN_URL,
			method="POST",
			headers={"Content-Type": "application/x-www-form-urlencoded"},
			body=body,
		)
		raise gen.Return(escape.json_decode(response.body))

	@gen.coroutine
	def get(self):
		code = self.get_argument('code', False)
		if not code:
			self.do_single_sign_on(self.get_query_argument('location', '/univention/management/'))
			return

		try:
			access = yield self.get_access_token(
				redirect_uri=self.reverse_abs_url('oidc-login'),
				code=self.get_argument('code'),
			)
		except HTTPClientError as exc:
			CORE.error('Could not authenticate user: %s' % (exc.response.body,))
			raise BadRequest(self._('Could not authenticate user.'))

		yield self.bearer_authorization(access)

		state = dict(parse_qsl(self.get_query_argument('state', '')))

		# protect against javascript:alert('XSS'), mailto:foo and other non relative links!
		location = urlparse(state.get('location', ''))
		if location.path.startswith('//'):
			location = urlparse('')
		location = urlunsplit(('', '', location.path, location.query, location.fragment))
		self.redirect(location or self.reverse_abs_url('index'), status=303)

	@gen.coroutine
	def do_single_sign_on(self, location):
		self.redirect = self.redirect
		extra_parameters = {'approval_prompt': 'auto'}
		for extra_parameter in self.extra_parameters:
			value = self.get_query_argument(extra_parameter, None)
			if value:
				extra_parameters[extra_parameter] = value
		extra_parameters['state'] = urlencode({'op': self.op, 'location': location})

		self.authorize_redirect(
			redirect_uri=self.reverse_abs_url('oidc-login'),
			client_id=self.client_id,
			scope=['profile', 'email'],
			response_type='code',
			extra_params=extra_parameters,
		)


class OIDCLogout(OIDCResource):

	def get(self):
		user = self.current_user

		if user is None or user.oidc is None:
			return self._logout_success()

		access_token = user.jwt
		if not access_token:
			raise BadRequest(self._("Not logged in"))

		logout_url = '%s?%s' % (self._OAUTH_LOGOUT_URL, urlencode({'redirect_uri': self.reverse_abs_url('oidc-logout-done')}))
		self.redirect(logout_url)

	def _logout_success(self):
		user = self.current_user
		if user:
			user.oidc = None
		self.redirect('/univention/logout', status=303)


class OIDCLogoutFinished(OIDCLogout):

	def get(self):
		self._logout_success()
