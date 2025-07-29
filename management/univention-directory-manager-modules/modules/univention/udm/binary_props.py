#
# SPDX-FileCopyrightText: 2018-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Classes for holding binary UDM  object properties."""


import base64
import bz2
import codecs
from io import BytesIO
from typing import BinaryIO, NamedTuple, Optional, Union, cast  # noqa: F401

import magic


FileType = NamedTuple('FileType', [('mime_type', str), ('encoding', str), ('text', str)])


def get_file_type(filename_or_file):
    # type: (Union[str, BinaryIO]) -> FileType
    """
    Get mime_type and encoding of file `filename_or_file`.

    Handles both magic libraries.

    :param filename_or_file: filename or open file
    :return: mime_type and encoding of `filename_or_file`
    """
    if hasattr(filename_or_file, 'seek'):
        f = cast(BinaryIO, filename_or_file)
        old_pos = f.tell()
        txt = f.read()
        f.seek(old_pos)
    elif isinstance(filename_or_file, str):
        with open(filename_or_file, 'rb') as fp:
            txt = fp.read()
    else:
        raise ValueError(f'Argument "filename_or_file" has unknown type {type(filename_or_file)!r}.')

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


class BaseBinaryProperty:
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
        return f'{self.__class__.__name__}({self._name})'

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
