#!/usr/bin/python3
#
# Univention Management Console
#  Univention Directory Manager Module
#
# SPDX-FileCopyrightText: 2017-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import logging
import re
from urllib.parse import quote

import ldap.dn
from ldap.controls.readentry import PostReadControl
from tornado.web import HTTPError

import univention.admin.types as udm_types
from univention.config_registry import ucr


RE_UUID = re.compile('[^A-Fa-f0-9-]')


def init_request_context_logging(request_id_context):
    if not ucr.is_true('directory/manager/rest/debug/prefix-with-request-id', True):
        return

    context_id_filter = RequestContextFilter(request_id_context)
    for comp in ('MAIN', 'ADMIN', 'LDAP', 'MODULE', 'tornado.access', 'tornado.application', 'tornado.general'):
        for handler in logging.getLogger(comp).handlers:
            handler.addFilter(context_id_filter)


class RequestContextFilter(logging.Filter):
    def __init__(self, request_id_context):
        self.request_id_context = request_id_context

    def filter(self, record):
        try:
            record.prefix = self.request_id_context.get()[:10]
        except LookupError:
            record.prefix = 'no requestID '  # no context exists yet
        return True


def parse_content_type(content_type):
    return content_type.partition(';')[0].strip().lower()


class NotFound(HTTPError):

    def __init__(self, object_type=None, dn=None):
        super().__init__(404, None, '%r %r' % (object_type, dn or ''))  # FIXME: create error message


def superordinate_names(module):
    superordinates = module.superordinate_names
    if set(superordinates) == {'settings/cn'}:
        return []
    return superordinates


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
