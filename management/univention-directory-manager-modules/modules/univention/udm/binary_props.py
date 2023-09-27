# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2018-2024 Univention GmbH
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
# you and Univention.
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

"""Classes for holding binary UDM  object properties."""

from __future__ import absolute_import, unicode_literals

import base64
import bz2
import codecs
from typing import BinaryIO, NamedTuple, Optional, Union, cast  # noqa: F401

import magic
from six import BytesIO, string_types


FileType = NamedTuple('FileType', [('mime_type', str), ('encoding', str), ('text', str)])


def get_file_type(filename_or_file):
    # type: (Union[str, BinaryIO]) -> FileType
    """
    Get mime_type and encoding of file `filename_or_file`.

    Handles both magic libraries.

    :param filename_or_file: filename or open file
    :type filename_or_file: str or file
    :return: mime_type and encoding of `filename_or_file`
    :rtype: FileType
    """
    if hasattr(filename_or_file, 'seek'):
        f = cast(BinaryIO, filename_or_file)
        old_pos = f.tell()
        txt = f.read()
        f.seek(old_pos)
    elif isinstance(filename_or_file, string_types):
        with open(filename_or_file, 'rb') as fp:
            txt = fp.read()
    else:
        raise ValueError('Argument "filename_or_file" has unknown type {!r}.'.format(type(filename_or_file)))

    if hasattr(magic, 'from_file'):
        mime = magic.Magic(mime=True, mime_encoding=True).from_buffer(txt)
        mime_type, charset = mime.split(';')
        encoding = charset.split('=')[-1]
        text = magic.Magic().from_buffer(txt)
    elif hasattr(magic, 'detect_from_content'):
        fm = magic.detect_from_content(txt)
        mime_type = fm.mime_type
        encoding = fm.encoding
        text = fm.name
    else:
        raise RuntimeError('Unknown version or type of "magic" library.')

    # auto detect utf-8 with BOM
    if encoding == 'utf-8' and txt.startswith(codecs.BOM_UTF8):
        encoding = 'utf-8-sig'

    return FileType(mime_type, encoding, text)


class BaseBinaryProperty(object):
    """
    Container for a binary UDM property.

    Data can be set and retrieved in both its raw form or encoded for LDAP.

    Internally data is held in the encoded state (the form in which it will be
    saved to LDAP).
    """

    def __init__(self, name, encoded_value=None, raw_value=None):
        # type: (str, Optional[bytes], Optional[bytes]) -> None
        assert not (encoded_value and raw_value), 'Only one of "encoded_value" and "raw_value" must be set.'
        assert (encoded_value or raw_value), 'One of "encoded_value" or "raw_value" must be set.'
        self._name = name
        self._value = b""
        if encoded_value:
            self.encoded = encoded_value
        elif raw_value:
            self.raw = raw_value

    def __repr__(self):
        # type: () -> str
        return '{}({})'.format(self.__class__.__name__, self._name)

    @property
    def encoded(self):
        # type: () -> bytes
        return self._value

    @encoded.setter
    def encoded(self, value):
        # type: (bytes) -> None
        self._value = value

    @property
    def raw(self):
        # type: () -> bytes
        raise NotImplementedError()

    @raw.setter
    def raw(self, value):
        # type: (bytes) -> None
        raise NotImplementedError()

    @property
    def content_type(self):
        # type: () -> FileType
        return get_file_type(BytesIO(self.raw))


class Base64BinaryProperty(BaseBinaryProperty):
    """
    Container for a binary UDM property encoded using base64.

    obj.props.<prop>.encoded == base64.b64encode(obj.props.<prop>.decoded)

    >>> binprop = Base64BinaryProperty('example', raw_value=b'raw value')
    >>> Base64BinaryProperty('example', encoded_value=binprop.encoded).raw == b'raw value'
    True
    >>> import base64
    >>> binprop.encoded == base64.b64encode(binprop.raw)
    True
    """

    @property
    def raw(self):
        # type: () -> bytes
        return base64.b64decode(self._value)

    @raw.setter
    def raw(self, value):
        # type: (bytes) -> None
        self._value = base64.b64encode(value)


class Base64Bzip2BinaryProperty(BaseBinaryProperty):
    """
    Container for a binary UDM property encoded using base64 after using bzip2.

    obj.props.<prop>.encoded == base64.b64encode(obj.props.<prop>.decoded)

    >>> binprop = Base64Bzip2BinaryProperty('example', raw_value=b'raw value')
    >>> Base64Bzip2BinaryProperty('example', encoded_value=binprop.encoded).raw == b'raw value'
    True
    >>> import bz2, base64
    >>> binprop.encoded == base64.b64encode(bz2.compress(binprop.raw))
    True
    """

    @property
    def raw(self):
        # type: () -> bytes
        return bz2.decompress(base64.b64decode(self._value))

    @raw.setter
    def raw(self, value):
        # type: (bytes) -> None
        self._value = base64.b64encode(bz2.compress(value))
