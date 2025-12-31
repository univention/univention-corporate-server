#
# Univention Directory Reports
#  analyse a tokenized list and perform the tasks
#
# SPDX-FileCopyrightText: 2007-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import copy
import datetime
import fnmatch
import re

import univention.admin.localization
import univention.admin.objects as ua_objects
from univention.directory.reports import admin
from univention.directory.reports.tokens import (
    AttributeToken, DateToken, PolicyToken, QueryToken, ResolveToken, TextToken,
)


translation = univention.admin.localization.translation('univention-directory-reports')
_ = translation.translate


class Interpreter:

    def __init__(self, base_object, tokens):
        self._base_object = base_object
        self._tokens = tokens

    def run(self, tokens=[], base_objects=[]):
        if not tokens:
            tokens = self._tokens
        if not base_objects:
            base_objects = [self._base_object]
        if not isinstance(base_objects, list | tuple):
            base_objects = [base_objects]
        for token in tokens:
            if isinstance(token, QueryToken | ResolveToken):
                if isinstance(token, QueryToken):
                    self.query(token, base_objects[0])
                else:
                    self.resolve(token, base_objects[0])
                if not token.objects or not len(token):
                    token.clear()
                    if 'alternative' in token.attrs:
                        token.insert(0, TextToken(token.attrs['alternative']))
                    continue
                if len(token.objects) > 1:
                    temp = copy.deepcopy(list(token))
                    self.run(list(token), token.objects[0])
                    for obj in token.objects[1:]:
                        base_tokens = copy.deepcopy(temp)
                        self.run(base_tokens, obj)
                        token.extend(base_tokens)
                else:
                    self.run(token, token.objects)
                if 'separator' in token.attrs:
                    cp = copy.deepcopy(list(token))
                    while len(token):
                        token.pop()
                    for item in cp:
                        token.append(item)
                        token.append(TextToken(token.attrs['separator']))
                    if len(token):
                        token.pop()
                if 'header' in token.attrs:
                    token.insert(0, TextToken(token.attrs['header']))
                if 'footer' in token.attrs:
                    token.append(TextToken(token.attrs['footer']))
            elif isinstance(token, AttributeToken):
                self.attribute(token, base_objects[0])
                if token.value:
                    if 'append' in token.attrs:
                        token.value += token.attrs['append']
                    if 'prepend' in token.attrs:
                        token.value = token.attrs['prepend'] + token.value
            elif isinstance(token, PolicyToken):
                self.policy(token, base_objects[0])
            elif isinstance(token, DateToken):
                token.value = datetime.datetime.today().strftime(token.attrs.get('format', "%A %B %d, %Y"))

    def resolve(self, token, base):
        if 'module' in token.attrs:
            attr = token.attrs.get('dn-attribute', None)
            if attr and base.has_property(attr) and base[attr]:
                values = base[attr]
                if not isinstance(values, list | tuple):
                    values = [values]
                for value in values:
                    new_base = admin.get_object(token.attrs['module'], value)
                    if new_base:
                        token.objects.append(new_base)

    def query(self, token, base):
        if 'module' in token.attrs:
            attr = token.attrs.get('start', None)
            if attr and base.has_property(attr) and base[attr]:
                admin.get_object(token.attrs['module'], base[attr][0])
                if not isinstance(base[attr], list | tuple):
                    base[attr] = [base[attr]]
                filter = token.attrs.get('pattern', None)
                if filter:
                    filter = filter.split('=', 1)
                regex = token.attrs.get('regex', None)
                if regex:
                    regex = regex.split('=', 1)
                    regex[1] = re.compile(regex[1])
                objects = self._query_recursive(base[attr], token.attrs['next'], token.attrs['module'], filter, regex)
                token.objects.extend(objects)

    def _query_recursive(self, objects, attr, module, filter=None, regex=None):
        _objs = []
        for dn in objects:
            obj = admin.get_object(module, dn)
            if not obj:
                continue
            if not filter and not regex:
                _objs.append(obj)
            elif filter and obj.has_property(filter[0]) and obj[filter[0]] and fnmatch.fnmatch(obj[filter[0]], filter[1]):
                _objs.append(obj)
            elif regex and obj.has_property(regex[0]) and obj[regex[0]] and regex[1].match(obj[regex[0]]):
                _objs.append(obj)
            if not obj.has_property(attr):
                continue

            _objs.extend(self._query_recursive(obj[attr], attr, module, filter, regex))

        return _objs

    def policy(self, token, base):
        if 'module' in token.attrs and ('inherited' in token.attrs or 'direct' in token.attrs):
            policy = ua_objects.getPolicyReference(base, token.attrs['module'])
            # need to call str() directly in order to force a correct translation
            token.value = str(_('No'))
            if 'direct' in token.attrs and policy:
                token.value = str(_('Yes'))
            elif 'inherited' in token.attrs and not policy:
                token.value = str(_('Yes'))

    def attribute(self, token, base):
        if 'name' in token.attrs:
            if token.attrs['name'] in base.info:
                value = base.info[token.attrs['name']]
                if isinstance(value, list | tuple):
                    if not value or (isinstance(value, str) and value.lower() == 'none'):
                        token.value = token.attrs.get('default', '')
                    else:
                        inner_separator = token.attrs.get('inner-separator', ' ')
                        if base.descriptions[token.attrs['name']].multivalue:
                            sep = token.attrs.get('separator', ', ')
                            if all(isinstance(element, list | tuple) for element in value):
                                if all(isinstance(v, str) for element in value for v in element):
                                    value = [inner_separator.join(element) for element in value]
                                else:  # safety fallback
                                    value = [inner_separator.join([str(v) for v in element]) for element in value]
                            elif not all(isinstance(element, str) for element in value):
                                value = [str(element) for element in value]
                            token.value = sep.join(value)
                        else:
                            if all(isinstance(v, str) for v in value):
                                token.value = inner_separator.join(value)
                            else:  # safety fallback
                                token.value = inner_separator.join([str(v) for v in value])
                else:
                    token.value = value
            elif 'default' in token.attrs:
                token.value = token.attrs['default']
            if token.value is None or token.value == '':
                token.value = ''
                if 'default' in token.attrs:
                    token.value = token.attrs['default']
