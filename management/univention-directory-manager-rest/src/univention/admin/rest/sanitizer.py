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

# TODO: use pydantic

import copy
import functools
import inspect

import ldap.dn

import univention.admin.syntax as udm_syntax
import univention.admin.types as udm_types
import univention.admin.uexceptions as udm_errors
from univention.admin.rest.utils import parse_content_type
from univention.config_registry import ucr
from univention.lib.i18n import Translation
from univention.management.console.error import UnprocessableEntity
from univention.management.console.modules.sanitizers import (  # noqa: F401
    BooleanSanitizer, ChoicesSanitizer, DictSanitizer, DNSanitizer, EmailSanitizer, IntegerSanitizer,
    LDAPSearchSanitizer, ListSanitizer, MultiValidationError, Sanitizer, SearchSanitizer, StringSanitizer,
    ValidationError,
)


_ = Translation('univention-directory-manager-rest').translate


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
                    # value[key] = QueryStringSanitizer(sanitizer.sanitizers).sanitize(key, {key: value[key]})

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
    base_internal = ldap.dn.str2dn('cn=internal'.lower())
    base_internal_len = len(base_internal)

    def _sanitize(self, value, name, further_arguments):
        value = super()._sanitize(value, name, further_arguments)
        if value:
            if ldap.dn.str2dn(value.lower())[-self.baselen:] != self.base and \
               ldap.dn.str2dn(value.lower())[-self.base_internal_len:] != self.base_internal:
                self.raise_validation_error(_('The ldap base is invalid. Use %(details)s.'), details=ldap.dn.dn2str(self.base))
        return value


class SanitizerBase:

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
