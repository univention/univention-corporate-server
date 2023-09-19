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

from __future__ import absolute_import, unicode_literals

from collections import namedtuple
from typing import BinaryIO, Optional, Union  # noqa: F401


FileType = namedtuple('namedtuple', ['mime_type', 'encoding', 'text'])


def get_file_type(filename_or_file):  # type: (Union[str, BinaryIO]) -> FileType
    ...


class BaseBinaryProperty(object):
    def __init__(self, name, encoded_value=None, raw_value=None):
        # type: (str, Optional[str], Optional[str]) -> None
        ...

    def __repr__(self):  # type: () -> str
        ...

    @property
    def encoded(self):  # type: () -> str
        ...

    @encoded.setter
    def encoded(self, value):  # type: (str) -> None
        ...

    @property
    def raw(self):  # type: () -> str
        ...

    @raw.setter
    def raw(self, value):  # type: (str) -> None
        ...

    @property
    def content_type(self):  # type: () -> FileType
        ...


class Base64BinaryProperty(BaseBinaryProperty):
    @property
    def raw(self):  # type: () -> str
        ...

    @raw.setter
    def raw(self, value):  # type: (str) -> None
        ...


class Base64Bzip2BinaryProperty(BaseBinaryProperty):
    @property
    def raw(self):  # type: () -> str
        ...

    @raw.setter
    def raw(self, value):  # type: (str) -> None
        ...
