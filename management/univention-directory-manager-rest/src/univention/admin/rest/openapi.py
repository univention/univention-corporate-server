#!/usr/bin/python3
#
# Univention Management Console
#  Univention Directory Manager Module
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2017-2024 Univention GmbH
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

import re
from urllib.parse import urlparse, urlunparse

import univention.admin.modules as udm_modules
import univention.admin.types as udm_types
from univention.admin.rest.ldap_connection import get_machine_ldap_read_connection
from univention.admin.rest.sanitizer import (
    BooleanSanitizer, BoolSanitizer, ChoicesSanitizer, DictSanitizer, DNSanitizer, IntegerSanitizer, ListSanitizer,
    Param, StringSanitizer,
)
from univention.admin.rest.utils import NotFound, superordinate_names
from univention.config_registry import ucr
from univention.lib.i18n import Translation
from univention.management.console.modules.udm.udm_ldap import UDM_Module


_ = Translation('univention-directory-manager-rest').translate


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
        # type_ = 'string'
        # definition['examples'] = {choice: {'value': choice, 'summary': choice} for choice in san.choices}
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


class RelationsBase:

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
                "description": "Created: The object did not exist and has been created.",
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
            'MoveStarted': {  # 202
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

        from univention.admin.rest.module import Object, ObjectAdd, Objects
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
                # "bearer": [],  # FIXME: /univention/components/python-udm-rest-api-client#25
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
                    # 'bearer': {  # FIXME: /univention/components/python-udm-rest-api-client#25
                    #     'scheme': 'bearer',
                    #     'type': 'http',
                    # },
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


class OpenAPIBase(_OpenAPIBase):

    requires_authentication = ucr.is_true('directory/manager/rest/require-auth', True)

    def check_acceptable(self):
        return 'json'

    def prepare(self):
        super().prepare()
        self.ldap_connection, self.ldap_position = get_machine_ldap_read_connection()

    def get(self, object_type=None):
        specs = self.get_openapi_schema(object_type)
        self.content_negotiation(specs)

    def get_json(self, response):
        response = super().get_json(response)
        response.pop('_links', None)
        response.pop('_embedded', None)
        return response
