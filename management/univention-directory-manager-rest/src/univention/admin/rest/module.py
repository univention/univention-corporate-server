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
import datetime
import functools
import hashlib
import inspect
import io
import json
import os
import re
import time
import traceback
import uuid
import xml.etree.ElementTree as ET
import zlib
from email.utils import parsedate
from http.client import responses
from typing import Dict, List, Optional
from urllib.parse import parse_qs, quote, unquote, urlencode, urljoin, urlparse, urlunparse

import defusedxml.minidom
import ldap
import tornado.gen
import tornado.httpclient
import tornado.httputil
import tornado.ioloop
import tornado.log
import tornado.web
from concurrent.futures import ThreadPoolExecutor
from genshi import XML
#from genshi.output import HTMLSerializer
from ldap.controls import SimplePagedResultsControl
from ldap.controls.readentry import PostReadControl
from ldap.controls.sss import SSSRequestControl
from ldap.dn import explode_rdn
from ldap.filter import filter_format
from tornado.concurrent import run_on_executor
from tornado.web import Finish, HTTPError, RequestHandler

import univention.admin.modules as udm_modules
import univention.admin.objects as udm_objects
import univention.admin.syntax as udm_syntax
import univention.admin.types as udm_types
import univention.admin.uexceptions as udm_errors
import univention.directory.reports as udr
import univention.udm
from univention.admin.rest.shared_memory import JsonEncoder, shared_memory
from univention.config_registry import handler_set
from univention.lib.i18n import Translation
from univention.management.console.config import ucr
from univention.management.console.error import LDAP_ConnectionFailed, LDAP_ServerDown, UMC_Error, UnprocessableEntity
from univention.management.console.ldap import get_connection, reset_cache
from univention.management.console.log import MODULE
from univention.management.console.modules.sanitizers import (
    BooleanSanitizer, ChoicesSanitizer, DictSanitizer, DNSanitizer, EmailSanitizer, IntegerSanitizer,
    LDAPSearchSanitizer, ListSanitizer, MultiValidationError, Sanitizer, SearchSanitizer, StringSanitizer,
    ValidationError,
)
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
# TODO: modify layout and properties for app-tabs
# TODO: loading the policies probably unnecessarily slows down things
# TODO: create a own translation domain for this file

_ = Translation('univention-directory-manager-rest').translate

RE_UUID = re.compile('[^A-Fa-f0-9-]')
MAX_WORKERS = ucr.get('directory/manager/rest/max-worker-threads', 35)


def get_user_ldap_write_connection(binddn, bindpw):
    return get_ldap_connection('user-write', binddn, bindpw)


def get_user_ldap_read_connection(binddn, bindpw):
    return get_ldap_connection('user-read', binddn, bindpw)


def get_machine_ldap_connection(type_):
    binddn = ucr.get(f'directory/manager/rest/ldap-connection/{type_}/binddn', ucr['ldap/hostdn'])
    with open(ucr.get(f'directory/manager/rest/ldap-connection/{type_}/password-file', '/etc/machine.secret')) as fd:
        password = fd.read().strip()
    return get_ldap_connection(type_, binddn, password)


def get_machine_ldap_write_connection():
    return get_machine_ldap_connection('machine-write')


def get_machine_ldap_read_connection():
    return get_machine_ldap_connection('machine-read')


def get_ldap_connection(type_, binddn, bindpw):
    default_uri = "ldap://%s:%d" % (ucr.get('ldap/master'), ucr.get_int('ldap/master/port', '7389'))
    uri = ucr.get(f'directory/manager/rest/ldap-connection/{type_}/uri', default_uri)
    start_tls = ucr.get_int('directory/manager/rest/ldap-connection/user-read/start-tls', 2)
    return get_connection(bind=None, binddn=binddn, bindpw=bindpw, host=None, port=None, base=ucr['ldap/base'], start_tls=start_tls, uri=uri)


class Param:

    @property
    def type(self):
        return type(self).__name__.lower()

    def __init__(self, sanitizer, alias=None, description=None, deprecated=None, example=None, examples=None, style=None, explode=None):
        self.sanitizer = sanitizer
        self.alias = alias
        self.description = description
        self.deprecated = deprecated
        self.example = example
        self.examples = examples
        self.style = style
        self.explode = explode


class Path(Param):
    pass


class Body(Param):

    def __init__(self, sanitizer, content_type='application/json', **kwargs):
        super().__init__(sanitizer, **kwargs)
        self.content_type = content_type


class Query(Param):
    pass


def parse_content_type(content_type):
    return content_type.partition(';')[0].strip().lower()


def sanitize(method):
    args = inspect.getfullargspec(method)
    all_args = dict(zip(reversed(args.args), reversed(args.defaults)))
    method.params = {
        ptype: {
            key: param
            for key, param in all_args.items()
            if isinstance(param, Param) and param.type == ptype
        } for ptype in ('path', 'query', 'body')
    }
    method.sanitizers = {}
    if method.params.get('query'):
        query_sanitizers = {param.alias or key: param.sanitizer for key, param in method.params['query'].items()}
        method.sanitizers['query_string'] = QueryStringSanitizer(query_sanitizers, required=True, further_arguments=['resource'], _copy_value=False)
    if method.params['body']:
        content_types = {param.content_type for param in method.params['body'].values()}
        method.sanitizers['body_arguments'] = DictSanitizer({
            content_type: DictSanitizer({
                param.alias or key: param.sanitizer if param.content_type == content_type else Sanitizer() for key, param in method.params['body'].items()
            }, required=True, further_arguments=['resource'], _copy_value=False)
            for content_type in content_types
        }, required=True, further_arguments=['resource'], _copy_value=False)

    method.sanitizer = DictSanitizer(method.sanitizers, further_arguments=['resource'], _copy_value=False)

    @functools.wraps(method)
    async def decorator(self, *args, **params):
        content_type = parse_content_type(self.request.headers.get('Content-Type', ''))
        payload = {
            'query_string': {k: [v.decode('UTF-8') for v in val] for k, val in self.request.query_arguments.items()} if self.request.query_arguments else {},
            'body_arguments': {
                'application/json': {},
                'application/x-www-form-urlencoded': {},
                'multipart/form-data': {},
            },
        }
        payload['body_arguments'][content_type] = self.request.body_arguments

        def _result_func(x):
            if x.get('body_arguments', {}).get(content_type):
                x['body_arguments'] = x['body_arguments'][content_type]
            return x
        arguments = self.sanitize_arguments(method.sanitizer, 'request.arguments', {'request.arguments': payload, 'resource': self}, _result_func=_result_func)
        self.request.decoded_query_arguments = {
            key: arguments['query_string'][param.alias or key]
            for key, param in method.params['query'].items()
        }
        self.request.body_arguments = {
            key: arguments['body_arguments'][content_type][param.alias or key]
            for key, param in method.params['body'].items()
        }
        return await method(self, *self.path_args, **self.path_kwargs, **self.request.decoded_query_arguments, **self.request.body_arguments)
    return decorator


class DictSanitizer(DictSanitizer):

    def __init__(self, sanitizers, allow_other_keys=True, **kwargs):
        self.default_sanitizer = kwargs.get('default_sanitizer', None)
        self.key_sanitizer = kwargs.get('key_sanitizer', None)
        super().__init__(sanitizers, allow_other_keys=allow_other_keys, **kwargs)

    def _sanitize(self, value, name, further_arguments):
        if not isinstance(value, dict):
            self.raise_formatted_validation_error(_('Not a "dict"'), name, type(value).__name__)

        if not self.allow_other_keys and any(key not in self.sanitizers for key in value):
            self.raise_validation_error(_('Has more than the allowed keys'))

        altered_value = copy.deepcopy(value) if self._copy_value else value

        multi_error = MultiValidationError()
        for attr in set(value) | set(self.sanitizers):
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
                    value[key] = {k[len(key) + 1:-1]: v[0] for k, v in value.items() if k.startswith(key + '[') and k.endswith(']')}
                    #value[key] = QueryStringSanitizer(sanitizer.sanitizers).sanitize(key, {key: value[key]})

        return super()._sanitize(value, name, further_arguments)


class ObjectPropertySanitizer(StringSanitizer):

    def __init__(self, **kwargs):
        """
        A LDAP attribute name.
        must at least be 1 character long.

        This sanitizer prevents LDAP search filter injections in the attribute name.

        TODO: in theory we should only allow existing searchable properties for the requested object type
        """
        args = {
            "minimum": 0,
            "regex_pattern": r'^[\w\d\-;]*$',
        }
        args.update(kwargs)
        StringSanitizer.__init__(self, **args)


class PropertiesSanitizer(DictSanitizer):

    def __init__(self, *args, **kwargs):
        super().__init__({}, *args, default_sanitizer=PropertySanitizer(), **kwargs)

    def sanitize(self, properties, module, obj):
        # TODO: add sanitizer for e.g. required properties (respect options!)

        self.default_sanitizer._module = module
        self.default_sanitizer._obj = obj
        try:
            return super().sanitize('properties', {'properties': properties})
        finally:
            self.default_sanitizer._module = None
            self.default_sanitizer._obj = None


class PropertySanitizer(Sanitizer):

    def __init__(self, *args, **kwargs):
        self._module = None
        self._obj = None
        super().__init__(*args, **kwargs)

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
            exc.message = ''
            self.raise_validation_error(_('The property %(name)s has an invalid value: %(details)s'), details=str(exc))


class BoolSanitizer(ChoicesSanitizer):

    def __init__(self, **kwargs):
        super().__init__(choices=['1', 'on', 'true', 'false', '0', 'off', '', None, True, False], **kwargs)

    def _sanitize(self, value, name, further_arguments):
        return super()._sanitize(value, name, further_arguments) in ('1', 'on', 'true', True)


class LDAPFilterSanitizer(StringSanitizer):

    def _sanitize(self, value, name, further_arguments):
        value = super()._sanitize(value, name, further_arguments)
        try:
            return udm_syntax.ldapFilter.parse(value)
        except udm_errors.valueError as exc:
            exc.message = ''
            self.raise_validation_error(str(exc))


class DNSanitizer(DNSanitizer):

    base = ldap.dn.str2dn(ucr['ldap/base'].lower())
    baselen = len(base)

    def _sanitize(self, value, name, further_arguments):
        value = super()._sanitize(value, name, further_arguments)
        if value and ldap.dn.str2dn(value.lower())[-self.baselen:] != self.base:
            self.raise_validation_error(_('The ldap base is invalid. Use %(details)s.'), details=ldap.dn.dn2str(self.base))
        return value


class NotFound(HTTPError):

    def __init__(self, object_type=None, dn=None):
        super().__init__(404, None, '%r %r' % (object_type, dn or ''))  # FIXME: create error message


def superordinate_names(module):
    superordinates = module.superordinate_names
    if set(superordinates) == {'settings/cn'}:
        return []
    return superordinates


class ResourceBase:

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

    def sanitize_arguments(self, sanitizer, *args, **kwargs):
        field = kwargs.pop('_fieldname', 'request.arguments')
        result = kwargs.pop('_result_func', lambda x: x)
        try:
            try:
                return sanitizer.sanitize(*args, **kwargs)
            except MultiValidationError:
                raise
            except ValidationError as exc:
                multi_error = MultiValidationError()
                multi_error.add_error(exc, field)
                raise multi_error
        except MultiValidationError as e:
            raise UnprocessableEntity(str(e), result=result(e.result()))

    def raise_sanitization_errors(self, errors):
        multi_error = MultiValidationError()
        for field, message in errors:
            property_name = field[-1]
            try:
                self.raise_sanitization_error(field, message)
            except UnprocessableEntity as exc:
                print(exc.result)
                multi_error.add_error(ValidationError(message, property_name, None), property_name)
        self.raise_sanitization_multi_error(multi_error)

    def raise_sanitization_multi_error(self, multi_error, field='properties', type='body'):
        if multi_error.has_errors():
            class FalseSanitizer(Sanitizer):
                def sanitize(self):
                    raise multi_error
            self.sanitize_arguments(FalseSanitizer(), _result_func=lambda x: {type: {field: x}}, _fieldname=field)

    def raise_sanitization_error(self, field, message, type='body'):
        fields = field if isinstance(field, (list, tuple)) else (field,)
        field = fields[-1]

        def _result(x):
            error = {type: {}}
            err = error[type]
            for f in fields:
                if f == field:
                    break
                err[f] = {}
                err = err[f]
            err.update(x)
            return error

        class FalseSanitizer(Sanitizer):
            def sanitize(self):
                self.raise_formatted_validation_error('%(message)s', field, None, message=message)
        self.sanitize_arguments(FalseSanitizer(), _result_func=_result, _fieldname=field)

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

    def content_negotiation_hal_json(self, response):
        data = self.content_negotiation_json(response)
        self.set_header('Content-Type', 'application/hal+json')
        return data

    def content_negotiation_html(self, response):
        self.set_header('Content-Type', 'text/html; charset=UTF-8')
        ajax = self.request.headers.get('X-Requested-With', '').lower() == 'xmlhttprequest'

        root = ET.Element("html")
        head = ET.SubElement(root, "head")
        titleelement = ET.SubElement(head, "title")
        titleelement.text = 'FIXME: fallback title'  # FIXME: set title
        ET.SubElement(head, 'meta', content='text/html; charset=utf-8', **{'http-equiv': 'content-type'})
        # if not ajax:
        #    ET.SubElement(head, 'script', type='text/javascript', src=self.abspath('../js/config.js'))
        #    ET.SubElement(head, 'script', type='text/javascript', src=self.abspath('js/udm.js'))
        #    ET.SubElement(head, 'script', type='text/javascript', async='', src=self.abspath('../js/dojo/dojo.js'))

        body = ET.SubElement(root, "body", dir='ltr')
        header = ET.SubElement(body, 'header')
        topnav = ET.SubElement(header, 'nav')
        logo = ET.SubElement(topnav, 'svg')
        ET.SubElement(logo, 'use', **{'xlink:href': "/univention/js/dijit/themes/umc/images/univention_u.svg#id", 'xmlns:xlink': "http://www.w3.org/1999/xlink"})
        h1 = ET.SubElement(topnav, 'h2', id='logo')
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
                params = {x.strip(): y.strip().strip('"').replace('\\"', '"').replace('\\\\', '\\') for x, y in ((param.split('=', 1) + [''])[:2] for param in _params.split(';'))}
            ET.SubElement(head, "link", href=link, **params)
            _links[params.get('rel')] = dict(params, href=link)
            if params.get('rel') == 'self':
                titleelement.text = params.get('title') or link or 'FIXME:notitle'
            if params.get('rel') in ('stylesheet', 'icon', 'self', 'up', 'udm:object/remove', 'udm:object/edit', 'udm:report'):
                continue
            if params.get('rel') in navigation_relations:
                continue
            if params.get('rel') in ('udm:user-photo',):
                ET.SubElement(nav, 'img', src=link, style='max-width: 200px')
                continue
            elif params.get('rel') in ('create-form', 'edit-form'):
                ET.SubElement(ET.SubElement(nav, 'form'), 'button', formaction=link, **params).text = params.get('title', link)
                continue
            # if params.get('rel') in ('udm:tree',):
            #    self.set_header('X-Frame-Options', 'SAMEORIGIN')
            #    body.insert(1, ET.Element('iframe', src=link, name='tree'))
            #    continue
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
            stream = ET.tostring(root, encoding='utf-8', method='xml')
            stream = defusedxml.minidom.parseString(stream)
            stream = stream.toprettyxml()
            stream = XML(stream)
            self.write(stream.render('xhtml'))
            # FIXME: transforms the <use xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="/univention/js/dijit/themes/umc/images/univention_u.svg#id"></use> to <use></use>
            # self.write(''.join(HTMLSerializer('html5')(stream)))
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

    def get_html(self, response: dict):
        root = []
        self.add_link(response, 'stylesheet', self.abspath('css/style.css'))

        # TODO: nav-layout?!

        # main layout
        forms = self.get_resources(response, 'udm:form')
        main_layout = self.get_resource(response, 'udm:layout', name='main-layout')
        if main_layout:
            main = ET.Element('div')  # TODO: get rid of the div
            root.append(main)
            self.get_html_layout(main, response, main_layout['layout'], [])
        else:
            # leftover forms
            for _form in forms:
                root.insert(0, self.get_html_form(_form, response))
                root[0].append(ET.Element('hr'))

        # errors
        if isinstance(response.get('error'), dict) and response['error'].get('code', 0) >= 400:
            error_response = response['error']
            error = ET.Element('div', **{'class': 'error'})
            root.append(error)
            ET.SubElement(error, 'h1').text = _('HTTP-Error %d: %s') % (error_response['code'], error_response['title'])
            ET.SubElement(error, 'p', style='white-space: pre').text = error_response['message']
            for error_detail in self.get_resources(response, 'udm:error'):
                ET.SubElement(error, 'p', style='white-space: pre').text = '%s(%s): %s' % ('.'.join(error_detail['location']), error_detail['type'], error_detail['message'])
            if error_response.get('traceback'):
                ET.SubElement(error, 'pre').text = error_response['traceback']
            response = {}

        # redirections
        if 400 > self._status_code >= 300 and self._status_code != 304:
            warning = ET.Element('div', **{'class': 'warning'})
            root.append(warning)
            href = self._headers.get("Location")
            ET.SubElement(warning, 'h1').text = _('HTTP redirection')
            ET.SubElement(warning, 'p', style='white-space: pre').text = 'You are being redirected to:'
            ET.SubElement(warning, 'a', href=href).text = href

        # print any leftover elements
        r = response.copy()
        r.pop('_links', None)
        r.pop('_embedded', None)
        if r:
            pre = ET.Element("pre")
            pre.text = json.dumps(r, indent=4)
            root.append(pre)

        return root

    def get_html_layout(self, root, response, layout, properties):
        for sec in layout:
            section = ET.SubElement(root, 'section', id=Layout.get_section_id(sec['label']))
            ET.SubElement(section, 'h1').text = sec['label']
            if sec.get('help'):
                ET.SubElement(section, 'span').text = sec['help']
            fieldset = ET.SubElement(section, 'fieldset')
            ET.SubElement(fieldset, 'legend').text = sec['description']
            if sec['layout']:
                self.render_layout(sec['layout'], fieldset, properties, response)
        return root

    def render_layout(self, layout, fieldset, properties, response):
        for elem in layout:
            if isinstance(elem, dict) and isinstance(elem.get('$form-ref'), list):
                for _form in elem['$form-ref']:
                    form = self.get_resource(response, 'udm:form', name=_form)
                    if form:
                        fieldset.append(self.get_html_form(form, response))
                continue
            elif isinstance(elem, dict):
                if not elem.get('label') and not elem.get('description'):
                    ET.SubElement(fieldset, 'br')
                    sub_fieldset = ET.SubElement(fieldset, 'div', style='display: flex')
                else:
                    sub_fieldset = ET.SubElement(fieldset, 'details', open='open')
                    ET.SubElement(sub_fieldset, 'summary').text = elem['label']
                    if elem['description']:
                        ET.SubElement(sub_fieldset, 'h2').text = elem['description']
                self.render_layout(elem['layout'], sub_fieldset, properties, response)
                continue
            elements = [elem] if isinstance(elem, str) else elem
            for elem in elements:
                for field in properties:
                    if field['name'] in (elem, 'properties.%s' % elem):
                        self.render_form_field(fieldset, field)
            if elements:
                ET.SubElement(fieldset, 'br')

    def get_html_form(self, _form, response):
        form = ET.Element('form', **{p: _form[p] for p in ('id', 'class', 'name', 'method', 'action', 'rel', 'enctype', 'accept-charset', 'novalidate') if _form.get(p)})
        if _form.get('layout'):
            layout = self.get_resource(response, 'udm:layout', name=_form['layout'])
            self.get_html_layout(form, response, layout['layout'], _form.get('fields'))
            return form

        for field in _form.get('fields', []):
            self.render_form_field(form, field)
            form.append(ET.Element('br'))

        return form

    def render_form_field(self, form, field):
        datalist = None
        name = field['name']

        if field.get('type') == 'submit' and field.get('add_noscript_warning'):
            ET.SubElement(ET.SubElement(form, 'noscript'), 'p').text = _('This form requires JavaScript enabled!')

        label = None
        if name:
            label = ET.Element('label', **{'for': name})
            label.text = field.get('label', name)

        multivalue = field.get('data-multivalue') == '1'
        values = field['value'] or [''] if multivalue else [field['value']]
        for value in values:
            elemattrs = {p: field[p] for p in ('id', 'disabled', 'form', 'multiple', 'required', 'size', 'type', 'placeholder', 'accept', 'alt', 'autocomplete', 'checked', 'max', 'min', 'minlength', 'pattern', 'readonly', 'src', 'step', 'style', 'alt', 'autofocus', 'class', 'cols', 'href', 'rel', 'title', 'list') if field.get(p)}
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

    def add_link(self, obj, relation, href, **kwargs):
        dont_set_http_header = kwargs.pop('dont_set_http_header', False)
        links = obj.setdefault('_links', {})
        links.setdefault(relation, []).append(dict(kwargs, href=href))
        if dont_set_http_header:
            return

        def quote_param(s):
            for char in '\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f':  # remove non printable characters
                s = s.replace(char, '')
            return s.encode('ISO8859-1', 'replace').decode('ISO8859-1').replace('\\', '\\\\').replace('"', '\\"')
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
        if form.get('name'):
            self.add_link(form, 'self', href='', name=form['name'], dont_set_http_header=True)
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
        layout = {'layout': layout}
        if name:
            self.add_link(layout, 'self', href='', name=name, dont_set_http_header=True)
        self.add_resource(obj, 'udm:layout', layout)
        if href:
            self.add_link(obj, 'udm:layout', href=href, name=name)

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

    def navigation(self):
        return ('udm:object-modules', 'udm:object-module', 'type', 'up', 'self')


class ConditionalResource:

    def set_entity_tags(self, obj, check_conditionals=True, remove_after_check=False):
        self.set_header('Etag', self.get_etag(obj))
        modified = self.modified_from_timestamp(obj.oldattr['modifyTimestamp'][0].decode('utf-8', 'replace'))
        if modified:
            self.set_header('Last-Modified', last_modified(modified))
        if check_conditionals:
            self.check_conditional_requests()
        if remove_after_check:
            self._headers.pop("Etag", None)
            self._headers.pop("Last-Modified", None)

    def get_etag(self, obj):
        # generate as early as possible, to not cause side effects e.g. default values in obj.info. It must be the same value for GET and PUT
        if not obj._open:
            raise RuntimeError('Object was not opened!')
        etag = hashlib.sha1()
        etag.update(obj.dn.encode('utf-8', 'replace'))
        etag.update(obj.module.encode('utf-8', 'replace'))
        etag.update(b''.join(obj.oldattr.get('entryCSN', [])))
        etag.update((obj.entry_uuid or '').encode('utf-8'))
        #etag.update(json.dumps({k: [v.decode('ISO8859-1', 'replace') for v in val] for k, val in obj.oldattr.items()}, sort_keys=True).encode('utf-8'))
        #etag.update(json.dumps(obj.info, sort_keys=True).encode('utf-8'))
        return '"%s"' % etag.hexdigest()

    def modified_from_timestamp(self, timestamp):
        modified = time.strptime(timestamp, '%Y%m%d%H%M%SZ')
        # make sure Last-Modified is only send if it is not now
        if modified < time.gmtime(time.time() - 1):
            return modified

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
            return x[2:] if x.startswith('W/') else x
        etag_matches = re.compile(r'\*|(?:W/)?"[^"]*"')

        def check_conditional_request_if_none_match():
            etags = etag_matches.findall(self.request.headers.get("If-None-Match", ""))
            if not etags:
                if self.request.headers.get("If-None-Match"):
                    raise HTTPError(400, 'Invalid "If-None-Match" syntax.')
                return

            if '*' in etags or wheak(etag) in map(wheak, etags):
                if safe_request:
                    self.set_status(304)  # Not modified
                    raise Finish()
                else:
                    message = _('The resource has meanwhile been changed. If-None-Match %s does not match entity tag %s.') % (', '.join(etags), etag)
                    raise HTTPError(412, message)  # Precondition Failed

        def check_conditional_request_if_match():
            etags = etag_matches.findall(self.request.headers.get("If-Match", ""))
            if not etags:
                if self.request.headers.get("If-Match"):
                    raise HTTPError(400, 'Invalid "If-Match" syntax.')
                return
            if '*' not in etags and wheak(etag) not in map(wheak, etags):
                message = _('The resource has meanwhile been changed. If-Match %s does not match entity tag %s.') % (', '.join(etags), etag)
                if not safe_request:
                    raise HTTPError(412, message)  # Precondition Failed
                elif self.request.headers.get('Range'):
                    raise HTTPError(416, message)  # Range Not Satisfiable

        check_conditional_request_if_none_match()
        check_conditional_request_if_match()


def _param_to_openapi(param):
    san = param.sanitizer
    type_ = ''
    definition = {key: val for key, val in {
        'description': param.description,
        'deprecated': param.deprecated,
        'example': param.example,
        'examples': param.examples,
        'style': param.style,
        'explode': param.explode,
    }.items() if val is not None}
    schema = {}
    if isinstance(san, DictSanitizer):
        type_ = 'object'
        schema['additionalProperties'] = san.allow_other_keys
        schema['properties'] = {
            prop: _param_to_openapi(Param(s or san.default_sanitizer))['schema']
            for prop, s in san.sanitizers.items()
            if s or san.default_sanitizer
        }
    elif isinstance(san, ListSanitizer):
        type_ = 'array'
        if san.min_elements is not None:
            schema['minItems'] = san.min_elements
        if san.max_elements is not None:
            schema['maxItems'] = san.max_elements
        if san.sanitizer:
            schema['items'] = _param_to_openapi(Param(san.sanitizer))['schema']
    elif isinstance(san, DNSanitizer):
        type_ = 'string'
        schema['format'] = 'dn'
    elif isinstance(san, BooleanSanitizer):
        type_ = 'boolean'
    elif isinstance(san, BoolSanitizer):
        type_ = 'boolean'
        #type_ = 'string'
        #definition['examples'] = {choice: {'value': choice, 'summary': choice} for choice in san.choices}
    elif isinstance(san, ChoicesSanitizer):
        type_ = 'string'
        definition['examples'] = {choice: {'value': choice, 'summary': choice} for choice in san.choices}
        schema['pattern'] = '^(%s)$' % ('|'.join(re.escape(choice) for choice in san.choices))
    elif isinstance(san, IntegerSanitizer):
        type_ = 'integer'
        if san.minimum is not None:
            schema['minimum'] = san.minimum
            if san.minimum_strict is True:
                schema['exclusiveMinimum'] = True
        if san.maximum is not None:
            schema['maximum'] = san.maximum
            if san.maximum_strict is True:
                schema['exclusiveMaximum'] = True
    elif isinstance(san, StringSanitizer):
        type_ = 'string'
        if san.minimum is not None:
            schema['minLength'] = san.minimum
        if san.maximum is not None:
            schema['maxLength'] = san.maximum
        if san.regex_pattern:
            schema['regex'] = san.regex_pattern.pattern
    else:
        raise TypeError(type(san))
    # if san.required is not None:
    #    schema['required'] = san.required
    if san.default or san.allow_none:
        schema['default'] = san.default
    if san.allow_none:
        schema['nullable'] = True
    schema['type'] = type_
    definition['schema'] = schema
    return definition


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


class Relations(Resource):

    def get(self, relation):
        iana_relations = {
            'search': "Refers to a resource that can be used to search through the link's context and related resources.",
            'create-form': 'The target IRI points to a resource where a submission form can be obtained.',
            'describedby': "Refers to a resource providing information about the link's context.",
            'edit': "Refers to a resource that can be used to edit the link's context.",
            'edit-form': 'The target IRI points to a resource where a submission form for editing associated resource can be obtained.',
            'first': 'An IRI that refers to the furthest preceding resource in a series of resources.',
            'help': 'Refers to context-sensitive help.',
            'index': 'Refers to an index.',
            'item': 'The target IRI points to a resource that is a member of the collection represented by the context IRI.',
            'last': 'An IRI that refers to the furthest following resource in a series of resources.',
            'latest-version': 'Points to a resource containing the latest (e.g., current) version of the context.',
            'next': "Indicates that the link's context is a part of a series, and that the next in the series is the link target. ",
            'original': 'The Target IRI points to an Original Resource.',
            'prev': "Indicates that the link's context is a part of a series, and that the previous in the series is the link target. ",
            'preview': "Refers to a resource that provides a preview of the link's context.",
            'previous': 'Refers to the previous resource in an ordered series of resources. Synonym for "prev".',
            'self': "Conveys an identifier for the link's context. ",
            'start': 'Refers to the first resource in a collection of resources.',
            'type': "Refers to a resource identifying the abstract semantic type of which the link's context is considered to be an instance.",
            'up': 'Refers to a parent document in a hierarchy of documents.',
            'icon': "Refers to an icon representing the link's context.",
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
            'next-free-ip': 'next IP configuration based on the given network object',
            'property-choices': 'determine valid values for a given syntax class',
            'user-photo': 'photo of the object',
            'license': 'information about UCS license',
            'license-request': 'Request a new UCS Core Edition license',
            'license-check': 'Check if the license limits are reached',
            'license-import': 'Import a new license in LDIF format',
            'service-specific-password': 'Generate a new service specific password',
            'error': 'Error',
            'warning': 'Warning',
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


class _OpenAPIBase:

    def get_openapi_schema(self, object_type=None):
        ldap_base = ucr['ldap/base'] if self.requires_authentication else "dc=example,dc=net"
        openapi_paths = {}  # defines all resources and methods they have
        openapi_tags = []  # defines the basic structure, a group of pathes builds a tag, the pathes must include a reference to the tag name
        global_parameters = [
            {'$ref': '#/components/parameters/user-agent'},
            {'$ref': '#/components/parameters/accept-language'},
            {'$ref': '#/components/parameters/if-none-match'},
            {'$ref': '#/components/parameters/if-modified-since'},
            {'$ref': '#/components/parameters/request-id'},
        ]
        _global_responses = {
            400: {'$ref': '#/components/responses/BadRequest'},
            401: {'$ref': '#/components/responses/Unauthorized'},
            403: {'$ref': '#/components/responses/Forbidden'},
            422: {'$ref': '#/components/responses/UnprocessableEntity'},
            500: {'$ref': '#/components/responses/ServerError'},
            503: {'$ref': '#/components/responses/ServiceUnavailable'},
            502: {'$ref': '#/components/responses/ServiceUnavailable'},
            504: {'$ref': '#/components/responses/ServiceUnavailable'},
        }
        _global_response_headers = {
            'Cache-Control': {'$ref': '#/components/headers/Cache-Control'},
            'Expires': {'$ref': '#/components/headers/Expires'},
            'Vary': {'$ref': '#/components/headers/Vary'},
            'Content-Language': {'$ref': '#/components/headers/Content-Language'},
            'Link': {'$ref': '#/components/headers/Link'},
            'X-Request-Id': {'$ref': '#/components/headers/X-Request-Id'},
        }

        def global_response_headers(responses={}):
            return dict(_global_response_headers, **{str(k): v for k, v in responses.items()})

        def global_responses(responses):
            return dict(_global_responses, **{str(k): v for k, v in responses.items()})

        def content_schema(schema_definition):
            return {
                'application/json': {'schema': schema_definition},
                'application/hal+json': {'schema': schema_definition},
                'text/html': {'schema': {'$ref': '#/components/schemas/html-response'}},
            }

        def content_schema_ref(schema_definition):
            return content_schema({'$ref': schema_definition})

        openapi_request_bodies = {}
        openapi_schemas = {
            "html-response": {
                "description": "**Experimental**: HTML response where developer can interactively navigate through objects. This will be replaced with a real frontend in the future.",
                "deprecated": True,
                "type": "string",
                        "format": "html",
                        "example": "<html/>",
                        "readOnly": True,
            },
            "dn": {
                "description": "The LDAP Distinguished Name (DN).",
                "type": "string",
                        "format": "dn",
                        "pattern": "^.+=.+$",
                        "minLength": 3,
                        "example": ldap_base,
                        "readOnly": True,
            },
            # "id": {
            #    "description": "The (not unique!) relative LDAP Distinguished Name (RDN).",
            #    "type": "string",
            #    "readOnly": True,
            # },
            "uuid": {
                "description": "The LDAP Entry-UUID.",
                "type": "string",
                        "format": "uuid",
                        "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                        "minLength": 36,
                        "maxLength": 36,
                        "readOnly": True,
            },
            "objectType": {
                "description": "The UDM Object-Type.",
                "type": "string",
                        "example": "users/user",
                        "readOnly": True,
                        "pattern": "^.+/.+$",
                        "minLength": 3,
            },
            "_links": {
                "description": "Hypertext Application Language (HAL) links.",
                "type": "object",
                        "properties": {
                            "self": {
                                "type": "array",
                                "minItems": 0,
                                "items": {
                                        "type": "object",
                                        "properties": {
                                                "href": {
                                                    "type": "string",
                                                    "description": "The URL.",
                                                },
                                        },
                                    "additionalProperties": True,
                                },
                            },
                        },
                "readOnly": True,
                "additionalProperties": True,
            },
            "_embedded": {
                "description": "Hypertext Application Language (HAL) embedded resources.",
                "type": "object",
                        "properties": {},
                        "readOnly": True,
                        "additionalProperties": True,
            },
            "position": {
                "description": "DN of LDAP node below which the object is located. Changing this causes a move of the object. When changing no other changes are applied.",
                "type": "string",
                        "format": "dn",
                        "example": f"cn=position,{ldap_base}",
            },
            "superordinate": {
                "description": "The superordinate DN of the object.",
                "type": "string",
                        "format": "dn",
                        "example": ldap_base,
            },
            'embedded-error': {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "_embedded": {
                        "type": "object",
                                "additionalProperties": True,
                                "properties": {
                                    "udm:error": {
                                        'description': 'Additional error information.',
                                        "type": "array",
                                                "minItems": 0,
                                                "items": {
                                                    "type": "object",
                                                            "additionalProperties": True,
                                                    "properties": {
                                                        'location': {'type': 'array', 'minItems': 1, 'items': {'type': 'string'}},
                                                        'message': {'type': 'string'},
                                                        'type': {'type': 'string'},
                                                    },
                                                },
                                    },
                                },
                    },
                    'code': {'type': 'integer', 'minimum': 400, 'maximum': 599, 'description': 'HTTP status code equivalent.'},
                    'message': {'type': 'string', 'description': 'A human readable error message.'},
                    'title': {'type': 'string', 'description': 'short title for the error.'},
                    'traceback': {'type': 'string', 'nullable': True, 'description': 'A stacktrace (if enabled and server error).'},
                },
            },
        }
        openapi_parameters = {
            "dn-path": {
                "description": "The (urlencoded) LDAP Distinguished Name (DN).",
                "in": "path",
                "name": "dn",
                        "required": True,
                        "schema": {
                            '$ref': '#/components/schemas/dn',
                        },
            },
            'template.get.query.position': {
            },
            'template.get.query.superordinate': {
            },
            'template.get.query.template': {
            },
            'objects.get.query.position': {
            },
            'objects.get.query.scope': {
            },
            'objects.get.query.filter': {
            },
            'objects.get.query.query': {
            },
            'objects.get.query.hidden': {
            },
            'objects.get.query.superordinate': {
            },
            'objects.get.query.properties': {
            },
            'objects.get.query.limit': {
            },
            'objects.get.query.page': {
            },
            'objects.get.query.dir': {
            },
            'objects.get.query.by': {
            },
            'object.delete.query.cleanup': {
            },
            'object.delete.query.recursive': {
            },
            'user-agent': {
                "in": "header",
                "name": "User-Agent",
                        "schema": {"type": "string"},
                        "description": "The user agent.",
                        "examples": {
                            "none": {"value": "", "summary": "none"},
                            "UCS version": {"value": "UCS 5.0-2-errata339", "summary": "UCS 5.0-2-errata339"},
                        },
            },
            'accept-language': {
                "in": "header",
                "name": "Accept-Language",
                        "schema": {"type": "string"},
                        "description": "The accepted response languages.",
                        "examples": {
                            "none": {"value": "", "summary": "Let server decide"},
                            "english": {"value": "en-US; q=1.0", "summary": "english"},
                            "german": {"value": "de-DE; q=1.0, en-US; q=0.9", "summary": "Prefer german"},
                        },
            },
            "if-match": {
                "in": "header",
                "name": "If-Match",
                        "schema": {"type": "string"},
                        "description": "Provide entity tag to make a conditional request to not overwrite any values in a race condition.",
                        "example": "",
            },
            "if-none-match": {
                "in": "header",
                "name": "If-None-Match",
                        "schema": {"type": "string", "format": "etag"},
                        "description": "Use request from cache by using the Etag entity tag if it matches.",
                        "example": "",
            },
            "if-unmodified-since": {
                "in": "header",
                "name": "If-Unmodified-Since",
                        "schema": {"type": "string", "format": "last-modified-date"},
                        "description": "Provide last modified time to make a conditional request to not overwrite any values in a race condition.",
                        # "example": "Wed, 21 Oct 2015 07:28:00 GMT",
            },
            "if-modified-since": {
                "in": "header",
                "name": "If-Modified-Since",
                        "schema": {"type": "string"},
                        "description": "Use request from cache by using the Last-Modified date if it matches.",
                        "example": "",
            },
            'request-id': {
                "in": "header",
                "name": "X-Request-Id",
                        "schema": {"type": "string", "format": "uuid"},
                        "description": "A request-ID used for logging and tracing.",
                        "examples": {
                            'unset': {'value': ''},
                            'uuid4': {'value': "218d9124-c0dc-415e-8417-a0fa197ee099"},
                        },
            },
        }
        openapi_responses = {
            'objects.post.response.created': {
                '$ref': '#/components/responses/ObjectCreated',
            },
            'object.get.response.notfound': {
                '$ref': '#/components/responses/ObjectNotFound',
            },
            'object.delete.response.nocontent': {
                '$ref': '#/components/responses/ObjectDeleted',
            },
            'object.delete.response.notfound': {
                '$ref': '#/components/responses/ObjectNotFound',
            },
            'object.put.response.created': {
                '$ref': '#/components/responses/PUTObjectCreated',
            },
            'object.put.response.accepted': {
                '$ref': '#/components/responses/MoveStarted',
            },
            'object.put.response.nocontent': {
                '$ref': '#/components/responses/SuccessNoDataRedirect',
            },
            'object.put.response.notfound': {
                '$ref': '#/components/responses/ObjectNotFound',
            },
            'object.patch.response.nocontent': {
                '$ref': '#/components/responses/SuccessNoDataRedirect',
            },
            'object.patch.response.notfound': {
                '$ref': '#/components/responses/ObjectNotFound',
            },
            "ObjectCreated": {  # 201
                "description": "Object created",
                "content": content_schema({
                    "type": "object",
                                "properties": {
                                    "dn": {'$ref': '#/components/schemas/dn'},
                                    "uuid": {'$ref': '#/components/schemas/uuid'},
                                },
                }),
                "headers": global_response_headers({
                    'Etag': {'$ref': '#/components/headers/Etag'},
                    'Last-Modified': {'$ref': '#/components/headers/Last-Modified'},
                }),
            },
            "PUTObjectCreated": {  # 201
                "description": "Created: The object did not exist and has been created. Deprecated: a move operation started, expect 202 in the future!",
                "content": content_schema({
                    "type": "object",
                            "properties": {
                                "dn": {'$ref': '#/components/schemas/dn'},
                                "uuid": {'$ref': '#/components/schemas/uuid'},
                            },
                }),
                "headers": global_response_headers({
                    'Etag': {'$ref': '#/components/headers/Etag'},
                    'Last-Modified': {'$ref': '#/components/headers/Last-Modified'},
                }),
            },
            'MoveStarted': {  # 202 (actually still 201)
                "description": "Accepted: asynchronous move or rename operation started.",
                'headers': global_response_headers({
                    'Location': {'$ref': '#/components/headers/Location'},
                }),
                "content": content_schema({
                    "type": "object",
                    "additionalProperties": True,
                }),
            },
            'SuccessNoDataRedirect': {  # 204
                "description": "Success. No response data. A link to the modified resource in the `Location` header.",
                'headers': global_response_headers({
                    'Location': {'$ref': '#/components/headers/Location'},
                    'Etag': {'$ref': '#/components/headers/Etag'},
                    'Last-Modified': {'$ref': '#/components/headers/Last-Modified'},
                }),
            },
            'ObjectDeleted': {  # 204
                "description": "Object deleted",
                "headers": global_response_headers(),
            },
            'MoveProgress': {  # 301
                'description': 'Gives information about the progress of a move operation.',
                'headers': global_response_headers({
                    'Retry-After': {'$ref': '#/components/headers/Retry-After'},
                    'Location': {'$ref': '#/components/headers/Location'},
                }),
                "content": content_schema({
                    "type": "object",
                    "additionalProperties": True,
                }),
            },
            'MoveSuccess': {  # 303
                'description': 'Redirects to the result of the move operation, i.e. the new object.',
                'headers': global_response_headers({'Location': {'$ref': '#/components/headers/Location'}}),
                "content": content_schema({
                    "type": "object",
                            "additionalProperties": True,
                }),
            },
            "BadRequest": {  # 400
                "description": 'Bad request syntax.',
                'headers': global_response_headers({}),
                "content": content_schema({
                    "type": "object",
                            "additionalProperties": True,
                }),
            },
            "Forbidden": {  # 403, e.g. unsupported operation, or GET users/self/$wrong_dn
                "description": 'Forbidden (e.g. unsupported operation)',
                'headers': global_response_headers({}),
                "content": content_schema({
                            "type": "object",
                            "additionalProperties": True,
                }),
            },
            "ObjectNotFound": {  # 404
                "description": "Object not found.",
                'headers': global_response_headers({}),
                "content": content_schema({
                    "type": "object",
                            "additionalProperties": True,
                }),
            },
            "ObjectGone": {  # 410
                "description": "Object has recently been removed.",
                'headers': global_response_headers({}),
                "content": content_schema({
                    "type": "object",
                            "additionalProperties": True,
                }),
            },
            "Unauthorized": {  # 401
                'description': 'Unauthorized. No Authorization provided or wrong credentials.',
                'headers': global_response_headers({}),
                "content": content_schema({
                    "type": "object",
                            "additionalProperties": True,
                }),
            },
            "UnprocessableEntity": {  # 422
                'description': 'Validation of input parameters failed.',
                'headers': global_response_headers({}),
                "content": content_schema_ref('#/components/schemas/embedded-error'),
            },
            "ServerError": {  # 500
                'description': 'Internal server errror.',
                'headers': global_response_headers({}),
                "content": content_schema_ref('#/components/schemas/embedded-error'),
            },
            "ServiceUnavailable": {  # 503 (+502 +504 +599)
                'description': '(LDAP) Server not available.',
                'headers': global_response_headers({
                    'Retry-After': {'$ref': '#/components/headers/Retry-After'},
                }),
                "content": content_schema({
                    "type": "object",
                    "additionalProperties": True,
                }),
            },
        }
        openapi_headers = {
            'Cache-Control': {"schema": {"type": "string"}, "description": "Controling directives for caching."},
            'Expires': {"schema": {"type": "string"}, "description": "An expiration time, when the response is stale and should not be used from cache anymore."},
            'Vary': {"schema": {"type": "string"}, "description": "The response headers which need to be considered when caching the response."},
            'Etag': {"schema": {"type": "string"}, "description": "An entity tag of the resource, which should be used for conditional PUT requests."},
            'Last-Modified': {"schema": {"type": "string"}, "description": "The time the resource was modified the last time, which should be used for conditional PUT requests."},
            'Allow': {"schema": {"type": "string"}, "description": "The allowed HTTP request methods for this resource."},
            'Content-Language': {"schema": {"type": "string"}, "description": "The language of the response"},
            'Retry-After': {"schema": {"type": "string"}, "description": "The time which should be waited before requesting the resource from the Location header."},
            'Accept-Patch': {"schema": {"type": "string"}, "description": "The accepted Content-Types for a PATCH request."},
            'Location': {"schema": {"type": "string"}, "description": "The location which should be followed."},
            'Link': {"schema": {"type": "string"}, "description": "A hypermedia link."},
            'X-Request-Id': {"schema": {"type": "string", "format": "uuid"}, "description": "The response of the request-ID used for logging and tracing."},
        }

        def _openapi_quote(string):
            return string.replace('~', '~0').replace('/', '~1')

        classes = {'object': Object, 'objects': Objects, 'template': ObjectAdd}
        for name, klass in classes.items():
            for method in ('get', 'post', 'put', 'delete'):
                func = getattr(klass, method, None)
                if not hasattr(func, 'params'):
                    continue
                for pname, param in func.params.get('query', {}).items():
                    key = '%s.%s.query.%s' % (name, method, param.alias or pname)
                    if key in openapi_parameters:
                        openapi_parameters[key].update({'in': 'query', 'name': param.alias or pname})
                        openapi_parameters[key].update(_param_to_openapi(param))

        def docstring(key, method, module):
            obj = getattr(classes[key], method)
            return '\n'.join(x.strip() for x in (obj.__doc__ or '').split('\n')).format(module=module)

        for name, _mod in sorted(udm_modules.modules.items()):
            if object_type and name != object_type:
                continue

            module = UDM_Module(name, ldap_connection=self.ldap_connection, ldap_position=self.ldap_position)
            tag = name
            model_name = name.replace('/', '-')  # for better look in swaggerUI, as they have a bug with showing the escaped variant
            schema_definition = f"#/components/schemas/{_openapi_quote(model_name)}"
            tag_description = {
                'description': f'{module.title} objects.',
                'name': name,
            }
            if module.help_text and module.help_link:
                tag_description.update({
                    'externalDocs': {
                        'description': module.help_text,
                        'url': module.help_link,
                    },
                })
            openapi_tags.append(tag_description)
            template_path = f'/{name}/add'
            objects_path = f'/{name}/'
            object_path = f'/{name}/{{dn}}'

            openapi_paths[objects_path] = {}
            openapi_paths[template_path] = {}
            openapi_paths[object_path] = {
                "parameters": [{"$ref": '#/components/parameters/dn-path'}],
            }

            openapi_request_bodies[model_name] = {
                'content': {
                    'application/json': {'schema': {'$ref': schema_definition}},  # + _openapi_quote('.request')}}
                },
                'required': True,
            }
            openapi_request_bodies[model_name + '.patch'] = {
                'content': {
                    'application/json': {'schema': {'$ref': schema_definition}},  # + _openapi_quote('.patch')}}
                },
                'required': True,
            }
            schema_request_body = f"#/components/requestBodies/{_openapi_quote(model_name)}"
            if 'search' in module.operations:
                _search_links = {
                    "search": {
                        "description": "Search for objects of this object type.",
                        "operationId": f"udm:{name}/object/search",
                    },
                    "create-form": {
                        "description": "Get a template for creating an object.",
                        "operationId": f"udm:{name}/object/template",
                    },
                }
                if 'add' not in module.operations:
                    _search_links.pop('create-form')
                pagination_parameters = []
                if not module.virtual:
                    pagination_parameters = [
                        # currently not supported by all modules:
                        {'$ref': '#/components/parameters/objects.get.query.limit'},
                        {'$ref': '#/components/parameters/objects.get.query.page'},
                        {'$ref': '#/components/parameters/objects.get.query.dir'},
                        {'$ref': '#/components/parameters/objects.get.query.by'},
                    ]

                openapi_paths[objects_path]['get'] = {
                    "summary": docstring('objects', 'get', module),
                    "description": "Information about the object type and links to search for objects. The found objects are either referenced as HAL links or embedded via HAL embedded resources.",
                    "operationId": f"udm:{name}/object/search",
                    "parameters": [
                        {'$ref': '#/components/parameters/objects.get.query.filter'},
                        {'$ref': '#/components/parameters/objects.get.query.position'},
                        {'$ref': '#/components/parameters/objects.get.query.scope'},
                        {'$ref': '#/components/parameters/objects.get.query.query'},
                        {'$ref': '#/components/parameters/objects.get.query.hidden'},
                        {'$ref': '#/components/parameters/objects.get.query.properties'},
                    ] + pagination_parameters + global_parameters,
                    "responses": global_responses({
                        200: {
                            '$ref': '#/components/responses/objects.%s.get.response.success' % (_openapi_quote(model_name),),
                        },
                    }),
                    "tags": [tag],
                }
                openapi_responses['objects.%s.get.response.success' % (model_name,)] = {
                    "description": "Successfull search (if query parameters were given) or a object type overview.",
                    "content": content_schema_ref(f"#/components/schemas/{_openapi_quote(model_name)}.list"),
                    "headers": global_response_headers(),
                    "links": _search_links,
                }
                if superordinate_names(module):
                    openapi_paths[objects_path]['get']['parameters'].append({'$ref': '#/components/parameters/objects.get.query.superordinate'})

            if 'add' in module.operations:
                openapi_paths[template_path]['get'] = {
                    "operationId": f"udm:{name}/object/template",
                    "summary": docstring('template', 'get', module),
                    "parameters": [
                        {'$ref': '#/components/parameters/template.get.query.position'},
                        {'$ref': '#/components/parameters/template.get.query.superordinate'},
                        {'$ref': '#/components/parameters/template.get.query.template'},
                    ] + global_parameters,
                    "responses": global_responses({
                        200: {
                            '$ref': '#/components/responses/template.%s.get.response.success' % (_openapi_quote(model_name),),
                        },
                    }),
                    "tags": [tag],
                }
                openapi_responses['template.%s.get.response.success' % (model_name,)] = {
                    "description": f"Successfully received a template suitable for creation of a new {module.object_name}.",
                    "content": content_schema_ref(f"#/components/schemas/{_openapi_quote(model_name)}"),
                    "headers": global_response_headers(),
                }
                openapi_paths[objects_path]['post'] = {
                    "operationId": f"udm:{name}/object/create",
                    "summary": docstring('objects', 'post', module),
                    "requestBody": {
                        "$ref": schema_request_body,
                    },
                    "parameters": [] + global_parameters,
                    "responses": global_responses({
                        201: {
                            '$ref': '#/components/responses/objects.post.response.created',
                        },
                    }),
                    "tags": [tag],
                }
            openapi_paths[object_path]["get"] = {
                "operationId": f"udm:{name}/object",
                "summary": docstring('object', 'get', module),
                "parameters": [] + global_parameters,
                "responses": global_responses({
                    "200": {
                        '$ref': '#/components/responses/object.%s.get.response.success' % (_openapi_quote(model_name),),
                    },
                    "404": {
                        '$ref': '#/components/responses/object.get.response.notfound',
                    },
                }),
                "tags": [tag],
            }
            openapi_responses['object.%s.get.response.success' % (model_name,)] = {
                "description": "Success",
                "content": content_schema_ref(f"#/components/schemas/{_openapi_quote(model_name)}"),
                "headers": global_response_headers({
                    'Etag': {'$ref': '#/components/headers/Etag'},
                    'Last-Modified': {'$ref': '#/components/headers/Last-Modified'},
                    # Caching
                }),
            }
            if 'remove' in module.operations:
                openapi_paths[object_path]["delete"] = {
                    "operationId": f"udm:{name}/object/remove",
                    "summary": docstring('object', 'delete', module),
                    "parameters": [
                        {'$ref': '#/components/parameters/object.delete.query.cleanup'},
                        {'$ref': '#/components/parameters/object.delete.query.recursive'},
                        {'$ref': '#/components/parameters/if-match'},
                        {'$ref': '#/components/parameters/if-unmodified-since'},
                    ] + global_parameters,
                    "responses": global_responses({
                        "204": {
                            '$ref': '#/components/responses/object.delete.response.nocontent',
                        },
                        "404": {
                            '$ref': '#/components/responses/object.delete.response.notfound',
                        },
                    }),
                    "tags": [tag],
                }
            if set(module.operations) & {'edit', 'move', 'move_subtree'}:
                openapi_paths[object_path]["put"] = {
                    "operationId": f"udm:{name}/object/modify",
                    "summary": docstring('object', 'put', module),
                    "requestBody": {
                        "$ref": schema_request_body,
                    },
                    "parameters": [
                        {'$ref': '#/components/parameters/if-match'},
                        {'$ref': '#/components/parameters/if-unmodified-since'},
                    ] + global_parameters,
                    "callbacks": {
                        'move-progress': {
                            '$ref': '#/components/callbacks/moveProgress',
                        },
                    },
                    "responses": global_responses({
                        "201": {
                            '$ref': '#/components/responses/object.put.response.created',
                        },
                        "202": {
                            '$ref': '#/components/responses/object.put.response.accepted',
                        },
                        "204": {
                            '$ref': '#/components/responses/object.put.response.nocontent',
                        },
                        "404": {
                            '$ref': '#/components/responses/object.put.response.notfound',
                        },
                    }),
                    "tags": [tag],
                }
                openapi_paths[object_path]["patch"] = {
                    "operationId": f'udm:{name}/object/update',
                    "summary": docstring('object', 'patch', module),
                    "requestBody": {
                        "$ref": schema_request_body + '.patch',
                    },
                    "parameters": [
                        {'$ref': '#/components/parameters/if-match'},
                        {'$ref': '#/components/parameters/if-unmodified-since'},
                    ] + global_parameters,
                    "responses": global_responses({
                        "204": {
                            '$ref': '#/components/responses/object.patch.response.nocontent',
                        },
                        "404": {
                            '$ref': '#/components/responses/object.patch.response.notfound',
                        },
                    }),
                    "tags": [tag],
                }

            properties_schema = {}
            for prop in module.properties(None):
                name = prop['id']
                if name.startswith('$'):
                    continue
                property = module.get_property(name)
                codec = udm_types.TypeHint.detect(property, name)
                properties_schema[name] = codec.get_openapi_definition()

            request_model_patch = {
                "dn": {
                    "$ref": '#/components/schemas/dn',
                },
                "properties": {
                    # must not be a reference as it breaks udm-rest-api-client
                    # which relies on implementation details of openapitools/openapi-generator-cli:v5.0.0!
                    'type': 'object',
                            "description": "Object type specific `UDM` properties.",
                            'properties': properties_schema,
                            "additionalProperties": True,  # not yet installed extended attributes
                },
                "options": {
                    "$ref": f'#/components/schemas/{_openapi_quote(model_name + ".options")}',
                },
                "policies": {
                    "$ref": f'#/components/schemas/{_openapi_quote(model_name + ".policies")}',
                },
            }
            if superordinate_names(module):
                request_model_patch['superordinate'] = {
                    "$ref": '#/components/schemas/superordinate',
                }
            openapi_schemas[f'{model_name}.request-patch'] = {
                "type": "object",
                "properties": request_model_patch,
            }
            openapi_schemas[f'{model_name}.request'] = {
                "allOf": [{
                    '$ref': f'#/components/schemas/{_openapi_quote(model_name + ".request-patch")}',
                }, {
                    'type': 'object',
                    'properties': {
                        "position": {
                            "$ref": '#/components/schemas/position',
                        },
                    },
                }],
            }
            openapi_schemas[f'{model_name}.response-mixin'] = {
                "type": "object",
                "properties": {
                    "_links": {
                        "$ref": '#/components/schemas/_links',
                    },
                    "_embedded": {
                        "$ref": '#/components/schemas/_embedded',
                    },
                    "uuid": {
                        "$ref": '#/components/schemas/uuid',
                    },
                    "objectType": {
                        "$ref": '#/components/schemas/objectType',
                    },
                    # "id": {"$ref": '#/components/schemas/id',},
                    "uri": {
                        "$ref": f'#/components/schemas/{_openapi_quote(model_name + ".uri")}',
                    },
                },
            }
            # we can't deploy this as it breaks older udm-rest-api-client
            # openapi_schemas[f"{model_name}.properties"] = {
            #    "description": "Object type specific `UDM` properties.",
            #    "type": "object",
            #    "properties": {},
            #    "additionalProperties": True,  # not yet installed extended attributes
            # }
            openapi_schemas[f"{model_name}.uri"] = {
                "type": "string",
                "format": "uri",
                "example": self.abspath(module.name) + '/%s={value},%s' % (module.mapping.mapName(module.identifies) or 'cn', module.get_default_container() if self.requires_authentication else ldap_base),
            }
            openapi_schemas[f"{model_name}.options"] = {
                "description": "Object type specific `UDM` options.",
                "type": "object",
                "properties": {oname: {
                        "description": opt.short_description,
                    "type": "boolean",
                            "default": bool(opt.default),
                            "example": bool(opt.default),
                } for oname, opt in module.options.items()},
                "additionalProperties": True,  # not yet installed extended options
            }
            openapi_schemas[f"{model_name}.policies"] = {
                "description": "Policies which apply for this object.",
                "type": "object",
                "properties": {pol['objectType']: {
                        "type": "array",
                    "minItems": 0,
                    "maxItems": 1,
                    "items": {
                                "type": "string",
                                "format": "dn",
                                "example": ldap_base,
                    },
                    "description": pol['label'],
                } for pol in module.policies},
                "additionalProperties": True,  # possitibility for future aditions
            }
            openapi_schemas[model_name] = {
                'allOf': [
                    {
                        '$ref': f'#/components/schemas/{_openapi_quote(model_name)}.request',
                    }, {
                        '$ref': f'#/components/schemas/{_openapi_quote(model_name)}.response-mixin',
                    },
                ],
            }
            openapi_schemas[f'{model_name}.list'] = {
                "type": "object",
                "properties": {
                        "_embedded": {
                            "type": "object",
                            "properties": {
                                    "udm:object": {
                                        "type": "array",
                                        "minItems": 0,
                                        "items": {
                                                "$ref": schema_definition,
                                        },
                                    },
                            },
                        },
                },
            }

        url = list(urlparse(self.abspath('')))
        fqdn = '%(hostname)s.%(domainname)s' % ucr
        urls = [
            urlunparse([_scheme, _host] + url[2:])
            for _host in (fqdn, url[1])
            for _scheme in ('https', 'http')
        ]
        specs = {
            'openapi': '3.0.3',
            'paths': openapi_paths,
            'info': {
                'description': 'Schema definition for the objects in the Univention Directory Manager REST interface.',
                'title': 'Univention Directory Manager REST interface',
                'version': '1.0.2',
            },
            'security': [{
                "basic": [],
            }],
            'tags': openapi_tags,
            'components': {
                'schemas': openapi_schemas,  # Reusable data models
                'requestBodies': openapi_request_bodies,
                'securitySchemes': {
                    'basic': {
                        'scheme': 'basic',
                        'type': 'http',
                    },
                },
                'parameters': openapi_parameters,  # Reusable path, query, header and cookie parameters
                'responses': openapi_responses,
                'headers': openapi_headers,
                'examples': {},
                'links': {},
                'callbacks': {
                    'moveProgress': {
                        '{$response.header.Location}': {
                            'get': {
                                'requestBody': {
                                    "content": {'application/json': {'schema': {'type': 'object', 'additionalProperties': True}}},
                                },
                                'responses': {
                                    '301': {'$ref': '#/components/responses/MoveProgress'},
                                    '303': {'$ref': '#/components/responses/MoveSuccess'},
                                },
                            },
                        },
                    },
                },
            },
            'servers': [{'url': _url.rstrip('/')} for _url in urls],
        }
        return specs


class OpenAPI(_OpenAPIBase, Resource):

    requires_authentication = ucr.is_true('directory/manager/rest/require-auth', True)

    def prepare(self):
        super().prepare()
        self.request.content_negotiation_lang = 'json'
        self.ldap_connection, self.ldap_position = get_machine_ldap_read_connection()

    def get(self, object_type=None):
        specs = self.get_openapi_schema(object_type)
        self.content_negotiation(specs)

    def get_json(self, response):
        response = super().get_json(response)
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

    def navigation(self):
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
                        self.add_link(response, 'udm:tab-switch', href=f'#{elem.get("id")}', title=elem.find('./h1').text)
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
                infos[key]['value'] = policy_obj.polinfo[key]
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
    if isinstance(dn, str):
        dn = dn.encode('utf-8')
    # duplicated slashes in URI path's can be normalized to one slash. Therefore we need to escape the slashes.
    return quote(dn.replace(b'//', b',/=/,'))  # .replace('/', quote('/', safe=''))


def unquote_dn(dn):
    # tornado already decoded it (UTF-8)
    return dn.replace(',/=/,', '//')


def last_modified(date):
    return '%s, %02d %s %04d %02d:%02d:%02d GMT' % (
        ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')[date.tm_wday],
        date.tm_mday,
        ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')[date.tm_mon - 1],
        date.tm_year, date.tm_hour, date.tm_min, date.tm_sec,
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


def _get_post_read_entry_uuid(response):
    for c in response.get('ctrls', []):
        if c.controlType == PostReadControl.controlType:
            uuid = c.entry['entryUUID'][0]
            if isinstance(uuid, bytes):  # starting with python-ldap 4.0
                uuid = uuid.decode('ASCII')
            return uuid


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
