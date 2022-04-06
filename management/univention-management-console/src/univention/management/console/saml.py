#!/usr/bin/python3
# -*- coding: utf-8 -*-
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

import os
import sys
import time
import json
import zlib
import base64
import traceback

import six
from six.moves.urllib_parse import urlparse, urlunsplit
from tornado.web import HTTPError

from saml2 import BINDING_HTTP_POST, BINDING_HTTP_ARTIFACT, BINDING_HTTP_REDIRECT
from saml2.client import Saml2Client
from saml2.metadata import create_metadata_string
from saml2.response import VerificationError, UnsolicitedResponse, StatusError
from saml2.s_utils import UnknownPrincipal, UnsupportedBinding
from saml2.sigver import MissingKey, SignatureError
from saml2.ident import code as encode_name_id, decode as decode_name_id

from univention.management.console.log import CORE
from univention.management.console.shared_memory import shared_memory
from univention.management.console.resource import Resource

from univention.lib.i18n import NullTranslation

try:
	from time import monotonic
except ImportError:
	from monotonic import monotonic

_ = NullTranslation('univention-management-console-frontend').translate

SERVICE_UNAVAILABLE = 503


class SAMLUser(object):
	"""SAML specific user information"""

	__slots__ = ('message', 'username', 'session_end_time', 'name_id')

	def __init__(self, response, message):
		self.name_id = encode_name_id(response.name_id)
		self.message = message
		self.username = u''.join(response.ava['uid'])
		self.session_end_time = 0
		if response.not_on_or_after:
			self.session_end_time = int(monotonic() + (response.not_on_or_after - time.time()))

	def on_logout(self):
		SAMLResource.on_logout(self.name_id)


class SamlError(HTTPError):
	"""Errors caused during SAML authentication"""

	def __init__(self, _=_):
		self._ = _

	def error(func=None, status=400):  # noqa: N805
		def _decorator(func):
			def _decorated(self, *args, **kwargs):
				message = func(self, *args, **kwargs) or ()
				super(SamlError, self).__init__(status, message)
				if "Passive authentication not supported." not in message:
					# "Passive authentication not supported." just means an active login is required. That is expected and needs no logging. It still needs to be raised though.
					CORE.warn('SamlError: %s %s' % (status, message))
				return self
			return _decorated
		if func is None:
			return _decorator
		return _decorator(func)

	def from_exception(self, etype, exc, etraceback):
		if isinstance(exc, UnknownPrincipal):
			return self.unknown_principal(exc)
		if isinstance(exc, UnsupportedBinding):
			return self.unsupported_binding(exc)
		if isinstance(exc, VerificationError):
			return self.verification_error(exc)
		if isinstance(exc, UnsolicitedResponse):
			return self.unsolicited_response(exc)
		if isinstance(exc, StatusError):
			return self.status_error(exc)
		if isinstance(exc, MissingKey):
			return self.missing_key(exc)
		if isinstance(exc, SignatureError):
			return self.signature_error(exc)
		six.reraise(etype, exc, etraceback)

	@error
	def unknown_principal(self, exc):
		return self._('The principal is unknown: %s') % (exc,)

	@error
	def unsupported_binding(self, exc):
		return self._('The requested SAML binding is not known: %s') % (exc,)

	@error
	def unknown_logout_binding(self, binding):
		return self._('The logout binding is not known.')

	@error
	def verification_error(self, exc):
		return self._('The SAML response could not be verified: %s') % (exc,)

	@error
	def unsolicited_response(self, exc):
		return self._('Received an unsolicited SAML response. Please try to single sign on again by accessing /univention/saml/. Error message: %s') % (exc,)

	@error
	def status_error(self, exc):
		return self._('The identity provider reported a status error: %s') % (exc,)

	@error(status=500)
	def missing_key(self, exc):
		return self._('The issuer %r is now known to the SAML service provider. This is probably a misconfiguration and might be resolved by restarting the univention-management-console-server.') % (str(exc),)

	@error
	def signature_error(self, exc):
		return self._('The SAML response contained a invalid signature: %s') % (exc,)

	@error
	def unparsed_saml_response(self):
		return self._("The SAML message is invalid for this service provider.")

	@error(status=500)
	def no_identity_provider(self):
		return self._('There is a configuration error in the service provider: No identity provider are set up for use.')

	@error  # TODO: multiple choices redirection status
	def multiple_identity_provider(self, idps, idp_query_param):
		return self._('Could not pick an identity provider. You can specify one via the query string parameter %(param)r from %(idps)r') % {'param': idp_query_param, 'idps': idps}


class SAMLResource(Resource):
	"""Base class for all SAML resources"""

	SP = None
	identity_cache = '/var/cache/univention-management-console/saml.bdb'
	configfile = '/usr/share/univention-management-console/saml/sp.py'
	idp_query_param = "IdpQuery"
	bindings = [BINDING_HTTP_REDIRECT, BINDING_HTTP_POST, BINDING_HTTP_ARTIFACT]
	outstanding_queries = {}

	@classmethod
	def on_logout(cls, name_id):
		if cls.SP:
			try:
				cls.SP.local_logout(decode_name_id(name_id))
			except Exception as exc:  # e.g. bsddb.DBNotFoundError
				CORE.warn('Could not remove SAML session: %s' % (exc,))


class SamlMetadata(SAMLResource):
	"""Get the SAML XML Metadata"""

	def get(self):
		metadata = create_metadata_string(self.configfile, None, valid='4', cert=None, keyfile=None, mid=None, name=None, sign=False)
		self.set_header('Content-Type', 'application/xml')
		self.finish(metadata)


class SamlACS(SAMLResource):
	"""SAML attribute consuming service (or Single Sign On redirection)"""

	@property
	def sp(self):
		if not self.SP and not self.reload():
			raise HTTPError(SERVICE_UNAVAILABLE, 'Single sign on is not available due to misconfiguration. See logfiles.')
		return self.SP

	@classmethod
	def reload(cls):
		CORE.info('Reloading SAML service provider configuration')
		sys.modules.pop(os.path.splitext(os.path.basename(cls.configfile))[0], None)
		try:
			cls.SP = Saml2Client(config_file=cls.configfile, identity_cache=cls.identity_cache, state_cache=shared_memory.saml_state_cache)
			return True
		except Exception:
			CORE.warn('Startup of SAML2.0 service provider failed:\n%s' % (traceback.format_exc(),))
		return False

	def get(self):
		binding, message, relay_state = self._get_saml_message()

		if message is None:
			return self.do_single_sign_on(relay_state=self.get_query_argument('location', '/univention/management/'))

		acs = self.attribute_consuming_service
		if relay_state == 'iframe-passive':
			acs = self.attribute_consuming_service_iframe
		acs(binding, message, relay_state)

	def post(self):
		return self.get()

	def attribute_consuming_service(self, binding, message, relay_state):
		response = self.acs(message, binding)
		saml = SAMLUser(response, message)
		# TODO/FIXME: do PAM auth here?!
		self.set_session(self.create_sessionid(), saml.username, saml=saml)
		self.current_user.authenticated = True
		# protect against javascript:alert('XSS'), mailto:foo and other non relative links!
		location = urlparse(relay_state)
		if location.path.startswith('//'):
			location = urlparse('')
		location = urlunsplit(('', '', location.path, location.query, location.fragment))
		self.redirect(location, status=303)

	def attribute_consuming_service_iframe(self, binding, message, relay_state):
		self.request.headers['Accept'] = 'application/json'  # enforce JSON response in case of errors
		self.request.headers['X-Iframe-Response'] = 'true'  # enforce textarea wrapping
		response = self.acs(message, binding)
		saml = SAMLUser(response, message)
		sessionid = self.create_sessionid()
		# TODO/FIXME: do PAM auth here?!
		self.set_session(sessionid, saml.username, saml=saml)
		self.current_user.authenticated = True
		self.set_header('Content-Type', 'text/html')
		data = {"status": 200, "result": {"username": saml.username}}
		self.finish(b'<html><body><textarea>%s</textarea></body></html>' % (json.dumps(data).encode('ASCII'),))

	def _logout_success(self):
		user = self.current_user
		if user:
			user.saml = None
		self.redirect('/univention/logout', status=303)

	def _get_saml_message(self):
		"""Get the SAML message and corresponding binding from the HTTP request"""
		if self.request.method not in ('GET', 'POST'):
			self.set_header('Allow', 'GET, HEAD, POST')
			raise HTTPError(405)

		if self.request.method == 'GET':
			binding = BINDING_HTTP_REDIRECT
			args = self.request.query_arguments
		elif self.request.method == "POST":
			binding = BINDING_HTTP_POST
			args = self.request.body_arguments

		relay_state = args.get('RelayState', [b''])[0].decode('UTF-8')
		try:
			message = args['SAMLResponse'][0].decode('UTF-8')
		except KeyError:
			try:
				message = args['SAMLRequest'][0].decode('UTF-8')
			except KeyError:
				try:
					message = args['SAMLart'][0].decode('UTF-8')
				except KeyError:
					return None, None, None
				message = self.sp.artifact2message(message, 'spsso')
				binding = BINDING_HTTP_ARTIFACT

		return binding, message, relay_state

	def acs(self, message, binding):  # attribute consuming service  # TODO: rename into parse
		try:
			response = self.sp.parse_authn_request_response(message, binding, self.outstanding_queries)
		except (UnknownPrincipal, UnsupportedBinding, VerificationError, UnsolicitedResponse, StatusError, MissingKey, SignatureError):
			raise SamlError().from_exception(*sys.exc_info())
		if response is None:
			raise SamlError().unparsed_saml_response()
		self.outstanding_queries.pop(response.in_response_to, None)
		return response

	def do_single_sign_on(self, **kwargs):
		binding, http_args = self.create_authn_request(**kwargs)
		self.http_response(binding, http_args)

	def create_authn_request(self, **kwargs):
		"""Creates the SAML <AuthnRequest> request and returns the SAML binding and HTTP response.

			Returns (binding, http-arguments)
		"""
		identity_provider_entity_id = self.select_identity_provider()
		binding, destination = self.get_identity_provider_destination(identity_provider_entity_id)

		relay_state = kwargs.pop('relay_state', None)

		reply_binding, service_provider_url = self.select_service_provider()
		sid, message = self.sp.create_authn_request(destination, binding=reply_binding, assertion_consumer_service_urls=(service_provider_url,), **kwargs)

		http_args = self.sp.apply_binding(binding, message, destination, relay_state=relay_state)
		self.outstanding_queries[sid] = service_provider_url  # self.request.full_url()  # TODO: shouldn't this contain service_provider_url?
		return binding, http_args

	def select_identity_provider(self):
		"""Select an identity provider based on the available identity providers.
			If multiple IDP's are set up the client might have specified one in the query string.
			Otherwise an error is raised where the user can choose one.

			Returns the EntityID of the IDP.
		"""
		idps = self.sp.metadata.with_descriptor("idpsso")
		if not idps and self.reload():
			idps = self.sp.metadata.with_descriptor("idpsso")
		if self.get_query_argument(self.idp_query_param, None) in idps:
			return self.get_query_argument(self.idp_query_param)
		if len(idps) == 1:
			return list(idps.keys())[0]
		if not idps:
			raise SamlError().no_identity_provider()
		raise SamlError().multiple_identity_provider(list(idps.keys()), self.idp_query_param)

	def get_identity_provider_destination(self, entity_id):
		"""Get the destination (with SAML binding) of the specified entity_id.

			Returns (binding, destination-URI)
		"""
		return self.sp.pick_binding("single_sign_on_service", self.bindings, "idpsso", entity_id=entity_id)

	def select_service_provider(self):
		"""Select the ACS-URI and binding of this service provider based on the request uri.
			Tries to preserve the current scheme (HTTP/HTTPS) and netloc (host/IP) but falls back to FQDN if it is not set up.

			Returns (binding, service-provider-URI)
		"""
		acs = self.sp.config.getattr("endpoints", "sp")["assertion_consumer_service"]
		service_url, reply_binding = acs[0]
		netloc = False
		p2 = urlparse(self.request.full_url())
		for _url, _binding in acs:
			p1 = urlparse(_url)
			if p1.scheme == p2.scheme and p1.netloc == p2.netloc:
				netloc = True
				service_url, reply_binding = _url, _binding
				if p1.path == p2.path:
					break
			elif not netloc and p1.netloc == p2.netloc:
				service_url, reply_binding = _url, _binding
		CORE.info('SAML: picked %r for %r with binding %r' % (service_url, self.request.full_url(), reply_binding))
		return reply_binding, service_url

	def http_response(self, binding, http_args):
		"""Converts the HTTP arguments from pysaml2 into the tornado response."""
		body = u''.join(http_args["data"])
		for key, value in http_args["headers"]:
			self.set_header(key, value)

		if binding in (BINDING_HTTP_ARTIFACT, BINDING_HTTP_REDIRECT):
			self.set_status(303 if self.request.supports_http_1_1() and self.request.method == 'POST' else 302)
			if not body:
				self.redirect(self._headers['Location'], status=self.get_status())
				return

		self.finish(body.encode('UTF-8'))


class SamlIframeACS(SamlACS):
	"""Passive SAML authentication via hidden iframe"""

	def get(self):
		self.do_single_sign_on(is_passive='true', relay_state='iframe-passive')


class SamlSingleLogout(SamlACS):
	"""SAML Single Logout by IDP"""

	def get(self, *args, **kwargs):  # single logout service
		binding, message, relay_state = self._get_saml_message()
		if message is None:
			raise HTTPError(400, 'The HTTP request is missing required SAML parameter.')

		try:
			is_logout_request = b'LogoutRequest' in zlib.decompress(base64.b64decode(message.encode('UTF-8')), -15).split(b'>', 1)[0]
		except Exception:
			CORE.error(traceback.format_exc())
			is_logout_request = False

		if is_logout_request:
			user = self.current_user
			if not user or user.saml is None:
				# The user is either already logged out or has no cookie because he signed in via IP and gets redirected to the FQDN
				name_id = None
			else:
				name_id = user.saml.name_id
				user.saml = None
			http_args = self.sp.handle_logout_request(message, name_id, binding, relay_state=relay_state)
			self.expire_session()
			self.http_response(binding, http_args)
			return
		else:
			response = self.sp.parse_logout_request_response(message, binding)
			self.sp.handle_logout_response(response)
		self._logout_success()


class SamlLogout(SamlACS):
	"""Initiate SAML Logout at the IDP"""

	def get(self):
		user = self.current_user

		if user is None or user.saml is None:
			return self._logout_success()

		# What if more than one
		try:
			data = self.sp.global_logout(user.saml.name_id)
		except KeyError:
			try:
				tb = sys.exc_info()[2]
				while tb.tb_next:
					tb = tb.tb_next
				if tb.tb_frame.f_code.co_name != 'entities':
					raise
			finally:
				tb = None
			# already logged out or UMC-Webserver restart
			user.saml = None
			data = {}

		for entity_id, logout_info in data.items():
			if not isinstance(logout_info, tuple):
				continue  # result from logout, should be OK

			binding, http_args = logout_info
			if binding not in (BINDING_HTTP_POST, BINDING_HTTP_REDIRECT):
				raise SamlError().unknown_logout_binding(binding)

			self.http_response(binding, http_args)
			return
		self._logout_success()
