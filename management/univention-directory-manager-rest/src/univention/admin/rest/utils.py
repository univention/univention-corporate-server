#!/usr/bin/python3
#
# Univention Management Console
#  Univention Directory Manager Module
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

import re
from urllib.parse import quote

import ldap.dn
from ldap.controls.readentry import PostReadControl
from tornado.web import HTTPError

import univention.admin.types as udm_types


RE_UUID = re.compile('[^A-Fa-f0-9-]')


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
