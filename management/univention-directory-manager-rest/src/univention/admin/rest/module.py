#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  Univention Directory Manager Module
#
# Copyright 2017-2019 Univention GmbH
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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import re
import io
import json
import time
import copy
import uuid
import zlib
import urllib
import base64
import httplib
import hashlib
import binascii
import datetime
import traceback
import functools
from email.utils import parsedate
from urlparse import urljoin, urlparse, urlunparse, parse_qs
from urllib import quote, unquote

import six

import tornado.web
import tornado.gen
import tornado.log
import tornado.ioloop
import tornado.httpclient
import tornado.httputil
from tornado.web import RequestHandler, HTTPError, Finish
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor

import ldap
from ldap.filter import filter_format
from ldap.dn import explode_rdn
from ldap.controls import SimplePagedResultsControl
from ldap.controls.sss import SSSRequestControl
import xml.etree.cElementTree as ET
import xml.dom.minidom
from genshi import XML
from genshi.output import HTMLSerializer

from univention.management.console.config import ucr
from univention.management.console.log import MODULE
from univention.management.console.ldap import get_user_connection, get_machine_connection
from univention.management.console.modules.udm.udm_ldap import get_module, UDM_Module, ldap_dn2path, read_syntax_choices, _get_syntax, container_modules, UDM_Error
from univention.management.console.modules.udm.udm_ldap import SuperordinateDoesNotExist, ObjectDoesNotExist, NoIpLeft, _object_property_filter
from univention.management.console.modules.udm.tools import check_license, LicenseError, LicenseImport as LicenseImporter, dump_license
from univention.management.console.modules.sanitizers import MultiValidationError, ValidationError, DictSanitizer, StringSanitizer, ListSanitizer, IntegerSanitizer, ChoicesSanitizer, DNSanitizer, EmailSanitizer, LDAPSearchSanitizer, Sanitizer, BooleanSanitizer
from univention.management.console.error import UMC_Error, LDAP_ServerDown, LDAP_ConnectionFailed, UnprocessableEntity

import univention.directory.reports as udr
import univention.admin.uexceptions as udm_errors
import univention.admin.modules as udm_modules
import univention.admin.syntax as udm_syntax
import univention.admin.types as udm_types
from univention.config_registry import handler_set

import univention.udm

from univention.lib.i18n import Translation
# FIXME: prevent in the javascript UMC module that navigation container query is called with container=='None'
# FIXME: it seems request.path contains the un-urlencoded path, could be security issue!
# TODO: 0f77c317e03844e8a16c484dde69abbcd2d2c7e3 is not integrated
# TODO: replace etree with genshi, etc.
# TODO: modify layout and properties for app-tabs
# TODO: loading the policies probably unnecessarily slows down things
# TODO: create a own translation domain for this file

_ = Translation('univention-management-console-module-udm').translate

MAX_WORKERS = 35

if 422 not in tornado.httputil.responses:
	tornado.httputil.responses[422] = 'Unprocessable Entity'  # Python 2 is missing this status code


def add_sanitizers(type_, sanitizers):
	def _decorator(method):
		setattr(method, 'sanitizers', getattr(method, 'sanitizers', {}))
		method.sanitizers[type_] = sanitizers
		return method
	return _decorator


def sanitize_body_arguments(**sanitizers):
	return add_sanitizers('body', sanitizers)


def sanitize_query_string(**sanitizers):
	return add_sanitizers('query', sanitizers)


class RequestSanitizer(DictSanitizer):

	def __init__(self, resource):
		sanitizers = getattr(getattr(resource, resource.request.method.lower()), 'sanitizers', {})
		super(RequestSanitizer, self).__init__({
			'query_string': QueryStringSanitizer(sanitizers.get('query', {}), required=True, further_arguments=['resource'], _copy_value=False),
			'body_arguments': DictSanitizer(sanitizers.get('body', {}), required=True, further_arguments=['resource'], _copy_value=False)
		}, further_arguments=['resource'], _copy_value=False)

	def sanitize(self, resource, *args, **kwargs):
		payload = {
			'query_string': resource.request.query_arguments or {},
			'body_arguments': resource.request.body_arguments or {},
			'__resource': resource,
			'__args': args,
			'__kwargs': kwargs,
		}
		if isinstance(payload['query_string'], dict):
			payload['query_string']['__resource'] = resource
		if isinstance(payload['body_arguments'], dict):
			payload['body_arguments']['__resource'] = resource
		value = super(RequestSanitizer, self).sanitize('request.arguments', {'request.arguments': payload, 'resource': resource})
		resource.request.query_arguments = value['query_string']
		resource.request.body_arguments = value['body_arguments']
		return value

	def _sanitize(self, value, name, further_arguments):
		return super(RequestSanitizer, self)._sanitize(value, name, further_arguments)


class DictSanitizer(DictSanitizer):

	def __init__(self, sanitizers, allow_other_keys=True, **kwargs):
		self.default_sanitizer = kwargs.get('default_sanitizer', None)
		self.key_sanitizer = kwargs.get('key_sanitizer', None)
		super(DictSanitizer, self).__init__(sanitizers, allow_other_keys=allow_other_keys, **kwargs)

	def _sanitize(self, value, name, further_arguments):
		if not isinstance(value, dict):
			self.raise_formatted_validation_error(_('Not a "dict"'), name, type(value).__name__)

		if not self.allow_other_keys and any(key not in self.sanitizers for key in value):
			self.raise_validation_error(_('Has more than the allowed keys'))

		altered_value = copy.deepcopy(value) if self._copy_value else value

		multi_error = MultiValidationError()
		for attr in set(value.keys() + self.sanitizers.keys()):
			sanitizer = self.sanitizers.get(attr, self.default_sanitizer)
			try:
				if self.key_sanitizer:
					attr = self.key_sanitizer.sanitize(attr, {attr: attr})
				if sanitizer:
					altered_value[attr] = sanitizer.sanitize(attr, value)
			except ValidationError as e:
				multi_error.add_error(e, attr)

		if multi_error.has_errors():
			raise multi_error

		return altered_value


class QueryStringSanitizer(DictSanitizer):

	def _sanitize(self, value, name, further_arguments):
		if isinstance(value, dict):
			for key, sanitizer in self.sanitizers.items():
				if len(value.get(key, [])) == 1 and not isinstance(sanitizer, ListSanitizer):
					value[key] = value[key][0]
				elif isinstance(sanitizer, DictSanitizer):
					value[key] = dict((k[len(key) + 1:-1], v[0]) for k, v in value.items() if k.startswith(key + '[') and k.endswith(']'))
					#value[key] = QueryStringSanitizer(sanitizer.sanitizers).sanitize(key, {key: value[key]})

		return super(QueryStringSanitizer, self)._sanitize(value, name, further_arguments)


class ObjectPropertySanitizer(StringSanitizer):

	def __init__(self, **kwargs):
		"""A LDAP attribute name.
			must at least be 1 character long.

			This sanitizer prevents LDAP search filter injections in the attribute name.

			TODO: in theory we should only allow existing searchable properties for the requested object type
		"""
		args = dict(
			minimum=0,
			regex_pattern=r'^[\w\d\-;]*$',
		)
		args.update(kwargs)
		StringSanitizer.__init__(self, **args)


class PropertiesSanitizer(DictSanitizer):

	def __init__(self, *args, **kwargs):
		super(PropertiesSanitizer, self).__init__({}, *args, default_sanitizer=PropertySanitizer(), **kwargs)

	def sanitize(self, resource, module, obj):
		# FIXME: for the automatic IP address assignment, we need to make sure that
		# the network is set before the IP address (see Bug #24077, comment 6)
		# The following code is a workaround to make sure that this is the
		# case, however, this should be fixed correctly.
		# This workaround has been documented as Bug #25163.
		def _tmp_cmp(i, j):
			if i[0] == 'network':
				return -1
			return 0
		properties = resource.request.body_arguments['properties']
		# TODO: add sanitizer for e.g. required properties (respect options!)

		# properties = dict(encode_properties(module, obj, properties))

		self.default_sanitizer._module = module
		self.default_sanitizer._obj = obj
		try:
			properties = super(PropertiesSanitizer, self).sanitize('properties', {'properties': properties})
		finally:
			self.default_sanitizer._module = None
			self.default_sanitizer._obj = None

		password_properties = module.password_properties
		for property_name, value in sorted(properties.items(), _tmp_cmp):
			if property_name in password_properties:
				MODULE.info('Setting password property %s' % (property_name,))
			else:
				MODULE.info('Setting property %s to %r' % (property_name, value))

			try:
				try:
					obj[property_name] = value
				except KeyError:
					if property_name != 'objectFlag':
						raise
				except udm_errors.valueMayNotChange:
					if obj[property_name] == value:  # UDM does not check equality before raising the exception
						continue
					raise udm_errors.valueMayNotChange()  # the original exception is ugly!
				except udm_errors.valueRequired:
					if value is None:
						# examples where this happens:
						# "password" of users/user: because password is required but on modify() None is send, which must not alter the current password
						# "unixhome" of users/user: is required, set to None in the request, the default value is set afterwards in create(). Bug #50053
						if property_name in password_properties:
							MODULE.info('Ignore unsetting password property %s' % (property_name,))
						else:
							current_value = obj.info.pop(property_name, None)
							MODULE.info('Unsetting property %s value %r' % (property_name, current_value))
						continue
					raise
			except (udm_errors.valueInvalidSyntax, udm_errors.valueError, udm_errors.valueMayNotChange, udm_errors.valueRequired, udm_errors.noProperty) as exc:
				multi_error = MultiValidationError()
				try:
					self.raise_formatted_validation_error(_('The property %(name)s has an invalid value: %(details)s'), property_name, value, details=str(UDM_Error(exc)))
				except ValidationError as exc:
					multi_error.add_error(exc, property_name)
					raise multi_error

		resource.request.body_arguments['properties'] = properties
		return properties


class PropertySanitizer(Sanitizer):

	def __init__(self, *args, **kwargs):
		self._module = None
		self._obj = None
		super(PropertySanitizer, self).__init__(*args, **kwargs)

	def _sanitize(self, value, name, further_arguments):
		property_obj = self._module.get_property(name)

		if property_obj is None:
			if name == 'objectFlag':
				return value  # not every object type has the extended attribute for objectFlag
			self.raise_validation_error(_('The %(module)s module has no property %(name)s.'), module=self._module.title)

		if not self._obj.has_property(name):
			return value  # value will not be set, so no validation is required

		codec = udm_types.TypeHint.detect(property_obj, name)
		try:
			return codec.encode_json(value)
		except udm_errors.valueError as exc:
			self.raise_validation_error(_('The property %(name)s has an invalid value: %(details)s'), details=str(exc))


class BoolSanitizer(ChoicesSanitizer):

	def __init__(self, **kwargs):
		super(BoolSanitizer, self).__init__(choices=['1', 'on', 'true', 'false', '0', 'off', '', None], **kwargs)

	def _sanitize(self, value, name, further_arguments):
		return super(BoolSanitizer, self)._sanitize(value, name, further_arguments) in ('1', 'on', 'true')


class LDAPFilterSanitizer(StringSanitizer):

	def _sanitize(self, value, name, further_arguments):
		value = super(LDAPFilterSanitizer, self)._sanitize(value, name, further_arguments)
		try:
			return udm_syntax.ldapFilter.parse(value)
		except udm_errors.valueError as exc:
			self.raise_validation_error(str(exc))


class DNSanitizer(DNSanitizer):

	base = ldap.dn.str2dn(ucr['ldap/base'].lower())
	baselen = len(base)

	def _sanitize(self, value, name, further_arguments):
		value = super(DNSanitizer, self)._sanitize(value, name, further_arguments)
		if value and ldap.dn.str2dn(value.lower())[-self.baselen:] != self.base:
			self.raise_validation_error(_('The ldap base is invalid. Use %(details)s.'), details=ldap.dn.dn2str(self.base))
		return value


class NotFound(HTTPError):

	def __init__(self, object_type=None, dn=None):
		super(NotFound, self).__init__(404, None, '%r %r' % (object_type, dn or ''))  # FIXME: create error message


def superordinate_names(module):
	superordinates = module.superordinate_names
	if set(superordinates) == {'settings/cn', }:
		return []
	return superordinates


class ResourceBase(object):

	pool = ThreadPoolExecutor(max_workers=MAX_WORKERS)

	requires_authentication = True
	authenticated = {}

	def force_authorization(self):
		self.set_header('WWW-Authenticate', 'Basic realm="Univention Management Console"')
		self.set_status(401)
		self.finish()

	def set_default_headers(self):
		self.set_header('Server', 'Univention/1.0')  # TODO:

	def prepare(self):
		self.request.content_negotiation_lang = 'html'
		self.request.path_decoded = urllib.unquote(self.request.path)
		authorization = self.request.headers.get('Authorization')
		if not authorization:
			if self.requires_authentication:
				return self.force_authorization()

		try:
			if authorization:
				self.parse_authorization(authorization)
		finally:
			self.request.content_negotiation_lang = self.check_acceptable()
			self.decode_request_arguments()
			self.sanitize_arguments(RequestSanitizer(self), self)

	def parse_authorization(self, authorization):
		if authorization in self.authenticated:
			(self.request.user_dn, self.request.username, self.ldap_connection, self.ldap_position) = self.authenticated[authorization]
			if self.ldap_connection.whoami():
				return  # the ldap connection is still valid and bound
		try:
			if not authorization.lower().startswith('basic '):
				raise ValueError()
			username, password = base64.decodestring(authorization.split(' ', 1)[1]).split(':', 1)
		except (ValueError, IndexError, binascii.Error):
			raise HTTPError(400)

		self.request.username = username
		try:
			self.request.user_dn = self._auth_get_userdn(username)
			self.ldap_connection, self.ldap_position = get_user_connection(bind=lambda lo: lo.bind(self.request.user_dn, password), write=True)
		except Exception:
			return self.force_authorization()

		if username not in ('cn=admin',):
			self._auth_check_allowed_groups()

		self.authenticated[authorization] = (self.request.user_dn, self.request.username, self.ldap_connection, self.ldap_position)

	def _auth_check_allowed_groups(self):
		allowed_groups = [value for key, value in ucr.items() if key.startswith('directory/manager/rest/authorized-groups/')]
		memberof = self.ldap_connection.getAttr(self.request.user_dn, b'memberOf')
		if not set(_map_normalized_dn(memberof)) & set(_map_normalized_dn(allowed_groups)):
			raise HTTPError(403, 'Not in allowed groups.')

	def _auth_get_userdn(self, username):
		if username in ('cn=admin',):
			return 'cn=admin,%(ldap/base)s' % ucr
		lo, po = get_machine_connection(write=False)
		return lo.searchDn(filter_format('(&(objectClass=person)(uid=%s))', [username]), unique=True)[0]

	def get_module(self, object_type):
		module = UDM_Module(object_type, ldap_connection=self.ldap_connection, ldap_position=self.ldap_position)
		if not module or not module.module:
			raise NotFound(object_type)
		return module

	def get_object(self, object_type, dn):
		module = self.get_module(object_type)
		obj = module.get(dn)
		if not obj:
			raise NotFound(object_type, dn)
		return obj

	def check_acceptable(self):
		accept = self.request.headers.get('Accept', 'text/html').split(',')
		langs = []
		for language in accept:
			score = 1.0
			parts = language.strip().split(";")
			for part in (x for x in parts[1:] if x.strip().startswith("q=")):
				try:
					score = float(part.strip()[2:])
					break
				except (ValueError, TypeError):
					raise
					score = 0.0
			langs.append((parts[0].strip(), score))
		langs.sort(key=lambda pair: pair[1], reverse=True)
		lang = None
		for name, q in langs:
			if q <= 0:
				continue
			if name in ('text/html', 'text/xml', 'application/xml', 'text/*', '*/*'):
				lang = 'html'
				break
			elif name in ('application/hal+json', 'application/*'):
				lang = 'hal_json'
				break
			elif name in ('application/json',):
				lang = 'json'
				break
		if not lang:
			raise HTTPError(406)
		return lang

	def decode_request_arguments(self):
		content_type = self.request.headers.get('Content-Type', '')
		if self.request.method in ('HEAD', 'GET', 'OPTIONS', 'DELETE'):
			if self.request.body:
				raise HTTPError(400, 'Safe HTTP method should not contain request body/Content-Type header.')
			return

		if content_type.startswith('application/json'):
			try:
				self.request.body_arguments = json.loads(self.request.body)
			except ValueError as exc:
				raise HTTPError(400, _('Invalid JSON document: %r') % (exc,))
		elif content_type.startswith('application/x-www-form-urlencoded') or content_type.startswith('multipart/form-data'):
			self.decode_form_arguments()

	def decode_form_arguments(self):
		pass

	def get_body_argument(self, name, *args):
		if self.request.headers.get('Content-Type', '').startswith('application/json'):
			return self.request.body_arguments.get(name)
		return super(ResourceBase, self).get_body_argument(name, *args)

	def get_body_arguments(self, name, *args):
		if self.request.headers.get('Content-Type', '').startswith('application/json'):
			return self.request.body_arguments.get(name)
		return super(ResourceBase, self).get_body_arguments(name, *args)

	def sanitize_arguments(self, sanitizer, *args, **kwargs):
		try:
			field = kwargs.pop('_fieldname', 'request.arguments')
			try:
				return sanitizer.sanitize(*args, **kwargs)
			except MultiValidationError:
				raise
			except ValidationError as exc:
				multi_error = MultiValidationError()
				multi_error.add_error(exc, field)
				raise multi_error
		except MultiValidationError as e:
			raise UnprocessableEntity(str(e), result=e.result())

	def raise_sanitization_error(self, field, message):
		class FalseSanitizer(Sanitizer):
			def sanitize(self):
				self.raise_formatted_validation_error('%(message)s', field, None, message=message)
		self.sanitize_arguments(FalseSanitizer(), _fieldname=field)

	def content_negotiation(self, response):
		self.add_header('Vary', ', '.join(self.vary()))
		lang = self.request.content_negotiation_lang
		formatter = getattr(self, '%s_%s' % (self.request.method.lower(), lang), getattr(self, 'get_%s' % (lang,)))
		codec = getattr(self, 'content_negotiation_%s' % (lang,))
		self.finish(codec(formatter(response)))

	def content_negotiation_json(self, response):
		self.set_header('Content-Type', 'application/json')
		return json.dumps(response)

	def content_negotiation_hal_json(self, response):
		self.set_header('Content-Type', 'application/hal+json')
		return json.dumps(response)

	def content_negotiation_html(self, response):
		self.set_header('Content-Type', 'text/html; charset=UTF-8')
		ajax = self.request.headers.get('X-Requested-With', '').lower() == 'xmlhttprequest'

		root = ET.Element("html")
		head = ET.SubElement(root, "head")
		titleelement = ET.SubElement(head, "title")
		titleelement.text = 'FIXME: fallback title'  # FIXME: set title
		ET.SubElement(head, 'meta', content='text/html; charset=utf-8', **{'http-equiv': 'content-type'})
		#if not ajax:
		#	ET.SubElement(head, 'script', type='text/javascript', src=self.abspath('../js/config.js'))
		#	ET.SubElement(head, 'script', type='text/javascript', src=self.abspath('js/udm.js'))
		#	ET.SubElement(head, 'script', type='text/javascript', async='', src=self.abspath('../js/dojo/dojo.js'))

		body = ET.SubElement(root, "body", dir='ltr')
		header = ET.SubElement(body, 'header')
		topnav = ET.SubElement(header, 'nav')
		h1 = ET.SubElement(topnav, 'h1', id='logo')
		home = ET.SubElement(h1, 'a', rel='home', href=self.abspath('/'))
		home.text = ' '
		nav = ET.SubElement(body, 'nav')
		links = ET.SubElement(nav, 'ul')
		main = ET.SubElement(body, 'main')
		_links = {}
		navigation_relations = self.navigation()
		for link in self._headers.get_list('Link'):
			link, foo, _params = link.partition(';')
			link = link.strip().lstrip('<').rstrip('>')
			params = {}
			if _params.strip():
				params = dict((x.strip(), y.strip().strip('"').replace('\\"', '"').replace('\\\\', '\\')) for x, y in ((param.split('=', 1) + [''])[:2] for param in _params.split(';')))
			ET.SubElement(head, "link", href=link, **params)
			_links[params.get('rel')] = dict(params, href=link)
			if params.get('rel') == 'self':
				titleelement.text = params.get('title') or link or 'FIXME:notitle'
			if params.get('rel') in ('stylesheet', 'icon', 'self', 'up', 'udm:object/remove', 'udm:object/edit'):
				continue
			if params.get('rel') in navigation_relations:
				continue
			if params.get('rel') in ('udm:user-photo',):
				ET.SubElement(nav, 'img', src=link, style='max-width: 200px')
				continue
			elif params.get('rel') in ('create-form', 'edit-form'):
				ET.SubElement(ET.SubElement(nav, 'form'), 'button', formaction=link, **params).text = params.get('title', link)
				continue
			#if params.get('rel') in ('udm:tree',):
			#	self.set_header('X-Frame-Options', 'SAMEORIGIN')
			#	body.insert(1, ET.Element('iframe', src=link, name='tree'))
			#	continue
			li = ET.SubElement(links, "li")
			ET.SubElement(li, "a", href=link, **params).text = params.get('title', link) or link

		for name in navigation_relations:
			params = _links.get(name)
			if params:
				ET.SubElement(topnav, 'a', **params).text = '›› %s' % (params.get('title') or params['href'],)

		if isinstance(response, (list, tuple)):
			main.extend(response)
		elif response is not None:
			main.append(response)

		if not ajax:
			stream = XML(xml.dom.minidom.parseString(ET.tostring(root, encoding='utf-8', method='xml')).toprettyxml())
			self.write(''.join((HTMLSerializer('html5')(stream))))
		else:
			self.write('<!DOCTYPE html>\n')
			tree = ET.ElementTree(main if ajax else root)
			tree.write(self)

	def get_hal_json(self, response):
		response.setdefault('_links', {})
		response.setdefault('_embedded', {})
		return self.get_json(response)

	def get_json(self, response):
		self.add_link(response, 'curies', self.abspath('relation/') + '{rel}', name='udm', templated=True)
		response.get('_embedded', {}).pop('udm:form', None)  # no public API, just to render html
		response.get('_embedded', {}).pop('udm:layout', None)  # save traffic, just to render html
		response.get('_embedded', {}).pop('udm:properties', None)  # save traffic, just to render html
		return response

	def get_html(self, response):
		root = []
		if isinstance(response, dict):
			self.add_link(response, 'stylesheet', self.abspath('css/style.css'))

			for _form in self.get_resources(response, 'udm:form'):
				root.insert(0, self.get_html_form(_form, response))

			if isinstance(response.get('error'), dict) and response['error'].get('code', 0) >= 400:
				error = ET.Element('div')
				root.append(error)
				ET.SubElement(error, 'h1').text = _('HTTP-Error %d: %s') % (response['error']['code'], response['error']['title'])
				ET.SubElement(error, 'p', style='white-space: pre').text = response['error']['message']
				if response['error'].get('traceback'):
					ET.SubElement(error, 'pre').text = response['error']['traceback']
				response = None

		if isinstance(response, (list, tuple)):
			print('WARNING: uses deprecated LIST response')
			for thing in response:
				pre = ET.Element("pre")
				pre.text = json.dumps(thing, indent=4)
				root.append(pre)
				root.append(ET.Element("br"))
		elif isinstance(response, dict):
			r = response.copy()
			r.pop('_links', None)
			r.pop('_embedded', None)
			if r:
				pre = ET.Element("pre")
				pre.text = json.dumps(r, indent=4)
				root.append(pre)
		return root

	def get_html_layout(self, root, layout, properties):
		for sec in layout:
			section = ET.SubElement(root, 'section')
			ET.SubElement(section, 'h1').text = sec['label']
			if sec.get('help'):
				ET.SubElement(section, 'span').text = sec['help']
			fieldset = ET.SubElement(section, 'fieldset')
			ET.SubElement(fieldset, 'legend').text = sec['description']
			self.render_layout(sec['layout'], fieldset, properties)
		return root

	def render_layout(self, layout, fieldset, properties):
		for elem in layout:
			if isinstance(elem, dict):
				sub_fieldset = ET.SubElement(fieldset, 'details', open='open')
				ET.SubElement(sub_fieldset, 'summary').text = elem['label']
				if elem['description']:
					ET.SubElement(sub_fieldset, 'h2').text = elem['description']
				self.render_layout(elem['layout'], sub_fieldset, properties)
				continue
			elements = [elem] if isinstance(elem, six.string_types) else elem
			for elem in elements:
				for field in properties:
					if field['name'] in (elem, 'properties.%s' % elem):
						self.render_form_field(fieldset, field)
			if elements:
				ET.SubElement(fieldset, 'br')

	def get_html_form(self, _form, response):
		form = ET.Element('form', **dict((p, _form[p]) for p in ('id', 'class', 'name', 'method', 'action', 'rel', 'enctype', 'accept-charset', 'novalidate') if _form.get(p)))
		if _form.get('layout'):
			layout = self.get_resource(response, 'udm:layout', name=_form['layout'])
			self.get_html_layout(form, layout['layout'], _form.get('fields'))
			return form

		for field in _form.get('fields', []):
			self.render_form_field(form, field)
			form.append(ET.Element('br'))
		form.append(ET.Element('hr'))
		return form

	def render_form_field(self, form, field):
		datalist = None
		name = field['name']

		if field.get('type') == 'submit' and field.get('add_noscript_warning'):
			ET.SubElement(ET.SubElement(form, 'noscript'), 'p').text = _('This form requires JavaScript enabled!')

		label = ET.Element('label', **{'for': name})
		label.text = field.get('label', name)

		multivalue = field.get('data-multivalue') == '1'
		values = field['value'] or [''] if multivalue else [field['value']]
		for value in values:
			elemattrs = dict((p, field[p]) for p in ('id', 'disabled', 'form', 'multiple', 'required', 'size', 'type', 'placeholder', 'accept', 'alt', 'autocomplete', 'checked', 'max', 'min', 'minlength', 'pattern', 'readonly', 'src', 'step', 'style', 'alt', 'autofocus', 'class', 'cols', 'href', 'rel', 'title', 'list') if field.get(p))
			elemattrs.setdefault('type', 'text')
			elemattrs.setdefault('placeholder', name)
			if field.get('type') == 'checkbox' and field.get('checked'):
				elemattrs['checked'] = 'checked'
			element = ET.Element(field.get('element', 'input'), name=name, value=str(value), **elemattrs)

			if field['element'] == 'select':
				for option in field.get('options', []):
					kwargs = {}
					if field['value'] == option['value'] or (isinstance(field['value'], list) and option['value'] in field['value']):
						kwargs['selected'] = 'selected'
					ET.SubElement(element, 'option', value=option['value'], **kwargs).text = option.get('label', option['value'])
			elif field.get('element') == 'a':
				element.text = field['label']
				label = None
			elif field.get('list') and field.get('datalist'):
				datalist = ET.Element('datalist', id=field['list'])
				for option in field.get('datalist', []):
					kwargs = {}
					if field['value'] == option['value'] or (isinstance(field['value'], list) and option['value'] in field['value']):
						kwargs['selected'] = 'selected'
					ET.SubElement(datalist, 'option', value=option['value'], **kwargs).text = option.get('label', option['value'])
			if label is not None:
				form.append(label)
				label = None
			if datalist is not None:
				form.append(datalist)
			form.append(element)
			if multivalue:
				btn = ET.Element('button')
				btn.text = '-'
				form.append(btn)
		if multivalue:
			btn = ET.Element('button')
			btn.text = '+'
			form.append(btn)

	def urljoin(self, *args, **query):
		base = urlparse(self.request.full_url())
		query_string = ''
		if query:
			qs = parse_qs(base.query)
			qs.update(dict((key, val if isinstance(val, (list, tuple)) else [val]) for key, val in query.items()))
			query_string = '?%s' % (urllib.urlencode(qs, True),)
		scheme = base.scheme
		for _scheme in self.request.headers.get_list('X-Forwarded-Proto'):
			if _scheme == 'https':
				scheme = 'https'
				break
			if _scheme == 'http':
				scheme = 'http'
		return urljoin(urljoin(urlunparse((scheme, base.netloc, 'univention/' if self.request.headers.get('X-Forwarded-Host') else '/', '', '', '')), quote(self.request.path_decoded.lstrip('/'))), '/'.join(args)) + query_string

	def abspath(self, *args):
		return urljoin(self.urljoin('/univention/udm/' if self.request.headers.get('X-Forwarded-Host') else '/udm/'), '/'.join(args))

	def add_link(self, obj, relation, href, **kwargs):
		dont_set_http_header = kwargs.pop('dont_set_http_header', False)
		links = obj.setdefault('_links', {})
		links.setdefault(relation, []).append(dict(kwargs, href=href))
		if dont_set_http_header:
			return

		def quote_param(s):
			for i in range(32):  # remove non printable characters
				s = s.replace(unichr(i), '')
			return s.replace('\\', '\\\\').replace('"', '\\"')
		kwargs['rel'] = relation
		params = []
		for param in ('rel', 'name', 'title', 'media'):
			if param in kwargs:
				params.append('%s="%s"' % (param, quote_param(kwargs.get(param, ''))))
		del kwargs['rel']
		header_name = 'Link-Template' if kwargs.get('templated') else 'Link'
		self.add_header(header_name, '<%s>; %s' % (href, '; '.join(params)))

	def add_resource(self, obj, relation, ressource):
		obj.setdefault('_embedded', {}).setdefault(relation, []).append(ressource)

	def get_resource(self, obj, relation, name=None):
		for resource in obj.get('_embedded', {}).get(relation, []):
			if not name:
				return resource
			if resource.get('_links', {}).get('self', [{}])[0].get('name') == name:
				return resource

	def get_resources(self, obj, relation):
		return obj.get('_embedded', {}).get(relation, [])

	def add_form(self, obj, action, method, **kwargs):
		form = {
			'action': action,
			'method': method,
		}
		form.setdefault('enctype', 'application/x-www-form-urlencoded')
		form.update(kwargs)
		self.add_resource(obj, 'udm:form', form)
		return form

	def add_form_element(self, form, name, value, type='text', element='input', **kwargs):
		field = {
			'name': name,
			'value': value,
			'type': type,
			'element': element,
		}
		field.update(kwargs)
		form.setdefault('fields', []).append(field)
		if field['type'] == 'submit':
			field['add_noscript_warning'] = form.get('method') not in ('GET', 'POST', None)
		return field

	def add_layout(self, obj, layout, name=None, href=None):
		self.add_resource(obj, 'udm:layout', {'_links': {'self': [{'name': name}]}, 'layout': layout})
		if href:
			self.add_link(obj, 'udm:layout', href=href, name=name)

	def log_exception(self, typ, value, tb):
		if isinstance(value, UMC_Error):
			return
		super(ResourceBase, self).log_exception(typ, value, tb)

	def write_error(self, status_code, exc_info=None, **kwargs):
		if not exc_info:  # or isinstance(exc_info[1], HTTPError):
			return super(ResourceBase, self).write_error(status_code, exc_info=exc_info, **kwargs)

		etype, exc, etraceback = exc_info
		if isinstance(exc, udm_errors.ldapError) and isinstance(getattr(exc, 'original_exception', None), (ldap.SERVER_DOWN, ldap.CONNECT_ERROR, ldap.INVALID_CREDENTIALS)):
			exc = exc.original_exception
		if isinstance(exc, ldap.SERVER_DOWN):
			exc = LDAP_ServerDown()
		if isinstance(exc, ldap.CONNECT_ERROR):
			exc = LDAP_ConnectionFailed(exc)
		_traceback = None
		message = str(exc)
		title = ''
		result = {}
		if isinstance(exc, UDM_Error):
			status_code = 400
		if isinstance(exc, UMC_Error):
			status_code = exc.status
			title = exc.msg
			if status_code == 503:
				self.add_header('Retry-After', '15')
			if title == message:
				title = httplib.responses.get(status_code)
			if isinstance(exc.result, dict):
				result = exc.result
		if isinstance(exc, UnprocessableEntity):
			error = ''
			for key, value in exc.result.items():
				formatter = _('Request argument "%s" %s\n')
				if key == 'query_string':
					formatter = _('Query string "%s": %s\n')
				if isinstance(value, dict):
					for k, v in value.items():
						error += formatter % (k, v)
				else:
					error += formatter % (key, value)
			message = '%s:\n%s' % (message, error)

		if not isinstance(exc, (UDM_Error, UMC_Error)) and status_code >= 500:
			_traceback = ''.join(traceback.format_exception(etype, exc, etraceback))

		response = {
			'error': {
				'title': title,
				'code': status_code,
				'message': message,
				'traceback': _traceback if self.application.settings.get("serve_traceback", True) else None,
				'error': result,
			},
		}
		self.add_link(response, 'self', self.urljoin(''), title=_('HTTP-Error %d: %s') % (status_code, title))
		self.set_status(status_code)
		self.add_caching(public=False, no_store=True, no_cache=True, must_revalidate=True)
		self.content_negotiation(response)

	def add_caching(self, expires=None, public=False, must_revalidate=False, no_cache=False, no_store=False, no_transform=False, max_age=None, shared_max_age=None, proxy_revalidate=False):
		control = [
			'public' if public else 'private',
			'must-revalidate' if must_revalidate else '',
			'no-cache' if no_cache else '',
			'no-store' if no_store else '',
			'no-transform' if no_transform else '',
			'max-age=%d' % (max_age,) if max_age else '',
			's-maxage=%d' % (shared_max_age,) if shared_max_age else '',
			'proxy-revalidate' if proxy_revalidate else '',
		]
		cache_control = ', '.join(x for x in control if x)
		if cache_control:
			self.set_header('Cache-Control', cache_control)
		if expires:
			self.set_header('Expires', expires)

	def vary(self):
		return ['Accept', 'Accept-Language', 'Accept-Encoding', 'Authorization']

	def modified_from_timestamp(self, timestamp):
		modified = time.strptime(timestamp, '%Y%m%d%H%M%SZ')
		# make sure Last-Modified is only send if it is not now
		if modified < time.gmtime(time.time() - 1):
			return modified

	def get_parent_object_type(self, module):
		flavor = module.flavor
		if '/' not in flavor:
			return module
		return UDM_Module(flavor, ldap_connection=self.ldap_connection, ldap_position=self.ldap_position)

	def navigation(self):
		return ('udm:object-modules', 'udm:object-module', 'type', 'up', 'self')


class Resource(ResourceBase, RequestHandler):

	def options(self, *args, **kwargs):
		"""Display API descriptions."""
		result = self._options(*args, **kwargs)

		def docstring(obj, *args, **kwargs):
			return '\n'.join(x.strip() for x in (obj.__doc__ or '').split('\n')).format(*args, **kwargs)

		def inspect_sanitizers(sans):
			props = {}
			for key, san in sans.items():
				description = ''
				type_ = ''
				kwargs = {}
				if isinstance(san, DictSanitizer):
					type_ = 'object'
				elif isinstance(san, ListSanitizer):
					type_ = 'array'
				elif isinstance(san, DNSanitizer):
					type_ = 'string'
					description = 'LDAP DN'
				elif isinstance(san, BooleanSanitizer):
					type_ = 'boolean'
				elif isinstance(san, BoolSanitizer):
					description = 'boolean value'
					type_ = 'string'
					kwargs['choices'] = san.choices
				elif isinstance(san, ChoicesSanitizer):
					type_ = 'string'
					kwargs['choices'] = san.choices
				elif isinstance(san, IntegerSanitizer):
					type_ = 'number'
				props[key] = dict({
					'type': type_,
					'description': description,
					'required': san.required,
					'default': san.default,
				}, **kwargs)
			return props
		result['methods'] = methods = {}
		result['description'] = docstring(self)
		for method in self._headers.get('Allow', '').split(', '):
			func = getattr(self, method.lower())
			sanitizers = getattr(func, 'sanitizers', {})
			methods[method] = {
				'summary': docstring(func, *args, **kwargs),
				'query': inspect_sanitizers(sanitizers.get('query', {})),
				'payload': inspect_sanitizers(sanitizers.get('body', {})),
				'headers': {
					'Accept': ['application/json', 'text/html'],
					'Accept-Language': ['en-US', 'en', 'de-DE', 'de'],
					'If-None-Match': ['etag'],
					'If-Match': ['etag'],
					'If-Unmodified-Since': ['last_modified'],
					'If-Modified-Since': ['last_modified'],
					'Content-Type': ['application/json', 'application/x-www-form-urlencoded', 'multipart/form-data'],
					'Authorization': ['basic'],
				},
				'responses': {
					200: {
						'description': 'Everything OK'
					},
					400: {
						'description': 'Bad request syntax (e.g. wrong content type)'
					},
					401: {
						'description': 'Unauthorized. No Authorization provided or wrong credentials'
					},
					404: {
						'description': 'Object not found'
					},
					422: {
						'description': 'Validation of input parameters failed'
					},
					500: {
						'description': 'Internal server errror'
					},
					502: {
						'description': '(LDAP) Server not available'
					},
					599: {
						'description': 'Error in Tornado web server'  # proxy server not reachable
					},
				},
			}
		self.add_caching(public=False, must_revalidate=True)
		self.content_negotiation(result)


class Nothing(Resource):

	def prepare(self, *args, **kwargs):
		super(Nothing, self).prepare(*args, **kwargs)
		raise NotFound()


class Favicon(ResourceBase, tornado.web.StaticFileHandler):

	@classmethod
	def get_absolute_path(cls, root, object_type=''):
		value = object_type.replace('/', '-')
		if value == 'favicon':
			return root
		if not value.replace('-', '').replace('_', '').isalpha():
			raise NotFound(object_type)
		return os.path.join(root, 'udm-%s.png' % (value,))


class Relations(Resource):

	def get(self, relation):
		iana_relations = {
			'search': 'Refers to a resource that can be used to search through the link\'s context and related resources.',
			'create-form': 'The target IRI points to a resource where a submission form can be obtained.',
			'describedby': "Refers to a resource providing information about the link's context.",
			'edit': 'Refers to a resource that can be used to edit the link\'s context.',
			'edit-form': 'The target IRI points to a resource where a submission form for editing associated resource can be obtained.',
			'first': 'An IRI that refers to the furthest preceding resource in a series of resources.',
			'help': 'Refers to context-sensitive help.',
			'index': 'Refers to an index.',
			'item': 'The target IRI points to a resource that is a member of the collection represented by the context IRI.',
			'last': 'An IRI that refers to the furthest following resource in a series of resources.',
			'latest-version': 'Points to a resource containing the latest (e.g., current) version of the context.',
			'next': 'Indicates that the link\'s context is a part of a series, and that the next in the series is the link target. ',
			'original': 'The Target IRI points to an Original Resource.',
			'prev': 'Indicates that the link\'s context is a part of a series, and that the previous in the series is the link target. ',
			'preview': 'Refers to a resource that provides a preview of the link\'s context.',
			'previous': 'Refers to the previous resource in an ordered series of resources. Synonym for "prev".',
			'self': 'Conveys an identifier for the link\'s context. ',
			'start': 'Refers to the first resource in a collection of resources.',
			'type': 'Refers to a resource identifying the abstract semantic type of which the link\'s context is considered to be an instance.',
			'up': 'Refers to a parent document in a hierarchy of documents.',
			'icon': 'Refers to an icon representing the link\'s context.',
		}
		univention_relations = {
			'relations': 'description of all relations',
			'object': 'represents an object',
			'object/get-by-dn': 'get an object from its DN',
			'object/get-by-uuid': 'get an object from its entry UUID',
			'object/remove': 'remove this object, edit-form is preferable',
			'object/move': 'move objects to a certain position',
			'object/edit': 'modify this object, edit-form is preferable',
			'object/property/reference/*': 'objects which are referencing or referenced by this object',
			'object-modules': 'list of available module categories',
			'object-module': 'the module belonging to the current selected resource',
			'object-types': 'list of object types matching the given flavor or container',
			'object-type': 'the object type belonging to the current selected resource',
			'children-types': 'list of object types which can be created underneath of the container or superordinate',
			'properties': 'properties of the given object type',
			'layout': 'layout information for the given object type',
			'tree': 'list of tree content for providing a hierarchical navigation',
			'policy-result': 'policy result by virtual policy object containing the values that the given object or container inherits',
			'report': 'create a report',
			'default-search': 'default search pattern/value for the given object property',
			'next-free-ip': 'next IP configuration based on the given network object',
			'property-choices': 'determine valid values for a given syntax class',
			'user-photo': 'photo of the object',
			'license': 'information about UCS license',
			'license-request': 'Request a new UCS Core Edition license',
			'license-check': 'Check if the license limits are reached',
			'license-import': 'Import a new license in LDIF format',
		}
		self.add_caching(public=True, must_revalidate=True)
		result = {}
		self.add_link(result, 'self', self.urljoin(''), title=_('Link relations'))
		self.add_link(result, 'up', self.urljoin('../'), title=_('All modules'))
		if relation and relation.startswith('object/property/reference/'):
			relation = 'object/property/reference/*'
		if relation:
			result['relation'] = univention_relations.get(relation, iana_relations.get(relation))
			if not result['relation']:
				raise NotFound()
		else:
			for relation in iana_relations:
				self.add_link(result, 'udm:relations', self.urljoin(relation), name=relation, title=relation)
			for relation in univention_relations:
				self.add_link(result, 'udm:relations', self.urljoin(relation), name='udm:%s' % relation, title='udm:%s' % relation)
		self.content_negotiation(result)


class OpenAPI(Resource):

	requires_authentication = False

	def prepare(self):
		super(OpenAPI, self).prepare()
		self.request.content_negotiation_lang = 'json'
		self.ldap_connection, self.ldap_position = get_machine_connection(write=False)

	def get(self, object_type=None):
		paths = {}  # defines all resources and methods they have
		tags = []  # defines the basic structure, a group of pathes builds a tag, the pathes must include a reference to the tag name
		models = {}  # defines "models" (and can be referenced)
		request_bodies = {}

		global_parameters = [
			{'$ref': '#/components/parameters/user-agent'},
			{'$ref': '#/components/parameters/accept-language'},
			{'$ref': '#/components/parameters/if-none-match'},
			{'$ref': '#/components/parameters/if-modified-since'},
		]
		_global_responses = {
		}
		_global_response_headers = {
			'Cache-Control': {'$ref': '#/components/headers/Cache-Control'},
			'Expires': {'$ref': '#/components/headers/Expires'},
			'Vary': {'$ref': '#/components/headers/Vary'},
			'Content-Language': {'$ref': '#/components/headers/Content-Language'},
			'Link': {'$ref': '#/components/headers/Link'},
		}

		def global_response_headers(responses={}):
			return dict(_global_response_headers, **responses)

		def global_responses(responses):
			return dict(_global_responses, **responses)

		base_object_definition = {
			"dn": {
				"description": "LDAP DN (Distinguished Name)",
				"type": "string",
				"format": "dn",
				"example": "dc=example,dc=net",
				"readOnly": True,
			},
			"uuid": {
				"description": "LDAP Entry-UUID",
				"type": "string",
				"format": "uuid"
			},
			# "id": {},
			"objectType": {
				"description": "UDM Object-Type",
				"type": "string",
				"example": "users/user",
				"readOnly": True,
			},
			"_links": {
				"description": "Hypertext Application Language (HAL) links",
				"type": "object",
				"properties": {
					"self": {
						"type": "array",
						"items": {
							"type": "object",
							"properties": {
								"href": {
									"type": "string",
									"description": "The URL",
								}
							},
							"additionalProperties": True,
						}
					}
				},
				"readOnly": True,
				"additionalProperties": True,
			},
			"_embedded": {
				"description": "Hypertext Application Language (HAL) embedded resources",
				"type": "object",
				"properties": {},
				"readOnly": True,
				"additionalProperties": True,
			},
			"position": {
				"description": "DN of LDAP node below which the object is located. Changing this causes a move of the object. When chaning no other changes are applied.",
				"type": "string",
				"format": "dn",
				"example": "cn=position,dc=example,dc=net",
			},
		}

		for name, mod in sorted(udm_modules.modules.items()):
			if object_type and name != object_type:
				continue
			module = UDM_Module(name, ldap_connection=self.ldap_connection, ldap_position=self.ldap_position)
			tag = name
			model_name = name.replace('/', '-')
			model_name_escaped = model_name.replace('~', '~0').replace('/', '~1')
			schema_definition = "#/components/schemas/%s" % (model_name_escaped,)
			tag_description = {
				'description': '%s objects' % (module.title,),
				'name': name,
			}
			if module.help_text and module.help_link:
				tag_description.update({
					'externalDocs': {
						'description': module.help_text,
						'url': module.help_link,
					}
				})
			tags.append(tag_description)
			models[model_name] = {
				"type": "object",
				"properties": {},
			}
			model = models[model_name]['properties']
			paths['/%s/' % (name,)] = objects_pathes = {}
			paths['/%s/add' % (name,)] = object_template_pathes = {}
			paths['/%s/{dn}' % (name,)] = object_pathes = {}
			object_pathes["parameters"] = [
				{
					"description": "The objects DN (urlencoded)",
					"in": "path",
					"name": "dn",
					"required": True,
					"schema": {
						"type": "string",
						"format": "dn",
					},
				}
			]
			models['%s-list' % (model_name,)] = {
				"type": "object",
				"properties": {
					"_embedded": {
						"type": "object",
						"properties": {
							"udm:object": {
								"type": "array",
								"items": {
									"$ref": schema_definition,
								}
							}
						}
					},

				}
			}

			def content_schema(schema_definition=schema_definition):
				return {
					'application/json': {'schema': {'$ref': schema_definition}},
					'application/hal+json': {'schema': {'$ref': schema_definition}},
					'text/html': {'schema': {'$ref': schema_definition}},  # TODO: describe as NON-API
				}

			request_bodies[model_name] = {
				'content': content_schema(),
				'required': True,
			}
			schema_request_body = "#/components/requestBodies/%s" % (model_name_escaped,)
			if 'search' in module.operations:
				objects_pathes['get'] = {
					"summary": "Search for %s" % (module.object_name_plural,),
					"description": "Information about the object type and links to search for objects. The found objects are either referenced as HAL links or embedded via HAL embedded resources.",
					"operationId": "udm:%s/object/search" % (name,),
					"parameters": [
						{'$ref': '#/components/parameters/search.filter'},
						{'$ref': '#/components/parameters/search.position'},
						{'$ref': '#/components/parameters/search.scope'},
						{'$ref': '#/components/parameters/search.query'},
						{'$ref': '#/components/parameters/search.hidden'},
						#{'$ref': '#/components/parameters/search.limit'},  # currently not supported by all modules
						#{'$ref': '#/components/parameters/search.page'},
						#{'$ref': '#/components/parameters/search.dir'},
						#{'$ref': '#/components/parameters/search.by'},
					] + global_parameters,
					"responses": global_responses({
						200: {
							"description": "Success",
							"content": content_schema("#/components/schemas/%s-list" % (model_name_escaped,)),
							"headers": global_response_headers(),
							"links": {
								"search": {
									"description": "Search for objects of this object type",
									"operationId": "udm:%s/object/search" % (name,)
								},
								"create-form": {
									"description": "get a template for creating an object",
									"operationId": "udm:%s/object/template" % (name,),
								},
							},
						}
					}),
					"tags": [tag],
				}
				if superordinate_names(module):
					objects_pathes['get']['parameters'].append({'$ref': '#/components/parameters/search.superordinate'})
			if 'add' in module.operations:
				object_template_pathes['get'] = {
					"operationId": "udm:%s/object/template" % (name,),
					"summary": "Get a template for creating an object. Contains all properties and their default values.",
					"parameters": [] + global_parameters,
					"responses": global_responses({
						201: {
							"description": "Success",
							"content": content_schema(),
							"headers": global_response_headers(),
						}
					}),
					"tags": [tag],
				}
				objects_pathes['post'] = {
					"operationId": "udm:%s/object/create" % (name,),
					"requestBody": {
						"$ref": schema_request_body,
					},
					"responses": global_responses({
						201: {
							"description": "Success",
							"content": content_schema(),
							"headers": global_response_headers(),
						}
					}),
					"summary": "Create a new %s object" % (module.object_name,),
					"tags": [tag],
				}
			object_pathes["get"] = {
				"operationId": "udm:%s/object" % (name,),
				"responses": global_responses({
					"200": {
						"description": "Success",
						"content": content_schema(),
						"headers": global_response_headers({
							'E-Tag': {'$ref': '#/components/headers/E-Tag'},
							'Last-Modified': {'$ref': '#/components/headers/Last-Modified'},
						}),
					},
					"404": {
						"description": "Object not found"
					}
				}),
				"summary": "Get a representation of the %s object" % (module.object_name,),
				"tags": [tag]
			}
			if 'remove' in module.operations:
				object_pathes["delete"] = {
					"operationId": "udm:%s/object/remove" % (name,),
					"parameters": [
						{'$ref': '#/components/parameters/remove.cleanup'},
						{'$ref': '#/components/parameters/remove.recursive'},
					] + global_parameters,
					"responses": global_responses({
						"204": {
							"description": "Object deleted",
							"headers": global_response_headers(),
						},
						"404": {
							"description": "Object not found",
							"headers": global_response_headers(),
						}
					}),
					"summary": "Remove a %s object" % (module.object_name_plural,),
					"tags": [tag],
				}
			if set(module.operations) & {'edit', 'move', 'move_subtree'}:
				object_pathes["put"] = {
					"operationId": "udm:%s/object/modify" % (name,),
					"requestBody": {
						"$ref": schema_request_body,
					},
					"parameters": [
						{'$ref': '#/components/parameters/if-match'},
						{'$ref': '#/components/parameters/if-unmodified-since'},
					] + global_parameters,
					"callbacks": {
						'move-progress': {
							'$ref': '#/components/callbacks/moveProgress'
						},
					},
					"responses": global_responses({
						"200": {
							"description": "Success",
							"content": content_schema(),
							"headers": global_response_headers(),
						},
						"404": {
							"description": "Object not found",
							"headers": global_response_headers(),
						}
					}),
					"summary": "Modify or move an %s object" % (module.object_name,),
					"tags": [tag],
				}
				object_pathes['patch'] = object_pathes['put'].copy()
				object_pathes['patch']['operationId'] = 'udm:%s/object/update' % (name,)

			model.update(dict(base_object_definition, **{
				"properties": {
					"type": "object",
					"properties": {},
					"additionalProperties": True,  # not yet installed extended attributes
				},
				"uri": {
					"type": "string",
					"format": "uri",
					"example": self.abspath(module.name) + '/%s=foo,dc=example,dc=net' % (module.mapping.mapName(module.identifies) or 'cn',),
				},
				"options": {
					"description": "Object type specific options.",
					"properties": dict((oname, {
						"description": opt.short_description,
						"type": "boolean",
						"default": bool(opt.default),
						"example": bool(opt.default),
					}) for oname, opt in module.options.items()),
					"type": "object"
				},
				"policies": {
					"description": "Policies which apply for this object.",
					"properties": dict((pol['objectType'], {
						"type": "array",
						"items": {
							"type": "string",
							"format": "dn",
							"example": ucr['ldap/base'],
						},
						"description": pol['label'],
					}) for pol in module.policies),
					"type": "object"
				},
			}))
			model_properties = model['properties']['properties']
			if superordinate_names(module):
				model['superordinate'] = {
					"type": "string",
					"format": "dn",
					"example": "dc=example,dc=net",
				}
			for prop in module.properties(None):
				name = prop['id']
				if name.startswith('$'):
					continue
				property = module.get_property(name)
				codec = udm_types.TypeHint.detect(property, name)
				model_properties[name] = codec.get_openapi_definition()

		url = list(urlparse(self.abspath('')))
		fqdn = '%(hostname)s.%(domainname)s' % ucr
		urls = [
			urlunparse([_scheme, _host] + url[2:])
			for _host in (fqdn, url[1])
			for _scheme in ('https', 'http')
		]
		specs = {
			'openapi': '3.0.0',
			'paths': paths,
			'info': {
				'description': 'Schema definition for the objects in the Univention Directory Manager REST interface',
				'title': 'Univention Directory Manager REST interface',
				'version': '1.0.0',
			},
			'security': [{
				"basic": []
			}],
			'tags': tags,
			'components': {
				'schemas': models,  # Reusable schemas (data models)
				'requestBodies': request_bodies,  # Reusable request bodies
				'securitySchemes': {  # Security scheme definitions (see Authentication)
					'basic': {
						'scheme': 'basic',
						'type': 'http',
					}
				},
				'parameters': {  # Reusable path, query, header and cookie parameters
					'search.position': {
						"in": "query",
						"name": "position",
						"schema": {
							"type": "string",
							"format": "dn",
							"nullable": True,
							"default": None,
						},
						"description": "Position which is used as search base.",
					},
					'search.scope': {
						"in": "query",
						"name": "scope",
						"schema": {
							"type": "string",
							"default": "sub",
						},
						"example": "sub",
						"description": "The `LDAP` search scope (sub, base, one).",
						"examples": {
							"sub": {"value": "sub", "summary": "sub-scope"},
							"base": {"value": "base", "summary": "base-scope"},
							"one": {"value": "one", "summary": "one-scope"},
						}
					},
					'search.filter': {
						"in": "query",
						"name": "filter",
						"schema": {"type": "string", "default": ""},
						"description": "A ldap filter which may contain `UDM` property names instead of `LDAP` attribute names.",
						"example": "(objectClass=*)",
						"examples": {
							"users-user": {
								"value": "(|(username=Administrator)(username=Admin*))",
							}
						},
					},
					'search.query': {
						"in": "query",
						"name": "query",
						"style": "deepObject",
						"schema": {"type": "object"},
						"description": "The values to search for (propertyname and search filter value). Alternatively with `filter` a raw ldap filter can be given.",
						"example": {'': '*'},
					},
					'search.hidden': {
						"in": "query",
						"name": "hidden",
						"schema": {
							"type": "boolean",
							"default": True,
						},
						"description": "Include hidden/system objects in the response.",
						"example": True,
					},
					'search.superordinate': {
						"in": "query",
						"name": "superordinate",
						"schema": {
							"type": "string",
							"format": "dn",
							"nullable": True,
							"default": None,
						},
						"description": "The superordinate DN of the objects to find. `position` is sufficient.",
						# "example": "cn=superordinate,dc=example,dc=net",
					},
					'search.limit': {
						"in": "query",
						"name": "limit",
						"schema": {
							"type": "integer",
							"nullable": True,
							"default": None,
						},
						"description": "How many results should be shown per page.",
						"example": 50,
					},
					'search.page': {
						"in": "query",
						"name": "page",
						"schema": {
							"type": "integer",
							"default": 1,
						},
						"description": "The search page, starting at one.",
						"example": 1,
					},
					'search.dir': {
						"in": "query",
						"name": "dir",
						"schema": {
							"type": "string",
							"default": "ASC",
						},
						"description": "The Sort direction (ASC or DESC).",
						"example": "ASC",
					},
					'search.by': {
						"in": "query",
						"name": "by",
						"schema": {"type": "string"},
						"description": "Sort the search result by the specified property.",
						#"example": "username",
					},
					'remove.cleanup': {
						"in": "query",
						"name": "cleanup",
						"schema": {
							"type": "boolean",
							"default": True,
						},
						"description": "Whether to perform a cleanup (e.g. of temporary objects, locks, etc).",
						"example": True,
					},
					'remove.recursive': {
						"in": "query",
						"name": "recursive",
						"schema": {
							"type": "boolean",
							"default": True,
						},
						"description": "Whether to remove referring objects (e.g. DNS or DHCP references).",
						"example": True,
					},
					'user-agent': {
						"in": "header",
						"name": "User-Agent",
						"schema": {"type": "string"},
						"description": "The user agent",
						"example": "UCS 4.4-1-errata241",
					},
					'accept-language': {
						"in": "header",
						"name": "Accept-Language",
						"schema": {"type": "string"},
						"description": "The accepted response languages",
						"example": "de-DE; q=1.0, en-US; q=0.9",
					},
					"if-match": {
						"in": "header",
						"name": "If-Match",
						"schema": {"type": "string"},
						"description": "provide entity tag to make a condition request to not overwrite any values in a race condition",
						"example": "",
					},
					"if-none-match": {
						"in": "header",
						"name": "If-None-Match",
						"schema": {"type": "string", "format": "etag"},
						"description": "",
						"example": "",
					},
					"if-unmodified-since": {
						"in": "header",
						"name": "If-Unmodified-Since",
						"schema": {"type": "string", "format": "last-modified-date"},
						"description": "provide last modified time to make a condition request to not overwrite any values in a race condition",
						# "example": "Wed, 21 Oct 2015 07:28:00 GMT",
					},
					"if-modified-since": {
						"in": "header",
						"name": "If-Modified-Since",
						"schema": {"type": "string"},
						"description": "",
						"example": "",
					},
				},
				'responses': {  # Reusable responses, such as 401 Unauthorized or 400 Bad Request
					'Errors': {
						'description': 'Error format',
					},
					'MoveProgress': {  # 301
						'description': 'Gives information about the progress of a move operation',
						'headers': global_response_headers({
							'Retry-After': {'$ref': '#/components/headers/Retry-After'},
							'Location': {'$ref': '#/components/headers/Location'},
						}),
						"content": {},
					},
					'MoveSuccess': {  # 303
						'description': 'Redirects to the result of the move operation, i.e. the new object',
						'headers': global_response_headers({'Location': {'$ref': '#/components/headers/Location'}}),
						"content": {},
					},
					"BadRequest": {  # 400
						"description": 'Bad request syntax',
					},
					"ObjectNotFound": {  # 404
						"description": "Object not found."
					},
					"ObjectGone": {  # 410
						"description": "Object has recently been removed.",
					},
					"Unauthorized": {  # 401
						'description': 'Unauthorized. No Authorization provided or wrong credentials'
					},
					"UnprocessableEntity": {  # 422
						'description': 'Validation of input parameters failed'
					},
					"ServerError": {  # 500
						'description': 'Internal server errror'
					},
					"ServiceUnavailable": {  # 503 (+502 +504)
						'description': '(LDAP) Server not available',
						'headers': global_response_headers({
							'Retry-After': {'$ref': '#/components/headers/Retry-After'}
						}),
					},
				},
				'headers': {  # Reusable response headers
					'Cache-Control': {"schema": {"type": "string"}, "description": "Controling directives for caching."},
					'Expires': {"schema": {"type": "string"}, "description": "An expiration time, when the response is stale and should not be used from cache anymore."},
					'Vary': {"schema": {"type": "string"}, "description": "The response headers which need to be considered when caching the response."},
					'E-Tag': {"schema": {"type": "string"}, "description": "An entity tag of the resource, which should be used for conditional PUT requests."},
					'Last-Modified': {"schema": {"type": "string"}, "description": "The time the resource was modified the last time, which should be used for conditional PUT requests."},
					'Allow': {"schema": {"type": "string"}, "description": "The allowed HTTP request methods for this resource"},
					'Content-Language': {"schema": {"type": "string"}, "description": "The language of the response"},
					'Retry-After': {"schema": {"type": "string"}, "description": "The time which should be waited before requesting the resource from the Location header"},
					'Accept-Patch': {"schema": {"type": "string"}, "description": "The accepted Content-Types for a PATCH request"},
					'Location': {"schema": {"type": "string"}, "description": "The location which should be followed."},
					'Link': {"schema": {"type": "string"}, "description": "A hypermedia link."},
				},
				'examples': {},  # Reusable examples
				'links': {},  # Reusable links
				'callbacks': {  # Reusable callbacks
					'moveProgress': {
						'{$response.header.Location}': {
							'get': {
								'requestBody': {
									"content": {},
								},
								'responses': {
									'301': {'$ref': '#/components/responses/MoveProgress'},
									'303': {'$ref': '#/components/responses/MoveSuccess'},
								}
							}
						}
					},
				},
			},
			'servers': [{'url': _url} for _url in urls],
		}
		self.content_negotiation(specs)

	def get_json(self, response):
		response = super(OpenAPI, self).get_json(response)
		response.pop('_links', None)
		response.pop('_embedded', None)
		return response


class Modules(Resource):

	mapping = {
		'users': 'users/user',
		'contacts': 'users/contact',
		'computers': 'computers/computer',
		'groups': 'groups/group',
		'networks': 'networks/network',
		'dhcp': 'dhcp/dhcp',
		'dns': 'dns/dns',
		'shares': 'shares/share',
		'printers': 'shares/print',
		'mail': 'mail/mail',
		'nagios': 'nagios/nagios',
		'policies': 'policies/policy',
		'self': 'users/self',
		'portal': 'settings/portal_all',
		'saml': 'saml/serviceprovider',
		'appcenter': 'appcenter/app',
		'kerberos': 'kerberos/kdcentry',
		'settings': 'settings/settings',
		'navigation': 'object',
		'container': 'container',
	}

	def get(self):
		result = {}
		self.add_link(result, 'self', self.urljoin(''), title=_('All modules'))
		for main_type, name in sorted(self.mapping.items(), key=lambda x: 0 if x[0] == 'navigation' else x[0]):
			title = _('All %s types') % (name,)
			if '/' in name:
				title = UDM_Module(name, ldap_connection=self.ldap_connection, ldap_position=self.ldap_position).object_name_plural

			self.add_link(result, 'udm:object-modules', self.urljoin(quote(main_type)) + '/', name='all' if main_type == 'navigation' else main_type, title=title)

		modules = udm_modules.modules.keys()
		for name in sorted(modules):
			_module = UDM_Module(name, ldap_connection=self.ldap_connection, ldap_position=self.ldap_position)
			self.add_link(result, 'udm:object-types', self.urljoin(quote(_module.name)) + '/', name=_module.name, title=_module.title, dont_set_http_header=True)

		self.add_link(result, 'udm:object/get-by-dn', self.urljoin('object') + '/{dn}', templated=True)
		self.add_link(result, 'udm:object/get-by-uuid', self.urljoin('object') + '/{uuid}', templated=True)
		self.add_link(result, 'udm:license', self.urljoin('license') + '/', name='license', title=_('UCS license'))
		self.add_link(result, 'udm:ldap-base', self.urljoin('ldap/base') + '/', title=_('LDAP base'))
		self.add_link(result, 'udm:relations', self.urljoin('relation') + '/', name='relation', title=_('All link relations'))
		self.add_caching(public=True)
		self.content_negotiation(result)

	def navigation(self):
		return ['self']


class ObjectTypes(Resource):
	"""get the object types of a specific flavor"""

	@sanitize_query_string(
		superordinate=DNSanitizer(required=False, allow_none=True)
	)
	def get(self, module_type):
		object_type = Modules.mapping.get(module_type)
		if not object_type:
			raise NotFound(object_type)

		title = _('All object types')
		module = None
		if '/' in object_type:
			# FIXME: what was/is the superordinate for?
			superordinate = self.request.query_arguments['superordinate']
			module = UDM_Module(object_type, ldap_connection=self.ldap_connection, ldap_position=self.ldap_position)
			if superordinate:
				module = get_module(object_type, superordinate, self.ldap_connection) or module  # FIXME: the object_type param is wrong?!
			title = module.object_name_plural

		result = {}

		self.add_link(result, 'up', self.urljoin('../'), title=_('All modules'))
		self.add_link(result, 'self', self.urljoin(''), name=module_type, title=title)
		if module_type == 'navigation':
			self.add_link(result, 'udm:tree', self.abspath('container/dc/tree'))
		elif module and module.has_tree:
			self.add_link(result, 'udm:tree', self.urljoin('../', object_type, 'tree'))

		if module and (module.help_link or module.help_text):
			self.add_link(result, 'help', module.help_link or '', title=module.help_text or module.help_link)

		if module_type == 'navigation':
			modules = udm_modules.modules.keys()
		elif module_type == 'container':
			modules = container_modules()
		else:
			modules = [x['id'] for x in module.child_modules]

		for name in sorted(modules):
			_module = UDM_Module(name, ldap_connection=self.ldap_connection, ldap_position=self.ldap_position)
			self.add_link(result, 'udm:object-types', self.urljoin('../%s' % quote(_module.name)) + '/', name=_module.name, title=_module.title)
			continue
			# TODO: get rid of entries. all of it can be put into the link!?
			result.setdefault('entries', []).append({
				'id': _module.name,
				'label': _module.title,
				'object_name': _module.object_name,
				'object_name_plural': _module.object_name_plural,
				#'help_link': _module.help_link,
				#'help_text': _module.help_text,
				'columns': _module.columns,  # FIXME: move to Objects?
				#'has_tree': _module.has_tree,
			})

		self.add_caching(public=True, must_revalidate=True)
		self.content_negotiation(result)


class SubObjectTypes(Resource):
	"""A list of possible sub-object-types which can be created underneath of the specified container or superordinate."""

	def get(self, object_type=None, position=None):
		"""Returns the list of object types matching the given flavor or container.

		requests.options = {}
			'superordinate' -- if available only types for the given superordinate are returned (not for the navigation)
			'container' -- if available only types suitable for the given container are returned (only for the navigation)
		"""
		if not position:
			# no container is specified, return all existing object types
			return self.module_definition(udm_modules.modules.keys())

		position = unquote_dn(position)

		# create a list of modules that can be created
		# ... all container types except container/dc
		allowed_modules = set([m for m in udm_modules.containers if udm_modules.name(m) != 'container/dc'])

		# the container may be a superordinate or have one as its parent
		# (or grandparent, ....)
		superordinate = udm_modules.find_superordinate(position, None, self.ldap_connection)
		if superordinate:
			# there is a superordinate... add its subtypes to the list of allowed modules
			allowed_modules.update(udm_modules.subordinates(superordinate))
		else:
			# add all types that do not have a superordinate
			allowed_modules.update(mod for mod in udm_modules.modules.values() if not udm_modules.superordinates(mod))

		# make sure that the object type can be created
		allowed_modules = [mod for mod in allowed_modules if udm_modules.supports(mod, 'add')]

		return self.module_definition(allowed_modules)

	def module_definition(self, modules):
		result = {'entries': []}
		for name in modules:
			_module = UDM_Module(name, ldap_connection=self.ldap_connection, ldap_position=self.ldap_position)
			result['entries'].append({
				'id': _module.name,
				'label': _module.title,
				#'object_name': _module.object_name,
				#'object_name_plural': _module.object_name_plural,
				#'help_link': _module.help_link,
				#'help_text': _module.help_text,
				#'columns': _module.columns,
				#'has_tree': _module.has_tree,
			})
			self.add_link(result, 'udm:object-types', self.abspath(_module.name) + '/', name=_module.name, title=_module.title)
		self.add_caching(public=True, must_revalidate=True)
		self.content_negotiation(result)


class LdapBase(Resource):

	def get(self):
		result = {}
		url = self.abspath('container/dc', quote_dn(ucr['ldap/base']))
		self.add_link(result, '', url)
		self.set_header('Location', url)
		self.set_status(301)
		self.add_caching(public=True, must_revalidate=True)
		self.content_negotiation(result)


class ObjectLink(Resource):
	"""If the object-type is not known but only the DN, this resource redirects to the correct object."""

	def get(self, dn):
		dn = unquote_dn(dn)
		attrs = self.ldap_connection.get(dn)
		modules = udm_modules.objectType(None, self.ldap_connection, dn, attrs) or []
		if not modules:
			raise NotFound(None, dn)
		for module in modules:
			module = UDM_Module(module, ldap_connection=self.ldap_connection, ldap_position=self.ldap_position)
			if module.module:
				break
		else:
			raise NotFound(None, dn)
		url = self.abspath(module.name, quote_dn(dn))
		self.set_header('Location', url)
		self.set_status(301)
		self.add_caching(public=True, must_revalidate=True)
		self.content_negotiation({})


class ObjectByUiid(ObjectLink):

	def get(self, uuid):
		try:
			dn = self.ldap_connection.searchDn(filter_format('entryUUID=%s', [uuid]))[0]
		except IndexError:
			raise NotFound()
		return super(ObjectByUiid, self).get(dn)


class ContainerQueryBase(Resource):

	@tornado.gen.coroutine
	def _container_query(self, object_type, container, modules, scope):
		"""Get a list of containers or child objects of the specified container."""

		if not container:
			container = ucr['ldap/base']
			defaults = {}
			if object_type != 'navigation':
				defaults['$operations$'] = ['search', ],  # disallow edit
			if object_type in ('dns/dns', 'dhcp/dhcp'):
				defaults.update({
					'label': UDM_Module(object_type, ldap_connection=self.ldap_connection, ldap_position=self.ldap_position).title,
					'icon': 'udm-%s' % (object_type.replace('/', '-'),),
				})
			self.add_link({}, 'next', self.urljoin('?container=%s' % (quote(container))))
			raise tornado.gen.Return([dict({
				'id': container,
				'label': ldap_dn2path(container),
				'icon': 'udm-container-dc',
				'path': ldap_dn2path(container),
				'objectType': 'container/dc',
				'$operations$': UDM_Module('container/dc', ldap_connection=self.ldap_connection, ldap_position=self.ldap_position).operations,
				'$flags$': [],
				'$childs$': True,
				'$isSuperordinate$': False,
			}, **defaults)])

		result = []
		for xmodule in modules:
			xmodule = UDM_Module(xmodule, ldap_connection=self.ldap_connection, ldap_position=self.ldap_position)
			superordinate = univention.admin.objects.get_superordinate(xmodule.module, None, self.ldap_connection, container)  # TODO: should also better be in a thread
			try:
				ucr['directory/manager/web/sizelimit'] = ucr.get('ldap/sizelimit', '400000')
				items = yield self.pool.submit(xmodule.search, container, scope=scope, superordinate=superordinate)
				for item in items:
					module = UDM_Module(item.module, ldap_connection=self.ldap_connection, ldap_position=self.ldap_position)
					result.append({
						'id': item.dn,
						'label': item[module.identifies],
						'icon': 'udm-%s' % (module.name.replace('/', '-')),
						'path': ldap_dn2path(item.dn),
						'objectType': module.name,
						'$operations$': module.operations,
						'$flags$': item.oldattr.get('univentionObjectFlag', []),
						'$childs$': module.childs,
						'$isSuperordinate$': udm_modules.isSuperordinate(module.module),
					})
			except UDM_Error as exc:
				raise HTTPError(400, None, str(exc))

		raise tornado.gen.Return(result)


class Tree(ContainerQueryBase):
	"""GET udm/(dns/dns|dhcp/dhcp|)/tree/ (the tree content of navigation/DNS/DHCP)"""

	@sanitize_query_string(
		container=DNSanitizer(default=None)
	)
	@tornado.gen.coroutine
	def get(self, object_type):
		ldap_base = ucr['ldap/base']
		container = self.request.query_arguments['container']

		modules = container_modules()
		scope = 'one'
		if not container:
			# get the tree root == the ldap base
			scope = 'base'
		elif object_type != 'navigation' and container and ldap_base.lower() == container.lower():
			# this is the tree root of DNS / DHCP, show all zones / services
			scope = 'sub'
			modules = [object_type]

		containers = yield self._container_query(object_type, container, modules, scope)
		self.add_caching(public=False, must_revalidate=True)
		self.content_negotiation(containers)


class MoveDestinations(ContainerQueryBase):

	@sanitize_query_string(
		container=DNSanitizer(default=None)
	)
	@tornado.gen.coroutine
	def get(self, object_type):
		scope = 'one'
		modules = container_modules()
		container = self.request.query_arguments['container']
		if not container:
			scope = 'base'

		containers = yield self._container_query(object_type, container, modules, scope)
		self.add_caching(public=False, must_revalidate=True)
		self.content_negotiation(containers)


class Properties(Resource):
	"""GET udm/users/user/properties (get properties of users/user object type)"""

	def get(self, object_type, dn=None):  # TODO: add link to DefaultValue
		result = {}
		if dn:
			dn = unquote_dn(dn)
		module = self.get_module(object_type)
		module.load(force_reload=True)  # reload for instant extended attributes

		self.add_link(result, 'up', self.urljoin('.'))
		properties = self.get_properties(module, dn)
		searchable = self.get_query_argument('searchable', False)
		if searchable:
			properties = dict((name, prop) for name, prop in properties.items() if prop.get('searchable', False))
		result['properties'] = properties

		self.add_caching(public=True, must_revalidate=True)
		self.content_negotiation(result)

	@classmethod
	def get_properties(cls, module, dn=None):
		properties = module.get_properties(dn)
		for policy in module.policies:
			properties.append({
				'id': 'policies[%s]' % (policy['objectType'],),
				'label': policy['label'],
				'description': policy['description'],
			})
		for prop in properties[:]:
			if prop['id'] == '$options$':
				for option in prop['widgets']:
					option['id'] = 'options[%s]' % (option['id'],)
					properties.append(option)
		for prop in properties:
			prop.setdefault('label', '')
			prop.setdefault('description', '')
			prop.setdefault('readonly', False)
			prop.setdefault('readonly_when_synced', False)
			prop.setdefault('disabled', False)
			prop.setdefault('required', False)
			prop.setdefault('syntax', '')
			prop.setdefault('identifies', False)
			prop.setdefault('searchable', False)
			prop.setdefault('multivalue', False)
		return dict((prop['id'], prop) for prop in properties if not prop['id'].startswith('$'))


class Layout(Resource):

	def get(self, object_type, dn=None):
		result = {}
		if dn:
			dn = unquote_dn(dn)
		module = self.get_module(object_type)
		module.load(force_reload=True)  # reload for instant extended attributes

		result['layout'] = self.get_layout(module)

		self.add_caching(public=True, must_revalidate=True)
		self.content_negotiation(result)

	@classmethod
	def get_layout(cls, module, dn=None):
		layout = module.get_layout(dn)

		# TODO: insert module.help_text into first layout element
		layout.insert(0, {'layout': [], 'advanced': False, 'description': _('Meta information'), 'label': _('Meta information'), 'is_app_tab': False})
		apps = cls.get_apps_layout(layout)
		if apps:
			apps['layout'].append('options')
		else:
			layout.append({'layout': ['options'], 'advanced': False, 'description': _('Here you can activate the user for one of the installed apps. The user can then log on to the app and use it.'), 'label': _('Apps & Options'), 'is_app_tab': False})
		advanced = {'layout': [], 'advanced': False, 'description': _('Advanced settings'), 'label': _('Advanced settings')}
		for x in layout[:]:
			if x['advanced']:
				advanced['layout'].append(x)
				layout.remove(x)
		if advanced['layout']:
			layout.append(advanced)
		layout.append({
			'layout': ['policies[%s]' % (policy['objectType'],) for policy in module.policies],
			'advanced': False,
			'description': _('Properties inherited from policies'),
			'label': _('Policies'),
			'is_app_tab': False,
			'help': _('List of all object properties that are inherited by policies. The values cannot be edited directly. By clicking on "Create new policy", a new tab with a new policy will be opened. If an attribute is already set, the corresponding policy can be edited in a new tab by clicking on the "edit" link.')
		})

		return layout

	@classmethod
	def get_apps_layout(cls, layout):
		for x in layout:
			if x.get('label') == 'Apps':
				return x

	@classmethod
	def get_reference_layout(cls, layout):
		for x in layout:
			if x.get('label', '').lower().startswith('referen'):
				return x


class ReportingBase(Resource):

	def initialize(self):
		self.reports_cfg = udr.Config()


class Report(ReportingBase):
	"""GET udm/users/user/report/$report_type?dn=...&dn=... (create a report of users)"""

	# i18n: translation for univention-directory-reports
	_('PDF Document')
	_('CSV Report')

	@tornado.gen.coroutine
	def get(self, object_type, report_type):
		dns = self.get_query_arguments('dn')
		yield self.create_report(object_type, report_type, dns)

	@tornado.gen.coroutine
	def post(self, object_type, report_type):
		dns = self.get_body_arguments('dn')
		yield self.create_report(object_type, report_type, dns)

	@tornado.gen.coroutine
	def create_report(self, object_type, report_type, dns):
		try:
			report_type in self.reports_cfg.get_report_names(object_type)
		except KeyError:
			raise NotFound(report_type)

		report = udr.Report(self.ldap_connection)
		try:
			report_file = yield self.pool.submit(report.create, object_type, report_type, dns)
		except udr.ReportError as exc:
			raise HTTPError(400, None, str(exc))

		with open(report_file) as fd:
			self.set_header('Content-Type', 'text/csv' if report_file.endswith('.csv') else 'application/pdf')
			self.set_header('Content-Disposition', 'attachment; filename="%s"' % (os.path.basename(report_file).replace('\\', '\\\\').replace('"', '\\"')))
			self.finish(fd.read())
		os.remove(report_file)


class NextFreeIpAddress(Resource):
	"""GET udm/networks/network/$DN/next-free-ip-address (get the next free IP in this network)"""

	def get(self, dn):  # TODO: threaded?! (might have caused something in the past in system setup?!)
		"""Returns the next IP configuration based on the given network object

		requests.options = {}
			'networkDN' -- the LDAP DN of the network object
			'increaseCounter' -- if given and set to True, network object counter for IP addresses is increased

		return: {}
		"""
		dn = unquote_dn(dn)
		obj = self.get_object('networks/network', dn)
		try:
			obj.refreshNextIp()
		except udm_errors.nextFreeIp:
			raise NoIpLeft(dn)

		result = {
			'ip': obj['nextIp'],
			'dnsEntryZoneForward': obj['dnsEntryZoneForward'],
			'dhcpEntryZone': obj['dhcpEntryZone'],
			'dnsEntryZoneReverse': obj['dnsEntryZoneReverse']
		}

		self.add_caching(public=False, must_revalidate=True)
		self.content_negotiation(result)

		if self.get_query_argument('increaseCounter', False):
			# increase the next free IP address
			obj.stepIp()
			obj.modify()


class DefaultValue(Resource):
	"""GET udm/users/user/properties/$property/default (get the default value for the specified property)
	Returns the default search pattern/value for the given object property"""

	def get(self, object_type, property_):
		module = self.get_module(object_type)
		result = module.get_default_values(property_)
		self.add_caching(public=False, must_revalidate=True)
		self.content_negotiation(result)


class FormBase(object):

	def add_property_form_elements(self, module, form, properties, values):
		password_properties = module.password_properties
		for key, prop in properties.items():
			if key.startswith('options[') and key.endswith(']'):
				self.add_form_element(form, 'options', prop['id'].split('[', 1)[1].split(']')[0], type='checkbox', checked=prop['value'], label=prop['label'])
			if key not in values:
				continue

			value = values[key]
			if value is None:
				value = ''
			kwargs = {'type': 'input'}
			if key == 'jpegPhoto':
				kwargs['type'] = 'file'
				kwargs['accept'] = 'image/jpg image/jpeg image/png'
				value = ''
			if key in password_properties:
				value = ''
				kwargs['type'] = 'password'
			if prop['type'] == 'ComboBox' and prop.get('staticValues'):
				kwargs['type']
				kwargs['list'] = 'list-%s' % (key,)
				kwargs['datalist'] = [{'value': s['id'], 'label': s['label']} for s in prop['staticValues']]
			elif prop['type'] == 'DateBox':
				kwargs['type'] = 'date'
			if prop['readonly']:
				kwargs['readonly'] = 'readonly'
			if prop['disabled']:
				kwargs['disabled'] = 'disabled'
			if prop['required']:
				kwargs['required'] = 'required'
			if prop['syntax'] == 'boolean':
				kwargs['type'] = 'checkbox'
				if value:
					kwargs['checked'] = 'checked'
			elif prop['syntax'] == 'integer':
				kwargs['type'] = 'number'
			kwargs['data-identifies'] = '1' if prop['identifies'] else '0'
			kwargs['data-searchable'] = '1' if prop['searchable'] else '0'
			kwargs['data-multivalue'] = '1' if prop['multivalue'] or prop['type'] == 'umc/modules/udm/MultiObjectSelect' else '0'
			kwargs['data-syntax'] = prop['syntax']
			kwargs['title'] = prop['description']
			# TODO: size, type, options, treshold, staticValues, editable, nonempty_is_default
			self.add_form_element(form, 'properties.%s' % (key,), value, label=prop['label'], placeholder=prop['label'], **kwargs)

	def decode_form_arguments(self):
		# TODO: add files
		# TODO: respect single-value
		# TODO: the types should be converted, e.g. type=checkbox to boolean, number to int
		for key in self.request.body_arguments.keys()[:]:
			for name in ('properties', 'policies'):
				if key.startswith('%s.' % (name,)):
					properties = self.request.body_arguments.setdefault(name, {})
					prop = key[len('%s.' % (name,)):]
					properties.setdefault(prop, []).append(self.request.body_arguments.pop(key))
				elif key.startswith('%s[' % (name,)) and key.endswith(']'):
					properties = self.request.body_arguments.setdefault(name, {})
					prop = key[len('%s[' % (name,)):-1]
					properties.setdefault(prop, []).append(self.request.body_arguments.pop(key))

	def superordinate_dn_to_object(self, module, superordinate):
		if not superordinate_names(module):
			return
		if superordinate:
			mod = get_module(module.name, superordinate, self.ldap_connection)
			if not mod:
				MODULE.error('Superordinate module not found: %s' % (superordinate,))
				raise SuperordinateDoesNotExist(superordinate)
			MODULE.info('Found UDM module for superordinate')
			superordinate = mod.get(superordinate)
		return superordinate


class Objects(FormBase, ReportingBase):

	search_sessions = {}

	@sanitize_query_string(
		position=DNSanitizer(required=False, default=None),
		filter=LDAPFilterSanitizer(required=False, default=None, allow_none=True),
		query=DictSanitizer({}, default_sanitizer=LDAPSearchSanitizer(required=False, default='*', add_asterisks=False, use_asterisks=True), key_sanitizer=ObjectPropertySanitizer()),
		property=ObjectPropertySanitizer(required=False, default=None),
		scope=ChoicesSanitizer(choices=['sub', 'one', 'base', 'base+one'], default='sub'),
		hidden=BoolSanitizer(default=True),
		properties=ListSanitizer(required=False, default=['*']),
		superordinate=DNSanitizer(required=False, default=None, allow_none=True),
		dir=ChoicesSanitizer(choices=['ASC', 'DESC'], default='ASC'),
		by=StringSanitizer(required=False),
		page=IntegerSanitizer(required=False, default=1, minimum=1),
		limit=IntegerSanitizer(required=False, default=None, minimum=0),
	)
	@tornado.gen.coroutine
	def get(self, object_type):
		"""Search for {} objects."""
		module = self.get_module(object_type)
		result = self._options(object_type)

		search = bool(self.request.query)
		container = self.request.query_arguments['position']
		hidden = self.request.query_arguments['hidden']
		ldap_filter = self.request.query_arguments['filter']
		scope = self.request.query_arguments['scope']
		properties = self.request.query_arguments['properties'][:]
		direction = self.request.query_arguments['dir']
		property_ = self.request.query_arguments['property']
		reverse = direction == 'DESC'
		by = self.request.query_arguments['by']
		page = self.request.query_arguments['page']
		items_per_page = self.request.query_arguments['limit']

		if not ldap_filter:
			filters = filter(None, [(_object_property_filter(module, attribute or property_ or None, value, hidden)) for attribute, value in self.request.query_arguments['query'].items()])
			if filters:
				ldap_filter = unicode(univention.admin.filter.conjunction('&', [univention.admin.filter.parse(fil) for fil in filters]))

		# TODO: replace the superordinate concept with container
		superordinate = self.superordinate_dn_to_object(module, self.request.query_arguments['superordinate'])
		if superordinate:
			container = container or superordinate.dn

		objects = []
		if search:
			try:
				objects, last_page = yield self.search(module, container, ldap_filter, superordinate, scope, hidden, items_per_page, page, by, reverse)
			except ObjectDoesNotExist as exc:
				self.raise_sanitization_error('position', str(exc))
			except SuperordinateDoesNotExist as exc:
				self.raise_sanitization_error('superordinate', str(exc))

		for obj in objects or []:
			if obj is None:
				continue
			objmodule = UDM_Module(obj.module, ldap_connection=self.ldap_connection, ldap_position=self.ldap_position)

			if '*' in properties:
				# TODO: i think we need error handling here, because between receiving the object and opening it, it or refernced objects might be removed.
				# best would be if lookup() would support opening because that already does error handling.
				obj.open()

			entry = Object.get_representation(objmodule, obj, properties, self.ldap_connection)
			entry['uri'] = self.abspath(obj.module, quote_dn(obj.dn))
			self.add_link(entry, 'self', entry['uri'], name=entry['dn'], title=entry['id'], dont_set_http_header=True)
			self.add_resource(result, 'udm:object', entry)

		if items_per_page:
			self.add_link(result, 'first', self.urljoin('', page='1'), title=_('First page'))
			if page > 1:
				self.add_link(result, 'prev', self.urljoin('', page=str(page - 1)), title=_('Previous page'))
			if not last_page:
				self.add_link(result, 'next', self.urljoin('', page=str(page + 1)), title=_('Next page'))
			else:
				self.add_link(result, 'last', self.urljoin('', page=str(last_page)), title=_('Last page'))

		if search:
			for i, report_type in enumerate(sorted(self.reports_cfg.get_report_names(object_type)), 1):
				form = self.add_form(result, self.urljoin('report', quote(report_type)), 'POST', rel='udm:report', name=report_type, id='report%d' % (i,))
				self.add_form_element(form, '', _('Create %s report') % _(report_type), type='submit')

			form = self.add_form(result, self.urljoin('multi-edit'), 'POST', name='multi-edit', id='multi-edit', rel='edit-form')
			self.add_form_element(form, '', _('Modify %s (multi edit)') % (module.object_name_plural,), type='submit')

			form = self.add_form(result, self.urljoin('move'), 'POST', name='move', id='move', rel='udm:object/move')
			self.add_form_element(form, 'position', '')
			self.add_form_element(form, '', _('Move %s') % (module.object_name_plural,), type='submit')

		search_layout_base = [{'description': _('Search for %s') % (module.object_name_plural,), 'label': _('Search'), 'layout': []}]
		search_layout = search_layout_base[0]['layout']
		self.add_layout(result, search_layout_base, 'search')
		form = self.add_form(result, self.urljoin(''), 'GET', rel='search', id='search', layout='search')
		self.add_form_element(form, 'position', container or '', label=_('Search in'))
		search_layout.append(['position', 'hidden'])
		if superordinate_names(module):
			self.add_form_element(form, 'superordinate', superordinate.dn if superordinate else '', label=_('Superordinate'))
			search_layout.append(['superordinate'])
		searchable_properties = [{'value': '', 'label': _('Defaults')}] + [{'value': prop['id'], 'label': prop['label']} for prop in module.properties(None) if prop.get('searchable')]
		self.add_form_element(form, 'property', property_ or '', element='select', options=searchable_properties, label=_('Property'))
		self.add_form_element(form, 'query[]', self.request.query_arguments['query'].get('', '*'), label=_('Search for'), placeholder=_('Search value (e.g. *)'))
		self.add_form_element(form, 'scope', scope, element='select', options=[{'value': 'sub'}, {'value': 'one'}, {'value': 'base'}, {'value': 'base+one'}], label=_('Search scope'))
		self.add_form_element(form, 'hidden', '1', type='checkbox', checked=bool(hidden), label=_('Include hidden objects'))
		search_layout.append(['property', 'query[]'])
		#self.add_form_element(form, 'fields', list(fields))
		if module.supports_pagination:
			self.add_form_element(form, 'limit', str(items_per_page or '0'), type='number', label=_('Limit'))
			self.add_form_element(form, 'page', str(page or '1'), type='number', label=_('Selected page'))
			self.add_form_element(form, 'by', by or '', element='select', options=searchable_properties, label=_('Sort by'))
			self.add_form_element(form, 'dir', direction if direction in ('ASC', 'DESC') else 'ASC', element='select', options=[{'value': 'ASC', 'label': _('Ascending')}, {'value': 'DESC', 'label': _('Descending')}], label=_('Direction'))
			search_layout.append(['page', 'limit'])
			search_layout.append(['by', 'dir'])
		search_layout.append('')
		self.add_form_element(form, '', _('Search'), type='submit')

		if search:
			result['results'] = len(self.get_resources(result, 'udm:object'))

		self.add_caching(public=False, no_cache=True, no_store=True, max_age=1, must_revalidate=True)
		self.content_negotiation(result)

	@tornado.gen.coroutine
	def search(self, module, container, ldap_filter, superordinate, scope, hidden, items_per_page, page, by, reverse):
		ctrls = {}
		serverctrls = []
		hashed = (self.request.user_dn, module.name, container or None, ldap_filter or None, superordinate or None, scope or None, hidden or None, items_per_page or None, by or None, reverse or None)
		session = self.search_sessions.get(hashed, {})
		last_cookie = session.get('last_cookie', '')
		current_page = session.get('page', 0)
		page_ctrl = SimplePagedResultsControl(True, size=items_per_page, cookie=last_cookie)  # TODO: replace with VirtualListViewRequest
		if module.supports_pagination:
			if items_per_page:
				serverctrls.append(page_ctrl)
			if by in ('uid', 'uidNumber', 'cn'):
				rule = ':caseIgnoreOrderingMatch' if by not in ('uidNumber',) else ''
				serverctrls.append(SSSRequestControl(ordering_rules=['%s%s%s' % ('-' if reverse else '', by, rule)]))
		objects = []
		# TODO: we have to store the results of the previous pages (or make them cacheable)
		# FIXME: we have to store the session across all processes
		ucr['directory/manager/web/sizelimit'] = ucr.get('ldap/sizelimit', '400000')
		last_page = page
		for i in range(current_page, page or 1):
			objects = yield self.pool.submit(module.search, container, superordinate=superordinate, filter=ldap_filter, scope=scope, hidden=hidden, serverctrls=serverctrls, response=ctrls)
			for control in ctrls.get('ctrls', []):
				if control.controlType == SimplePagedResultsControl.controlType:
					page_ctrl.cookie = control.cookie
			if not page_ctrl.cookie:
				self.search_sessions.pop(hashed, None)
				break
		else:
			self.search_sessions[hashed] = {'last_cookie': page_ctrl.cookie, 'page': page}
			last_page = 0
		raise tornado.gen.Return((objects, last_page))

	def get_html(self, response):
		if self.request.method in ('GET', 'HEAD'):
			r = response.copy()
			r.pop('entries', None)
			root = super(Objects, self).get_html(r)
		else:
			root = super(Objects, self).get_html(response)
		if self.request.method in ('GET', 'HEAD'):
			for thing in response.get('entries', self.get_resources(response, 'udm:object')):
				if isinstance(thing, dict) and thing.get('uri'):
					x = thing.copy()
					a = ET.Element("a", href=x.pop('uri'), rel="udm:object item")
					a.text = x.get('dn')
					pre = ET.Element("pre")
					pre.text = json.dumps(x, indent=4)
					root.append(ET.Element("br"))
					# There is a bug in chrome, so we cannot have form='report1 report2'. so, only 1 report is possible :-/
					root.append(ET.Element('input', type='checkbox', name='dn', value=x['dn'], form=' '.join([report['id'] for report in self.get_resources(response, 'udm:form') if report['rel'] == 'udm:report'][-1:])))
					root.append(a)
					root.append(pre)
					root.append(ET.Element("br"))
				else:
					pre = ET.Element("pre")
					pre.text = json.dumps(thing, indent=4)
					root.append(pre)
					root.append(ET.Element("br"))
		return root

	@sanitize_body_arguments(
		position=DNSanitizer(required=False, allow_none=True),
		superordinate=DNSanitizer(required=False, allow_none=True),
		options=DictSanitizer({}, default_sanitizer=BooleanSanitizer(), required=False),
		policies=DictSanitizer({}, default_sanitizer=ListSanitizer(DNSanitizer()), required=False),
		properties=DictSanitizer({}, required=True),
	)
	@tornado.gen.coroutine
	def post(self, object_type):
		"""Create a {} object."""
		obj = Object(self.application, self.request)
		obj.ldap_connection, obj.ldap_position = self.ldap_connection, self.ldap_position
		obj = yield obj.create(object_type)
		self.set_header('Location', self.urljoin(quote_dn(obj.dn)))
		self.set_status(201)
		self.add_caching(public=False, must_revalidate=True)
		self.content_negotiation({})

	def _options(self, object_type):
		result = {}
		module = self.get_module(object_type)
		parent = self.get_parent_object_type(module)
		methods = ['GET', 'OPTIONS']
		self.add_link(result, 'udm:object-modules', self.urljoin('../../'), title=_('All modules'))
		self.add_link(result, 'up', self.urljoin('../'), title=parent.object_name_plural)
		self.add_link(result, 'self', self.urljoin(''), name=module.name, title=module.object_name_plural)
		self.add_link(result, 'describedby', self.urljoin(''), method='OPTIONS')
		if 'search' in module.operations:
			searchfields = ['position', 'query[]', 'filter', 'scope', 'hidden', 'properties']
			if superordinate_names(module):
				searchfields.append('superordinate')
			if module.supports_pagination:
				searchfields.extend(['limit', 'page', 'by', 'dir'])
			self.add_link(result, 'search', self.urljoin('') + '{?%s}' % ','.join(searchfields), templated=True, title=_('Search for %s') % (module.object_name_plural,))
		if 'add' in module.operations:
			methods.append('POST')
			self.add_link(result, 'create-form', self.urljoin('add'), title=_('Create a %s') % (module.object_name,))
			self.add_link(result, 'create-form', self.urljoin('add') + '{?position,superordinate%s}' % (',template' if module.template else ''), templated=True, title=_('Create a %s') % (module.object_name,))
		if module.help_link or module.help_text:
			self.add_link(result, 'help', module.help_link or '', title=module.help_text or module.help_link)
		self.add_link(result, 'icon', self.urljoin('favicon.ico'), type='image/x-icon')
		if module.has_tree:
			self.add_link(result, 'udm:tree', self.urljoin('tree'), title=_('Object type tree'))
#		self.add_link(result, '', self.urljoin(''))
		self.set_header('Allow', ', '.join(methods))
		return result

	def options_html(self, response):
		#root = self.get_html(response)
		root = ET.Element('pre')
		root.text = json.dumps(response, indent=4)
		return root


class ObjectsMove(Resource):

	@sanitize_body_arguments(
		position=DNSanitizer(required=True),
		dn=ListSanitizer(DNSanitizer(required=True), min_elements=1),
	)
	def post(self, object_type):
		# FIXME: this can only move objects of the same object_type but should move everything
		position = self.request.body_arguments['position']
		dns = self.request.body_arguments['dn']  # TODO: validate: moveable, etc.
		queue = Operations.queue.setdefault(self.request.user_dn, {})
		status = {
			'id': str(uuid.uuid4()),
			'finished': False,
			'errors': False,
			'moved': [],
		}
		queue[status['id']] = status
		self.set_status(201)
		self.set_header('Location', self.abspath('progress', status['id']))
		self.finish()
		try:
			for i, dn in enumerate(dns, 1):
				module = get_module(object_type, dn, self.ldap_connection)
				dn = yield self.pool.submit(module.move, dn, position)
				status['moved'].append(dn)
				status['description'] = _('Moved %d of %d objects. Last object was: %s.') % (i, len(dns), dn)
				status['max'] = len(dns)
				status['value'] = i
		except:
			status['errors'] = True
			status['traceback'] = traceback.format_exc()  # FIXME: error handling
			raise
		else:
			status['uri'] = self.urljoin(dn)
		finally:
			status['finished'] = True


class Object(FormBase, Resource):

	@tornado.gen.coroutine
	def get(self, object_type, dn):
		"""Get a representation of the {} object {} with all its properties, policies, options, metadata and references.
		Includes also instructions how to modify, remove or move the object.
		"""
		dn = unquote_dn(dn)
		copy = bool(self.get_query_argument('copy', None))  # TODO: move into own resource: ./copy

		if object_type == 'users/self' and not self.ldap_connection.compare_dn(dn, self.request.user_dn):
			raise HTTPError(403)

		module = get_module(object_type, dn, self.ldap_connection)
		if module is None:
			raise NotFound(object_type, dn)

		obj = yield self.pool.submit(module.get, dn)
		if not obj:
			# FIXME: return HTTP 410 Gone for removed objects
			# if self.ldap_connection.searchDn(filter_format('(&(reqDN=%s)(reqType=d))', [dn]), base='cn=translog'):
			# 	raise Gone(object_type, dn)
			raise NotFound(object_type, dn)
		if object_type not in ('users/self', 'users/passwd') and not univention.admin.modules.recognize(object_type, obj.dn, obj.oldattr):
			raise NotFound(object_type, dn)

		self.set_metadata(obj)
		self.set_entity_tags(obj)

		props = {}
		props.update(self._options(object_type, obj.dn))
		props['uri'] = self.abspath(obj.module, quote_dn(obj.dn))
		props.update(self.get_representation(module, obj, ['*'], self.ldap_connection, copy))
		for reference in module.get_references(obj):
			# TODO: add a reference for the "position" object?!
			if reference['module'] != 'udm':
				continue  # can not happen currently
			for dn in set(_map_normalized_dn(filter(None, [reference['id']]))):
				rel = {'__policies': 'udm:object/policy/reference'}.get(reference['property'], 'udm:object/property/reference/%s' % (reference['property'],))
				self.add_link(props, rel, self.abspath(reference['objectType'], quote_dn(dn)), name=dn, title=reference['label'], dont_set_http_header=True)

		if module.name == 'networks/network':
			self.add_link(props, 'udm:next-free-ip', self.urljoin(quote_dn(obj.dn), 'next-free-ip-address'), title=_('Next free IP address'))

		if obj.has_property('jpegPhoto'):
			self.add_link(props, 'udm:user-photo', self.urljoin(quote_dn(obj.dn), 'properties/jpegPhoto.jpg'), type='image/jpeg', title=_('User photo'))

		self.add_caching(public=False, must_revalidate=True)
		self.content_negotiation(props)

	def _options(self, object_type, dn):
		dn = unquote_dn(dn)
		module = self.get_module(object_type)
		props = {}
		parent_module = self.get_parent_object_type(module)
		self.add_link(props, 'udm:object-modules', self.urljoin('../../'), title=_('All modules'))
		self.add_link(props, 'udm:object-module', self.urljoin('../'), name=parent_module.name, title=parent_module.object_name_plural)
		#self.add_link(props, 'udm:object-types', self.urljoin('../'))
		self.add_link(props, 'type', self.urljoin('x/../'), name=module.name, title=module.object_name)
		self.add_link(props, 'up', self.urljoin('x/../'), name=module.name, title=module.object_name)
		self.add_link(props, 'self', self.urljoin(''), title=dn)
		self.add_link(props, 'describedby', self.urljoin(''), method='OPTIONS')
		self.add_link(props, 'icon', self.urljoin('favicon.ico'), type='image/x-icon')
		self.add_link(props, 'udm:object/remove', self.urljoin(''), method='DELETE')
		self.add_link(props, 'udm:object/edit', self.urljoin(''), method='PUT')
		# self.add_link(props, '', self.urljoin('report/PDF Document?dn=%s' % (quote(obj.dn),))) # rel=alternate media=print?
#		for mod in module.child_modules:
#			mod = self.get_module(mod['id'])
#			if mod and set(superordinate_names(mod)) & {module.name, }:
#				self.add_link(props, 'udm:children-types', self.urljoin('../../%s/?superordinate=%s' % (quote(mod.name), quote(obj.dn))), name=mod.name, title=mod.object_name_plural)

		methods = ['GET', 'OPTIONS']
		if module.childs:
			self.add_link(props, 'udm:children-types', self.urljoin(quote_dn(dn), 'children-types/'), name=module.name, title=_('Sub object types of %s') % (module.object_name,))

		can_modify = set(module.operations) & {'edit', 'move', 'subtree_move'}
		can_remove = 'remove' in module.operations
		if can_modify or can_remove:
			if can_modify:
				methods.extend(['PUT', 'PATCH'])
			if can_remove:
				methods.append('DELETE')
			self.add_link(props, 'edit-form', self.urljoin(quote_dn(dn), 'edit'), title=_('Modify, move or remove this %s' % (module.object_name,)))

		self.set_header('Allow', ', '.join(methods))
		if 'PATCH' in methods:
			self.set_header('Accept-Patch', 'application/json-patch+json, application/json')
		return props

	def set_metadata(self, obj):  # FIXME: move into UDM core!
		obj.oldattr.update(self.ldap_connection.get(obj.dn, attr=[b'+']))

	def set_entity_tags(self, obj):
		self.set_header('Etag', self.get_etag(obj))
		modified = self.modified_from_timestamp(obj.oldattr['modifyTimestamp'][0].decode('utf-8', 'replace'))
		if modified:
			self.set_header('Last-Modified', last_modified(modified))
		self.check_conditional_requests()

	def get_etag(self, obj):
		# generate as early as possible, to not cause side effects e.g. default values in obj.info. It must be the same value for GET and PUT
		if not obj._open:
			raise RuntimeError('Object was not opened!')
		etag = hashlib.sha1()
		etag.update(obj.dn.encode('utf-8', 'replace'))
		etag.update(obj.module.encode('utf-8', 'replace'))
		etag.update(b''.join(obj.oldattr.get('entryCSN', [])))
		etag.update(b''.join(obj.oldattr.get('entryUUID', [])))
		etag.update(json.dumps(obj.info, sort_keys=True).encode('utf-8'))
		return u'"%s"' % etag.hexdigest()

	@classmethod
	def get_representation(cls, module, obj, properties, ldap_connection, copy=False, add=False):
		def _remove_uncopyable_properties(obj):
			if not copy:
				return
			for name, p in obj.descriptions.items():
				if not p.copyable:
					obj.info.pop(name, None)

		# TODO: check if we really want to set the default values
		_remove_uncopyable_properties(obj)
		obj.set_defaults = True
		obj.set_default_values()
		_remove_uncopyable_properties(obj)

		values = {}
		if properties:
			values = obj.info.copy()
			if '*' not in properties:
				for key in list(values.keys()):
					if key not in properties:
						values.pop(key)
			else:
				values = dict((key, obj[key]) for key in obj.descriptions if add or obj.has_property(key))
			for passwd in module.password_properties:
				values[passwd] = None
			values = dict(decode_properties(module, obj, values))

		if add:
			# we need to remove dynamic default values as they reference other currently not set variables
			# (e.g. shares/share sets sambaName='' or users/user sets unixhome=/home/)
			for name, p in obj.descriptions.items():
				regex = re.compile(r'<(?P<key>[^>]+)>(?P<ext>\[[\d:]+\])?')  # from univention.admin.pattern_replace()
				if name not in obj.info or name not in values:
					continue
				if isinstance(p.base_default, six.string_types) and regex.search(p.base_default):
					values[name] = None

		props = {}
		props['dn'] = obj.dn
		props['objectType'] = module.name
		props['id'] = module.obj_description(obj)
		if not props['id']:
			props['id'] = '+'.join(explode_rdn(obj.dn, True))
		#props['path'] = ldap_dn2path(obj.dn, include_rdn=False)
		props['position'] = ldap_connection.parentDn(obj.dn) if obj.dn else obj.position.getDn()
		props['properties'] = values
		props['options'] = dict((opt['id'], opt['value']) for opt in module.get_options(udm_object=obj))
		props['policies'] = {}
		if '*' in properties or add:
			for policy in module.policies:
				props['policies'].setdefault(policy['objectType'], [])
			for policy in obj.policies:
				pol_mod = get_module(None, policy, ldap_connection)
				if pol_mod and pol_mod.name:
					props['policies'].setdefault(pol_mod.name, []).append(policy)
		if superordinate_names(module):
			props['superordinate'] = obj.superordinate and obj.superordinate.dn
		if obj.oldattr.get('entryUUID'):
			props['uuid'] = obj.oldattr['entryUUID'][0].decode('utf-8', 'replace')
		# TODO: objectFlag is available for every module. remove the extended attribute and always map it.
		# alternative: add some other meta information to this object, e.g. is_hidden_object: True, is_synced_from_active_directory: True, ...
		props['properties'].setdefault('objectFlag', [x.decode('utf-8', 'replace') for x in obj.oldattr.get('univentionObjectFlag', [])])
		if copy or add:
			props.pop('dn', None)
			props.pop('id', None)
		return props

	@sanitize_body_arguments(
		position=DNSanitizer(required=True),
		superordinate=DNSanitizer(required=False, allow_none=True),
		options=DictSanitizer({}, default_sanitizer=BooleanSanitizer()),
		policies=DictSanitizer({}, default_sanitizer=ListSanitizer(DNSanitizer())),
		properties=DictSanitizer({}, required=True),
	)
	@tornado.gen.coroutine
	def put(self, object_type, dn):
		"""Modify or move the {} object {}."""
		dn = unquote_dn(dn)
		module = get_module(object_type, dn, self.ldap_connection)
		if not module:
			raise NotFound(object_type)

		obj = yield self.pool.submit(module.get, dn)
		if not obj:
			obj = yield self.create(object_type, dn)
			self.set_header('Location', self.urljoin(quote_dn(obj.dn)))
			self.set_status(201)
			self.add_caching(public=False, must_revalidate=True)
			self.content_negotiation({})
			return

		self.set_metadata(obj)
		self.set_entity_tags(obj)

		position = self.request.body_arguments['position']
		if position and not self.ldap_connection.compare_dn(self.ldap_connection.parentDn(dn), position):
			yield self.move(module, dn, position)
			return
		else:
			obj = yield self.modify(module, obj)
			self.set_header('Location', self.urljoin(quote_dn(obj.dn)))
			self.add_caching(public=False, must_revalidate=True, no_cache=True, no_store=True)
			self.set_status(204)
			raise Finish()

	@sanitize_body_arguments(
		position=DNSanitizer(required=False, default=''),
		superordinate=DNSanitizer(required=False, allow_none=True),
		options=DictSanitizer({}, default_sanitizer=BooleanSanitizer(), required=False),
		policies=DictSanitizer({}, default_sanitizer=ListSanitizer(DNSanitizer()), required=False),
		properties=DictSanitizer({}),
	)
	@tornado.gen.coroutine
	def patch(self, object_type, dn):
		"""Modify partial properties of the {} object {}."""
		dn = unquote_dn(dn)
		module = get_module(object_type, dn, self.ldap_connection)
		if not module:
			raise NotFound(object_type)

		obj = yield self.pool.submit(module.get, dn)
		if not obj:
			raise NotFound(object_type, dn)

		self.set_metadata(obj)
		self.set_entity_tags(obj)

		entry = Object.get_representation(module, obj, ['*'], self.ldap_connection, False)
		if self.request.body_arguments['options'] is None:
			self.request.body_arguments['options'] = entry['options']
		if self.request.body_arguments['policies'] is None:
			self.request.body_arguments['policies'] = entry['policies']
		if self.request.body_arguments['properties'] is None:
			self.request.body_arguments['properties'] = {}
		if self.request.body_arguments['position'] is None:
			self.request.body_arguments['position'] = entry['position']
		obj = yield self.modify(module, obj)
		self.add_caching(public=False, must_revalidate=True, no_cache=True, no_store=True)
		self.set_header('Location', self.urljoin(quote_dn(obj.dn)))
		self.set_status(204)
		raise Finish()

	@tornado.gen.coroutine
	def create(self, object_type, dn=None):
		module = self.get_module(object_type)
		container = self.request.body_arguments['position']
		superordinate = self.request.body_arguments['superordinate']
		if dn:
			container = self.ldap_connection.parentDn(dn)
			# TODO: validate that properties are equal to rdn

		ldap_position = univention.admin.uldap.position(self.ldap_position.getBase())
		if container:
			ldap_position.setDn(container)
		elif superordinate:
			ldap_position.setDn(superordinate)
		else:
			ldap_position.setDn(module.get_default_container())

		superordinate = self.superordinate_dn_to_object(module, superordinate)

		obj = module.module.object(None, self.ldap_connection, ldap_position, superordinate=superordinate)
		obj.open()
		self.set_properties(module, obj)

		if dn and not self.ldap_connection.compare_dn(dn, obj._ldap_dn()):
			self.raise_sanitization_error('dn', _('Trying to create an object with wrong RDN.'))

		dn = yield self.pool.submit(self.handle_udm_errors, obj.create)
		raise tornado.gen.Return(obj)

	@tornado.gen.coroutine
	def modify(self, module, obj):
		assert obj._open
		self.set_properties(module, obj)
		yield self.pool.submit(self.handle_udm_errors, obj.modify)
		raise tornado.gen.Return(obj)

	def handle_udm_errors(self, action):
		try:
			exists_msg = None
			exc = None
			try:
				return action()
			except udm_errors.objectExists as exc:
				exists_msg = 'dn: %s' % (exc.args[0],)
			except udm_errors.uidAlreadyUsed as exc:
				exists_msg = '(uid)'
			except udm_errors.groupNameAlreadyUsed as exc:
				exists_msg = '(group)'
			except udm_errors.dhcpServerAlreadyUsed as exc:
				exists_msg = '(dhcpserver)'
			except udm_errors.macAlreadyUsed as exc:
				exists_msg = '(mac)'
			except udm_errors.noLock as exc:
				exists_msg = '(nolock)'
			if exists_msg and exc:
				self.raise_sanitization_error('dn', _('Object exists: %s: %s') % (exists_msg, str(UDM_Error(exc))))
		except (udm_errors.pwQuality, udm_errors.pwToShort, udm_errors.pwalreadyused) as exc:
			self.raise_sanitization_error('password', str(UDM_Error(exc)))
		except udm_errors.invalidOptions as exc:
			self.raise_sanitization_error('options', str(UDM_Error(exc)))
		except (udm_errors.invalidOperation, udm_errors.invalidChild, udm_errors.insufficientInformation) as exc:
			self.raise_sanitization_error('dn', str(UDM_Error(exc)))  # TODO: invalidOperation and invalidChild should be 403 Forbidden
		except udm_errors.invalidDhcpEntry as exc:
			self.raise_sanitization_error('dhcpEntryZone', str(UDM_Error(exc)))
		except udm_errors.circularGroupDependency as exc:
			self.raise_sanitization_error('memberOf', str(UDM_Error(exc)))  # or "nestedGroup"
		except (udm_errors.valueError) as exc:  # valueInvalidSyntax, valueRequired, etc.
			self.raise_sanitization_error(getattr(exc, 'property', 'properties'), str(UDM_Error(exc)))
		except udm_errors.prohibitedUsername as exc:
			self.raise_sanitization_error('username', str(UDM_Error(exc)))
		except udm_errors.uidNumberAlreadyUsedAsGidNumber as exc:
			self.raise_sanitization_error('uidNumber', str(UDM_Error(exc)))
		except udm_errors.gidNumberAlreadyUsedAsUidNumber as exc:
			self.raise_sanitization_error('gidNumber', str(UDM_Error(exc)))
		except udm_errors.mailAddressUsed as exc:
			self.raise_sanitization_error('mailPrimaryAddress', str(UDM_Error(exc)))
		except (udm_errors.adGroupTypeChangeLocalToAny, udm_errors.adGroupTypeChangeDomainLocalToUniversal, udm_errors.adGroupTypeChangeToLocal) as exc:
			self.raise_sanitization_error('adGroupType', str(UDM_Error(exc)))
		except udm_errors.base as exc:
			UDM_Error(exc).reraise()

	def set_properties(self, module, obj):
		options = self.request.body_arguments['options'] or {}  # TODO: AppAttributes.data_for_module(self.name).iteritems() ?
		options_enable = set(opt for opt, enabled in options.items() if enabled)
		options_disable = set(opt for opt, enabled in options.items() if enabled is False)  # ignore None!
		obj.options = list(set(obj.options) - options_disable | options_enable)
		if self.request.body_arguments['policies']:
			obj.policies = functools.reduce(lambda x, y: x + y, self.request.body_arguments['policies'].values())
		self.sanitize_arguments(PropertiesSanitizer(), self, module=module, obj=obj)

	@tornado.gen.coroutine
	def move(self, module, dn, position):
		queue = Operations.queue.setdefault(self.request.user_dn, {})
		status = {
			'id': str(uuid.uuid4()),
			'finished': False,
			'errors': False,
		}
		queue[status['id']] = status
		self.set_status(201)
		self.set_header('Location', self.abspath('progress', status['id']))
		self.add_caching(public=False, must_revalidate=True)
		self.content_negotiation(status)
		try:
			dn = yield self.pool.submit(module.move, dn, position)
		except:
			status['errors'] = True
			status['traceback'] = traceback.format_exc()  # FIXME: error handling
			raise
		else:
			status['uri'] = self.urljoin(dn)
		finally:
			status['finished'] = True

	@sanitize_query_string(
		cleanup=BoolSanitizer(default=True),
		recursive=BoolSanitizer(default=True),
	)
	@tornado.gen.coroutine
	def delete(self, object_type, dn):
		"""Remove the {} object {}."""
		dn = unquote_dn(dn)
		module = get_module(object_type, dn, self.ldap_connection)
		if not module:
			raise NotFound(object_type)

		cleanup = bool(self.request.query_arguments['cleanup'])
		recursive = bool(self.request.query_arguments['recursive'])
		try:
			yield self.pool.submit(module.remove, dn, cleanup, recursive)
		except udm_errors.primaryGroupUsed:
			raise
		self.add_caching(public=False, must_revalidate=True)
		self.set_status(204)
		raise Finish()

	def check_conditional_requests(self):
		etag = self._headers.get("Etag", "")
		if etag:
			self.check_conditional_request_etag(etag)

		last_modified = parsedate(self._headers.get('Last-Modified', ''))
		if last_modified is not None:
			last_modified = datetime.datetime(*last_modified[:6])
			self.check_conditional_request_modified_since(last_modified)
			self.check_conditional_request_unmodified_since(last_modified)

	def check_conditional_request_modified_since(self, last_modified):
		date = parsedate(self.request.headers.get('If-Modified-Since', ''))
		if date is not None:
			if_since = datetime.datetime(*date[:6])
			if if_since >= last_modified:
				self.set_status(304)
				raise Finish()

	def check_conditional_request_unmodified_since(self, last_modified):
		date = parsedate(self.request.headers.get('If-Unmodified-Since', ''))
		if date is not None:
			if_not_since = datetime.datetime(*date[:6])
			if last_modified > if_not_since:
				raise HTTPError(412, _('If-Unmodified-Since does not match Last-Modified.'))

	def check_conditional_request_etag(self, etag):
		safe_request = self.request.method in ('GET', 'HEAD', 'OPTIONS')

		def wheak(x):
			return x[2:] if x.startswith(b'W/') else x
		etag_matches = re.compile(r'\*|(?:W/)?"[^"]*"')

		def check_conditional_request_if_none_match():
			etags = etag_matches.findall(self.request.headers.get("If-None-Match", ""))
			if not etags:
				return

			if '*' in etags or wheak(etag) in map(wheak, etags):
				if safe_request:
					self.set_status(304)  # Not modified
					raise Finish()
				else:
					message = _('If-None-Match %s does not match entity tag(s) %s.') % (etag, ', '.join(etags))
					raise HTTPError(412, message)  # Precondition Failed

		def check_conditional_request_if_match():
			etags = etag_matches.findall(self.request.headers.get("If-Match", ""))
			if not etags:
				return
			if wheak(etag) not in map(wheak, etags):
				message = _('If-Match %s does not match entity tag(s) %s.') % (etag, ', '.join(etags))
				if not safe_request:
					raise HTTPError(412, message)  # Precondition Failed
				elif self.request.headers.get('Range'):
					raise HTTPError(416, message)  # Range Not Satisfiable

		check_conditional_request_if_none_match()
		check_conditional_request_if_match()


class UserPhoto(Resource):

	@tornado.gen.coroutine
	def get(self, object_type, dn):
		dn = unquote_dn(dn)
		module = get_module(object_type, dn, self.ldap_connection)
		if module is None:
			raise NotFound(object_type, dn)

		obj = yield self.pool.submit(module.get, dn)
		if not obj:
			raise NotFound(object_type, dn)

		if not obj.has_property('jpegPhoto'):
			raise NotFound(object_type, dn)

		data = obj.info.get('jpegPhoto', '').decode('base64')
		modified = self.modified_from_timestamp(self.ldap_connection.getAttr(obj.dn, b'modifyTimestamp')[0].decode('utf-8'))
		if modified:
			self.add_header('Last-Modified', last_modified(modified))
		self.set_header('Content-Type', 'image/jpeg')
		self.add_caching(public=False, max_age=2592000, must_revalidate=True)
		self.finish(data)

	@tornado.gen.coroutine
	def post(self, object_type, dn):
		dn = unquote_dn(dn)
		module = get_module(object_type, dn, self.ldap_connection)
		if module is None:
			raise NotFound(object_type, dn)

		obj = yield self.pool.submit(module.get, dn)
		if not obj:
			raise NotFound(object_type, dn)

		if not obj.has_property('jpegPhoto'):
			raise NotFound(object_type, dn)

		photo = self.request.files['jpegPhoto'][0]['body']
		if len(photo) > 262144:
			raise HTTPError(413, 'too large: maximum: 262144 bytes')
		obj['jpegPhoto'] = photo.encode('base64')

		yield self.pool.submit(obj.modify)

		self.set_status(204)
		raise Finish()


class ObjectAdd(FormBase, Resource):
	"""GET a form containing information about all properties, methods, URLs to create a specific object"""

	@sanitize_query_string(
		position=DNSanitizer(required=False),
		superordinate=DNSanitizer(required=False),
		template=DNSanitizer(required=False),
	)
	@tornado.gen.coroutine
	def get(self, object_type):
		module = self.get_module(object_type)
		if 'add' not in module.operations:
			raise NotFound(object_type)

		module.load(force_reload=True)  # reload for instant extended attributes

		result = {}

		self.add_link(result, 'self', self.urljoin(''), title=_('Add %s') % (module.object_name,))
		template = None
		if module.template:
			template = self.request.query_arguments.get('template')
		result.update(self.get_create_form(module, template=template, position=self.request.query_arguments.get('position'), superordinate=self.request.query_arguments.get('superordinate')))

		if module.template:
			template = UDM_Module(module.template, ldap_connection=self.ldap_connection, ldap_position=self.ldap_position)
			templates = template.search(ucr.get('ldap/base'))
			if templates:
				form = self.add_form(result, action='', method='GET', id='template', layout='template')  # FIXME: preserve query string
				template_layout = [{'label': _('Template'), 'description': 'A template defines rules for default object properties.', 'layout': ['template', '']}]
				self.add_layout(result, template_layout, 'template')
				self.add_form_element(form, 'template', '', element='select', options=[{'value': _obj.dn, 'label': _obj[template.identifies]} for _obj in templates])
				self.add_form_element(form, '', _('Fill template values'), type='submit')

		self.add_caching(public=True, must_revalidate=True)
		self.content_negotiation(result)

	def get_create_form(self, module, dn=None, copy=False, template=None, position=None, superordinate=None):
		result = {}
		self.add_link(result, 'icon', self.urljoin('favicon.ico'), type='image/x-icon')
		self.add_link(result, 'udm:object-modules', self.urljoin('../../'), title=_('All modules'))
		self.add_link(result, 'udm:object-module', self.urljoin('../'), title=self.get_parent_object_type(module).object_name_plural)
		self.add_link(result, 'type', self.urljoin('.'), title=module.object_name)
		self.add_link(result, 'create', self.urljoin('.'), title=module.object_name, method='POST')

		layout = Layout.get_layout(module)
		self.add_layout(result, layout, 'create-form', href=self.urljoin('layout'))

		properties = Properties.get_properties(module)
		self.add_resource(result, 'udm:properties', {'properties': properties})
		self.add_link(result, 'udm:properties', href=self.urljoin('properties'))

		meta_layout = layout[0]
		meta_layout['layout'].extend(['position'])
		# TODO: wizard: first select position & template

		for policy in module.policies:
			form = self.add_form(result, action=self.urljoin(policy['objectType']) + '/', method='GET', name=policy['objectType'], rel='udm:policy-result')
			self.add_form_element(form, 'position', position or '', label=_('The container where the object is going to be created in'))
			self.add_form_element(form, 'policy', '', label=policy['label'], title=policy['description'])
			self.add_form_element(form, '', _('Policy result'), type='submit')

		ldap_position = univention.admin.uldap.position(self.ldap_position.getBase())
		if position:
			ldap_position.setDn(position)
		else:
			ldap_position.setDn(module.get_default_container())
		superordinate = self.superordinate_dn_to_object(module, superordinate)

		obj = module.module.object(dn, self.ldap_connection, ldap_position, superordinate=superordinate)
		obj.open()
		result.update(Object.get_representation(module, obj, ['*'], self.ldap_connection, copy, True))

		form = self.add_form(result, action=self.urljoin(''), method='POST', id='add', layout='create-form')
		self.add_form_element(form, 'position', position or '')
		if superordinate_names(module):
			meta_layout['layout'].append('superordinate')
			self.add_form_element(form, 'superordinate', '')  # TODO: replace with <select>

		if template:
			self.add_form_element(form, 'template', template, readonly='readonly')
			meta_layout['layout'].append('template')

		values = {}
		for prop in properties:
			try:
				values[prop] = obj[prop]  # don't use .get()!
			except KeyError:
				pass

		values = dict(decode_properties(module, obj, values))
		self.add_property_form_elements(module, form, properties, values)

		for policy in module.policies:
			self.add_form_element(form, 'policies[%s]' % (policy['objectType']), '', label=policy['label'])

		meta_layout['layout'].append('')
		self.add_form_element(form, '', _('Create %s') % (module.object_name,), type='submit')

		form = self.add_form(result, action=self.request.full_url(), method='GET', id='position', layout='position')  # FIXME: preserve query string
		self.add_form_element(form, 'position', position or '', element='select', options=sorted(({'value': x, 'label': ldap_dn2path(x)} for x in module.get_default_containers()), key=lambda x: x['label'].lower()))
		self.add_form_element(form, '', _('Select position'), type='submit')
		position_layout = [{'label': _('Container'), 'description': "The container in which the LDAP object shall be created.", 'layout': ['position', '']}]
		self.add_layout(result, position_layout, 'position')
		return result


class ObjectCopy(ObjectAdd):

	@sanitize_query_string(
		dn=DNSanitizer(required=True)
	)
	@tornado.gen.coroutine
	def get(self, object_type):
		module = self.get_module(object_type)
		if 'copy' not in module.operations:
			raise NotFound(object_type)

		result = {}
		self.add_link(result, 'self', self.urljoin(''), title=_('Copy %s') % (module.object_name,))
		result.update(self.get_create_form(module, dn=self.request.query_arguments['dn'], copy=True))
		self.add_caching(public=True, must_revalidate=True)
		self.content_negotiation(result)


class ObjectEdit(FormBase, Resource):
	"""GET a form containing ways to modify, remove, move a specific object"""

	@tornado.gen.coroutine
	def get(self, object_type, dn):
		dn = unquote_dn(dn)
		module = get_module(object_type, dn, self.ldap_connection)
		if module is None:
			raise NotFound(object_type, dn)

		if not set(module.operations) & {'remove', 'move', 'subtree_move', 'edit'}:
			# modification of this object type is not possible
			raise NotFound(object_type, dn)

		result = {}
		module.load(force_reload=True)  # reload for instant extended attributes

		obj = yield self.pool.submit(module.get, dn)
		if not obj:
			raise NotFound(object_type, dn)

		if object_type not in ('users/self', 'users/passwd') and not univention.admin.modules.recognize(object_type, obj.dn, obj.oldattr):
			raise NotFound(object_type, dn)

		self.add_link(result, 'icon', self.urljoin('../favicon.ico'), type='image/x-icon')
		self.add_link(result, 'udm:object-modules', self.urljoin('../../../'), title=_('All modules'))
		self.add_link(result, 'udm:object-module', self.urljoin('../../'), title=self.get_parent_object_type(module).object_name_plural)
		self.add_link(result, 'type', self.urljoin('../'), title=module.object_name)
		self.add_link(result, 'up', self.urljoin('..', quote_dn(obj.dn)), title=obj.dn)
		self.add_link(result, 'self', self.urljoin(''), title=_('Modify'))

		if 'remove' in module.operations:
			# TODO: add list of referring objects
			form = self.add_form(result, id='remove', action=self.urljoin('.').rstrip('/'), method='DELETE', layout='remove')
			remove_layout = [{'label': _('Remove'), 'description': _("Remove the object"), 'layout': ['cleanup', 'recursive', '']}]
			self.add_layout(result, remove_layout, 'remove')
			self.add_form_element(form, 'cleanup', '1', type='checkbox', checked=True, label=_('Perform a cleanup'), title=_('e.g. temporary objects, locks, etc.'))
			self.add_form_element(form, 'recursive', '1', type='checkbox', checked=True, label=_('Remove referring objects'), title=_('e.g. DNS or DHCP references of a computer'))
			self.add_form_element(form, '', _('Remove'), type='submit')

		if set(module.operations) & {'move', 'subtree_move'}:
			form = self.add_form(result, id='move', action=self.urljoin('.').rstrip('/'), method='PUT')
			self.add_form_element(form, 'position', self.ldap_connection.parentDn(obj.dn))  # TODO: replace with <select>
			self.add_form_element(form, '', _('Move'), type='submit')

		if 'edit' in module.operations:
			representation = Object.get_representation(module, obj, ['*'], self.ldap_connection)
			result.update(representation)
			for policy in module.policies:
				ptype = policy['objectType']
				form = self.add_form(result, action=self.urljoin(ptype) + '/', method='GET', name=ptype, rel='udm:policy-result')
				pol = (representation['policies'].get(ptype, ['']) or [''])[0]
				self.add_form_element(form, 'policy', pol, label=policy['label'], title=policy['description'], placeholder=_('Policy DN'))
				self.add_form_element(form, '', _('Policy result'), type='submit')

			obj.open()
			layout = Layout.get_layout(module, dn if object_type != 'users/self' else None)
			layout[0]['layout'].extend(['dn', 'jpegPhoto-preview', ''])
			properties = Properties.get_properties(module, dn)
			self.add_resource(result, 'udm:properties', {'properties': properties})
			self.add_link(result, 'udm:properties', href=self.urljoin('properties'))
			is_ad_synced_object = ucr.is_true('ad/member') and 'synced' in obj.oldattr.get('univentionObjectFlag', [])
			is_ad_synced_object = 'synced' in obj.oldattr.get('univentionObjectFlag', [])
			if is_ad_synced_object:
				layout[0]['layout'].insert(0, '$active_directory_warning$')
				properties['$active_directory_warning$'] = {'id': '$active_directory_warning$', 'label': _('The %s "%s" is part of the Active Directory domain.') % (module.object_name, obj[module.identifies])}
				self.add_form_element(form, '$active_directory_warning$', '1', type='checkbox', checked=True, label=_('The %s "%s" is part of the Active Directory domain.') % (module.object_name, obj[module.identifies]))
				for prop in properties.values():
					if prop.get('readonly_when_synced'):
						prop['disabled'] = True

			enctype = 'application/x-www-form-urlencoded'
			if obj.has_property('jpegPhoto'):
				enctype = 'multipart/form-data'
				form = self.add_form(result, action=self.urljoin('properties/jpegPhoto.jpg'), method='POST', enctype='multipart/form-data')
				self.add_form_element(form, 'jpegPhoto', '', type='file', accept='image/jpg image/jpeg image/png')
				self.add_form_element(form, '', _('Upload user photo'), type='submit')

			form = self.add_form(result, id='edit', action=self.urljoin('.').rstrip('/'), method='PUT', enctype=enctype, layout='edit-form')
			self.add_layout(result, layout, 'edit-form')
			self.add_form_element(form, 'dn', obj.dn, readonly='readonly', disabled='disabled')

			values = {}
			for key, prop in properties.items():
				if obj.module == 'users/user' and key == 'password':
					prop['required'] = False
				if prop['readonly_when_synced'] and is_ad_synced_object:
					prop['disabled'] = True
				try:
					values[key] = obj[key]  # don't use .get() !
				except KeyError:
					continue

			values = dict(decode_properties(module, obj, values))
			self.add_property_form_elements(module, form, properties, values)
			if 'jpegPhoto' in properties:
				properties['jpegPhoto-preview'] = {'id': 'jpegPhoto-preview', 'label': ' '}
				self.add_form_element(form, 'jpegPhoto-preview', '', type='image', label=' ', src=self.urljoin('properties/jpegPhoto.jpg'), alt=_('No photo set'))

			for policy in module.policies:
				ptype = policy['objectType']
				pol = (representation['policies'].get(ptype, ['']) or [''])[0]
				self.add_form_element(form, 'policies[%s]' % (ptype), pol, label=policy['label'], placeholder=_('Policy DN'))

			references = Layout.get_reference_layout(layout)
			if references:
				for reference in module.get_policy_references(obj.dn):
					if reference['module'] != 'udm':
						continue
					self.add_form_element(form, 'references', '', href=self.abspath(reference['objectType'], quote_dn(reference['id'])), label=reference['label'], element='a')
				references['layout'].append('references')

			self.add_form_element(form, '', _('Modify %s') % (module.object_name,), type='submit')

		self.add_caching(public=False, must_revalidate=True)
		self.content_negotiation(result)


class ObjectMultiEdit(ObjectEdit):
	pass


class PropertyChoices(Resource):
	"""GET udm/users/user/$DN/property/$name/choices (get possible values/choices for that property)"""

	@tornado.gen.coroutine
	def get(self, object_type, dn, property_):
		dn = unquote_dn(dn)
		module = self.get_module(object_type)
		try:
			syntax = module.module.property_descriptions[property_].syntax
		except KeyError:
			raise NotFound(object_type, dn)
		request_body = {'syntax': syntax.name}  # FIXME
		choices = yield self.pool.submit(read_syntax_choices, _get_syntax(syntax.name), request_body, ldap_connection=self.ldap_connection, ldap_position=self.ldap_position)
		self.add_caching(public=False, must_revalidate=True)
		self.content_negotiation(choices)


class PolicyResultBase(Resource):
	"""get the possible policies of the policy-type for user objects located at the containter"""

	@run_on_executor(executor='pool')
	def _get(self, object_type, policy_type, dn, is_container=False):
		"""Returns a virtual policy object containing the values that
		the given object or container inherits"""

		policy_dn = self.request.query_arguments['policy']

		if is_container:
			# editing a new (i.e. non existing) object -> use the parent container
			obj = self.get_object(get_module(None, dn, self.ldap_connection).module, dn)
		else:
			# editing an exiting UDM object -> use the object itself
			obj = self.get_object(object_type, dn)

		if policy_dn:
			policy_obj = self.get_object(policy_type, policy_dn)
		else:
			policy_obj = self.get_module(policy_type).get(None)
		policy_obj.clone(obj)

		# There are 2x2x2 (=8) cases that may occur (c.f., Bug #31916):
		# (1)
		#   [edit] editing existing UDM object
		#   -> the existing UDM object itself is loaded
		#   [new]  virtually edit non-existing UDM object (when a new object is being created)
		#   -> the parent container UDM object is loaded
		# (2)
		#   [w/pol]   UDM object has assigend policies in LDAP directory
		#   [w/o_pol] UDM object has no policies assigend in LDAP directory
		# (3)
		#   [inherit] user request to (virtually) change the policy to 'inherited'
		#   [set_pol] user request to (virtually) assign a particular policy
		faked_policy_reference = None
		if not is_container and not policy_dn:
			# case: [edit; w/pol; inherit]
			# -> current policy is (virtually) overwritten with 'None'
			faked_policy_reference = [None]
		elif is_container and policy_dn:
			# cases:
			# * [new; w/pol; inherit]
			# * [new; w/pol; set_pol]
			# -> old + temporary policy are both (virtually) set at the parent container
			faked_policy_reference = obj.policies + [policy_dn]
		else:
			# cases:
			# * [new; w/o_pol; inherit]
			# * [new; w/o_pol; set_pol]
			# * [edit; w/pol; set_pol]
			# * [edit; w/o_pol; inherit]
			# * [edit; w/o_pol; set_pol]
			faked_policy_reference = [policy_dn]

		policy_obj.policy_result(faked_policy_reference)
		infos = copy.copy(policy_obj.polinfo_more)
		for key, value in infos.items():
			if key in policy_obj.polinfo:
				if isinstance(infos[key], (tuple, list)):
					continue
				infos[key]['value'] = policy_obj.polinfo[key]
		if policy_dn:
			self.add_link(infos, 'udm:policy-edit', self.abspath(policy_obj.module, policy_dn), title=_('Click to edit the inherited properties of the policy'))
		return infos


class PolicyResult(PolicyResultBase):
	"""get the possible policies of the policy-type for user objects located at the containter
	GET udm/users/user/$userdn/policies/$policy_type/?policy=$dn (for a existing object)
	"""

	@sanitize_query_string(
		policy=DNSanitizer(required=False, default=None)
	)
	@tornado.gen.coroutine
	def get(self, object_type, dn, policy_type):
		dn = unquote_dn(dn)
		infos = yield self._get(object_type, policy_type, dn, is_container=False)
		self.add_caching(public=False, no_cache=True, must_revalidate=True, no_store=True)
		self.content_negotiation(infos)


class PolicyResultContainer(PolicyResultBase):
	"""get the possible policies of the policy-type for user objects located at the containter
	GET udm/users/user/policies/$policy_type/?policy=$dn&position=$dn (for a container, where a object should be created in)
	"""

	@sanitize_query_string(
		policy=DNSanitizer(required=False, default=None),
		position=DNSanitizer(required=True)
	)
	@tornado.gen.coroutine
	def get(self, object_type, policy_type):
		container = self.request.query_arguments['position']
		infos = yield self._get(object_type, policy_type, container, is_container=True)
		self.add_caching(public=False, no_cache=True, must_revalidate=True, no_store=True)
		self.content_negotiation(infos)


class Operations(Resource):
	"""GET /udm/progress/$progress-id (get the progress of a started operation like move, report, maybe add/put?, ...)"""

	queue = {}

	def get(self, progress):
		progressbars = self.queue.get(self.request.user_dn, {})
		if progress not in progressbars:
			raise NotFound()
		result = progressbars[progress]
		if result.get('uri'):
			self.set_status(303)
			self.add_header('Location', result['uri'])
			self.add_link(result, 'self', result['uri'])
			self.queue.get(self.request.user_dn, {}).pop(progress, {})
		else:
			self.set_status(301)
			self.add_header('Location', self.urljoin(''))
			self.add_header('Retry-After', '1')
		self.add_caching(public=False, no_store=True, no_cache=True, must_revalidate=True)
		self.content_negotiation(result)

	def get_html(self, response):
		root = super(Operations, self).get_html(response)
		if isinstance(response, dict):
			if 'value' in response and 'max' in response:
				h1 = ET.Element('h1')
				h1.text = response.get('description', '')
				root.append(h1)
				root.append(ET.Element('progress', value=str(response['value']), max=str(response['max'])))
		return root


class LicenseRequest(Resource):

	@sanitize_query_string(
		email=EmailSanitizer(required=True),
	)
	@tornado.gen.coroutine
	def get(self):
		data = {
			'email': self.request.query_arguments['email'],
			'licence': dump_license(),
		}
		if not data['licence']:
			raise HTTPError(500, _('Cannot parse License from LDAP'))

		# TODO: we should also send a link (self.request.full_url()) to the license server, so that the email can link to a url which automatically inserts the license:
		# self.request.urljoin('import', license=urllib.quote(zlib.compress(''.join(_[17:] for _ in open('license.ldif', 'rb').readlines() if _.startswith('univentionLicense')), 6)[2:-4].encode('base64').rstrip()))

		data = urllib.urlencode(data)
		url = 'https://license.univention.de/keyid/conversion/submit'
		http_client = tornado.httpclient.HTTPClient()
		try:
			yield http_client.fetch(url, method='POST', body=data, user_agent='UMC/AppCenter', headers={'Content-Type': 'application/x-www-form-urlencoded'})
		except tornado.httpclient.HTTPError as exc:
			error = str(exc)
			if exc.response.code >= 500:
				error = _('This seems to be a problem with the license server. Please try again later.')
			match = re.search('<span id="details">(?P<details>.*?)</span>', exc.response.body, flags=re.DOTALL)
			if match:
				error = match.group(1).replace('\n', '')
			# FIXME: use original error handling
			raise HTTPError(400, _('Could not request a license from Univention: %s') % (error,))

		# creating a new ucr variable to prevent duplicated registration (Bug #35711)
		handler_set(['ucs/web/license/requested=true'])
		self.add_caching(public=False, no_store=True, no_cache=True, must_revalidate=True)
		self.content_negotiation({'message': _('A new license has been requested and sent to your email address.')})


class LicenseCheck(Resource):

	def get(self):
		message = _('The license is valid.')
		try:
			check_license(self.ldap_connection)
		except LicenseError as exc:
			message = str(exc)
		self.add_caching(public=False, max_age=120, must_revalidate=True)
		self.content_negotiation(message)


class License(Resource):

	def get(self):
		license_data = {}
		self.add_link(license_data, 'udm:license-check', self.urljoin('check'), title=_('Check license status'))
		self.add_link(license_data, 'udm:license-request', self.urljoin('request'))
		self.add_link(license_data, 'udm:license-import', self.urljoin(''))

		form = self.add_form(license_data, self.urljoin('request'), 'GET', rel='udm:license-request')
		self.add_form_element(form, 'email', '', type='email', label=_('E-Mail address'))
		self.add_form_element(form, '', _('Request new license'), type='submit')

		form = self.add_form(license_data, self.urljoin('import'), 'POST', rel='udm:license-import', enctype='multipart/form-data')
		self.add_form_element(form, 'license', '', type='file', label=_('License file (ldif format)'))
		self.add_form_element(form, '', _('Import license'), type='submit')

		try:
			import univention.admin.license as udm_license
		except:
			license_data['licenseVersion'] = 'gpl'
		else:
			license_data['licenseVersion'] = udm_license._license.version
			if udm_license._license.version == '1':
				for item in ('licenses', 'real'):
					license_data[item] = {}
					for lic_type in ('CLIENT', 'ACCOUNT', 'DESKTOP', 'GROUPWARE'):
						count = getattr(udm_license._license, item)[udm_license._license.version][getattr(udm_license.License, lic_type)]
						if isinstance(count, six.string_types):
							try:
								count = int(count)
							except:
								count = None
						license_data[item][lic_type.lower()] = count

				if 'UGS' in udm_license._license.types:
					udm_license._license.types = filter(lambda x: x != 'UGS', udm_license._license.types)
			elif udm_license._license.version == '2':
				for item in ('licenses', 'real'):
					license_data[item] = {}
					for lic_type in ('SERVERS', 'USERS', 'MANAGEDCLIENTS', 'CORPORATECLIENTS'):
						count = getattr(udm_license._license, item)[udm_license._license.version][getattr(udm_license.License, lic_type)]
						if isinstance(count, six.string_types):
							try:
								count = int(count)
							except:
								count = None
						license_data[item][lic_type.lower()] = count
				license_data['keyID'] = udm_license._license.licenseKeyID
				license_data['support'] = udm_license._license.licenseSupport
				license_data['premiumSupport'] = udm_license._license.licensePremiumSupport

			license_data['licenseTypes'] = udm_license._license.types
			license_data['oemProductTypes'] = udm_license._license.oemProductTypes
			license_data['endDate'] = udm_license._license.endDate
			license_data['baseDN'] = udm_license._license.licenseBase
			free_license = ''
			if license_data['baseDN'] == 'Free for personal use edition':
				free_license = 'ffpu'
			if license_data['baseDN'] == 'UCS Core Edition':
				free_license = 'core'
			if free_license:
				license_data['baseDN'] = ucr.get('ldap/base', '')
			license_data['freeLicense'] = free_license
			license_data['sysAccountsFound'] = udm_license._license.sysAccountsFound
		self.add_caching(public=False, max_age=120, must_revalidate=True)
		self.content_negotiation(license_data)


class LicenseImport(Resource):

	def get(self):
		text = '''dn: cn=admin,cn=license,cn=univention,%(ldap/base)s
cn: admin
objectClass: top
objectClass: univentionLicense
objectClass: univentionObject
univentionObjectType: settings/license
''' % ucr
		for line in zlib.decompress(unquote(text).decode('base64'), -15).splitlines():
			text += 'univentionLicense%s\n' % (line.strip(),)

		self.import_license(io.BytesIO(text))

	def post(self):
		return self.import_license(io.BytesIO(self.request.files['license'][0]['body']))

	def import_license(self, fd):
		try:
				# check license and write it to LDAP
				importer = LicenseImporter(fd)
				importer.check(ucr.get('ldap/base', ''))
				importer.write(self.ldap_connection)
		except ldap.LDAPError as exc:
			# LDAPError e.g. LDIF contained non existing attributes
			raise HTTPError(400, _('Importing the license failed: LDAP error: %s.') % exc.args[0].get('info'))
		except (ValueError, AttributeError) as exc:
			# AttributeError: missing univentionLicenseBaseDN
			# ValueError raised by ldif.LDIFParser when e.g. dn is duplicated
			raise HTTPError(400, _('Importing the license failed: %s.') % (exc,))
		except LicenseError as exc:
			raise HTTPError(400, str(exc))
		self.content_negotiation({'message': _('The license was imported successfully.')})


def decode_properties(module, obj, properties):
	for key, value in properties.items():
		prop = module.get_property(key)
		codec = udm_types.TypeHint.detect(prop, key)
		yield key, codec.decode_json(value)


def encode_properties(module, obj, properties):
	for key, value in properties.items():
		prop = module.get_property(key)
		codec = udm_types.TypeHint.detect(prop, key)
		yield key, codec.encode_json(value)


def quote_dn(dn):
	if isinstance(dn, six.text_type):
		dn = dn.encode('utf-8')
	# duplicated slashes in URI path's can be normalized to one slash. Therefore we need to escape the slashes.
	return quote(dn.replace(b'//', b',/=/,'))  # .replace('/', quote('/', safe=''))


def unquote_dn(dn):
	# tornado already decoded it (UTF-8)
	return dn.replace(u',/=/,', u'//')


def last_modified(date):
	return '%s, %02d %s %04d %02d:%02d:%02d GMT' % (
		('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')[date.tm_wday],
		date.tm_mday,
		('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')[date.tm_mon - 1],
		date.tm_year, date.tm_hour, date.tm_min, date.tm_sec
	)


def _try(func, exceptions):
	def deco(*args, **kwargs):
		try:
			return func(*args, **kwargs)
		except exceptions:
			pass
	return deco


def _map_try(values, func, exceptions):
	return filter(None, map(_try(func, exceptions), values))


def _map_normalized_dn(dns):
	return _map_try(dns, lambda dn: ldap.dn.dn2str(ldap.dn.str2dn(dn)), Exception)


class Application(tornado.web.Application):

	def __init__(self, **kwargs):
		#module_type = '([a-z]+)'
		module_type = '(%s)' % '|'.join(re.escape(mod) for mod in Modules.mapping.keys())
		object_type = '([a-z]+/[a-z_]+)'
		policies_object_type = '(policies/[a-z_]+)'
		dn = '((?:[^/]+%s.+,)?%s)' % (self.multi_regex('='), self.multi_regex(ucr['ldap/base']),)
		# FIXME: with that dn regex, it is not possible to have urls like (/udm/$dn/foo/$dn/) because ldap-base at the end matches the last dn
		# Note: the ldap base is part of the url to support "/" as part of the DN. otherwise we can use: '([^/]+(?:=|%3d|%3D)[^/]+)'
		# Note: we cannot use .replace('/', '%2F') for the dn part as url-normalization could replace this and apache doesn't pass URLs with %2F to the ProxyPass without http://httpd.apache.org/docs/current/mod/core.html#allowencodedslashes
		property_ = '([^/]+)'
		super(Application, self).__init__([
			(r"/(?:udm/)?(favicon).ico", Favicon, {"path": "/var/www/favicon.ico"}),
			(r"/udm/(?:index.html)?", Modules),
			(r"/udm/openapi.json", OpenAPI),
			(r"/udm/relation/(.*)", Relations),
			(r"/udm/license/", License),
			(r"/udm/license/import", LicenseImport),
			(r"/udm/license/check", LicenseCheck),
			(r"/udm/license/request", LicenseRequest),
			(r"/udm/ldap/base/", LdapBase),
			(r"/udm/object/%s" % (dn,), ObjectLink),
			(r"/udm/object/([a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12})", ObjectByUiid),
			(r"/udm/%s/" % (module_type,), ObjectTypes),
			(r"/udm/(navigation)/tree", Tree),
			(r"/udm/(%s|navigation)/move-destinations/" % (object_type,), MoveDestinations),
			(r"/udm/navigation/children-types/", SubObjectTypes),
			(r"/udm/%s/" % (object_type,), Objects),
			(r"/udm/%s/openapi.json" % (object_type,), OpenAPI),
			(r"/udm/%s/add" % (object_type,), ObjectAdd),
			(r"/udm/%s/copy" % (object_type,), ObjectCopy),
			(r"/udm/%s/move" % (object_type,), ObjectsMove),
			(r"/udm/%s/multi-edit" % (object_type,), ObjectMultiEdit),
			(r"/udm/%s/tree" % (object_type,), Tree),
			(r"/udm/%s/properties" % (object_type,), Properties),
			(r"/udm/%s/layout" % (object_type,), Layout),
			(r"/udm/%s/favicon.ico" % (object_type,), Favicon, {"path": "/usr/share/univention-management-console-frontend/js/dijit/themes/umc/icons/16x16/"}),
			(r"/udm/%s/%s" % (object_type, dn), Object),
			(r"/udm/%s/%s/edit" % (object_type, dn), ObjectEdit),
			(r"/udm/%s/%s/children-types/" % (object_type, dn), SubObjectTypes),
			(r"/udm/%s/report/([^/]+)" % (object_type,), Report),
			(r"/udm/%s/%s/%s/" % (object_type, dn, policies_object_type), PolicyResult),
			(r"/udm/%s/%s/" % (object_type, policies_object_type), PolicyResultContainer),
			(r"/udm/%s/%s/layout" % (object_type, dn), Layout),
			(r"/udm/%s/%s/properties" % (object_type, dn), Properties),
			(r"/udm/%s/%s/properties/choices" % (object_type, dn), Properties),
			(r"/udm/%s/%s/properties/%s/choices" % (object_type, dn, property_), PropertyChoices),
			(r"/udm/%s/%s/properties/jpegPhoto.jpg" % (object_type, dn), UserPhoto),
			(r"/udm/%s/properties/%s/default" % (object_type, property_), DefaultValue),
			(r"/udm/networks/network/%s/next-free-ip-address" % (dn,), NextFreeIpAddress),
			(r"/udm/progress/([a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12})", Operations),
			# TODO: decorator for dn argument, which makes sure no invalid dn syntax is used
		], default_handler_class=Nothing, **kwargs)

	def multi_regex(self, chars):
		# Bug in tornado: requests go against the raw url; https://github.com/tornadoweb/tornado/issues/2548, therefore we must match =, %3d, %3D
		return ''.join('(?:%s|%s|%s)' % (re.escape(c), re.escape(urllib.quote(c).lower()), re.escape(urllib.quote(c).upper())) if c in '=,' else re.escape(c) for c in chars)
