#!/usr/bin/python3
# SPDX-FileCopyrightText: 2013-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""
Univention common Python library with
helper functions for MIME type handling.
"""

from __future__ import annotations

import bz2
import io
import zlib
from typing import TYPE_CHECKING, Any

import magic
from PIL import Image


if TYPE_CHECKING:
    from collections.abc import Callable


MIME_TYPE = magic.Magic(magic.MAGIC_MIME_TYPE)
MIME_DESCRIPTION = magic.Magic(magic.MAGIC_NONE)

UMC_ICON_BASEDIR = "/usr/share/univention-management-console-frontend/js/dijit/themes/umc/icons"

compression_mime_type_handlers = {
    "application/x-gzip": lambda x: zlib.decompress(x, 16 + zlib.MAX_WBITS),
    # "application/gzip": lambda x: zlib.decompress(x, 16 + zlib.MAX_WBITS),  # TODO: enable Bug #51594
    "application/x-bzip2": bz2.decompress,
    "application/bzip2": bz2.decompress,
}


def get_mime_type(data: bytes) -> str:
    """
    Guess |MIME| type of data.

    :param bytes data: Some data.
    :returns: The |MIME| type string.
    :rtype: str
    """
    return MIME_TYPE.from_buffer(data)


def get_mime_description(data: bytes) -> str:
    """
    Guess type of data silimar to :command:`file`.

    :param bytes data: Some data.
    :returns: A descriptive string.
    :rtype: str
    """
    return MIME_DESCRIPTION.from_buffer(data)


def compression_mime_type_of_buffer(data: bytes) -> tuple[str, Callable[[Any], bytes]]:
    """
    Guess |MIME| type of compressed data.

    :param bytes data: Some compressed data.
    :returns: A 2-tuple (mime_type, uncompress_function).
    :rtype: tuple[str, str]
    :raises univention.admin.uexceptions.valueError: if the compression format is not recognized.
    """
    mime_type = get_mime_type(data)
    if mime_type in compression_mime_type_handlers:
        return (mime_type, compression_mime_type_handlers[mime_type])
    else:
        import univention.admin.uexceptions
        raise univention.admin.uexceptions.valueError("Not a supported compression format: %s" % (mime_type,))


def uncompress_buffer(data: bytes) -> tuple[str | None, bytes]:
    """
    Return uncompressed data and its |MIME| type.

    :param bytes data: Some compressed data.
    :returns: A 2-tuple (mime_type, uncompressed_data). On errors `mime_type` is `None` and `uncompressed_data` is `data`.
    :rtype: tuple[str, bytes]
    """
    import univention.admin.uexceptions
    try:
        (mime_type, compression_mime_type_handler) = compression_mime_type_of_buffer(data)
        return (mime_type, compression_mime_type_handler(data))
    except univention.admin.uexceptions.valueError:
        return (None, data)


def uncompress_file(filename: str) -> tuple[str | None, bytes]:
    """
    Return uncompressed file content and its |MIME| type.

    :param str filename: The name of the file.
    :returns: A 2-tuple (mime_type, uncompressed_data). On errors `mime_type` is `None` and `uncompressed_data` is `data`.
    :rtype: tuple[str, bytes]
    """
    with open(filename, 'rb') as f:
        return uncompress_buffer(f.read())


def image_mime_type_of_buffer(data: bytes) -> str:
    """
    Guess |MIME| type of image.

    :param bytes data: Some image data.
    :returns: The |MIME| type string.
    :rtype: str
    :raises univention.admin.uexceptions.valueError: if the image format is not supported.
    """
    mime_type = get_mime_type(data)
    if mime_type in ('image/jpeg', 'image/png', 'image/svg+xml', 'application/x-gzip'):
        return mime_type
    else:
        import univention.admin.uexceptions
        raise univention.admin.uexceptions.valueError("Not a supported image format: %s" % (mime_type,))


def imagedimensions_of_buffer(data: bytes) -> tuple[int, int]:
    """
    Return image dimension of image.

    :param bytes data: Some image data.
    :returns: A 2-tuple (width, height)
    :rtype: tuple[int, int]
    """
    fp = io.BytesIO(data)
    im = Image.open(fp)
    return im.size


def imagecategory_of_buffer(data: bytes) -> tuple[str, str | None, str] | None:
    """
    Return |MIME| types and size information for image.

    :strparam bytes data: Some (compressed) image data.
    :returns: a 3-tuple (image_mime_type, compression_mime_type, dimension) where `dimension` is `{width}x{height}` or `scalable`. `None` if the format is not recognized.
    :rtype: tuple[str, str, str]
    """
    (compression_mime_type, uncompressed_data) = uncompress_buffer(data)
    mime_type = image_mime_type_of_buffer(uncompressed_data)
    if mime_type in ('image/jpeg', 'image/png'):
        return (mime_type, compression_mime_type, "%sx%s" % imagedimensions_of_buffer(uncompressed_data))
    elif mime_type in ('image/svg+xml', 'application/x-gzip'):
        return (mime_type, compression_mime_type, "scalable")
    return None


def default_filename_suffix_for_mime_type(mime_type: str, compression_mime_type: str) -> str | None:
    """
    Return default file name suffix for image.

    :param str mime_type: The |MIME| type of the image.
    :param str compression_mime_type: The |MIME| type of the compression.
    :returns: A suffix string or `None` if the image format is not supported.
    :rytpe: str
    """
    if mime_type == 'image/svg+xml':
        if not compression_mime_type:
            return '.svg'
        elif compression_mime_type == 'application/x-gzip':
            return '.svgz'
    elif mime_type == 'image/png':
        return '.png'
    elif mime_type == 'image/jpeg':
        return '.jpg'
    return None
