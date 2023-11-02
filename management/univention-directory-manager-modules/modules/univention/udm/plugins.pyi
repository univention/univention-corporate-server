# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2018-2023 Univention GmbH
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

from collections import OrderedDict  # noqa: F401
from typing import Any, Dict, Iterable, TypeVar  # noqa: F401

import univention
import typing_extensions


PluginTV = TypeVar('PluginTV', bound=univention.udm.plugins.Plugin)  # noqa: PYI001


class Plugin(type):

    def __new__(mcs, name, bases, attrs):  # type: (Plugin, str, Iterable[str], Dict[str, Any]) -> PluginTV
        new_cls = super(Plugin, mcs).__new__(mcs, name, bases, attrs)
        Plugins.add_plugin(new_cls)
        return new_cls


class Plugins(object):

    _plugins: typing_extensions.TypeAlias = None  # type: OrderedDict
    _imported = {}  # type: Dict[str, bool]

    def __init__(self, python_path):  # type: (str) -> None
        ...

    @classmethod
    def add_plugin(cls, plugin):  # type: (PluginTV) -> None
        ...

    def __iter__(self):  # type: () -> PluginTV
        ...

    def load(self):  # type: () -> None
        ...
