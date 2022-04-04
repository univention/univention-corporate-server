#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  UMC server
#
# Copyright 2006-2022 Univention GmbH
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

from __future__ import division

import os
import sys
import time
import json
import zlib
import base64
import signal
import logging
import tempfile
import traceback
import threading
from argparse import ArgumentParser
from six.moves.urllib_parse import urlparse, urlunsplit
from six.moves.http_client import REQUEST_ENTITY_TOO_LARGE, LENGTH_REQUIRED, NOT_FOUND, BAD_REQUEST, UNAUTHORIZED, SERVICE_UNAVAILABLE

import six
import setproctitle
from ipaddress import ip_address
from tornado.web import Application as TApplication, HTTPError
from tornado.httpserver import HTTPServer
from tornado.netutil import bind_sockets
import tornado
from concurrent.futures import ThreadPoolExecutor

from univention.management.console.protocol.session import Resource, Auth, Upload, Command, UCR, Meta, Info, Modules, Categories, UserPreferences, Hosts, Set, SetPassword, SetLocale, SetUserPreferences
from univention.management.console.log import CORE, log_init, log_reopen
from univention.management.console.config import ucr, get_int
from univention.management.console.shared_memory import shared_memory

from saml2 import BINDING_HTTP_POST, BINDING_HTTP_ARTIFACT, BINDING_HTTP_REDIRECT
from saml2.client import Saml2Client
from saml2.metadata import create_metadata_string
from saml2.response import VerificationError, UnsolicitedResponse, StatusError
from saml2.s_utils import UnknownPrincipal, UnsupportedBinding
from saml2.sigver import MissingKey, SignatureError
from saml2.ident import code as encode_name_id

from univention.lib.i18n import NullTranslation

try:
	from time import monotonic
except ImportError:
	from monotonic import monotonic

_ = NullTranslation('univention-management-console-frontend').translate

_session_timeout = get_int('umc/http/session/timeout', 300)

REQUEST_ENTITY_TOO_LARGE, LENGTH_REQUIRED, NOT_FOUND, BAD_REQUEST, UNAUTHORIZED, SERVICE_UNAVAILABLE = int(REQUEST_ENTITY_TOO_LARGE), int(LENGTH_REQUIRED), int(NOT_FOUND), int(BAD_REQUEST), int(UNAUTHORIZED), int(SERVICE_UNAVAILABLE)

pool = ThreadPoolExecutor(max_workers=get_int('umc/http/maxthreads', 35))
TEMPUPLOADDIR = '/var/tmp/univention-management-console-frontend'

if 422 not in tornado.httputil.responses:
	tornado.httputil.responses[422] = 'Unprocessable Entity'  # Python 2 is missing this status code


class NotFound(HTTPError):

	def __init__(self):
		super(NotFound, self).__init__(404)


class UploadManager(dict):
	"""Store file uploads in temporary files so that module processes can access them"""

	def add(self, request_id, store):
		with tempfile.NamedTemporaryFile(prefix=request_id, dir=TEMPUPLOADDIR, delete=False) as tmpfile:
			tmpfile.write(store['body'])
		self.setdefault(request_id, []).append(tmpfile.name)

		return tmpfile.name

	def cleanup(self, request_id):
		if request_id in self:
			filenames = self[request_id]
			for filename in filenames:
				if os.path.isfile(filename):
					os.unlink(filename)
			del self[request_id]
			return True

		return False


_upload_manager = UploadManager()


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


class Application(TApplication):
	"""The tornado application with all UMC resources"""

	def __init__(self, **kwargs):
		tornado.locale.load_gettext_translations('/usr/share/locale', 'univention-management-console')
		super(Application, self).__init__([
			#(r'/auth/sso', AuthSSO),
			(r'/auth/?', Auth),
			(r'/upload/', Upload),
			(r'/(upload)/(.+)', Command),
			(r'/(command)/(.+)', Command),
			(r'/get/session-info', SessionInfo),
			(r'/get/ipaddress', GetIPAddress),
			(r'/get/ucr', UCR),
			(r'/get/meta', Meta),
			(r'/get/info', Info),
			(r'/get/modules', Modules),
			(r'/get/categories', Categories),
			(r'/get/user/preferences', UserPreferences),
			(r'/get/hosts', Hosts),
			(r'/set/?', Set),
			(r'/set/password', SetPassword),
			(r'/set/locale', SetLocale),
			(r'/set/user/preferences', SetUserPreferences),
			(r'/saml/', SamlACS),
			(r'/saml/metadata', SamlMetadata),
			(r'/saml/slo/?', SamlSingleLogout),
			(r'/saml/logout', SamlLogout),
			(r'/saml/iframe/?', SamlIframeACS),
			(r'/', Index),
			(r'/logout', Logout),
		], default_handler_class=Nothing, **kwargs)

		SamlACS.reload()


class Index(Resource):
	"""Redirect to correct path when bypassing gateway"""

	def get(self):
		self.redirect('/univention/', status=305)

	def post(self, path):
		return self.get(path)


class Logout(Resource):
	"""Logout a user"""

	def get(self, **kwargs):
		session = self.current_user
		if session.saml is not None:
			return self.redirect('/univention/saml/logout', status=303)
		self.expire_session()
		self.redirect(ucr.get('umc/logout/location') or '/univention/', status=303)

	def post(self, path):
		return self.get(path)


class Nothing(Resource):

	def prepare(self, *args, **kwargs):
		super(Nothing, self).prepare(*args, **kwargs)
		raise NotFound()


class SessionInfo(Resource):
	"""Get information about the current session"""

	def get(self):
		info = {}
		session = self.current_user
		if not session.authenticated:
			raise HTTPError(UNAUTHORIZED)
		info['username'] = session.user.username
		info['auth_type'] = session.get_umc_auth_type()  # prior: session.saml and 'SAML'
		info['remaining'] = int(session.session_end_time - monotonic())
		self.content_negotiation(info)

	def post(self):
		return self.get()


class GetIPAddress(Resource):
	"""Get the most likely IP address of the client"""

	def get(self):
		try:
			addresses = self.addresses
		except ValueError:
			# hacking attempt
			addresses = [self.request.remote_ip]
		self.content_negotiation(addresses, False)

	@property
	def addresses(self):
		addresses = self.request.headers.get('X-Forwarded-For', self.request.remote_ip).split(',') + [self.request.remote_ip]
		addresses = set(ip_address(x.decode('ASCII', 'ignore').strip() if isinstance(x, bytes) else x.strip()) for x in addresses)
		addresses.discard(ip_address(u'::1'))
		addresses.discard(ip_address(u'127.0.0.1'))
		return tuple(address.exploded for address in addresses)

	def post(self):
		return self.get()


class CPCommand(Resource):

	def post(self, path):
		return self.get(path)

	def get_request(self, path, args):
		if self._is_file_upload():
			return self.get_request_upload(path, args)

		if not path:
			raise HTTPError(NOT_FOUND)

		req = Request('COMMAND', [path], options=args.get('options', {}))
		if 'flavor' in args:
			req.flavor = args['flavor']

		return req

	def get_response(self, sessionid, path, args):
		response = super(CPCommand, self).get_response(sessionid, path, args)

		# check if the request is a iframe upload
		if 'X-Iframe-Response' in self.request.headers:
			# this is a workaround to make iframe uploads work, they need the textarea field
			self.set_header('Content-Type', 'text/html')
			return '<html><body><textarea>%s</textarea></body></html>' % (response)

		return response

	def get_request_upload(self, path, args):
		CORE.info('Handle upload command')
		self.request.headers['Accept'] = 'application/json'  # enforce JSON response in case of errors
		if args.get('options', {}).get('iframe', False) not in ('false', False, 0, '0'):
			self.request.headers['X-Iframe-Response'] = 'true'  # enforce textarea wrapping
		req = Request('UPLOAD', arguments=[path or ''])
		req.body = self._get_upload_arguments(req)
		return req

	def _is_file_upload(self):
		return self.request.headers.get('Content-Type', '').startswith('multipart/form-data')

	def _get_upload_arguments(self, req):
		options = []
		body = {}

		# check if enough free space is available
		min_size = get_int('umc/server/upload/min_free_space', 51200)  # kilobyte
		s = os.statvfs(TEMPUPLOADDIR)
		free_disk_space = s.f_bavail * s.f_frsize // 1024  # kilobyte
		if free_disk_space < min_size:
			CORE.error('there is not enough free space to upload files')
			raise HTTPError(BAD_REQUEST, 'There is not enough free space on disk')

		for name, field in self.request.files.items():
			for part in field:
				tmpfile = _upload_manager.add(req.id, part)
				options.append(self._sanitize_file(tmpfile, name, part))

		for name in self.request.body_arguments:
			value = self.get_body_arguments(name)
			if len(value) == 1:
				value = value[0]
			body[name] = value

		body['options'] = options
		return body

	def _sanitize_file(self, tmpfile, name, store):
		# check if filesize is allowed
		st = os.stat(tmpfile)
		max_size = get_int('umc/server/upload/max', 64) * 1024
		if st.st_size > max_size:
			CORE.warn('file of size %d could not be uploaded' % (st.st_size))
			raise HTTPError(BAD_REQUEST, 'The size of the uploaded file is too large')

		filename = store['filename']
		# some security
		for c in '<>/':
			filename = filename.replace(c, '_')

		return {
			'filename': filename,
			'name': name,
			'tmpfile': tmpfile,
			'content_type': store['content_type'],
		}


#class AuthSSO(Resource):
#
#	def parse_authorization(self):
#		return  # do not call super method: prevent basic auth
#
#	def get(self):
#		CORE.info('/auth/sso: got new auth request')
#
#		user = self.get_user()
#		if not user or not user.saml or user.timed_out(monotonic()):
#			# redirect user to login page in case he's not authenticated or his session timed out
#			self.redirect('/univention/saml/', status=303)
#			return
#
#		req = Request('AUTH')
#		req.body = {
#			"auth_type": "SAML",
#			"username": user.username,
#			"password": user.saml.message
#		}
#
#		try:
#			self._auth_request(req, user.sessionid)
#		except UMC_HTTPError as exc:
#			if exc.status == UNAUTHORIZED:
#				# slapd down, time synchronization between IDP and SP is wrong, etc.
#				CORE.error('SAML authentication failed: Make sure slapd runs and the time on the service provider and identity provider is identical.')
#				raise HTTPError(
#					500,
#					'The SAML authentication failed. This might be a temporary problem. Please login again.\n'
#					'Further information can be found in the following logfiles:\n'
#					'* /var/log/univention/management-console-web-server.log\n'
#					'* /var/log/univention/management-console-server.log\n'
#				)
#			raise
#
#		# protect against javascript:alert('XSS'), mailto:foo and other non relative links!
#		location = urlparse(self.get_query_argument('return', '/univention/management/'))
#		if location.path.startswith('//'):
#			location = urlparse('')
#		location = urlunsplit(('', '', location.path, location.query, location.fragment))
#		self.redirect(location, status=303)
#
#	def post(self):
#		return self.get()


class SAMLResource(Resource):
	"""Base class for all SAML resources"""

	SP = None
	identity_cache = '/var/cache/univention-management-console/saml.bdb'
	configfile = '/usr/share/univention-management-console/saml/sp.py'
	idp_query_param = "IdpQuery"
	bindings = [BINDING_HTTP_REDIRECT, BINDING_HTTP_POST, BINDING_HTTP_ARTIFACT]
	outstanding_queries = {}


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


class Server(object):
	"""univention-management-console-server"""

	def __init__(self):
		self.parser = ArgumentParser()
		self.parser.add_argument(
			'-d', '--debug', type=int, default=get_int('umc/server/debug/level', 1),
			help='if given than debugging is activated and set to the specified level [default: %(default)s]'
		)
		self.parser.add_argument(
			'-L', '--log-file', default='stdout',
			help='specifies an alternative log file [default: %(default)s]'
		)
		self.parser.add_argument(
			'-c', '--processes', default=get_int('umc/http/processes', 1), type=int,
			help='How many processes to start'
		)
		self.options = self.parser.parse_args()
		self._child_number = None

		# TODO? not really
		# os.environ['LANG'] = locale.normalize(self.options.language)

		# init logging
		log_init(self.options.log_file, self.options.debug, self.options.processes > 1)

	def signal_handler_hup(self, signo, frame):
		"""Handler for the reload action"""
		ucr.load()
		log_reopen()
		self._inform_childs(signal)
		print(''.join(['%s:\n%s' % (th, ''.join(traceback.format_stack(sys._current_frames()[th.ident]))) for th in threading.enumerate()]))

	def signal_handler_reload(self, signo, frame):
		log_reopen()
		SamlACS.reload()
		self._inform_childs(signal)

	def _inform_childs(self, signal):
		if self._child_number is not None:
			return  # we are the child process
		try:
			children = list(shared_memory.children.items())
		except EnvironmentError:
			children = []
		for child, pid in children:
			try:
				os.kill(pid, signal)
			except EnvironmentError as exc:
				CORE.process('Failed sending signal %d to process %d: %s' % (signal, pid, exc))

	def run(self):
		setproctitle.setproctitle('%s # /usr/sbin/univention-management-console-server' % (setproctitle.getproctitle(),))
		signal.signal(signal.SIGHUP, self.signal_handler_hup)
		signal.signal(signal.SIGUSR1, self.signal_handler_reload)

		sockets = bind_sockets(get_int('umc/http/port', 8090), ucr.get('umc/http/interface', '127.0.0.1'), backlog=get_int('umc/http/requestqueuesize', 100), reuse_port=True)
		if self.options.processes != 1:
			shared_memory.start()

			CORE.process('Starting with %r processes' % (self.options.processes,))
			try:
				self._child_number = tornado.process.fork_processes(self.options.processes, 0)
			except RuntimeError as exc:
				CORE.warn('Child process died: %s' % (exc,))
				os.kill(os.getpid(), signal.SIGTERM)
				raise SystemExit(str(exc))
			if self._child_number is not None:
				shared_memory.children[self._child_number] = os.getpid()

		application = Application(serve_traceback=ucr.is_true('umc/http/show_tracebacks', True))
		server = HTTPServer(
			application,
			idle_connection_timeout=get_int('umc/http/response-timeout', 310),  # is this correct? should be internal response timeout
			max_body_size=get_int('umc/http/max_request_body_size', 104857600),
		)
		self.server = server
		server.add_sockets(sockets)

		channel = logging.StreamHandler()
		channel.setFormatter(tornado.log.LogFormatter(fmt='%(color)s%(asctime)s  %(levelname)10s      (%(process)9d) :%(end_color)s %(message)s', datefmt='%d.%m.%y %H:%M:%S'))
		logger = logging.getLogger()
		logger.setLevel(logging.INFO)
		logger.addHandler(channel)

		ioloop = tornado.ioloop.IOLoop.current()

		try:
			ioloop.start()
		except Exception:
			CORE.error(traceback.format_exc())
			ioloop.stop()
			pool.shutdown(False)
			raise
		except (KeyboardInterrupt, SystemExit):
			ioloop.stop()
			pool.shutdown(False)


if __name__ == '__main__':
	Server().run()
