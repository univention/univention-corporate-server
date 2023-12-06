#!/usr/bin/python3
#
# Univention Directory Manager
#  UDM REST API
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2017-2023 Univention GmbH
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
import binascii
import copy
import functools
import io
import json
import os
import re
import traceback
import uuid
import xml.etree.ElementTree as ET
import zlib
from http.client import responses
from typing import Dict, List, Optional
from urllib.parse import parse_qs, quote, unquote, urlencode, urljoin, urlparse, urlunparse

import ldap
import tornado.gen
import tornado.httpclient
import tornado.httputil
import tornado.ioloop
import tornado.log
import tornado.web
from concurrent.futures import ThreadPoolExecutor
from ldap.controls import SimplePagedResultsControl
from ldap.controls.readentry import PostReadControl
from ldap.controls.sss import SSSRequestControl
from ldap.dn import explode_rdn
from ldap.filter import filter_format
from tornado.concurrent import run_on_executor
from tornado.web import Finish, HTTPError, RequestHandler

import univention
import univention.admin.modules as udm_modules
import univention.admin.objects as udm_objects
import univention.admin.types as udm_types
import univention.admin.uexceptions as udm_errors
import univention.directory.reports as udr
from univention.admin.rest.hal import HAL
from univention.admin.rest.html_ui import HTML
from univention.admin.rest.http_conditional import ConditionalResource, last_modified
from univention.admin.rest.ldap_connection import (
    get_machine_ldap_read_connection, get_user_ldap_read_connection, get_user_ldap_write_connection, reset_cache,
)
from univention.admin.rest.openapi import OpenAPIBase, RelationsBase, _OpenAPIBase
from univention.admin.rest.sanitizer import (
    Body, BooleanSanitizer, BoolSanitizer, ChoicesSanitizer, DictSanitizer, DNSanitizer, EmailSanitizer,
    IntegerSanitizer, LDAPFilterSanitizer, LDAPSearchSanitizer, ListSanitizer, MultiValidationError,
    ObjectPropertySanitizer, PropertiesSanitizer, Query, SanitizerBase, SearchSanitizer, StringSanitizer,
    ValidationError, sanitize,
)
from univention.admin.rest.shared_memory import JsonEncoder, shared_memory
from univention.admin.rest.utils import (
    RE_UUID, NotFound, _get_post_read_entry_uuid, _map_normalized_dn, decode_properties, parse_content_type, quote_dn,
    superordinate_names, unquote_dn,
)
from univention.config_registry import handler_set
from univention.lib.i18n import Translation
from univention.management.console.config import ucr
from univention.management.console.error import LDAP_ConnectionFailed, LDAP_ServerDown, UMC_Error, UnprocessableEntity
from univention.management.console.log import MODULE
from univention.management.console.modules.udm.tools import (
    LicenseError, LicenseImport as LicenseImporter, check_license, dump_license,
)
from univention.management.console.modules.udm.udm_ldap import (
    NoIpLeft, ObjectDoesNotExist, SuperordinateDoesNotExist, UDM_Error, UDM_Module, container_modules, get_module,
    ldap_dn2path,
)
from univention.password import generate_password, password_config


# FIXME: prevent in the javascript UMC module that navigation container query is called with container=='None'
# FIXME: it seems request.path contains the un-urlencoded path, could be security issue!
# TODO: 0f77c317e03844e8a16c484dde69abbcd2d2c7e3 is not integrated
# TODO: replace etree with genshi, etc.
# TODO: loading the policies probably unnecessarily slows down things

_ = Translation('univention-directory-manager-rest').translate

MAX_WORKERS = ucr.get('directory/manager/rest/max-worker-threads', 35)


class ResourceBase(SanitizerBase, HAL, HTML):

    pool = ThreadPoolExecutor(max_workers=MAX_WORKERS)

    @tornado.gen.coroutine
    def pool_submit(self, *args, **kwargs):
        future = self.pool.submit(*args, **kwargs)
        return (yield future)

    requires_authentication = True

    def force_authorization(self):
        self.set_header('WWW-Authenticate', 'Basic realm="Univention Directory Manager"')
        self.set_status(401)
        self.finish()

    def set_default_headers(self):
        self.set_header('Server', 'Univention/1.0')  # TODO:
        self.set_header('Access-Control-Expose-Headers', '*, Authorization, X-Request-Id')

    def prepare(self):
        self.request.x_request_id = RE_UUID.sub('', self.request.headers.get('X-Request-Id', str(uuid.uuid4())))[:36]
        self.set_header('X-Request-Id', self.request.x_request_id)
        self.request.content_negotiation_lang = 'html'
        self.request.path_decoded = unquote(self.request.path)
        self.request.decoded_query_arguments = self.request.query_arguments.copy()
        authorization = self.request.headers.get('Authorization')
        if not authorization and self.requires_authentication:
            return self.force_authorization()

        try:
            if authorization:
                self.parse_authorization(authorization)
        finally:
            self.request.content_negotiation_lang = self.check_acceptable()
            self.decode_request_arguments()

    def _request_summary(self):
        return '%s: %s' % (self.request.x_request_id[:10], super()._request_summary())

    def parse_authorization(self, authorization):
        if authorization in shared_memory.authenticated:  # cache for the userdn, which eliminates a search / request
            username, userdn, password = shared_memory.authenticated[authorization]
            already_authenticated = True
        else:
            already_authenticated = False
            username = userdn = password = None
            if authorization.lower().startswith('basic '):
                try:
                    username, password = base64.b64decode(authorization.split(' ', 1)[1].encode('ISO8859-1')).decode('ISO8859-1').split(':', 1)
                except (ValueError, IndexError, binascii.Error):
                    pass
            if not username or not password:
                raise HTTPError(400, 'The basic auth credentials are malformed.')

            userdn = self._auth_get_userdn(username)
            if not userdn:
                return self.force_authorization()

        try:
            self.ldap_connection, self.ldap_position = get_user_ldap_read_connection(userdn, password)
            if already_authenticated and not self.ldap_connection.whoami():  # the ldap connection is not bound anymore
                reset_cache(self.ldap_connection)
                self.ldap_connection, self.ldap_position = get_user_ldap_read_connection(userdn, password)

            self.request.user_dn = userdn
            self.request.username = username
        except (ldap.LDAPError, udm_errors.base):
            return self.force_authorization()
        except Exception:
            MODULE.error('Unknown error during authentication: %s' % (traceback.format_exc(), ))
            return self.force_authorization()

        if not already_authenticated:
            self._auth_check_allowed_groups()

        shared_memory.authenticated[authorization] = (username, userdn, password)

    @property
    def ldap_write_connection(self):
        username, userdn, password = shared_memory.authenticated[self.request.headers.get('Authorization')]
        return get_user_ldap_write_connection(userdn, password)[0]

    def _auth_check_allowed_groups(self):
        if self.request.username in ('cn=admin',):
            return
        allowed_groups = [value for key, value in ucr.items() if key.startswith('directory/manager/rest/authorized-groups/')]
        memberof = self.ldap_connection.getAttr(self.request.user_dn, 'memberOf')
        if not set(_map_normalized_dn(memberof)) & set(_map_normalized_dn(allowed_groups)):
            raise HTTPError(403, 'Not in allowed groups.')

    def _auth_get_userdn(self, username):
        if username in ('cn=admin',):
            return 'cn=admin,%(ldap/base)s' % ucr
        lo, po = get_machine_ldap_read_connection()
        dns = lo.searchDn(filter_format('(&(objectClass=person)(uid=%s))', [username]), unique=True)
        return dns[0] if dns else None

    def get_module(self, object_type, ldap_connection=None):
        module = UDM_Module(object_type, ldap_connection=ldap_connection or self.ldap_connection, ldap_position=self.ldap_position)
        if not module or not module.module:
            raise NotFound(object_type)
        return module

    def get_module_object(self, object_type, dn, ldap_connection=None):
        module = self.get_module(object_type, ldap_connection=ldap_connection)
        try:
            obj = module.get(dn)
        except UDM_Error as exc:
            if not isinstance(exc.exc, udm_errors.noObject):
                raise
            obj = None
        if not obj:
            raise NotFound(object_type, dn)
        return module, obj

    def get_object_by_dn(self, dn, ldap_connection=None):
        object_type = get_module(None, dn, self.ldap_connection).module
        return self.get_object(object_type, dn, ldap_connection=ldap_connection)

    def get_object(self, object_type, dn, ldap_connection=None):
        return self.get_module_object(object_type, dn, ldap_connection=ldap_connection)[1]

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
            raise HTTPError(406, 'The requested Content-Type does not exists. Specify a valid Accept header.')
        if lang == 'html' and not ucr.is_true('directory/manager/rest/html-view-enabled'):
            raise HTTPError(406, 'The unsupported HTML view of the UDM REST API is disabled. Please use the JSON interface via the "Accept: application/json" HTTP header or enable it via the UCR variable "directory/manager/rest/html-view-enabled". To get a developer overview the OpenAPI schema interface can be reached at /univention/udm/schema/.')
        return lang

    def decode_request_arguments(self):
        content_type = parse_content_type(self.request.headers.get('Content-Type', ''))
        if self.request.method in ('HEAD', 'GET', 'OPTIONS', 'DELETE'):
            if self.request.body:
                raise HTTPError(400, 'Safe HTTP method should not contain request body/Content-Type header.')
            return

        if content_type in ('application/json',):
            try:
                self.request.body_arguments = json.loads(self.request.body)
            except ValueError as exc:
                raise HTTPError(400, _('Invalid JSON document: %r') % (exc,))
        elif content_type in ('application/x-www-form-urlencoded', 'multipart/form-data'):
            self.decode_form_arguments()

    def decode_form_arguments(self):
        pass

    def get_body_argument(self, name, *args):
        if parse_content_type(self.request.headers.get('Content-Type', '')) in ('application/json',):
            return self.request.body_arguments.get(name)
        return super().get_body_argument(name, *args)

    def get_body_arguments(self, name, *args):
        if parse_content_type(self.request.headers.get('Content-Type', '')) in ('application/json',):
            return self.request.body_arguments.get(name)
        return super().get_body_arguments(name, *args)

    def content_negotiation(self, response):
        self.add_header('Vary', ', '.join(self.vary()))
        lang = self.request.content_negotiation_lang
        formatter = getattr(self, f'{self.request.method.lower()}_{lang}', getattr(self, f'get_{lang}'))
        codec = getattr(self, f'content_negotiation_{lang}')
        self.finish(codec(formatter(response)))

    def content_negotiation_json(self, response):
        self.set_header('Content-Type', 'application/json')
        try:
            return json.dumps(response, cls=JsonEncoder)
        except TypeError:
            MODULE.error(f'Cannot JSON serialize: {response!r}')
            raise

    def get_json(self, response):
        self.add_link(response, 'curies', self.abspath('relation/') + '{rel}', name='udm', templated=True)
        response.get('_embedded', {}).pop('udm:form', None)  # no public API, just to render html
        response.get('_embedded', {}).pop('udm:layout', None)  # save traffic, just to render html
        response.get('_embedded', {}).pop('udm:properties', None)  # save traffic, just to render html
        return response

    def urljoin(self, *args, **query):
        base = urlparse(self.request.full_url())
        query_string = ''
        if query:
            qs = parse_qs(base.query)
            qs.update({key: val if isinstance(val, (list, tuple)) else [val] for key, val in query.items()})
            query_string = f'?{urlencode(qs, True)}'
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

    def log_exception(self, typ, value, tb):
        if isinstance(value, UMC_Error):
            return
        super().log_exception(typ, value, tb)

    def write_error(self, status_code, exc_info=None, **kwargs):
        self.set_header('X-Request-Id', self.request.x_request_id)
        if not exc_info:  # or isinstance(exc_info[1], HTTPError):
            return super().write_error(status_code, exc_info=exc_info, **kwargs)

        etype, exc, etraceback = exc_info
        if isinstance(exc, udm_errors.ldapError) and isinstance(getattr(exc, 'original_exception', None), (ldap.SERVER_DOWN, ldap.CONNECT_ERROR, ldap.INVALID_CREDENTIALS)):
            exc = exc.original_exception
        if isinstance(exc, ldap.SERVER_DOWN):
            exc = LDAP_ServerDown()
        if isinstance(exc, ldap.CONNECT_ERROR):
            exc = LDAP_ConnectionFailed(exc)
        message = str(exc)
        title = ''
        error = {}
        response = {
            'error': {},
        }
        if isinstance(exc, UDM_Error):
            status_code = 400
        if isinstance(exc, UMC_Error):
            status_code = exc.status
            title = exc.msg
            if status_code == 503:
                self.add_header('Retry-After', '15')
            if title == message:
                title = responses.get(status_code)
            if isinstance(exc.result, dict):
                error = exc.result
                if isinstance(exc, UnprocessableEntity) and error.get('body', {}).get('properties'):
                    error = error['body']['properties']
                elif isinstance(exc, UnprocessableEntity) and error.get('query', {}):
                    error = error['query']
        if isinstance(exc, UnprocessableEntity):
            error_summary = ''

            def _append_error(key, message, location, formatter):
                error_summary = ''
                if isinstance(message, dict):
                    for k, v in message.items():
                        error_summary += _append_error(k, v, list(location) + [k], formatter)
                else:
                    error_summary += formatter % (key, message)
                    self.add_resource(response, 'udm:error', {
                        'location': location,
                        'message': message,
                        'type': 'value_error',
                    })
                return error_summary

            for key, value in exc.result.items():
                formatter = _('Request argument "%s" %s\n')
                location = key
                if key == 'query_string':
                    formatter = _('Query string "%s": %s\n')
                    location = 'query'
                elif key == 'body_arguments':
                    formatter = _('Body data "%s": %s\n')
                    location = 'body'
                error_summary += _append_error(key, value, (location,), formatter)
            message = f'{message}:\n{error_summary}'

        if status_code >= 500:
            _traceback = None
            if not isinstance(exc, (UDM_Error, UMC_Error)):
                _traceback = ''.join(traceback.format_exception(etype, exc, etraceback))
            response['error']['traceback'] = _traceback if self.application.settings.get("serve_traceback", True) else None

        # backwards compatibility :'-(
        response['error'].update({
            'code': status_code,
            'title': title,
            'message': message,
            'error': error,  # deprecated, use embedded udm:error instead
        })

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

    def get_parent_object_type(self, module):
        flavor = module.flavor
        if '/' not in flavor:
            return module
        return UDM_Module(flavor, ldap_connection=self.ldap_connection, ldap_position=self.ldap_position)


class Resource(ResourceBase, RequestHandler):

    def options(self, *args, **kwargs):
        """Display API descriptions."""
        result = self._options(*args, **kwargs)
        result.update(self.get_openapi_schema(args and args[0]))

        self.add_caching(public=False, must_revalidate=True)
        self.content_negotiation(result)

    def _options(self, *args, **kwargs):
        return {}

    def get_openapi_schema(self, object_type=None):
        return {}

    def options_json(self, response):
        response = super().get_json(response)
        response.pop('_links', None)
        response.pop('_embedded', None)
        return response


class Nothing(Resource):

    def prepare(self, *args, **kwargs):
        super().prepare(*args, **kwargs)
        raise NotFound()


class Favicon(ResourceBase, tornado.web.StaticFileHandler):

    @classmethod
    def get_absolute_path(cls, root, object_type=''):
        value = object_type.replace('/', '-')
        if value == 'favicon':
            return root
        if not value.replace('-', '').replace('_', '').isalpha():
            raise NotFound(object_type)
        return os.path.join(root, f'udm-{value}.png')


class Relations(RelationsBase, Resource):
    pass


class OpenAPI(OpenAPIBase, Resource):
    pass


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
        'portal': 'portals/all',
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
        for main_type, name in sorted(self.mapping.items(), key=lambda x: "\x00" if x[0] == 'navigation' else x[0]):
            title = _('All %s types') % (name,)
            if '/' in name:
                title = UDM_Module(name, ldap_connection=self.ldap_connection, ldap_position=self.ldap_position).object_name_plural

            self.add_link(result, 'udm:object-modules', self.urljoin(quote(main_type)) + '/', name='all' if main_type == 'navigation' else main_type, title=title)

        for name in sorted(udm_modules.modules):
            _module = UDM_Module(name, ldap_connection=self.ldap_connection, ldap_position=self.ldap_position)
            self.add_link(result, 'udm:object-types', self.urljoin(quote(_module.name)) + '/', name=_module.name, title=_module.title, dont_set_http_header=True)

        self.add_link(result, 'udm:object/get-by-dn', self.urljoin('object') + '/{dn}', templated=True)
        self.add_link(result, 'udm:object/get-by-uuid', self.urljoin('object') + '/{uuid}', templated=True)
        self.add_link(result, 'udm:license', self.urljoin('license') + '/', name='license', title=_('UCS license'))
        self.add_link(result, 'udm:ldap-base', self.urljoin('ldap/base') + '/', title=_('LDAP base'))
        self.add_link(result, 'udm:relations', self.urljoin('relation') + '/', name='relation', title=_('All link relations'))
        self.add_caching(public=True)
        self.content_negotiation(result)

    def bread_crumps_navigation(self):
        return ['self']


class ObjectTypes(Resource):
    """get the object types of a specific flavor"""

    @sanitize
    async def get(
        self,
        module_type,
        superordinate: Optional[str] = Query(DNSanitizer(required=False, allow_none=True)),
    ):
        object_type = Modules.mapping.get(module_type)
        if not object_type:
            raise NotFound(object_type)

        title = _('All object types')
        module = None
        if '/' in object_type:
            # FIXME: what was/is the superordinate for?
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
                # 'help_link': _module.help_link,
                # 'help_text': _module.help_text,
                'columns': _module.columns,  # FIXME: move to Objects?
                # 'has_tree': _module.has_tree,
            })

        self.add_caching(public=True, must_revalidate=True)
        self.content_negotiation(result)


class SubObjectTypes(Resource):
    """A list of possible sub-object-types which can be created underneath of the specified container or superordinate."""

    def get(self, object_type=None, position=None):
        """
        Returns the list of object types matching the given flavor or container.

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
        allowed_modules = {m for m in udm_modules.containers if udm_modules.name(m) != 'container/dc'}

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
                # 'object_name': _module.object_name,
                # 'object_name_plural': _module.object_name_plural,
                # 'help_link': _module.help_link,
                # 'help_text': _module.help_text,
                # 'columns': _module.columns,
                # 'has_tree': _module.has_tree,
            })
            self.add_link(result, 'udm:object-types', self.abspath(_module.name) + '/', name=_module.name, title=_module.title)
        self.add_caching(public=True, must_revalidate=True)
        self.content_negotiation(result)


class LdapBase(Resource):

    def get(self):
        result = {}
        url = self.abspath('container/dc', quote_dn(ucr['ldap/base']))
        self.add_link(result, 'self', url)
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

        result = {}
        url = self.abspath(module.name, quote_dn(dn))
        self.add_link(result, 'self', url)
        self.set_header('Location', url)
        self.set_status(301)
        self.add_caching(public=True, must_revalidate=True)
        self.content_negotiation(result)


class ObjectByUiid(ObjectLink):

    def get(self, uuid):
        try:
            dn = self.ldap_connection.searchDn(filter_format('entryUUID=%s', [uuid]))[0]
        except IndexError:
            raise NotFound()
        return super().get(dn)


class ContainerQueryBase(Resource):

    async def _container_query(self, object_type, container, modules, scope):
        """Get a list of containers or child objects of the specified container."""
        if not container:
            container = ucr['ldap/base']
            defaults = {}
            if object_type != 'navigation':
                defaults['$operations$'] = ['search']  # disallow edit
            if object_type in ('dns/dns', 'dhcp/dhcp'):
                defaults.update({
                    'label': UDM_Module(object_type, ldap_connection=self.ldap_connection, ldap_position=self.ldap_position).title,
                    'icon': 'udm-%s' % (object_type.replace('/', '-'),),
                })
            self.add_link({}, 'next', self.urljoin('?container=%s' % (quote(container))))
            return [dict({
                'id': container,
                'label': ldap_dn2path(container),
                'icon': 'udm-container-dc',
                'path': ldap_dn2path(container),
                'objectType': 'container/dc',
                #'$operations$': UDM_Module('container/dc', ldap_connection=self.ldap_connection, ldap_position=self.ldap_position).operations,
                '$flags$': [],
                '$childs$': True,
                '$isSuperordinate$': False,
            }, **defaults)]

        result = []
        for xmodule in modules:
            xmodule = UDM_Module(xmodule, ldap_connection=self.ldap_connection, ldap_position=self.ldap_position)
            superordinate = univention.admin.objects.get_superordinate(xmodule.module, None, self.ldap_connection, container)  # TODO: should also better be in a thread
            try:
                ucr['directory/manager/web/sizelimit'] = ucr.get('ldap/sizelimit', '400000')
                items = await self.pool_submit(xmodule.search, container, scope=scope, superordinate=superordinate)
                for item in items:
                    module = UDM_Module(item.module, ldap_connection=self.ldap_connection, ldap_position=self.ldap_position)
                    result.append({
                        'id': item.dn,
                        'label': module.obj_description(item),
                        'icon': 'udm-%s' % (module.name.replace('/', '-')),
                        'path': ldap_dn2path(item.dn),
                        'objectType': module.name,
                        #'$operations$': module.operations,
                        '$flags$': [x.decode('UTF-8') for x in item.oldattr.get('univentionObjectFlag', [])],
                        '$childs$': module.childs,
                        '$isSuperordinate$': udm_modules.isSuperordinate(module.module),
                    })
            except UDM_Error as exc:
                raise HTTPError(400, None, str(exc))

        return result


class Tree(ContainerQueryBase):
    """GET udm/(dns/dns|dhcp/dhcp|)/tree/ (the tree content of navigation/DNS/DHCP)"""

    @sanitize
    async def get(
        self,
        object_type,
        container: str = Query(DNSanitizer(default=None)),
    ):
        # TODO: add appropriate 404 errors
        ldap_base = ucr['ldap/base']

        modules = container_modules()
        scope = 'one'
        if not container:
            # get the tree root == the ldap base
            scope = 'base'
        elif object_type != 'navigation' and container and ldap_base.lower() == container.lower():
            # this is the tree root of DNS / DHCP, show all zones / services
            scope = 'sub'
            modules = [object_type]

        result = {}
        containers = await self._container_query(object_type, container, modules, scope)
        for _container in containers:
            self.add_link(_container, 'item', href=self.urljoin('./tree?container=%s' % (quote(_container['id']),)), title=_container['label'])  # should be "self" and with no header added
            #self.add_link(result, 'item', href=self.urljoin('./tree?container=%s' % (quote(_container['id']),)), title=_container['label'], path=_container['path'])
            self.add_resource(result, 'udm:tree', _container)

        self.add_link(result, 'self', self.urljoin(''), title='Tree')
        if container:
            parent_dn = self.ldap_connection.parentDn(container)
            if parent_dn:
                self.add_link(result, 'up', self.urljoin('tree?container=%s' % (quote(parent_dn),)), title='Parent container')

        if object_type != 'navigation':
            module = self.get_module(object_type)
            self.add_link(result, 'icon', self.urljoin('../../favicon.ico'), type='image/x-icon')
            self.add_link(result, 'udm:object-modules', self.urljoin('../../'), title=_('All modules'))
            self.add_link(result, 'udm:object-module', self.urljoin('../'), title=self.get_parent_object_type(module).object_name_plural)
            self.add_link(result, 'type', self.urljoin('.'), title=module.object_name)
        else:
            self.add_link(result, 'icon', self.urljoin('../favicon.ico'), type='image/x-icon')
            self.add_link(result, 'udm:object-modules', self.urljoin('../'), title=_('All modules'))

        self.add_caching(public=False, must_revalidate=True)
        self.content_negotiation(result)


class MoveDestinations(ContainerQueryBase):

    @sanitize
    async def get(
        self,
        object_type,
        container: str = Query(DNSanitizer(default=None)),
    ):
        # TODO: add appropriate 404 errors
        scope = 'one'
        modules = container_modules()
        if not container:
            scope = 'base'

        result = {}
        containers = await self._container_query(object_type or 'navigation', container, modules, scope)
        self.add_caching(public=False, must_revalidate=True)
        for _container in containers:
            self.add_link(_container, 'item', href=self.urljoin('./?container=%s' % (quote(_container['id']),)), title=_container['label'])
            self.add_resource(result, 'udm:tree', _container)

        self.add_link(result, 'self', self.urljoin(''), title='Move destinations')
        if container:
            parent_dn = self.ldap_connection.parentDn(container)
            if parent_dn:
                self.add_link(result, 'up', self.urljoin('./?container=%s' % (quote(parent_dn),)), title='Parent container')

        if object_type and object_type != 'navigation':
            module = self.get_module(object_type)
            self.add_link(result, 'icon', self.urljoin('../favicon.ico'), type='image/x-icon')
            self.add_link(result, 'udm:object-modules', self.urljoin('../../../'), title=_('All modules'))
            self.add_link(result, 'udm:object-module', self.urljoin('../../'), title=self.get_parent_object_type(module).object_name_plural)
            self.add_link(result, 'type', self.urljoin('../'), title=module.object_name)
        self.content_negotiation(result)


class Properties(Resource):
    """GET udm/users/user/properties (get properties of users/user object type)"""

    @sanitize
    async def get(
        self,
        object_type,
        dn=None,
        searchable: bool = Query(BoolSanitizer(required=False)),
    ):
        result = {}
        if dn:
            dn = unquote_dn(dn)
        module = self.get_module(object_type)
        module.load(force_reload=True)  # reload for instant extended attributes

        self.add_link(result, 'self', self.urljoin(''), title=_('Properties for %s') % (module.object_name,))
        if dn:
            self.add_link(result, 'icon', self.urljoin('../favicon.ico'), type='image/x-icon')
            self.add_link(result, 'udm:object-modules', self.urljoin('../../../'), title=_('All modules'))
            self.add_link(result, 'udm:object-module', self.urljoin('../../'), title=self.get_parent_object_type(module).object_name_plural)
            self.add_link(result, 'type', self.urljoin('../'), title=module.object_name)
            self.add_link(result, 'up', self.urljoin('..', quote_dn(dn)), title=dn)
        else:
            self.add_link(result, 'icon', self.urljoin('./favicon.ico'), type='image/x-icon')
            self.add_link(result, 'udm:object-modules', self.urljoin('../../'), title=_('All modules'))
            self.add_link(result, 'udm:object-module', self.urljoin('../'), title=self.get_parent_object_type(module).object_name_plural)
            # self.add_link(result, 'type', self.urljoin('.'), title=module.object_name)
            self.add_link(result, 'up', self.urljoin('.'), title=module.object_name)
        properties = self.get_properties(module, dn)
        if searchable:
            properties = {name: prop for name, prop in properties.items() if prop.get('searchable', False)}
        result['properties'] = properties

        for propname, prop in properties.items():
            if prop.get('dynamicValues') or prop.get('staticValues') or prop.get('type') == 'umc/modules/udm/MultiObjectSelect':
                self.add_link(result, 'udm:property-choices', self.urljoin('properties', propname, 'choices'), name=propname, title=_('Get choices for property %s') % (propname,))

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
            prop.setdefault('show_in_lists', True)
        return {prop['id']: prop for prop in properties if not prop['id'].startswith('$')}


class Layout(Resource):

    def get(self, object_type, dn=None):
        result = {}
        if dn:
            dn = unquote_dn(dn)
        module = self.get_module(object_type)
        module.load(force_reload=True)  # reload for instant extended attributes

        self.add_link(result, 'self', self.urljoin(''), title=_('Layout for %s') % (module.object_name,))
        if dn:
            self.add_link(result, 'icon', self.urljoin('../favicon.ico'), type='image/x-icon')
            self.add_link(result, 'udm:object-modules', self.urljoin('../../../'), title=_('All modules'))
            self.add_link(result, 'udm:object-module', self.urljoin('../../'), title=self.get_parent_object_type(module).object_name_plural)
            self.add_link(result, 'type', self.urljoin('../'), title=module.object_name)
            self.add_link(result, 'up', self.urljoin('..', quote_dn(dn)), title=dn)
        else:
            self.add_link(result, 'icon', self.urljoin('./favicon.ico'), type='image/x-icon')
            self.add_link(result, 'udm:object-modules', self.urljoin('../../'), title=_('All modules'))
            self.add_link(result, 'udm:object-module', self.urljoin('../'), title=self.get_parent_object_type(module).object_name_plural)
            # self.add_link(result, 'type', self.urljoin('.'), title=module.object_name)
            self.add_link(result, 'up', self.urljoin('.'), title=module.object_name)

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
            'help': _('List of all object properties that are inherited by policies. The values cannot be edited directly. By clicking on "Create new policy", a new tab with a new policy will be opened. If an attribute is already set, the corresponding policy can be edited in a new tab by clicking on the "edit" link.'),
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

    @classmethod
    def get_section_id(cls, label):
        label = re.sub(r'[^a-z0-9_:-]', '_', label.lower())
        return re.sub(r'^[^a-z]+', 'id_', label)


class ReportingBase:

    def initialize(self):
        self.reports_cfg = udr.Config()


class Report(ReportingBase, Resource):
    """GET udm/users/user/report/$report_type?dn=...&dn=... (create a report of users)"""

    # i18n: translation for univention-directory-reports
    _('PDF Document')
    _('CSV Report')

    async def get(self, object_type, report_type):
        dns = self.get_query_arguments('dn')
        await self.create_report(object_type, report_type, dns)

    @sanitize
    async def post(
        self,
        object_type,
        report_type,
        dn: List[str] = Query(ListSanitizer(DNSanitizer())),
    ):
        await self.create_report(object_type, report_type, dn)

    async def create_report(self, object_type, report_type, dns):
        try:
            assert report_type in self.reports_cfg.get_report_names(object_type)
        except (KeyError, AssertionError):
            raise NotFound(report_type)

        report = udr.Report(self.ldap_connection)
        try:
            report_file = await self.pool_submit(report.create, object_type, report_type, dns or [])
        except udr.ReportError as exc:
            raise HTTPError(400, None, str(exc))

        with open(report_file, 'rb') as fd:  # noqa: ASYNC101
            self.set_header('Content-Type', 'text/csv' if report_file.endswith('.csv') else 'application/pdf')
            self.set_header('Content-Disposition', 'attachment; filename="%s"' % (os.path.basename(report_file).replace('\\', '\\\\').replace('"', '\\"')))
            self.finish(fd.read())
        os.remove(report_file)


class NextFreeIpAddress(Resource):
    """GET udm/networks/network/$DN/next-free-ip-address (get the next free IP in this network)"""

    def get(self, object_type, dn):  # TODO: threaded?! (might have caused something in the past in system setup?!)
        """
        Returns the next IP configuration based on the given network object

        requests.options = {}
                'networkDN' -- the LDAP DN of the network object
                'increaseCounter' -- if given and set to True, network object counter for IP addresses is increased

        return: {}
        """
        dn = unquote_dn(dn)
        obj = self.get_object(object_type, dn)
        try:
            obj.refreshNextIp()
        except udm_errors.nextFreeIp:
            raise NoIpLeft(dn)

        result = {
            'ip': obj['nextIp'],
            'dnsEntryZoneForward': obj['dnsEntryZoneForward'],
            'dhcpEntryZone': obj['dhcpEntryZone'],
            'dnsEntryZoneReverse': obj['dnsEntryZoneReverse'],
        }

        self.add_caching(public=False, must_revalidate=True)
        self.content_negotiation(result)

        if self.get_query_argument('increaseCounter', False):
            # increase the next free IP address
            obj.stepIp()
            obj.modify()


class FormBase:

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
                kwargs['list'] = f'list-{key}'
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
            self.add_form_element(form, f'properties.{key}', value, label=prop['label'], placeholder=prop['label'], **kwargs)

    def decode_form_arguments(self):
        # TODO: add files
        # TODO: respect single-value
        # TODO: the types should be converted, e.g. type=checkbox to boolean, number to int
        for key in list(self.request.body_arguments.keys()):
            for name in ('properties', 'policies'):
                if key.startswith(f'{name}.'):
                    properties = self.request.body_arguments.setdefault(name, {})
                    prop = key[len(f'{name}.'):]
                    properties.setdefault(prop, []).append(self.request.body_arguments.pop(key))
                elif key.startswith(f'{name}[') and key.endswith(']'):
                    properties = self.request.body_arguments.setdefault(name, {})
                    prop = key[len(f'{name}['):-1]
                    properties.setdefault(prop, []).append(self.request.body_arguments.pop(key))

    def superordinate_dn_to_object(self, module, superordinate):
        if not superordinate_names(module):
            return
        if superordinate:
            mod = get_module(module.name, superordinate, self.ldap_connection)
            if not mod:
                MODULE.error(f'Superordinate module not found: {superordinate}')
                raise SuperordinateDoesNotExist(superordinate)
            MODULE.info('Found UDM module for superordinate')
            superordinate = mod.get(superordinate)
        return superordinate


class Objects(ConditionalResource, FormBase, ReportingBase, _OpenAPIBase, Resource):

    @sanitize
    async def get(
        self,
        object_type: str,
        position: str = Query(DNSanitizer(required=False, default=None, allow_none=True), description="Position which is used as search base."),
        ldap_filter: str = Query(
            LDAPFilterSanitizer(required=False, default="", allow_none=True),
            alias='filter',
            description="A LDAP filter which may contain `UDM` property names instead of `LDAP` attribute names.",
            examples={
                "any-object": {
                        "value": "(objectClass=*)",
                },
                "admin-user": {
                    "value": "(|(username=Administrator)(username=Admin*))",
                },
            },
        ),
        query: Dict = Query(
            DictSanitizer({}, default_sanitizer=LDAPSearchSanitizer(required=False, default='*', add_asterisks=False, use_asterisks=True), key_sanitizer=ObjectPropertySanitizer()),
            description="The values to search for (propertyname and search filter value). Alternatively with `filter` a raw LDAP filter can be given.",
            style="deepObject",
            examples={
                'nothing': {
                        'value': None,
                },
                'property': {
                    'value': {'': '*'},
                },
            },
        ),
        property: str = Query(
            ObjectPropertySanitizer(required=False, default=None),
            description="The property to search for if not specified via `query`",
        ),
        scope: str = Query(ChoicesSanitizer(choices=['sub', 'one', 'base', 'base+one'], default='sub'), description="The LDAP search scope (sub, base, one)."),
        hidden: bool = Query(BoolSanitizer(default=True), description="Include hidden/system objects in the response.", example=True),
        properties: List[str] = Query(
            ListSanitizer(StringSanitizer(), required=False, default=['*'], allow_none=True, min_elements=0),
            style="form",
            explode=True,
            description="The properties which should be returned, if not given all properties are returned.",
            examples={
                'no restrictions': {'value': None},
                        'only small subset': {'value': ['username', 'firstname', 'lastname']},
            },
        ),
        superordinate: Optional[str] = Query(
            DNSanitizer(required=False, default=None, allow_none=True),
            description="The superordinate DN of the objects to find. `position` is sufficient.",
            # example=f"cn=superordinate,{ldap_base}"
        ),
        dir: str = Query(
            ChoicesSanitizer(choices=['ASC', 'DESC'], default='ASC'),
            deprecated=True,
            description="**Broken/Experimental**: The Sort direction (ASC or DESC).",
        ),
        by: str = Query(
            StringSanitizer(required=False),
            deprecated=True,
            description="**Broken/Experimental**: Sort the search result by the specified property.",
            # example="username",
        ),
        page: int = Query(
            IntegerSanitizer(required=False, default=1, minimum=1),
            deprecated=True,
            description="**Broken/Experimental**: The search page, starting at one.",
            example=1,
        ),
        limit: int = Query(
            IntegerSanitizer(required=False, default=None, allow_none=True, minimum=0),
            deprecated=True,
            description="**Broken/Experimental**: How many results should be shown per page.",
            examples={
                "no limit": {"value": "", "summary": "get all entries"},
                "limit to 50": {"value": 50, "summary": "limit to 50 entries"},
            },
        ),
    ):
        """Search for {module.object_name_plural} objects"""
        module = self.get_module(object_type)
        result = self._options(object_type)

        search = bool(self.request.query)
        properties = properties[:]
        direction = dir
        property_ = property
        reverse = direction == 'DESC'
        items_per_page = limit

        if not ldap_filter:
            filters = filter(None, [(module._object_property_filter(attribute or property_ or None, value, hidden)) for attribute, value in query.items()])
            if filters:
                ldap_filter = str(univention.admin.filter.conjunction('&', [univention.admin.filter.parse(fil) for fil in filters]))

        # TODO: replace the superordinate concept with container
        superordinate = self.superordinate_dn_to_object(module, superordinate)
        if superordinate:
            position = position or superordinate.dn

        objects = []
        if search:
            try:
                objects, last_page = await self.search(module, position, ldap_filter, superordinate, scope, hidden, items_per_page, page, by, reverse)
            except ObjectDoesNotExist as exc:
                self.raise_sanitization_error('position', str(exc), type='query')
            except SuperordinateDoesNotExist as exc:
                self.raise_sanitization_error('superordinate', str(exc), type='query')

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
            grid_layout = [
                # 'add', 'modify', 'delete', 'move', 'copy'
                'create-form', 'multi-edit', 'move',
            ]

            for i, report_type in enumerate(sorted(self.reports_cfg.get_report_names(object_type)), 1):
                grid_layout.append(report_type)
                form = self.add_form(result, self.urljoin('report', quote(report_type)), 'POST', rel='udm:report', name=report_type, id='report%d' % (i,))
                self.add_form_element(form, '', _('Create %s report') % _(report_type), type='submit')
                self.add_link(result, 'udm:report', self.urljoin('report', quote(report_type)) + '{?dn}', name=report_type, title=_('Create %s report') % _(report_type), method='POST', templated=True)

            form = self.add_form(result, self.urljoin('multi-edit'), 'POST', name='multi-edit', id='multi-edit', rel='edit-form')
            self.add_form_element(form, '', _('Modify %s (multi edit)') % (module.object_name_plural,), type='submit')

            form = self.add_form(result, self.urljoin('move'), 'POST', name='move', id='move', rel='udm:object/move')
            self.add_form_element(form, 'position', '')
            self.add_form_element(form, '', _('Move %s') % (module.object_name_plural,), type='submit')

            main_layout = [
                {'description': f'{module.object_name_plural} ({module.description})', 'label': module.object_name_plural, 'layout': [
                    {'$form-ref': ['search']},
                    {'layout': [{'$form-ref': grid_layout}]},
                ]},
            ]
            self.add_layout(result, main_layout, 'main-layout')
        else:
            for i, report_type in enumerate(sorted(self.reports_cfg.get_report_names(object_type)), 1):
                self.add_link(result, 'udm:report', self.urljoin('report', quote(report_type)) + '{?dn}', name=report_type, title=_('Create %s report') % _(report_type), method='POST', templated=True)

        search_layout_base = [{'description': _('Search for %s') % (module.object_name_plural,), 'label': _('Search'), 'layout': []}]
        search_layout = search_layout_base[0]['layout']
        self.add_layout(result, search_layout_base, 'search')
        form = self.add_form(result, self.urljoin(''), 'GET', rel='search', id='search', name='search', layout='search')
        self.add_form_element(form, 'position', position or '', label=_('Search in'))
        search_layout.append(['position', 'hidden'])
        if superordinate_names(module):
            self.add_form_element(form, 'superordinate', superordinate.dn if superordinate else '', label=_('Superordinate'))
            search_layout.append(['superordinate'])
        searchable_properties = [{'value': '', 'label': _('Defaults')}] + [{'value': prop['id'], 'label': prop['label']} for prop in module.properties(None) if prop.get('searchable')]
        self.add_form_element(form, 'property', property_ or '', element='select', options=searchable_properties, label=_('Property'))
        self.add_form_element(form, 'query*', query.get('', '*'), label=_('Search for'), placeholder=_('Search value (e.g. *)'))
        self.add_form_element(form, 'scope', scope, element='select', options=[{'value': 'sub'}, {'value': 'one'}, {'value': 'base'}, {'value': 'base+one'}], label=_('Search scope'))
        self.add_form_element(form, 'hidden', '1', type='checkbox', checked=bool(hidden), label=_('Include hidden objects'))
        search_layout.append(['property', 'query*'])
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
        else:
            self.add_link(result, 'udm:layout', self.urljoin('layout'), title=_('Module layout'))
            self.add_link(result, 'udm:properties', self.urljoin('properties'), title=_('Module properties'))
            for policy_module in module.policies:
                policy_module = policy_module['objectType']
                self.add_link(result, 'udm:policy-result', self.urljoin(f'{policy_module}/{{?policy,position}}'), name=policy_module, title=_('Evaluate referenced %s policies') % (policy_module,), templated=True)

        self.add_caching(public=False, no_cache=True, no_store=True, max_age=1, must_revalidate=True)
        self.content_negotiation(result)

    async def search(self, module, container, ldap_filter, superordinate, scope, hidden, items_per_page, page, by, reverse):
        ctrls = {}
        serverctrls = []
        hashed = (self.request.user_dn, module.name, container or None, ldap_filter or None, superordinate or None, scope or None, hidden or None, items_per_page or None, by or None, reverse or None)
        session = shared_memory.search_sessions.get(hashed, {})
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
        for _i in range(current_page, page or 1):
            objects = await self.pool_submit(module.search, container, superordinate=superordinate, filter=ldap_filter, scope=scope, hidden=hidden, serverctrls=serverctrls, response=ctrls)
            for control in ctrls.get('ctrls', []):
                if control.controlType == SimplePagedResultsControl.controlType:
                    page_ctrl.cookie = control.cookie
            if not page_ctrl.cookie:
                shared_memory.search_sessions.pop(hashed, None)
                break
        else:
            shared_memory.search_sessions[hashed] = {'last_cookie': page_ctrl.cookie, 'page': page}
            last_page = 0
        return (objects, last_page)

    def get_html(self, response):
        if self.request.method in ('GET', 'HEAD'):
            r = response.copy()
            r.pop('entries', None)
            num_of_entries = r.pop('results', 0)
            root = super().get_html(r)
        else:
            root = super().get_html(response)

        if self.request.method in ('GET', 'HEAD'):
            has_four_rows = self.request.decoded_query_arguments.get('property')
            table = ET.Element('table', **{'class': 'grid'})
            table_header = ET.SubElement(table, 'tr')
            th1 = ET.SubElement(table_header, 'th')  # TODO: all-checkbox
            ET.SubElement(table_header, 'th').text = 'Name'  # TODO: sort-direction switch
            if has_four_rows:
                ET.SubElement(table_header, 'th').text = has_four_rows  # TODO: display name
            ET.SubElement(table_header, 'th').text = 'Path'
            root.append(table)

            try:
                num_of_objects = ET.SubElement(root[0].findall('.//div/form/..')[-1], 'span')
                num_of_objects.text = f'$x users of {num_of_entries} selected.'
            except IndexError:
                pass

            # There is a bug in chrome, so we cannot have form='report1 report2'. so, only 1 report is possible :-/
            ET.SubElement(th1, 'input', type='checkbox', name='dn', form=' '.join([report['id'] for report in self.get_resources(response, 'udm:form') if report['rel'] == 'udm:report'][-1:]))

            for thing in self.get_resources(response, 'udm:object'):
                row = ET.SubElement(table, 'tr')
                x = thing.copy()

                td1 = ET.SubElement(row, 'td')
                td2 = ET.SubElement(row, 'td')
                if has_four_rows:
                    td4 = ET.SubElement(row, 'td')
                td3 = ET.SubElement(row, 'td')

                # There is a bug in chrome, so we cannot have form='report1 report2'. so, only 1 report is possible :-/
                ET.SubElement(td1, 'input', type='checkbox', name='dn', value=x['dn'], form=' '.join([report['id'] for report in self.get_resources(response, 'udm:form') if report['rel'] == 'udm:report'][-1:]))

                a = ET.SubElement(td2, "a", href=x.pop('uri'), rel="udm:object item")
                a.text = x['id']

                td3.text = ldap_dn2path(thing['position'])

                if has_four_rows:
                    td4.text = thing['properties'].get(has_four_rows)  # TODO: syntax.to_string()

                pre = ET.SubElement(row, "pre", dn=x['dn'], style='display: none')
                pre.text = json.dumps(x, indent=4)
        return root

    @sanitize
    async def post(
        self,
        object_type,
        position: str = Body(DNSanitizer(required=False, allow_none=True)),
        superordinate: str = Body(DNSanitizer(required=False, allow_none=True)),
        options: Dict = Body(DictSanitizer({}, default_sanitizer=BooleanSanitizer(), required=False)),
        policies: Dict = Body(DictSanitizer({}, default_sanitizer=ListSanitizer(DNSanitizer()), required=False)),
        properties: Dict = Body(DictSanitizer({}, required=True)),
    ):
        """Create a new {module.object_name} object"""
        obj = Object(self.application, self.request)
        obj.ldap_connection, obj.ldap_position = self.ldap_connection, self.ldap_position
        serverctrls = [PostReadControl(True, ['entryUUID', 'modifyTimestamp', 'entryCSN'])]
        response = {}
        result = {}
        representation = {
            'position': position,
            'superordinate': superordinate,
            'options': options,
            'policies': policies,
            'properties': properties,
        }
        new_obj = await obj.create(object_type, None, representation, result, serverctrls=serverctrls, response=response)
        self.set_header('Location', self.urljoin(quote_dn(new_obj.dn)))
        self.set_entity_tags(new_obj, check_conditionals=False)
        self.set_status(201)
        self.add_caching(public=False, no_cache=True, must_revalidate=True)

        uuid = _get_post_read_entry_uuid(response)

        result.update({
            'dn': new_obj.dn,
            'uuid': uuid,
        })
        self.content_negotiation(result)

    def _options(self, object_type):
        result = {}
        module = self.get_module(object_type)
        parent = self.get_parent_object_type(module)
        methods = ['GET', 'OPTIONS']
        self.add_link(result, 'udm:object-modules', self.urljoin('../../'), title=_('All modules'))
        self.add_link(result, 'up', self.urljoin('../'), title=parent.object_name_plural)
        self.add_link(result, 'self', self.urljoin(''), name=module.name, title=module.object_name_plural)
        self.add_link(result, 'describedby', self.urljoin(''), title=_('%s module') % (module.name,), method='OPTIONS')
        if 'search' in module.operations:
            searchfields = ['position', 'query*', 'filter', 'scope', 'hidden', 'properties']
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
#        self.add_link(result, '', self.urljoin(''))
        self.set_header('Allow', ', '.join(methods))
        return result

    def options_html(self, response):
        #root = self.get_html(response)
        root = ET.Element('pre')
        root.text = json.dumps(response, indent=4)
        return root


class ObjectsMove(Resource):

    @sanitize
    async def post(
        self,
        object_type,
        position: str = Body(DNSanitizer(required=True)),
        dn: List[str] = Body(ListSanitizer(DNSanitizer(required=True), min_elements=1)),
    ):
        # FIXME: this can only move objects of the same object_type but should move everything
        dns = dn  # TODO: validate: moveable, etc.

        status_id = str(uuid.uuid4())
        status = shared_memory.dict()
        status.update({
            'id': status_id,
            'finished': False,
            'errors': False,
            'moved': shared_memory.list(),
        })

        try:
            shared_memory.queue[self.request.user_dn]
        except KeyError:
            shared_memory.queue[self.request.user_dn] = shared_memory.dict()
        shared_memory.queue[self.request.user_dn][status_id] = status

        self.set_status(201)  # FIXME: must be 202
        self.set_header('Location', self.abspath('progress', status['id']))
        self.finish()
        try:
            for i, dn in enumerate(dns, 1):
                module = get_module(object_type, dn, self.ldap_write_connection)
                dn = await self.pool_submit(module.move, dn, position)
                status['moved'].append(dn)
                status['description'] = _('Moved %d of %d objects. Last object was: %s.') % (i, len(dns), dn)
                status['max'] = len(dns)
                status['value'] = i
        except Exception:
            status['errors'] = True
            status['traceback'] = traceback.format_exc()  # FIXME: error handling
            raise
        else:
            status['uri'] = self.urljoin(quote_dn(dn))
        finally:
            status['finished'] = True


class Object(ConditionalResource, FormBase, _OpenAPIBase, Resource):

    async def get(self, object_type, dn):
        """
        Get a representation of the {module.object_name} object with all its properties, policies, options, metadata and references.
        Includes also instructions how to modify, remove or move the object.
        """
        dn = unquote_dn(dn)
        copy = bool(self.get_query_argument('copy', None))  # TODO: move into own resource: ./copy

        if object_type == 'users/self' and not self.ldap_connection.compare_dn(dn, self.request.user_dn):
            raise HTTPError(403)

        try:
            module, obj = await self.pool_submit(self.get_module_object, object_type, dn)
        except NotFound:
            # FIXME: return HTTP 410 Gone for removed objects
            # if self.ldap_connection.searchDn(filter_format('(&(reqDN=%s)(reqType=d))', [dn]), base='cn=translog'):
            #     raise Gone(object_type, dn)
            raise
        if object_type not in ('users/self', 'users/passwd') and not univention.admin.modules.recognize(object_type, obj.dn, obj.oldattr):
            raise NotFound(object_type, dn)

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

        if module.name == 'users/user':
            self.add_link(props, 'udm:service-specific-password', self.urljoin(quote_dn(obj.dn), 'service-specific-password'), title=_('Generate a new service specific password'))
        self.add_link(props, 'udm:layout', self.urljoin(quote_dn(obj.dn), 'layout'), title=_('Module layout'))
        self.add_link(props, 'udm:properties', self.urljoin(quote_dn(obj.dn), 'properties'), title=_('Module properties'))
        for policy_module in props.get('policies', {}).keys():
            self.add_link(props, 'udm:policy-result', self.urljoin(quote_dn(obj.dn), f'{policy_module}/{{?policy}}'), name=policy_module, title=_('Evaluate referenced %s policies') % (policy_module,), templated=True)

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
        self.add_link(props, 'describedby', self.urljoin(''), title=_('%s module') % (module.name,), method='OPTIONS')
        self.add_link(props, 'icon', self.urljoin('favicon.ico'), type='image/x-icon')
        self.add_link(props, 'udm:object/remove', self.urljoin(''), method='DELETE')
        self.add_link(props, 'udm:object/edit', self.urljoin(''), method='PUT')
        # self.add_link(props, '', self.urljoin('report/PDF Document?dn=%s' % (quote(obj.dn),))) # rel=alternate media=print?
#        for mod in module.child_modules:
#            mod = self.get_module(mod['id'])
#            if mod and set(superordinate_names(mod)) & {module.name, }:
#                self.add_link(props, 'udm:children-types', self.urljoin('../../%s/?superordinate=%s' % (quote(mod.name), quote(obj.dn))), name=mod.name, title=mod.object_name_plural)

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
            self.add_link(props, 'edit-form', self.urljoin(quote_dn(dn), 'edit'), title=_('Modify, move or remove this %s') % (module.object_name,))

        self.set_header('Allow', ', '.join(methods))
        if 'PATCH' in methods:
            self.set_header('Accept-Patch', 'application/json-patch+json, application/json')
        return props

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
            if '*' not in properties:
                values = {key: value for (key, value) in obj.info.items() if (key in properties) and obj.descriptions[key].show_in_lists}
            else:
                values = {key: obj[key] for key in obj.descriptions if (add or obj.has_property(key)) and obj.descriptions[key].show_in_lists}

            for passwd in module.password_properties:
                if passwd in values:
                    values[passwd] = None
            values = dict(decode_properties(module, obj, values))

        if add:
            # we need to remove dynamic default values as they reference other currently not set variables
            # (e.g. shares/share sets sambaName='' or users/user sets unixhome=/home/)
            for name, p in obj.descriptions.items():
                regex = re.compile(r'<(?P<key>[^>]+)>(?P<ext>\[[\d:]+\])?')  # from univention.admin.pattern_replace()
                if name not in obj.info or name not in values:
                    continue
                if isinstance(p.base_default, str) and regex.search(p.base_default):
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
        props['options'] = {opt['id']: opt['value'] for opt in module.get_options(udm_object=obj)}
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
        if obj.entry_uuid:
            props['uuid'] = obj.entry_uuid
        # TODO: objectFlag is available for every module. remove the extended attribute and always map it.
        # alternative: add some other meta information to this object, e.g. is_hidden_object: True, is_synced_from_active_directory: True, ...
        if '*' in properties or 'objectFlag' in properties:
            props['properties'].setdefault('objectFlag', [x.decode('utf-8', 'replace') for x in obj.oldattr.get('univentionObjectFlag', [])])
        if copy or add:
            props.pop('dn', None)
            props.pop('id', None)
        return props

    @sanitize
    async def put(
        self,
        object_type,
        dn,
        position: str = Body(DNSanitizer(required=True)),
        superordinate: str = Body(DNSanitizer(required=False, allow_none=True)),
        options: Dict = Body(DictSanitizer({}, default_sanitizer=BooleanSanitizer())),
        policies: Dict = Body(DictSanitizer({}, default_sanitizer=ListSanitizer(DNSanitizer()))),
        properties: Dict = Body(DictSanitizer({}, required=True)),
    ):
        """Modify or move an {module.object_name} object"""
        dn = unquote_dn(dn)
        try:
            module, obj = await self.pool_submit(self.get_module_object, object_type, dn, ldap_connection=self.ldap_write_connection)
        except NotFound:
            module, obj = None, None

        representation = {
            'position': position,
            'superordinate': superordinate,
            'options': options,
            'policies': policies,
            'properties': properties,
        }
        serverctrls = [PostReadControl(True, ['entryUUID', 'modifyTimestamp', 'entryCSN'])]
        response = {}
        if not obj:
            module = self.get_module(object_type)
            result = {}

            obj = await self.create(object_type, dn, representation, result, serverctrls=serverctrls, response=response)
            self.set_header('Location', self.urljoin(quote_dn(obj.dn)))
            self.set_status(201)
            self.add_caching(public=False, must_revalidate=True)

            uuid = _get_post_read_entry_uuid(response)

            result.update({
                'dn': obj.dn,
                'uuid': uuid,
            })
            self.content_negotiation(result)
            return

        self.set_entity_tags(obj)

        if position and not self.ldap_write_connection.compare_dn(self.ldap_write_connection.parentDn(dn), position):
            await self.move(module, dn, position)
            return
        else:
            result = {}
            obj = await self.modify(module, obj, representation, result, serverctrls=serverctrls, response=response)
            self.set_header('Location', self.urljoin(quote_dn(obj.dn)))
            self.set_entity_tags(obj, check_conditionals=False)
            self.add_caching(public=False, must_revalidate=True, no_cache=True, no_store=True)
            if result:
                self.content_negotiation(result)
            else:
                self.set_status(204)
            raise Finish()

    @sanitize
    async def patch(
        self,
        object_type,
        dn,
        position: Optional[str] = Body(DNSanitizer(required=False, default='')),
        superordinate: Optional[str] = Body(DNSanitizer(required=False, allow_none=True)),
        options: Optional[Dict] = Body(DictSanitizer({}, default_sanitizer=BooleanSanitizer(), required=False)),
        policies: Optional[Dict] = Body(DictSanitizer({}, default_sanitizer=ListSanitizer(DNSanitizer()), required=False)),
        properties: Optional[Dict] = Body(DictSanitizer({})),
    ):
        """Modify an {module.object_name} object (moving is currently not possible)"""
        dn = unquote_dn(dn)
        module, obj = await self.pool_submit(self.get_module_object, object_type, dn, self.ldap_write_connection)

        self.set_entity_tags(obj)

        entry = Object.get_representation(module, obj, ['*'], self.ldap_write_connection, False)
        representation = {
            'position': position,
            'superordinate': superordinate,
            'options': options,
            'policies': policies,
            'properties': properties,
        }
        if representation['options'] is None:
            representation['options'] = entry['options']
        if representation['policies'] is None:
            representation['policies'] = entry['policies']
        if representation['properties'] is None:
            representation['properties'] = {}
        if representation['position'] is None:
            representation['position'] = entry['position']
        if representation['superordinate'] is None:
            representation['superordinate'] = entry.get('superordinate')
        serverctrls = [PostReadControl(True, ['entryUUID', 'modifyTimestamp', 'entryCSN'])]
        response = {}
        result = {}
        obj = await self.modify(module, obj, representation, result, serverctrls=serverctrls, response=response)

        self.set_entity_tags(obj, check_conditionals=False)
        self.add_caching(public=False, must_revalidate=True, no_cache=True, no_store=True)
        self.set_header('Location', self.urljoin(quote_dn(obj.dn)))
        if result:
            self.content_negotiation(result)
        else:
            self.set_status(204)
        raise Finish()

    async def create(self, object_type, dn=None, representation=None, result=None, **kwargs):
        module = self.get_module(object_type, ldap_connection=self.ldap_write_connection)
        container = self.request.body_arguments['position']
        superordinate = self.request.body_arguments['superordinate']
        if dn:
            container = self.ldap_write_connection.parentDn(dn)
            # TODO: validate that properties are equal to rdn

        ldap_position = univention.admin.uldap.position(self.ldap_position.getBase())
        if container:
            ldap_position.setDn(container)
        elif superordinate:
            ldap_position.setDn(superordinate)
        else:
            ldap_position.setDn(module.get_default_container())

        superordinate = self.superordinate_dn_to_object(module, superordinate)

        obj = module.module.object(None, self.ldap_write_connection, ldap_position, superordinate=superordinate)
        obj.open()
        self.set_properties(module, obj, representation, result)

        if dn and not self.ldap_write_connection.compare_dn(dn, obj._ldap_dn()):
            self.raise_sanitization_error('dn', _('Trying to create an object with wrong RDN.'))

        dn = await self.pool_submit(self.handle_udm_errors, obj.create, **kwargs)
        return obj

    async def modify(self, module, obj, representation, result, **kwargs):
        assert obj._open
        self.set_properties(module, obj, representation, result)
        await self.pool_submit(self.handle_udm_errors, obj.modify, **kwargs)
        return obj

    def handle_udm_errors(self, action, *args, **kwargs):
        try:
            exists_msg = None
            error = None
            try:
                return action(*args, **kwargs)
            except udm_errors.objectExists as exc:
                exists_msg = f'dn: {exc.args[0]}'
                error = exc
            except udm_errors.uidAlreadyUsed as exc:
                exists_msg = '(uid)'
                error = exc
            except udm_errors.groupNameAlreadyUsed as exc:
                exists_msg = '(group)'
                error = exc
            except udm_errors.dhcpServerAlreadyUsed as exc:
                exists_msg = '(dhcpserver)'
                error = exc
            except udm_errors.macAlreadyUsed as exc:
                exists_msg = '(mac)'
                error = exc
            except udm_errors.noLock as exc:
                exists_msg = '(nolock)'
                error = exc
            if exists_msg and error:
                self.raise_sanitization_error('dn', _('Object exists: %s: %s') % (exists_msg, str(UDM_Error(error))))
        except (udm_errors.pwQuality, udm_errors.pwToShort, udm_errors.pwalreadyused) as exc:
            self.raise_sanitization_error(('properties', 'password'), str(UDM_Error(exc)))
        except udm_errors.invalidOptions as exc:
            self.raise_sanitization_error('options', str(UDM_Error(exc)))
        except udm_errors.insufficientInformation as exc:
            if exc.missing_properties:
                self.raise_sanitization_errors([('properties', property_name), _('The property "%(name)s" is required.') % {'name': property_name}] for property_name in exc.missing_properties)
            self.raise_sanitization_error('dn', str(UDM_Error(exc)))
        except (udm_errors.invalidOperation, udm_errors.invalidChild) as exc:
            self.raise_sanitization_error('dn', str(UDM_Error(exc)))  # TODO: invalidOperation and invalidChild should be 403 Forbidden
        except udm_errors.invalidDhcpEntry as exc:
            self.raise_sanitization_error(('properties', 'dhcpEntryZone'), str(UDM_Error(exc)))
        except udm_errors.circularGroupDependency as exc:
            self.raise_sanitization_error(('properties', 'memberOf'), str(UDM_Error(exc)))  # or "nestedGroup"
        except (udm_errors.valueError) as exc:  # valueInvalidSyntax, valueRequired, etc.
            self.raise_sanitization_error(('properties', getattr(exc, 'property', 'properties')), str(UDM_Error(exc)))
        except udm_errors.prohibitedUsername as exc:
            self.raise_sanitization_error(('properties', 'username'), str(UDM_Error(exc)))
        except udm_errors.uidNumberAlreadyUsedAsGidNumber as exc:
            self.raise_sanitization_error(('properties', 'uidNumber'), str(UDM_Error(exc)))
        except udm_errors.gidNumberAlreadyUsedAsUidNumber as exc:
            self.raise_sanitization_error(('properties', 'gidNumber'), str(UDM_Error(exc)))
        except udm_errors.mailAddressUsed as exc:
            self.raise_sanitization_error(('properties', 'mailPrimaryAddress'), str(UDM_Error(exc)))
        except (udm_errors.adGroupTypeChangeLocalToAny, udm_errors.adGroupTypeChangeDomainLocalToUniversal, udm_errors.adGroupTypeChangeToLocal) as exc:
            self.raise_sanitization_error(('properties', 'adGroupType'), str(UDM_Error(exc)))
        except udm_errors.base as exc:
            UDM_Error(exc).reraise()

    def set_properties(self, module, obj, representation, result):
        options = representation['options'] or {}  # TODO: AppAttributes.data_for_module(self.name).iteritems() ?
        options_enable = {opt for opt, enabled in options.items() if enabled}
        options_disable = {opt for opt, enabled in options.items() if enabled is False}  # ignore None!
        obj.options = list(set(obj.options) - options_disable | options_enable)
        if representation['policies']:
            obj.policies = functools.reduce(lambda x, y: x + y, representation['policies'].values())
        try:
            properties = PropertiesSanitizer(_copy_value=False).sanitize(representation['properties'], module=module, obj=obj)
        except MultiValidationError as exc:
            multi_error = exc
            properties = representation['properties']
            for prop_name in multi_error.validation_errors:
                properties.pop(prop_name)
        else:
            multi_error = MultiValidationError()

        # FIXME: for the automatic IP address assignment, we need to make sure that
        # the network is set before the IP address (see Bug #24077, comment 6)
        # The following code is a workaround to make sure that this is the
        # case, however, this should be fixed correctly.
        # This workaround has been documented as Bug #25163.
        def _tmp_cmp(i):
            if i[0] == 'mac':  # must be set before network, dhcpEntryZone
                return ("\x00", i[1])
            if i[0] == 'network':  # must be set before ip, dhcpEntryZone, dnsEntryZoneForward, dnsEntryZoneReverse
                return ("\x01", i[1])
            if i[0] in ('ip', 'mac'):  # must be set before dnsEntryZoneReverse, dnsEntryZoneForward
                return ("\x02", i[1])
            return i

        password_properties = module.password_properties
        for property_name, value in sorted(properties.items(), key=_tmp_cmp):
            self.set_property(obj, property_name, value, result, multi_error, password_properties)

        self.raise_sanitization_multi_error(multi_error)

    def set_property(self, obj, property_name, value, result, multi_error, password_properties):
        if property_name in password_properties:
            MODULE.info(f'Setting password property {property_name}')
        else:
            MODULE.info(f'Setting property {property_name} to {value!r}')

        try:
            try:
                obj[property_name] = value
            except KeyError:
                if property_name != 'objectFlag':
                    raise
            except udm_errors.valueMayNotChange:
                if obj[property_name] == value:  # UDM does not check equality before raising the exception
                    return
                raise udm_errors.valueMayNotChange()  # the original exception is ugly!
            except udm_errors.valueRequired:
                if value is None:
                    # examples where this happens:
                    # "password" of users/user: because password is required but on modify() None is send, which must not alter the current password
                    # "unixhome" of users/user: is required, set to None in the request, the default value is set afterwards in create(). Bug #50053
                    if property_name in password_properties:
                        MODULE.info(f'Ignore unsetting password property {property_name}')
                    else:
                        current_value = obj.info.pop(property_name, None)
                        MODULE.info(f'Unsetting property {property_name} value {current_value!r}')
                    return
                raise
        except (udm_errors.valueInvalidSyntax, udm_errors.valueError, udm_errors.valueMayNotChange, udm_errors.valueRequired, udm_errors.noProperty) as exc:
            try:
                self.raise_sanitization_error(property_name, _('The property %(name)s has an invalid value: %(details)s') % {'name': property_name, 'details': UDM_Error(exc)})
            except ValidationError as exc:
                multi_error.add_error(exc, property_name)

    async def move(self, module, dn, position):
        status_id = str(uuid.uuid4())
        status = shared_memory.dict()
        status.update({
            'id': status_id,
            'finished': False,
            'errors': False,
        })

        # shared_memory.queue[self.request.user_dn] = queue.copy()
        try:
            shared_memory.queue[self.request.user_dn]
        except KeyError:
            shared_memory.queue[self.request.user_dn] = shared_memory.dict()
        shared_memory.queue[self.request.user_dn][status_id] = status

        self.set_status(201)  # FIXME: must be 202
        self.set_header('Location', self.abspath('progress', status['id']))
        self.add_caching(public=False, must_revalidate=True)
        self.content_negotiation(dict(status))
        try:
            dn = await self.pool_submit(module.move, dn, position)
        except Exception:
            status['errors'] = True
            status['traceback'] = traceback.format_exc()  # FIXME: error handling
            raise
        else:
            status['uri'] = self.urljoin(quote_dn(dn))
        finally:
            status['finished'] = True

    @sanitize
    async def delete(
        self,
        object_type,
        dn,
        cleanup: bool = Query(BoolSanitizer(default=True), description="Whether to perform a cleanup (e.g. of temporary objects, locks, etc).", example=True),
        recursive: bool = Query(BoolSanitizer(default=True), description="Whether to remove referring objects (e.g. DNS or DHCP references).", example=True),
    ):
        """Remove a {module.object_name_plural} object"""
        dn = unquote_dn(dn)
        module, obj = await self.pool_submit(self.get_module_object, object_type, dn, self.ldap_write_connection)
        assert obj._open

        self.set_entity_tags(obj, remove_after_check=True)

        try:
            def remove():
                try:
                    MODULE.info('Removing LDAP object %s' % (dn,))
                    obj.remove(remove_childs=recursive)
                    if cleanup:
                        udm_objects.performCleanup(obj)
                except udm_errors.base as exc:
                    UDM_Error(exc).reraise()
            await self.pool_submit(remove)
        except udm_errors.primaryGroupUsed:
            raise
        self.add_caching(public=False, must_revalidate=True)
        self.set_status(204)
        raise Finish()


class UserPhoto(ConditionalResource, Resource):

    async def get(self, object_type, dn):
        dn = unquote_dn(dn)
        module = get_module(object_type, dn, self.ldap_connection)
        if module is None:
            raise NotFound(object_type, dn)

        obj = await self.pool_submit(module.get, dn)
        if not obj:
            raise NotFound(object_type, dn)

        if not obj.has_property('jpegPhoto'):
            raise NotFound(object_type, dn)

        data = base64.b64decode(obj.info.get('jpegPhoto', '').encode('ASCII'))
        modified = self.modified_from_timestamp(self.ldap_connection.getAttr(obj.dn, 'modifyTimestamp')[0].decode('utf-8'))
        if modified:
            self.add_header('Last-Modified', last_modified(modified))
        self.set_header('Content-Type', 'image/jpeg')
        self.add_caching(public=False, max_age=2592000, must_revalidate=True)
        self.finish(data)

    async def post(self, object_type, dn):
        dn = unquote_dn(dn)
        module = get_module(object_type, dn, self.ldap_write_connection)
        if module is None:
            raise NotFound(object_type, dn)

        obj = await self.pool_submit(module.get, dn)
        if not obj:
            raise NotFound(object_type, dn)

        if not obj.has_property('jpegPhoto'):
            raise NotFound(object_type, dn)

        photo = self.request.files['jpegPhoto'][0]['body']
        if len(photo) > 262144:
            raise HTTPError(413, 'too large: maximum: 262144 bytes')
        obj['jpegPhoto'] = base64.b64encode(photo).decode('ASCII')

        await self.pool_submit(obj.modify)

        self.set_status(204)
        raise Finish()


class ObjectAdd(FormBase, _OpenAPIBase, Resource):
    """GET a form containing information about all properties, methods, URLs to create a specific object"""

    @sanitize
    async def get(
        self,
        object_type,
        position: str = Query(DNSanitizer(required=False, allow_none=True), description="Position which is used as search base."),
        superordinate: str = Query(DNSanitizer(required=False, allow_none=True), description="The superordinate DN of the object to create. `position` is sufficient."),  # example=f"cn=superordinate,{ldap_base}"
        template: str = Query(DNSanitizer(required=False, allow_none=True), description="**Experimental**: A |UDM| template object.", deprecated=True),
    ):
        """Get a template for creating an {module.object_name} object (contains all properties and their default values)"""
        module = self.get_module(object_type)  # ldap_connection=self.ldap_write_connection ?
        if 'add' not in module.operations:
            raise NotFound(object_type)

        module.load(force_reload=True)  # reload for instant extended attributes

        result = {}

        self.add_link(result, 'self', self.urljoin(''), title=_('Add %s') % (module.object_name,))
        if not module.template:
            template = None
        result.update(self.get_create_form(module, template=template, position=position, superordinate=superordinate))

        if module.template:
            template = UDM_Module(module.template, ldap_connection=self.ldap_connection, ldap_position=self.ldap_position)  # ldap_connection=self.ldap_write_connection ?
            templates = template.search(ucr.get('ldap/base'))
            if templates:
                form = self.add_form(result, action='', method='GET', id='template', layout='template')  # FIXME: preserve query string
                template_layout = [{'label': _('Template'), 'description': 'A template defines rules for default object properties.', 'layout': ['template', '']}]
                self.add_layout(result, template_layout, 'template')
                self.add_form_element(form, 'template', '', element='select', options=[{'value': _obj.dn, 'label': template.obj_description(_obj)} for _obj in templates])
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
        self.add_link(result, 'udm:properties', href=self.urljoin('properties'), title=_('Properties for %s') % (module.object_name,))

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

        form = self.add_form(result, action=self.urljoin(''), method='GET', id='position', layout='position')  # FIXME: preserve query string
        self.add_form_element(form, 'position', position or '', element='select', options=sorted(({'value': x, 'label': ldap_dn2path(x)} for x in module.get_default_containers()), key=lambda x: x['label'].lower()))
        self.add_form_element(form, '', _('Select position'), type='submit')
        position_layout = [{'label': _('Container'), 'description': "The container in which the LDAP object shall be created.", 'layout': ['position', '']}]
        self.add_layout(result, position_layout, 'position')
        return result

    def get_html(self, response):
        root = super().get_html(response)
        if self.request.method in ('GET', 'HEAD'):
            for form in root:
                if form.get('id') == 'add':
                    for elem in form.findall('.//section'):
                        self.add_link(response, 'udm:tab-switch', href=f'#{elem.get("id")}', title=elem.find('./h1').text)
        return root


class ObjectCopy(ObjectAdd):

    @sanitize
    async def get(
        self,
        object_type,
        dn: str = Query(DNSanitizer(required=True)),
    ):
        module = self.get_module(object_type)  # ldap_connection=self.ldap_write_connection ?
        if 'copy' not in module.operations:
            raise NotFound(object_type)

        result = {}
        self.add_link(result, 'self', self.urljoin(''), title=_('Copy %s') % (module.object_name,))
        result.update(self.get_create_form(module, dn=dn, copy=True))
        self.add_caching(public=True, must_revalidate=True)
        self.content_negotiation(result)


class ObjectEdit(FormBase, Resource):
    """GET a form containing ways to modify, remove, move a specific object"""

    async def get(self, object_type, dn):
        dn = unquote_dn(dn)
        module = get_module(object_type, dn, self.ldap_connection)
        if module is None:
            raise NotFound(object_type, dn)

        if not set(module.operations) & {'remove', 'move', 'subtree_move', 'edit'}:
            # modification of this object type is not possible
            raise NotFound(object_type, dn)

        result = {}
        module.load(force_reload=True)  # reload for instant extended attributes

        obj = await self.pool_submit(module.get, dn)
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

            assert obj._open
            layout = Layout.get_layout(module, dn if object_type != 'users/self' else None)
            layout[0]['layout'].extend(['dn', 'jpegPhoto-preview', ''])
            properties = Properties.get_properties(module, dn)
            self.add_resource(result, 'udm:properties', {'properties': properties})
            self.add_link(result, 'udm:properties', href=self.urljoin('properties'), title=_('Properties for %s') % (module.object_name,))
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

    def get_html(self, response):
        root = super().get_html(response)
        if self.request.method in ('GET', 'HEAD'):
            for form in root:
                if form.get('id') == 'edit':
                    for elem in form.findall('.//section'):
                        self.add_link(response, 'udm:tab-switch', href=f'#{elem.get("id")}', title=elem.find('./h1').text, dont_set_http_header=True)
        return root


class ObjectMultiEdit(ObjectEdit):
    pass


class PropertyChoices(Resource):
    """GET udm/users/user/$DN/properties/$name/choices (get possible values/choices for that property)"""

    @sanitize
    async def get(
        self,
        object_type,
        dn,
        property_,
        dn_: str = Query(DNSanitizer(required=False), alias='dn'),
        property: str = Query(ObjectPropertySanitizer(required=False)),
        value: str = Query(SearchSanitizer(required=False)),
        hidden: bool = Query(BooleanSanitizer(required=False, default=True)),
        dependencies: str = Query(DictSanitizer({}, required=False)),
    ):
        dn = unquote_dn(dn)
        module = self.get_module(object_type)
        try:
            prop = module.module.property_descriptions[property_]
        except KeyError:
            raise NotFound(object_type, dn)
        type_ = udm_types.TypeHint.detect(prop, property_)
        options = {key: val for key, val in {
            'dn': dn_,
            'property': property,
            'value': value,
            'hidden': hidden,
            'dependencies': dependencies,
        }.items() if val is not None}
        choices = await self.pool_submit(type_.get_choices, self.ldap_connection, options)
        result = {'choices': choices}

        self.add_link(result, 'self', self.urljoin(''), title=_('Property choices for %s property %s') % (module.object_name, prop.short_description))
        if dn:
            self.add_link(result, 'icon', self.urljoin('../../../favicon.ico'), type='image/x-icon')
            self.add_link(result, 'udm:object-modules', self.urljoin('../../../../../'), title=_('All modules'))
            self.add_link(result, 'udm:object-module', self.urljoin('../../../../'), title=self.get_parent_object_type(module).object_name_plural)
            self.add_link(result, 'type', self.urljoin('../../../'), title=module.object_name)
            self.add_link(result, 'up', self.urljoin('../../..', quote_dn(dn)), title=dn)
        else:
            self.add_link(result, 'icon', self.urljoin('./../../favicon.ico'), type='image/x-icon')
            self.add_link(result, 'udm:object-modules', self.urljoin('../../../../'), title=_('All modules'))
            self.add_link(result, 'udm:object-module', self.urljoin('../../../'), title=self.get_parent_object_type(module).object_name_plural)
            # self.add_link(result, 'type', self.urljoin('.'), title=module.object_name)
            self.add_link(result, 'up', self.urljoin('../../'), title=module.object_name)
        self.add_caching(public=False, must_revalidate=True)
        self.content_negotiation(result)


class PolicyResultBase(Resource):
    """get the possible policies of the policy-type for user objects located at the container"""

    @run_on_executor(executor='pool')
    def _get(self, object_type, policy_type, dn, is_container=False):
        """
        Returns a virtual policy object containing the values that
        the given object or container inherits
        """
        policy_dn = self.request.decoded_query_arguments['policy']

        if is_container:
            # editing a new (i.e. non existing) object -> use the parent container
            obj = self.get_object_by_dn(dn)
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
        for key, _value in infos.items():
            if key in policy_obj.polinfo:
                if isinstance(infos[key], (tuple, list)):
                    continue
                _value['value'] = policy_obj.polinfo[key]
        if policy_dn:
            self.add_link(infos, 'udm:policy-edit', self.abspath(policy_obj.module, policy_dn), title=_('Click to edit the inherited properties of the policy'))
        return infos


class PolicyResult(PolicyResultBase):
    """
    get the possible policies of the policy-type for user objects located at the containter
    GET udm/users/user/$userdn/policies/$policy_type/?policy=$dn (for a existing object)
    """

    @sanitize
    async def get(
        self,
        object_type,
        dn,
        policy_type,
        policy: str = Query(DNSanitizer(required=False, default=None)),
    ):
        dn = unquote_dn(dn)
        infos = await self._get(object_type, policy_type, dn, is_container=False)
        self.add_caching(public=False, no_cache=True, must_revalidate=True, no_store=True)
        self.content_negotiation(infos)


class PolicyResultContainer(PolicyResultBase):
    """
    get the possible policies of the policy-type for user objects located at the containter
    GET udm/users/user/policies/$policy_type/?policy=$dn&position=$dn (for a container, where a object should be created in)
    """

    @sanitize
    async def get(
        self,
        object_type,
        policy_type,
        policy: str = Query(DNSanitizer(required=False, default=None)),
        position: str = Query(DNSanitizer(required=True)),
    ):
        infos = await self._get(object_type, policy_type, position, is_container=True)
        self.add_caching(public=False, no_cache=True, must_revalidate=True, no_store=True)
        self.content_negotiation(infos)


class Operations(Resource):
    """GET /udm/progress/$progress-id (get the progress of a started operation like move, report, maybe add/put?, ...)"""

    def check_acceptable(self):
        if self.request.headers.get('Accept') == '*/*':
            # python-udm-rest-api-client <= 1.2.2 doesn't provide "Accept: application/json" header
            return 'json'
        return super().check_acceptable()

    def get(self, progress):
        progressbars = shared_memory.queue.get(self.request.user_dn, {})
        if progress not in progressbars:
            raise NotFound()
        result = dict(progressbars[progress])
        if result.get('uri'):
            self.set_status(303)
            self.add_header('Location', result['uri'])
            self.add_link(result, 'self', result['uri'])
            shared_memory.queue.get(self.request.user_dn, {}).pop(progress, {})
        else:
            self.set_status(301)
            self.add_header('Location', self.urljoin(''))
            self.add_header('Retry-After', '1')
        self.add_caching(public=False, no_store=True, no_cache=True, must_revalidate=True)
        self.content_negotiation(result)

    def get_html(self, response):
        root = super().get_html(response)
        if isinstance(response, dict) and 'value' in response and 'max' in response:
            h1 = ET.Element('h1')
            h1.text = response.get('description', '')
            root.append(h1)
            root.append(ET.Element('progress', value=str(response['value']), max=str(response['max'])))
        return root


class LicenseRequest(Resource):

    @sanitize
    async def get(
        self,
        email: str = Query(EmailSanitizer(required=True)),
    ):
        data = {
            'email': email,
            'licence': dump_license(),
        }
        if not data['licence']:
            raise HTTPError(500, _('Cannot parse License from LDAP'))

        # TODO: we should also send a link (self.request.full_url()) to the license server, so that the email can link to a url which automatically inserts the license:
        # self.request.urljoin('import', license=quote(base64.b64encode(zlib.compress(b''.join(_[17:] for _ in open('license.ldif', 'rb').readlines() if _.startswith(b'univentionLicense')), 6)[2:-4])))

        data = urlencode(data)
        url = 'https://license.univention.de/keyid/conversion/submit'
        http_client = tornado.httpclient.AsyncHTTPClient()
        try:
            await http_client.fetch(url, method='POST', body=data, user_agent='UMC/AppCenter', headers={'Content-Type': 'application/x-www-form-urlencoded'})
        except tornado.httpclient.HTTPError as exc:
            error = str(exc)
            if exc.response.code >= 500:
                error = _('This seems to be a problem with the license server. Please try again later.')
            match = re.search(b'<span id="details">(?P<details>.*?)</span>', exc.response.body, flags=re.DOTALL)
            if match:
                error = match.group(1).decode('UTF-8', 'replace').replace('\n', '')
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
        self.content_negotiation({'message': message})


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
        except ImportError:
            license_data['licenseVersion'] = 'gpl'
        else:
            license_data['licenseVersion'] = udm_license._license.version
            if udm_license._license.version == '1':
                for item in ('licenses', 'real'):
                    license_data[item] = {}
                    for lic_type in ('CLIENT', 'ACCOUNT', 'DESKTOP', 'GROUPWARE'):
                        count = getattr(udm_license._license, item)[udm_license._license.version][getattr(udm_license.License, lic_type)]
                        if isinstance(count, str):
                            try:
                                count = int(count)
                            except ValueError:
                                count = None
                        license_data[item][lic_type.lower()] = count

                if 'UGS' in udm_license._license.types:
                    udm_license._license.types = filter(lambda x: x != 'UGS', udm_license._license.types)
            elif udm_license._license.version == '2':
                for item in ('licenses', 'real'):
                    license_data[item] = {}
                    for lic_type in ('SERVERS', 'USERS', 'MANAGEDCLIENTS', 'CORPORATECLIENTS'):
                        count = getattr(udm_license._license, item)[udm_license._license.version][getattr(udm_license.License, lic_type)]
                        if isinstance(count, str):
                            try:
                                count = int(count)
                            except ValueError:
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

    @sanitize
    async def get(
        self,
        license: str = Query(StringSanitizer(required=True)),
    ):
        text = '''dn: cn=admin,cn=license,cn=univention,%(ldap/base)s
cn: admin
objectClass: top
objectClass: univentionLicense
objectClass: univentionObject
univentionObjectType: settings/license
''' % ucr
        for line in zlib.decompress(base64.b64decode(license.encode('ASCII')), -15).decode('UTF-8').splitlines():
            text += f'univentionLicense{line.strip()}\n'

        self.import_license(io.BytesIO(text.encode('UTF-8')))

    def post(self):
        return self.import_license(io.BytesIO(self.request.files['license'][0]['body']))

    def import_license(self, fd):
        try:
            # check license and write it to LDAP
            importer = LicenseImporter(fd)
            importer.check(ucr.get('ldap/base', ''))
            importer.write(self.ldap_write_connection)
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


class ServiceSpecificPassword(Resource):

    @sanitize
    async def post(
        self,
        object_type,
        dn,
        service: str = Body(StringSanitizer(required=True)),
    ):
        module = get_module(object_type, dn, self.ldap_write_connection)
        if module is None:
            raise NotFound(object_type, dn)

        cfg = password_config(service)
        new_password = generate_password(**cfg)

        obj = await self.pool_submit(module.get, dn)
        obj['serviceSpecificPassword'] = {'service': service, 'password': new_password}

        try:
            await self.pool_submit(obj.modify)
        except udm_errors.valueError as exc:
            # ValueError raised if Service is not supported
            raise HTTPError(400, str(exc))
        result = {'service': service, 'password': new_password}
        self.content_negotiation(result)


class Application(tornado.web.Application):

    def __init__(self, **kwargs):
        #module_type = '([a-z]+)'
        module_type = '(%s)' % '|'.join(re.escape(mod) for mod in Modules.mapping)
        object_type = '([A-Za-z0-9_-]+/[A-Za-z0-9_-]+)'
        policies_object_type = '(policies/[A-Za-z0-9_-]+)'
        dn = '((?:[^/]+%s.+%s)?%s)' % (self.multi_regex('='), self.multi_regex(','), self.multi_regex(ucr['ldap/base']))
        # FIXME: with that dn regex, it is not possible to have urls like (/udm/$dn/foo/$dn/) because ldap-base at the end matches the last dn
        # Note: the ldap base is part of the url to support "/" as part of the DN. otherwise we can use: '([^/]+(?:=|%3d|%3D)[^/]+)'
        # Note: we cannot use .replace('/', '%2F') for the dn part as url-normalization could replace this and apache doesn't pass URLs with %2F to the ProxyPass without http://httpd.apache.org/docs/current/mod/core.html#allowencodedslashes
        property_ = '([^/]+)'
        super().__init__([
            ("/(?:udm/)?(favicon).ico", Favicon, {"path": "/var/www/favicon.ico"}),
            ("/udm/(?:index.html)?", Modules),
            ("/udm/openapi.json", OpenAPI),
            ("/udm/relation/(.*)", Relations),
            ("/udm/license/", License),
            ("/udm/license/import", LicenseImport),
            ("/udm/license/check", LicenseCheck),
            ("/udm/license/request", LicenseRequest),
            ("/udm/ldap/base/", LdapBase),
            (f"/udm/object/{dn}", ObjectLink),
            ("/udm/object/([a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12})", ObjectByUiid),
            (f"/udm/{module_type}/", ObjectTypes),
            ("/udm/(navigation)/tree", Tree),
            (f"/udm/(?:{object_type}|navigation)/move-destinations/", MoveDestinations),
            ("/udm/navigation/children-types/", SubObjectTypes),
            (f"/udm/{object_type}/", Objects),
            (f"/udm/{object_type}/openapi.json", OpenAPI),
            (f"/udm/{object_type}/add", ObjectAdd),
            (f"/udm/{object_type}/copy", ObjectCopy),
            (f"/udm/{object_type}/move", ObjectsMove),
            (f"/udm/{object_type}/multi-edit", ObjectMultiEdit),
            (f"/udm/{object_type}/tree", Tree),
            (f"/udm/{object_type}/properties", Properties),
            (f"/udm/{object_type}/()properties/{property_}/choices", PropertyChoices),
            (f"/udm/{object_type}/layout", Layout),
            (f"/udm/{object_type}/favicon.ico", Favicon, {"path": "/usr/share/univention-management-console-frontend/js/dijit/themes/umc/icons/16x16/"}),
            (f"/udm/{object_type}/{dn}", Object),
            (f"/udm/{object_type}/{dn}/edit", ObjectEdit),
            (f"/udm/{object_type}/{dn}/children-types/", SubObjectTypes),
            (f"/udm/{object_type}/report/([^/]+)", Report),
            (f"/udm/{object_type}/{dn}/{policies_object_type}/", PolicyResult),
            (f"/udm/{object_type}/{policies_object_type}/", PolicyResultContainer),
            (f"/udm/{object_type}/{dn}/layout", Layout),
            (f"/udm/{object_type}/{dn}/properties", Properties),
            (f"/udm/{object_type}/{dn}/properties/{property_}/choices", PropertyChoices),
            (f"/udm/{object_type}/{dn}/properties/jpegPhoto.jpg", UserPhoto),
            (f"/udm/(networks/network)/{dn}/next-free-ip-address", NextFreeIpAddress),
            (f"/udm/(users/user)/{dn}/service-specific-password", ServiceSpecificPassword),
            ("/udm/progress/([a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12})", Operations),
            # TODO: decorator for dn argument, which makes sure no invalid dn syntax is used
        ], default_handler_class=Nothing, **kwargs)

    def multi_regex(self, chars):
        # Bug in tornado: requests go against the raw url; https://github.com/tornadoweb/tornado/issues/2548, therefore we must match =, %3d, %3D
        return ''.join(f'(?:{re.escape(c)}|{re.escape(quote(c).lower())}|{re.escape(quote(c).upper())})' if c in '=,' else re.escape(c) for c in chars)
