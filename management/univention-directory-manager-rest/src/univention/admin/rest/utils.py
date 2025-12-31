#!/usr/bin/python3
#
# Univention Management Console
#  Univention Directory Manager Module
#
# SPDX-FileCopyrightText: 2017-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import logging
import re
from urllib.parse import quote

import ldap.dn
from ldap.controls.readentry import PostReadControl
from tornado.web import HTTPError

import univention.admin.types as udm_types
from univention.config_registry import ucr
from univention.management.console.log import add_filter


RE_UUID = re.compile('[^A-Fa-f0-9-]')


def init_request_context_logging(request_context):
    structured = ucr.is_true('directory/manager/rest/debug/structured-logging', True)
    if not structured and not ucr.is_true('directory/manager/rest/debug/prefix-with-request-id', True):
        return

    add_filter(RequestContextFilter(request_context, structured))


class RequestContextFilter(logging.Filter):
    def __init__(self, request_context, structured_logging=False):
        self.request_context = request_context
        self.structured_logging = structured_logging

    def filter(self, record):
        try:
            request_context = self.request_context.get()
        except LookupError:
            request_context = {}
        record.request_id = request_context.get('request_id', '-')
        if not self.structured_logging:
            record.prefix = f"[{(record.request_id or '')[:10]}] "  # backwards compatibility
        if dn := request_context.get('requester_dn'):
            record.requester_dn = dn
        if ip := request_context.get('requester_ip'):
            record.requester_ip = ip
        if hostname := request_context.get('requester_hostname'):
            record.requester_hostname = hostname
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
