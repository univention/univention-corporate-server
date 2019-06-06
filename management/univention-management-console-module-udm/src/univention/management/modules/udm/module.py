#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  Univention Directory Manager Module
#
# Copyright 2017-2019 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import re
import json
import time
import copy
import urllib
import base64
import binascii
import tempfile
from urlparse import urljoin, urlparse, urlunparse, parse_qs
from urllib import quote
import traceback

import tornado.web
import tornado.gen
import tornado.log
import tornado.ioloop
import tornado.httpclient
from tornado.web import RequestHandler, HTTPError
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor

import ldap
from ldap.filter import filter_format
from ldap.dn import explode_rdn
from ldap.controls import SimplePagedResultsControl
import xml.etree.cElementTree as ET

from univention.management.console.config import ucr
from univention.management.console.ldap import get_user_connection, get_machine_connection
from univention.management.console.modules.udm.udm_ldap import get_module, set_bind_function, UDM_Module, ldap_dn2path, read_syntax_choices, _get_syntax, container_modules, UDM_Error
from univention.management.console.modules.udm.udm_ldap import SuperordinateDoesNotExist, NoIpLeft, SearchLimitReached
from univention.management.console.modules.udm.tools import check_license, LicenseError, LicenseImport, dump_license
from univention.management.console.error import UMC_Error, LDAP_ServerDown, LDAP_ConnectionFailed

import univention.directory.reports as udr
import univention.admin.uexceptions as udm_errors
import univention.admin.modules as udm_modules
from univention.config_registry import handler_set

import univention.udm

from univention.lib.i18n import Translation
# TODO: PAM authentication ?
# TODO: set Last-Modified
# FIXME: add_asterisks sanitizer
# FIXME: prevent in the javascript UMC module that navigation container query is called with container=='None'
# TODO: translation
# FIXME: it seems request.path contains the un-urlencoded path, could be security issue!
# TODO: 0f77c317e03844e8a16c484dde69abbcd2d2c7e3 is not integrated
# TODO: replace etree with genshi, etc.

_ = Translation('univention-management-console-module-udm').translate

MAX_WORKERS = 35


class NotFound(HTTPError):

	def __init__(self, object_type, dn=None):
		super(NotFound, self).__init__(404, None, '%r %r' % (object_type, dn or ''))  # FIXME: create error message


class RessourceBase(object):

	pool = ThreadPoolExecutor(max_workers=MAX_WORKERS)

	authenticated = {}

	def force_authorization(self):
		self.set_header('WWW-Authenticate', 'Basic realm="Univention Management Console"')
		self.set_status(401)
		self.finish()

	def prepare(self):
		self.request.path_decoded = urllib.unquote(self.request.path)
		authorization = self.request.headers.get('Authorization')
		if not authorization:
			return self.force_authorization()

		try:
			self.parse_authorization(authorization)
		finally:
			self.request.content_negotiation_lang = self.check_acceptable()
			self.decode_request_arguments()

	def parse_authorization(self, authorization):
		if authorization in self.authenticated:
			(self.request.user_dn, self.request.username, self.ldap_connection, self.ldap_position) = self.authenticated[authorization]
			if self.ldap_connection.whoami():
				return
		try:
			if not authorization.lower().startswith('basic '):
				raise ValueError()
			username, password = base64.decodestring(authorization.split(' ', 1)[1]).split(':', 1)
		except (ValueError, IndexError, binascii.Error):
			raise HTTPError(400)

		lo, po = get_machine_connection(write=False)
		try:
			userdn = lo.searchDn(filter_format('(&(objectClass=person)(uid=%s))', [username]), unique=True)[0]
			self.ldap_connection, self.ldap_position = get_user_connection(bind=lambda lo: lo.bind(userdn, password), write=True)
			set_bind_function(lambda lo: lo.bind(userdn, password))
			self.request.user_dn = userdn
			self.request.username = username
		except:
			return self.force_authorization()
		else:
			self.authenticated[authorization] = (userdn, username, self.ldap_connection, self.ldap_position)

	def get_module(self, object_type):
		module = UDM_Module(object_type)
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
			for part in (x for x in parts[1:] if x.startswith("q=")):
				try:
					score = float(part)
					break
				except (ValueError, TypeError):
					score = 0.0
			langs.append((parts[0].strip(), score))
		langs.sort(key=lambda pair: pair[1], reverse=True)
		lang = None
		for name, q in langs:
			if name in ('text/html', 'text/xml', 'application/xml', 'text/*', '*/*'):
				lang = 'html'
				break
			elif name in ('application/json', 'application/*'):
				lang = 'json'
				break
		if not lang:
			raise HTTPError(406)
		return lang

	def decode_request_arguments(self):
		if self.request.headers.get('Content-Type', '').startswith('application/json'):
			try:
				self.request.body_arguments = json.loads(self.request.body)
			except ValueError as exc:
				raise HTTPError(400, _('Invalid JSON document: %r') % (exc,))

	def get_body_argument(self, name, *args):
		if self.request.headers.get('Content-Type', '').startswith('application/json'):
			return self.request.body_arguments.get(name)
		return super(Ressource, self).get_body_argument(name, *args)

	def get_body_arguments(self, name, *args):
		if self.request.headers.get('Content-Type', '').startswith('application/json'):
			return self.request.body_arguments.get(name)
		return super(Ressource, self).get_body_arguments(name, *args)

	def content_negotiation(self, response):
		lang = self.request.content_negotiation_lang
		formatter = getattr(self, '%s_%s' % (self.request.method.lower(), lang), getattr(self, 'get_%s' % (lang,)))
		codec = getattr(self, 'content_negotiation_%s' % (lang,))
		self.finish(codec(formatter(response)))

	def content_negotiation_json(self, response):
		self.set_header('Content-Type', 'application/json')
		return json.dumps(response)

	def content_negotiation_html(self, response):
		self.set_header('Content-Type', 'text/html')

		root = ET.Element("html")
		head = ET.SubElement(root, "head")
		titleelement = ET.SubElement(head, "title")
		titleelement.text = 'FIXME: fallback'
		body = ET.SubElement(root, "body")
		for link in self._headers.get_list('Link'):
			link, foo, _params = link.partition(';')
			link = link.strip().lstrip('<').rstrip('>')
			params = {}
			if _params.strip():
				params = dict((x.strip(), y.strip().strip('"')) for x, y in ((param.split('=', 1) + [''])[:2] for param in _params.split(';')))
			ET.SubElement(head, "link", href=link, **params)
			ET.SubElement(body, "a", href=link, **params).text = params.get('title', link) or link
			ET.SubElement(body, "br")
			if params.get('rel') == 'self':
				titleelement.text = params.get('title') or link or 'FIXME:notitle'

		if isinstance(response, (list, tuple)):
			body.extend(response)
		elif response is not None:
			body.append(response)

		self.write('<!DOCTYPE html>\n')
		tree = ET.ElementTree(root)
		tree.write(self)

	def get_json(self, response):
		return response

	def get_html(self, response):
		root = []
		if isinstance(response, dict):
			for key in ('entries', 'error', 'errors'):
				if response.get(key):
					response = response[key]
					break
		if isinstance(response, (list, tuple)):
			for thing in response:
				if isinstance(thing, dict) and thing.get('uri'):
					x = thing.copy()
					a = ET.Element("a", href=x.pop('uri'), rel="/udm/relation/object")
					a.text = x.get('dn')
					pre = ET.Element("pre")
					pre.text = json.dumps(x, indent=4)
					root.append(ET.Element("br"))
					root.append(a)
					root.append(pre)
					root.append(ET.Element("br"))
				else:
					pre = ET.Element("pre")
					pre.text = json.dumps(thing, indent=4)
					root.append(pre)
					root.append(ET.Element("br"))
		else:
			pre = ET.Element("pre")
			pre.text = json.dumps(response, indent=4)
			root.append(pre)
		return root

	def urljoin(self, *args):
		base = urlparse(self.request.full_url())
		return urljoin(urljoin(urlunparse((base.scheme, base.netloc, 'univention/' if self.request.headers.get('X-Forwarded-Host') else '/', '', '', '')), self.request.path_decoded.lstrip('/')), '/'.join(args))

	def add_link(self, obj, relation, href, **kwargs):
		links = obj.setdefault('_links', {})
		links.setdefault(relation, []).append(dict(kwargs, href=href))
		self.add_header('Link', '<%s>; rel="%s"; name="%s"; title="%s"' % (href, relation, kwargs.get('name', ''), kwargs.get('title', '')))  # TODO: quoting

	def write_error(self, status_code, exc_info=None, **kwargs):
		if not exc_info:  # or isinstance(exc_info[1], HTTPError):
			return super(Ressource, self).write_error(status_code, exc_info=exc_info, **kwargs)

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
		if isinstance(exc, UMC_Error):
			status_code = exc.status
			title = exc.msg

		if not isinstance(exc, (UDM_Error, UMC_Error)) and status_code >= 500:
			_traceback = traceback.format_exception(etype, exc, etraceback)

		if not self.settings.get("serve_traceback"):
			_traceback = None

		self.set_status(status_code)
		self.content_negotiation({
			'error': {
				'title': title,
				'code': status_code,
				'message': message,
				'traceback': _traceback,
			},
		})

	def add_caching(self, expires=None):
		cache_control = ''
		if cache_control:
			self.add_header('Cache-Control', cache_control)
		if expires:
			self.add_header('Expires', expires)


class Ressource(RessourceBase, RequestHandler):
	pass


class Favicon(RessourceBase, tornado.web.StaticFileHandler):

	@classmethod
	def get_absolute_path(cls, root, object_type):
		value = object_type.replace('/', '-')
		if not value.replace('-', '').replace('_', '').isalpha():
			raise NotFound(object_type)
		return '/usr/share/univention-management-console-frontend/js/dijit/themes/umc/icons/16x16/udm-%s.png' % (value,)


class Relations(Ressource):

	def get(self, relation):
		relations = {
			# IANA:
			'search': 'Refers to a resource that can be used to search through the link\'s context and related resources.',
			'create-form': 'The target IRI points to a resource where a submission form can be obtained.',
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
			# Univention:
			'object': '',
			'object-modules': 'list of available module categories',
			'object-modules/all': 'list of all available modules',
			'object-types': 'list of object types matching the given flavor or container',
			'properties': 'properties of the given object type',
			'options': 'options specified for the given object type',
			'layout': 'layout information for the given object type',
			'templates': 'list of template objects for the given object type',
			'default-containers': 'list of default containers for the given object type',
			'tree': 'list of tree content for providing a hierarchical navigation',
			'policies': 'list of policy types that apply to the given object type',  # virtual policy object containing the values that the given object or container inherits
			'report-types': 'list of reports for the given object type',
			'default-search': 'default search pattern/value for the given object property',
			'next-free-ip': 'next IP configuration based on the given network object',
			'property-choices': 'determine valid values for a given syntax class',
			'object/remove': 'remove this object, edit-form is preferable',
			'object/edit': 'modify this object, edit-form is preferable',
			'license-request': 'Request a new UCS Core Edition license',
			'license-check': 'Check if the license limits are reached',
			'license-import': 'Import a new license in LDIF format',
		}
		result = relations.get(relation)
		self.content_negotiation(result)


class Modules(Ressource):

	mapping = {
		'users': 'users/user',
		'computers': 'computers/computer',
		'groups': 'groups/group',
		'networks': 'networks/network',
		'dhcp': 'dhcp/dhcp',
		'dns': 'dns/dns',
		'shares': 'shares/share',
		'printers': 'shares/print',
		'mail': 'mails/mail',
		'nagios': 'nagios/nagios',
		'policies': 'policies/policy',
		'self': 'users/self',
		#'directory': 'navigation',
	}

	def get(self):
		result = {}
		for main_type in self.mapping:
			self.add_link(result, '/udm/relation/object-modules', self.urljoin(quote(main_type)) + '/', name=main_type)
		self.add_link(result, '/udm/relation/object-modules', self.urljoin('navigation') + '/', name='all')
		self.add_link(result, '/udm/relation/object-modules/all', self.urljoin('navigation') + '/', name='all')
		self.add_link(result, '/udm/relation/object-modules', self.urljoin('license') + '/', name='license')
		self.content_negotiation(result)


class ObjectTypes(Ressource):
	"""get the object types of a specific flavor"""

	def get(self, module_type):
		"""Returns the list of object types matching the given flavor or container.

		requests.options = {}
			'superordinate' -- if available only types for the given superordinate are returned (not for the navigation)
			'container' -- if available only types suitable for the given container are returned (only for the navigation)
		"""
		object_type = Modules.mapping.get(module_type)
		if not object_type:
			raise NotFound(object_type)

		superordinate = self.get_query_argument('superordinate', None)
		module = UDM_Module(object_type)
		if superordinate:
			module = get_module(object_type, superordinate, self.ldap_connection) or module  # FIXME: the object_type param is wrong?!

		result = {}
		result['entries'] = module.child_modules or []
		if not result['entries'] and module.module:
			result['entries'].append({'id': module.name, 'label': module.title})

		self.add_link(result, 'parent', self.urljoin('../'), title=_('Object modules'), name='FIXME:udm/relation/object-modules')  # FIXME: name is wrong
		self.add_link(result, 'self', self.urljoin(''))
		for mod in result['entries']:
			self.add_link(result, '/udm/relation/object-types', self.urljoin('../%s' % quote(mod['id'])) + '/', name=mod['id'], title=mod['label'])
		self.content_negotiation(result)


class ObjectTypesNavigation(Ressource):

	def get(self):
		superordinate = self.get_query_argument('superordinate', None)
		container = self.get_query_argument('container', None) or superordinate
		result = {}
		if not container:
			# no container is specified, return all existing object types
			entries = [{
				'id': module[0],
				'label': getattr(module[1], 'short_description', module[0])
			} for module in udm_modules.modules.items()]
			for mod in entries:
				self.add_link(result, '/udm/relation/object-types', self.urljoin('../%s' % quote(mod['id'])) + '/', name=mod['id'], title=mod['label'])
			result['entries'] = entries
			self.content_negotiation(result)
			return

		if 'None' == container:
			# if 'None' is given, use the LDAP base
			container = ucr.get('ldap/base')

		# create a list of modules that can be created
		# ... all container types except container/dc
		allowed_modules = set([m for m in udm_modules.containers if udm_modules.name(m) != 'container/dc'])

		# the container may be a superordinate or have one as its parent
		# (or grandparent, ....)
		superordinate = udm_modules.find_superordinate(container, None, self.ldap_connection)
		if superordinate:
			# there is a superordinate... add its subtypes to the list of allowed modules
			allowed_modules.update(udm_modules.subordinates(superordinate))
		else:
			# add all types that do not have a superordinate
			allowed_modules.update(mod for mod in udm_modules.modules.values() if not udm_modules.superordinates(mod))

		# make sure that the object type can be created
		allowed_modules = [mod for mod in allowed_modules if udm_modules.supports(mod, 'add')]

		# return the final list of object types
		entries = [{
			'id': udm_modules.name(module),
			'label': getattr(module, 'short_description', udm_modules.name(module))
		} for module in allowed_modules]
		for mod in entries:
			self.add_link(result, '/udm/relation/object-types', self.urljoin('../%s' % quote(mod['id'])) + '/', name=mod['id'], title=mod['label'])
		result['entries'] = entries
		self.content_negotiation(result)


class ContainerQueryBase(Ressource):

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
					'label': UDM_Module(object_type).title,
					'icon': 'udm-%s' % (object_type.replace('/', '-'),),
				})
			self.add_link({}, 'next', self.urljoin('?container=%s' % (quote(container))))
			raise tornado.gen.Return([dict({
				'id': container,
				'label': ldap_dn2path(container),
				'icon': 'udm-container-dc',
				'path': ldap_dn2path(container),
				'objectType': 'container/dc',
				'$operations$': UDM_Module('container/dc').operations,
				'$flags$': [],
				'$childs$': True,
				'$isSuperordinate$': False,
			}, **defaults)])

		result = []
		for xmodule in modules:
			xmodule = UDM_Module(xmodule)
			superordinate = univention.admin.objects.get_superordinate(xmodule.module, None, self.ldap_connection, container)  # TODO: should also better be in a thread
			try:
				items = yield self.pool.submit(xmodule.search, container, scope=scope, superordinate=superordinate)
				for item in items:
					module = UDM_Module(item.module)
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

	@tornado.gen.coroutine
	def get(self, object_type):
		ldap_base = ucr['ldap/base']
		container = self.get_query_argument('container', None)

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
		self.content_negotiation(containers)


class MoveDestinations(ContainerQueryBase):

	@tornado.gen.coroutine
	def get(self, object_type):
		scope = 'one'
		modules = container_modules()
		container = self.get_query_argument('container', None)
		if not container:
			scope = 'base'

		containers = yield self._container_query(object_type, container, modules, scope)
		self.content_negotiation(containers)


class Properties(Ressource):
	"""GET udm/users/user/properties (get properties of users/user object type)"""

	def get(self, object_type, dn=None):
		if dn:
			dn = unquote_dn(dn)
		module = self.get_module(object_type)
		module.load(force_reload=True)  # reload for instant extended attributes

		properties = module.get_properties(dn)
		searchable = self.get_query_argument('searchable', False)
		if searchable:
			properties = [prop for prop in properties if prop.get('searchable', False)]

		self.content_negotiation(properties)


class Options(Ressource):
	"""GET udm/users/user/options (get options of users/user object type)"""

	def get(self, object_type):
		"""Returns the options specified for the given object type"""
		result = self.get_module(object_type).options.keys()
		self.content_negotiation(result)


class Layout(Ressource):
	"""GET udm/users/user/$dn/layout (get layout of users/user object type)"""

	def get(self, object_type, dn=None):
		"""Returns the layout information for the given object type."""

		module = self.get_module(object_type)
		module.load(force_reload=True)  # reload for instant extended attributes

		if object_type == 'users/self':
			dn = None

		if dn:
			dn = unquote_dn(dn)
		result = module.get_layout(dn)
		self.content_negotiation(result)


class Templates(Ressource):
	"""GET udm/users/user/templates (get the list of templates of users/user object type)"""

	def get(self, object_type):
		"""Returns the list of template objects for the given object"""

		module = self.get_module(object_type)
		result = []
		if module.template:
			template = UDM_Module(module.template)
			objects = template.search(ucr.get('ldap/base'))
			for obj in objects:
				obj.open()
				result.append({'id': obj.dn, 'label': obj[template.identifies]})

		self.content_negotiation(result)


class DefaultContainers(Ressource):
	"""GET udm/users/user/containers (get default containers for users/user)"""

	def get(self, object_type):
		"""Returns the list of default containers for the given object
		type. Therefor the python module and the default object in the
		LDAP directory are searched.
		"""
		module = self.get_module(object_type)
		containers = [{'id': x, 'label': ldap_dn2path(x)} for x in module.get_default_containers()]
		containers.sort(cmp=lambda x, y: cmp(x['label'].lower(), y['label'].lower()))
		self.content_negotiation(containers)


class Policies(Ressource):
	"""GET udm/users/user/policies (get the list of policy-types that apply for users/user object type)"""

	def get(self, object_type):
		module = self.get_module(object_type)
		result = module.policies
		self.content_negotiation(result)


class ReportingBase(Ressource):

	def initialize(self):
		self.reports_cfg = udr.Config()


class ReportTypes(ReportingBase):
	"""GET udm/users/user/report-types (get report-types of users/*)"""

	def get(self, object_type):
		"""Returns a list of reports for the given object type"""
		# i18n: translattion for univention-directory-reports
		# _('PDF Document')
		result = [{'id': name, 'label': _(name)} for name in sorted(self.reports_cfg.get_report_names(object_type))]
		self.content_negotiation(result)


class Report(ReportingBase):
	"""GET udm/users/user/report/$report_type?dn=...&dn=... (create a report of users)"""

	@tornado.gen.coroutine
	def get(self, object_type, report_type):
		# TODO: better use only POST because GET is limited in argument length sometimes?
		dns = self.get_query_arguments('dn')
		yield self.create_report(object_type, report_type, dns)

	@tornado.gen.coroutine
	def post(self, object_type, report_type):
		# TODO: 202 accepted with progress?
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


class NextFreeIpAddress(Ressource):
	"""GET udm/networks/network/$DN/next-ip (get the next free IP in this network)"""

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

		self.content_negotiation(result)

		if self.request.get_query_argument('increaseCounter'):
			# increase the next free IP address
			obj.stepIp()
			obj.modify()


class DefaultValue(Ressource):
	"""GET udm/users/user/properties/$property/default (get the default value for the specified property)"""

	def get(self, object_type, property_):
		module = self.get_module(object_type)
		result = module.get_default_values(property_)
		self.content_negotiation(result)


class Objects(Ressource):

	@tornado.gen.coroutine
	def get(self, object_type):
		"""GET udm/users/user/ (nach Benutzern suchen)"""
		module = self.get_module(object_type)
		result = self._options(object_type)

		# TODO: replace the superordinate concept by container
		superordinate = self.get_query_argument('superordinate', None)

		container = self.get_query_argument('position', None)
		objectProperty = self.get_query_argument('property', None)
		objectPropertyValue = self.get_query_argument('propertyvalue', '*')
		scope = self.get_query_argument('scope', 'sub')
		hidden = self.get_query_argument('hidden', False)
		fields = self.get_query_arguments('fields', [])
		fields = (set(fields) | set([objectProperty])) - set(['name', 'None', None, ''])
		properties = self.get_query_arguments('properties', [])
		try:
			page = int(self.get_query_argument('page', 1))
			items_per_page = int(self.get_query_argument('pagesize', None))  # TODO: rename: items-per-page, pagelength, pagecount, pagesize
			if items_per_page <= 0:
				raise ValueError()
		except (TypeError, ValueError):
			items_per_page = None
			page = None

		# TODO: add limit, page, ordering, ...
		result['query'] = {
			'position': container,
			'property': objectProperty,
			'propertyvalue': objectPropertyValue,
			'scope': 'sub',
			'hidden': '1' if hidden else '',
			'fields': list(fields),
			'page': str(page or '1'),
			'pagesize': str(items_per_page or '0'),
		}

		if superordinate:
			mod = get_module(superordinate, superordinate, self.ldap_connection)
			if not mod:
				raise SuperordinateDoesNotExist(superordinate)
			superordinate = mod.get(superordinate)
			container = container or superordinate.dn

		ctrls = {}
		serverctrls = []
		if items_per_page:
			serverctrls = [SimplePagedResultsControl(True, size=items_per_page, cookie='')]
		entries = []
		try:
			ucr['directory/manager/web/sizelimit'] = ucr.get('ldap/sizelimit', '400000')
			for i in range(page or 1):  # FIXME: iterating over searches is slower than doing it all by hand
				objects = yield self.pool.submit(module.search, container, objectProperty or None, objectPropertyValue, superordinate, scope=scope, hidden=hidden, serverctrls=serverctrls, response=ctrls)
				if ctrls.get('ctrls'):
					serverctrls[0].cookie = ctrls['ctrls'][0].cookie
		except SearchLimitReached as exc:
			objects = []
			result['errors'] = [str(exc)]

		for obj in objects or []:
			if obj is None:
				continue
			module = get_module(object_type, obj.dn, self.ldap_connection)
			if module is None:
				# This happens when concurrent a object is removed between the module.search() and get_module() call
				# MODULE.warn('LDAP object does not exists %s (flavor: %s). The object is ignored.' % (obj.dn, request.flavor))
				continue

			entry = Object.get_representation(module, obj, properties, self.ldap_connection)
			entry.update({
				'$childs$': module.childs,
				'name': module.obj_description(obj),
				'path': ldap_dn2path(obj.dn, include_rdn=False),
				'uri': self.urljoin(quote_dn(obj.dn)),
				'fields': {},  # TODO: wrap via encode_properties() instead of module.property_description() ?!
			})
			if '$value$' in fields:
				entry['$value$'] = [module.property_description(obj, column['name']) for column in module.columns]
			if '*' in fields or '*' in properties:
				obj.open()
				fields = set(obj.info.keys())
			for field in fields - set(module.password_properties) - set(entry.keys()):
				entry['fields'][field] = module.property_description(obj, field)
			entries.append(entry)

		if items_per_page:
			qs = parse_qs(urlparse(self.request.full_url()).query)
			qs['page'] = ['1']
			self.add_link(result, 'first', '%s?%s' % (self.urljoin(''), urllib.urlencode(qs, True)), title=_('First page'))
			if page > 1:
				qs['page'] = [str(page - 1)]
				self.add_link(result, 'prev', '%s?%s' % (self.urljoin(''), urllib.urlencode(qs, True)), title=_('Previous page'))
			qs['page'] = [str(page + 1)]
			self.add_link(result, 'next', '%s?%s' % (self.urljoin(''), urllib.urlencode(qs, True)), title=_('Next page'))

		result['entries'] = entries  # TODO: is "entries" a good name? items, objects
		self.content_negotiation(result)

	def get_html(self, response):
		root = super(Objects, self).get_html(response)
		if self.request.method == 'GET' and isinstance(root, list) and isinstance(response, dict) and response.get('query'):
			form = ET.Element('form', method='GET', rel='search')
			for key, value in response['query'].items():
				label = ET.Element('label', **{'for': key})
				label.text = key
				form.append(label)
				if isinstance(value, list):
					for value in value:
						form.append(ET.Element('input', type={'hidden': 'checkbox'}.get(key, 'text'), name=key, placeholder=key, value=value or ''))
				else:
					form.append(ET.Element('input', type={'hidden': 'checkbox'}.get(key, 'text'), name=key, placeholder=key, value=value or ''))
				form.append(ET.Element('br'))
			form.append(ET.Element('input', type='submit', value=_('Search')))
			root.insert(0, form)
		return root

	@tornado.gen.coroutine
	def post(self, object_type):
		"""POST udm/users/user/ (Benutzer hinzufügen)"""
		module = self.get_module(object_type)
		container = self.get_body_argument('position')
		superordinate = self.get_body_argument('superordinate')
		options = self.get_body_arguments('options')
		policies = self.get_body_arguments('policies')
		properties = self.get_body_arguments('properties')

		ldap_position = univention.admin.uldap.position(self.ldap_position.getBase())
		if container:
			ldap_position.setDn(container)
		elif superordinate:
			ldap_position.setDn(superordinate)
		else:
			if hasattr(module.module, 'policy_position_dn_prefix'):
				container = '%s,cn=policies,%s' % (self.module.policy_position_dn_prefix, ldap_position.getBase())
			else:
				defaults = module.get_default_containers()
				container = defaults[0] if defaults else ldap_position.getBase()

			ldap_position.setDn(container)

		#if superordinate:
		#	mod = get_module(module.name, superordinate, ldap_connection)
		#	if not mod:
		#		MODULE.error('Superordinate module not found: %s' % (superordinate,))
		#		raise SuperordinateDoesNotExist(superordinate)
		#	MODULE.info('Found UDM module for superordinate')
		#	superordinate = mod.get(superordinate)

		obj = module.module.object(None, self.ldap_connection, ldap_position, superordinate=superordinate)
		obj.open()
		obj.options = [opt for opt, enabled in dict(options).items() if enabled]  # TODO: AppAttributes.data_for_module(self.name).iteritems() ?
		obj.policies = reduce(lambda x, y: x + y, policies, [])
		properties = dict((prop, properties[prop]) for prop in dict(obj.items()) if obj.has_property(prop) and prop in properties)  # FIXME: remove prop in properties?!
		properties = dict(encode_properties(module.name, properties, self.ldap_connection))

		try:
			for key, value in dict(properties.items()).items():  # UDM_Error: Value may not change. key=gidNumber old=5086 new=5086
				if not obj.descriptions[key].may_change:
					if obj[key] == value:
						properties.pop(key)

			module._map_properties(obj, properties)
			dn = yield self.pool.submit(obj.create)
		except udm_errors.objectExists:
			raise
		except udm_errors.base as exc:
			UDM_Error(exc).reraise()
		self.set_header('Location', self.urljoin(quote_dn(dn)))
		self.set_status(201)
		self.content_negotiation({})

	def options(self, object_type):
		result = self._options(object_type)
		self.content_negotiation(result)

	def _options(self, object_type):
		result = {}
		module = self.get_module(object_type)
		methods = ['GET', 'OPTIONS']
		self.add_link(result, 'udm/relation/object-modules', self.urljoin('../../'), title=_('Object modules'))
		self.add_link(result, 'parent', self.urljoin('../'))
		self.add_link(result, 'self', self.urljoin(''))
		if 'search' in module.operations:
			self.add_link(result, 'search', self.urljoin(''))
		if 'add' in module.operations:
			methods.append('POST')
			self.add_link(result, 'create-form', self.urljoin('add'))
#		self.add_link(result, 'edit-form', self.urljoin('edit'))
		self.add_link(result, 'icon', self.urljoin('favicon.ico'), type='image/x-icon')
		self.add_link(result, 'udm/relation/properties', self.urljoin('properties'))
		self.add_link(result, 'udm/relation/options', self.urljoin('options'))
		self.add_link(result, 'udm/relation/layout', self.urljoin('layout'))
		self.add_link(result, 'udm/relation/templates', self.urljoin('templates'))
		self.add_link(result, 'udm/relation/default-containers', self.urljoin('default-containers'))
		self.add_link(result, 'udm/relation/tree', self.urljoin('tree'))
		self.add_link(result, 'udm/relation/policies', self.urljoin('policies'))
		self.add_link(result, 'udm/relation/report-types', self.urljoin('report-types'))
#		self.add_link(result, '', self.urljoin(''))
		self.set_header('Allow', ', '.join(methods))
		return result


class Object(Ressource):

	@tornado.gen.coroutine
	def get(self, object_type, dn):
		"""GET udm/users/user/$DN (get all properties/values of the user)"""
		dn = unquote_dn(dn)
		props = {}
		copy = bool(self.get_query_argument('copy', None))  # TODO: move into own ressource: ./copy

		if object_type == 'users/self' and not self.ldap_connection.compare_dn(dn, self.request.user_dn):
			raise HTTPError(403)

		module = get_module(object_type, dn, self.ldap_connection)
		if module is None:
			raise NotFound(object_type, dn)

		obj = yield self.pool.submit(module.get, dn)
		if not obj:
			raise NotFound(object_type, dn)
		if object_type not in ('users/self', 'users/passwd') and not univention.admin.modules.recognize(object_type, obj.dn, obj.oldattr):
			raise NotFound(object_type, dn)

		self.add_link(props, 'udm/relation/object-modules', self.urljoin('../../'), title=_('Object modules'))
		self.add_link(props, '/udm/relation/object-types', self.urljoin('../'))
		self.add_link(props, 'parent', self.urljoin('x/../'), name=module.name, title=module.object_name)
		self.add_link(props, 'self', self.urljoin(''))
		self.add_link(props, '/udm/relation/object/remove', self.urljoin(''), method='DELETE')
		self.add_link(props, '/udm/relation/object/edit', self.urljoin(''), method='PUT')
		for mod in module.child_modules:
			mod = self.get_module(mod['id'])
			if mod and set(mod.superordinate_names) & {module.name, }:
				self.add_link(props, '/udm/relation/object-types', self.urljoin('../../%s/?superordinate=%s' % (quote(mod.name), quote(obj.dn))), name=mod.name, title=mod.object_name_plural)

		props['uri'] = self.urljoin(quote_dn(obj.dn))
		props.update(self.get_representation(module, obj, ['*'], self.ldap_connection, copy))
		if set(module.operations) & {'edit', 'move', 'remove', 'subtree_move'}:
			self.add_link(props, 'edit-form', self.urljoin(quote_dn(obj.dn), 'edit'), title=_('Modify, move or remove this object'))

		meta = dict((key, [val.decode('utf-8', 'replace') for val in value]) for key, value in self.ldap_connection.get(obj.dn, attr=[b'+']).items())
		props['meta'] = meta
		self.add_header('Last-Modified', last_modified(time.strptime(meta['modifyTimestamp'][0], '%Y%m%d%H%M%SZ')))
		self.content_negotiation(props)

	@classmethod
	def get_representation(cls, module, obj, properties, ldap_connection, copy=False):
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
			for passwd in module.password_properties:
				values.pop(passwd, None)
			if '*' not in properties:
				for key in list(values.keys()):
					if key not in properties:
						values.pop(key)
			values = dict(decode_properties(module.name, values, ldap_connection))

		props = {}
		props['dn'] = obj.dn
		props['objectType'] = module.name
		props['id'] = '+'.join(explode_rdn(obj.dn, True))
		props['superordinate'] = obj.superordinate and obj.superordinate.dn
		props['position'] = ldap_connection.parentDn(obj.dn)
		props['properties'] = values
		props['options'] = dict((opt['id'], opt['value']) for opt in module.get_options(udm_object=obj))
		props['policies'] = {}
		if '*' in properties:
			for policy in obj.policies:
				pol_mod = get_module(None, policy, ldap_connection)
				if pol_mod and pol_mod.name:
					props['policies'].setdefault(pol_mod.name, []).append(policy)
			props['$references$'] = module.get_references(obj.dn)
		props['$labelObjectType$'] = module.title
		props['$labelObjectTypeSingular$'] = module.object_name
		props['$labelObjectTypePlural$'] = module.object_name_plural
		props['flags'] = obj.oldattr.get('univentionObjectFlag', [])
		props['$operations$'] = module.operations
		if copy:
			props.pop('dn')
		return props

	@tornado.gen.coroutine
	def put(self, object_type, dn):
		"""PUT udm/users/user/$DN (Benutzer hinzufügen / modifizieren)"""
		dn = unquote_dn(dn)
		module = get_module(object_type, dn, self.ldap_connection)
		if not module:
			raise NotFound(object_type)  # FIXME: create

		position = self.get_body_arguments('position')
		if position and not self.ldap_connection.compare_dn(self.ldap_connection.parentDn(dn), position):
			yield self.move(module, dn, position)
		else:
			obj = yield self.modify(module, None, dn)
			self.set_status(302)
			self.set_header('Location', self.urljoin(quote_dn(obj.dn)))

		self.content_negotiation({})

	@tornado.gen.coroutine
	def patch(self, object_type, dn):
		dn = unquote_dn(dn)
		module = get_module(object_type, dn, self.ldap_connection)
		if not module:
			raise NotFound(object_type)
		yield self.modify(module, self.request.body_arguments, dn)
		self.content_negotiation({})

	@tornado.gen.coroutine
	def modify(self, module, properties, dn):
		obj = module.module.object(None, self.ldap_connection, self.ldap_position, dn)
		obj.open()
		obj.options = [opt for opt, enabled in dict(self.get_body_arguments('options')).items() if enabled]
		obj.policies = reduce(lambda x, y: x + y, self.get_body_arguments('policies'), [])
		if properties is None:
			properties = self.get_body_arguments('properties')
			properties = dict((prop, properties[prop]) for prop in dict(obj.items()) if obj.has_property(prop) and prop in properties)  # FIXME: remove prop in properties?!

		properties = dict(encode_properties(module.name, properties, self.ldap_connection))

		validation = yield self._validate(module, properties)
		if not all(x['valid'] if isinstance(x['valid'], bool) else all(x['valid']) for x in validation):
			raise HTTPError(422)

		try:
			for key, value in dict(properties.items()).items():  # UDM_Error: Value may not change. key=gidNumber old=5086 new=5086
				if not obj.descriptions[key].may_change:
					if obj[key] == value:
						properties.pop(key)

			module._map_properties(obj, properties)
			yield self.pool.submit(obj.modify)
		except udm_errors.base as exc:
			UDM_Error(exc).reraise()
		else:
			raise tornado.gen.Return(obj)

	@tornado.gen.coroutine
	def move(self, module, dn, position):
		queue = Operations.queue.setdefault(self.request.user_dn, {})
		status = {
			'id': '1',
			'finished': False,
			'errors': False,
		}
		queue[status['id']] = status
		self.set_status(201)
		self.set_header('Location', self.urljoin('progress', status['id']))
		self.finish()
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

	@tornado.gen.coroutine
	def delete(self, object_type, dn):
		"""DELETE udm/users/user/$DN (Benutzer löschen)"""
		dn = unquote_dn(dn)
		module = get_module(object_type, dn, self.ldap_connection)
		if not module:
			raise NotFound(object_type)

		cleanup = bool(self.get_query_argument('cleanup', False))
		recursive = bool(self.get_query_argument('recursive', False))
		yield self.pool.submit(module.remove, dn, cleanup, recursive)
		self.content_negotiation({})

	def options(self, object_type, dn):
		dn = unquote_dn(dn)
		self.set_header('Allow', 'GET, PUT, DELETE, OPTIONS')

	@tornado.gen.coroutine
	def _validate(self, module, properties):  # (thread)
		"""Validates the correctness of values for properties of the
		given object type. Therefor the syntax definition of the properties is used.

		return: [ { 'property' : <name>, 'valid' : (True|False), 'details' : <message> }, ... ]
		"""

		result = []
		for property_name, value in properties.items():
			# ignore special properties named like $.*$, e.g. $options$
			if property_name.startswith('$') and property_name.endswith('$'):
				continue
			property_obj = module.get_property(property_name)

			if property_obj is None:
				raise HTTPError(400, None, _('Property %s not found') % property_name)

			# FIXME: the following seems to be obsolete since encode_properties() is called?!
			#if not property_obj.multivalue:
			#	value = value[0]

			# check each element if 'value' is a list
			if isinstance(value, (tuple, list)) and property_obj.multivalue:
				subResults = []
				subDetails = []
				for ival in value:
					try:
						property_obj.syntax.parse(ival)
						subResults.append(True)
						subDetails.append('')
					except (udm_errors.valueInvalidSyntax, udm_errors.valueError, TypeError) as exc:
						subResults.append(False)
						subDetails.append(str(exc))
				result.append({'property': property_name, 'valid': subResults, 'details': subDetails})
			# otherwise we have a single value
			else:
				try:
					property_obj.syntax.parse(value)
					result.append({'property': property_name, 'valid': True})
				except (udm_errors.valueInvalidSyntax, udm_errors.valueError) as exc:
					result.append({'property': property_name, 'valid': False, 'details': str(exc)})
		raise tornado.gen.Return(result)


class ObjectAdd(Ressource):
	"""GET a form containing information about all properties, methods, URLs to create a specific object"""

	@tornado.gen.coroutine
	def get(self, object_type):
		self.content_negotiation({})


class ObjectEdit(Ressource):
	"""GET a form containing ways to modify, remove, move a specific object"""

	@tornado.gen.coroutine
	def get(self, object_type, dn):
		dn = unquote_dn(dn)
		module = get_module(object_type, dn, self.ldap_connection)
		if module is None:
			raise NotFound(object_type, dn)

		obj = yield self.pool.submit(module.get, dn)
		if not obj:
			raise NotFound(object_type, dn)
		if object_type not in ('users/self', 'users/passwd') and not univention.admin.modules.recognize(object_type, obj.dn, obj.oldattr):
			raise NotFound(object_type, dn)
		result = {'module': module, 'object': obj}
		self.content_negotiation(result)

	def get_html(self, response):
		root = []
		mod = response['module']
		obj = response['object']
		if 'remove' in mod.operations:
			form = ET.Element('form', action=self.urljoin('.').rstrip('/'), method='DELETE', rel='')
			form.append(ET.Element('input', type='submit', value=_('Remove')))
			root.append(form)
			root.append(ET.Element('br'))
		if set(mod.operations) & {'move', 'subtree_move'}:
			form = ET.Element('form', action=self.urljoin('.').rstrip('/'), method='PUT', rel='')
			form.append(ET.Element('input', type='text', name='position', value=obj.position.getDn()))
			form.append(ET.Element('input', type='submit', value=_('Move')))
			root.append(form)
			root.append(ET.Element('br'))
		if 'edit' in mod.operations:
			form = ET.Element('form', action=self.urljoin('.').rstrip('/'), method='PUT', rel='')
			for key, value in encode_properties(obj.module, obj.info, self.ldap_connection):
				label = ET.Element('label', **{'for': key})
				label.text = key
				form.append(label)
				form.append(ET.Element('input', type='text', value=str(value), name=key))
				form.append(ET.Element('br'))
			form.append(ET.Element('input', type='submit', value=_('Modify')))
			root.append(form)
		return root


class PropertyChoices(Ressource):
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
		self.content_negotiation(choices)


class PolicyTypes(Ressource):
	"""GET udm/users/user/$DN/policies/$policy_type (get the policies of policy-type for the given object)"""

	def get(self, object_type, dn, policy_type):
		"""Returns a list of policy types that apply to the given object type"""
		dn = unquote_dn(dn)
		module = self.get_module(object_type)
		result = module.policies
		self.content_negotiation(result)


class PolicyResult(Ressource):
	"""GET udm/users/user/policies/$policy_type/$dn?container=true...&policy=... (get the possible policies of the policy-type for user objects located at the containter)"""

	@tornado.gen.coroutine
	def get(self, object_type, policy_type, dn):
		dn = unquote_dn(dn)
		infos = yield self._get(object_type, policy_type, dn)
		self.content_negotiation(infos)

	@run_on_executor(executor='pool')
	def _get(self, object_type, policy_type, dn):
		"""Returns a virtual policy object containing the values that
		the given object or container inherits"""

		dn = unquote_dn(dn)
		is_container = bool(self.get_query_argument('container', None))
		policy_dn = self.get_query_argument('policy', None)

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
		return infos


class Operations(Ressource):
	"""GET /udm/progress/$progress-id (get the progress of a started operation like move, report, maybe add/put?, ...)"""

	queue = {}

	def get(self, progress):
		result = self.queue.get(self.request.user_dn, {}).get(progress, {})
		if result.get('uri'):
			self.set_status(303)
			self.add_header('Location', result['uri'])
			self.add_link
		self.content_negotiation(result)


class LicenseRequest(Ressource):

	@tornado.gen.coroutine
	def get(self):
		data = {
			'email': self.get_query_argument('email'),
			'licence': dump_license(),
		}
		if not data['licence']:
			raise HTTPError(400, _('Cannot parse License from LDAP'))

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
			raise HTTPError(400, _('Requesting license failed: %s') % (error,))

		# creating a new ucr variable to prevent duplicated registration (Bug #35711)
		handler_set(['ucs/web/license/requested=true'])
		self.content_negotiation({'message': _('A new license has been requested.')})


class LicenseCheck(Ressource):

	def get(self):
		message = _('The license is valid.')
		try:
			check_license(self.ldap_connection)
		except LicenseError as exc:
			message = str(exc)
		self.content_negotiation(message)


class License(Ressource):

	def get(self):
		license_data = {}
		self.add_link(license_data, '/udm/relation/license-check', self.urljoin('check'), title=_('Check license status'))
		self.add_link(license_data, '/udm/relation/license-request', self.urljoin('request'))
		self.add_link(license_data, '/udm/relation/license-import', self.urljoin(''))
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
						if isinstance(count, basestring):
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
						if isinstance(count, basestring):
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
		self.content_negotiation(license_data)

	def get_html(self, response):
		root = super(License, self).get_html(response)
		if self.request.method == 'GET' and isinstance(root, list) and isinstance(response, dict):
			form = ET.Element('form', method='get', rel='/udm/relation/license-request', action=self.urljoin('request'))
			label = ET.Element('label', **{'for': 'email'})
			label.text = _('E-Mail address')
			form.append(label)
			form.append(ET.Element('input', type='email', name='email'))
			form.append(ET.Element('input', type='submit', value=_('Request new license')))
			root.insert(0, form)

			form = ET.Element('form', method='POST', enctype='multipart/form-data', rel='/udm/relation/license-import')
			label = ET.Element('label', **{'for': 'license'})
			label.text = _('License file (ldif format)')
			form.append(label)
			form.append(ET.Element('input', type='file', name='license'))
			form.append(ET.Element('input', type='submit', value=_('Import license')))
			root.insert(0, form)
		return root

	def post(self):
		lic_file = tempfile.NamedTemporaryFile(delete=False)
		lic_file.write(self.request.files['license'][0]['body'])
		lic_file.close()
		filename = lic_file.name
		try:
			with open(filename, 'rb') as fd:
				# check license and write it to LDAP
				importer = LicenseImport(fd)
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
		finally:
			os.unlink(filename)
		self.content_negotiation({'message': _('The license was imported successfully.')})


def decode_properties(object_type, properties, lo, version=1):
	mod = univention.udm.UDM(lo, version).get(object_type)
	mod.connection = lo
	codecs = mod._udm_object_class.udm_prop_class._encoders
	for key, value in properties.items():
		if key in codecs:
			mod_obj = mod._udm_object_class()
			mod_obj._udm_module = mod
			mod_obj._lo = lo
			codec = mod_obj._init_encoder(codecs[key], property_name=key)
			value = codec.decode(value)
			if key == 'jpegPhoto':
				value = value.raw.decode('latin-1')
		yield key, value


def encode_properties(object_type, properties, lo, version=1):
	mod = univention.udm.UDM(lo, version).get(object_type)
	mod.connection = lo
	codecs = mod._udm_object_class.udm_prop_class._encoders
	for key, value in properties.items():
		if key in codecs:
			mod_obj = mod._udm_object_class()
			mod_obj._udm_module = mod
			mod_obj._lo = lo
			codec = mod_obj._init_encoder(codecs[key], property_name=key)
			value = codec.encode(value)
		yield key, value


def quote_dn(dn):
	if isinstance(dn, unicode):
		dn = dn.encode('utf-8')
	return quote(dn)  # .replace('/', quote('/', safe=''))


def unquote_dn(dn):
	# tornado already decoded it (UTF-8)
	return dn


def last_modified(date):
	return '%s, %02d %s %04d %02d:%02d:%02d GMT' % (
		('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')[date.tm_wday],
		date.tm_mday,
		('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')[date.tm_mon - 1],
		date.tm_year, date.tm_hour, date.tm_min, date.tm_sec
	)


class Application(tornado.web.Application):

	def __init__(self, **kwargs):
		module_type = '([a-z]+)'
		object_type = '([a-z]+/[a-z_]+)'
		policies_object_type = '(policies/[a-z_]+)'
		dn = '([^/]+%s.+,%s)' % (self.multi_regex('='), self.multi_regex(ucr['ldap/base']),)
		# FIXME: with that dn regex, it is not possible to have urls like (/udm/$dn/foo/$dn/) because ldap-base at the end matches the last dn
		# Note: the ldap base is part of the url to support "/" as part of the DN. otherwise we can use: '([^/]+(?:=|%3d|%3D)[^/]+)'
		# Note: we cannot use .replace('/', '%2F') for the dn part as url-normalization could replace this and apache doesn't pass URLs with %2F to the ProxyPass without http://httpd.apache.org/docs/current/mod/core.html#allowencodedslashes
		property_ = '([^/]+)'
		super(Application, self).__init__([
			(r"/favicon.ico", Favicon, {"path": "/usr/share/univention-management-console-frontend/js/dijit/themes/umc/icons/16x16/"}),
			(r"/udm/", Modules),
			(r"/udm/relation/(.*)", Relations),
			(r"/udm/license/", License),
			(r"/udm/license/check", LicenseCheck),
			(r"/udm/license/request", LicenseRequest),
			(r"/udm/navigation/", ObjectTypesNavigation),
			(r"/udm/%s/tree" % (object_type,), Tree),
			(r"/udm/%s/properties" % (object_type,), Properties),
			(r"/udm/%s/" % (module_type,), ObjectTypes),
			(r"/udm/(navigation)/tree", Tree),
			(r"/udm/(%s|navigation)/move-destinations/" % (object_type,), MoveDestinations),
			(r"/udm/%s/options" % (object_type,), Options),
			(r"/udm/%s/templates" % (object_type,), Templates),
			(r"/udm/%s/default-containers" % (object_type,), DefaultContainers),  # TODO: maybe rename conflicts with above except trailing slash
			(r"/udm/%s/policies" % (object_type,), Policies),
			(r"/udm/%s/favicon.ico" % (object_type,), Favicon, {"path": "/usr/share/univention-management-console-frontend/js/dijit/themes/umc/icons/16x16/"}),
			(r"/udm/%s/report-types" % (object_type,), ReportTypes),
			(r"/udm/%s/report/([^/]+)" % (object_type,), Report),
			(r"/udm/%s/%s/properties/" % (object_type, dn), Properties),
			(r"/udm/%s/%s/properties/%s/choices" % (object_type, dn, property_), PropertyChoices),
			(r"/udm/%s/properties/%s/default" % (object_type, property_), DefaultValue),
			(r"/udm/%s/%s/%s/" % (object_type, dn, policies_object_type), PolicyTypes),
			(r"/udm/%s/%s/%s/" % (object_type, policies_object_type, dn), PolicyResult),
			(r"/udm/%s/add/?" % (object_type,), ObjectAdd),
			(r"/udm/%s/" % (object_type,), Objects),
			(r"/udm/%s/%s" % (object_type, dn), Object),
			# (r"/udm/%s/%s" % (object_type, uuid), ObjectByUiid),  # TODO: implement getting object by UUID
			(r"/udm/%s/%s/edit/?" % (object_type, dn), ObjectEdit),
			(r"/udm/%s/layout" % (object_type,), Layout),
			(r"/udm/%s/%s/layout" % (object_type, dn), Layout),
			(r"/udm/networks/network/([^/]+)/next-free-ip-address", NextFreeIpAddress),
			(r"/udm/progress/([0-9]+)", Operations),
			# TODO: meta info
			# TODO: decorator for dn argument, which makes sure no invalid dn syntax is used
		])

	def multi_regex(self, chars):
		# Bug in tornado: requests go against the raw url; https://github.com/tornadoweb/tornado/issues/2548, therefore we must match =, %3d, %3D
		return ''.join('(?:%s|%s|%s)' % (re.escape(c), re.escape(urllib.quote(c).lower()), re.escape(urllib.quote(c).upper())) if c in '=,' else re.escape(c) for c in chars)
