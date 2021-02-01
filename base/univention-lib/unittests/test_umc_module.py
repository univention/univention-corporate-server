#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2020-2021 Univention GmbH
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

import pytest
import bz2
import tempfile

from .conftest import import_lib_module

umc_module = import_lib_module('umc_module')

PNG_HEADER = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
ICON = b'\x00\x00\x01\x00\x01\x00\x01\x01\x00\x00\x01\x00 \x000\x00\x00\x00\x16\x00\x00\x00(\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00\x01\x00 \x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00'
PNG = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xdc\xccY\xe7\x00\x00\x00\x00IEND\xaeB`\x82'
JPG = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x01,\x01,\x00\x00\xff\xdb\x00C\x00\x03\x02\x02\x03\x02\x02\x03\x03\x03\x03\x04\x03\x03\x04\x05\x08\x05\x05\x04\x04\x05\n\x07\x07\x06\x08\x0c\n\x0c\x0c\x0b\n\x0b\x0b\r\x0e\x12\x10\r\x0e\x11\x0e\x0b\x0b\x10\x16\x10\x11\x13\x14\x15\x15\x15\x0c\x0f\x17\x18\x16\x14\x18\x12\x14\x15\x14\xff\xdb\x00C\x01\x03\x04\x04\x05\x04\x05\t\x05\x05\t\x14\r\x0b\r\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xc4\x00\x1f\x01\x00\x03\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x11\x00\x02\x01\x02\x04\x04\x03\x04\x07\x05\x04\x04\x00\x01\x02w\x00\x01\x02\x03\x11\x04\x05!1\x06\x12AQ\x07aq\x13"2\x81\x08\x14B\x91\xa1\xb1\xc1\t#3R\xf0\x15br\xd1\n\x16$4\xe1%\xf1\x17\x18\x19\x1a&\'()*56789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xfdS\xa0\x0f\xff\xd9'


# TODO: replace with mock
try:
	import univention.admin.uexceptions
except ImportError:
	import univention  # noqa: E402
	import argparse  # noqa: E402
	import sys  # noqa: E402
	univention.admin = argparse.Namespace()
	univention.admin.uexceptions = argparse.Namespace()
	univention.admin.uexceptions.valueError = ValueError
	sys.modules['univention.admin'] = univention.admin
	sys.modules['univention.admin.uexceptions'] = univention.admin.uexceptions


def test_get_mime_type():
	assert umc_module.get_mime_type(PNG_HEADER) == 'image/png'


def test_get_mime_description():
	assert umc_module.get_mime_description(PNG_HEADER) == 'PNG image data, 0 x 0, 0-bit grayscale, non-interlaced'


def test_compression_mime_type_of_buffer():
	assert umc_module.compression_mime_type_of_buffer(bz2.compress(PNG_HEADER)) == ('application/x-bzip2', bz2.decompress)


def test_uncompress_buffer():
	assert umc_module.uncompress_buffer(bz2.compress(PNG_HEADER)) == ('application/x-bzip2', PNG_HEADER)
	assert umc_module.uncompress_buffer(b'foo') == (None, b'foo')


def test_uncompress_file():
	with tempfile.NamedTemporaryFile('wb') as fd:
		fd.write(bz2.compress(PNG_HEADER))
		fd.flush()
		assert umc_module.uncompress_file(fd.name) == ('application/x-bzip2', PNG_HEADER)


def test_image_mime_type_of_buffer():
	assert umc_module.image_mime_type_of_buffer(PNG_HEADER) == 'image/png'
	with pytest.raises(Exception):
		umc_module.image_mime_type_of_buffer(b'foo')


def test_imagedimensions_of_buffer():
	assert umc_module.imagedimensions_of_buffer(ICON) == (1, 1)


@pytest.mark.parametrize('buf,result', [
	pytest.param(PNG, ('image/png', 'application/x-bzip2', '1x1'), id="PNG"),
	pytest.param(JPG, ('image/jpeg', 'application/x-bzip2', '1x1'), id="JPG"),
	pytest.param(ICON, ('image/x-icon', 'application/x-bzip2', '1x1'), marks=pytest.mark.xfail(reason='valueError: Not a supported image format: image/x-icon'), id="ICON"),
])
def test_imagecategory_of_buffer(buf, result):
	assert umc_module.imagecategory_of_buffer(bz2.compress(buf)) == result


@pytest.mark.parametrize('mime_type,compression_mime_type,suffix', [
	('image/svg+xml', None, '.svg'),
	('image/svg+xml', 'application/x-gzip', '.svgz'),
	('image/png', None, '.png'),
	('image/jpeg', None, '.jpg'),
	('image/x-icon', None, None),
])
def test_default_filename_suffix_for_mime_type(mime_type, compression_mime_type, suffix):
	assert umc_module.default_filename_suffix_for_mime_type(mime_type, compression_mime_type) == suffix
