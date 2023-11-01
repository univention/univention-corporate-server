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


from collections import namedtuple
from typing import Any  # noqa: F401


ConnectionConfig = namedtuple('ConnectionConfig', ['klass', 'method', 'args', 'kwargs'])


is_interactive = bool()


class UDebug(object):

    target = 0x0A  # type: int
    level2str = {
        4: 'DEBUG',
        0: 'ERROR',
        3: 'INFO',
        2: 'INFO',
        1: 'WARN',
    }

    @classmethod
    def all(cls, msg):  # type: (str) -> None
        ...

    debug = all

    @classmethod
    def error(cls, msg):  # type: (str) -> None
        ...

    @classmethod
    def info(cls, msg):  # type: (str) -> None
        ...

    @classmethod
    def process(cls, msg):  # type: (str) -> None
        ...

    @classmethod
    def warn(cls, msg):  # type: (str) -> None
        ...

    warning = warn

    @classmethod
    def _log(cls, level, msg):  # type: (int, str) -> None
        ...


def load_class(module_path, class_name):  # type: (str, str) -> type
    ...


def get_connection(connection_config):  # type: (ConnectionConfig) -> Any
    ...
