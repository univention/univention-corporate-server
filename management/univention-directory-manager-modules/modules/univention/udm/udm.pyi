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


from typing import Any, Dict, List, Optional, Tuple, Type  # noqa: F401

from .base import BaseModuleTV, BaseObjectTV  # noqa: F401
from .utils import ConnectionConfig  # noqa: F401


class UDM(object):
    _module_object_cache = {}  # type: Dict[Tuple[str, int, int], BaseModuleTV]
    _imported = False
    _modules = []  # type: List[BaseModuleTV]

    def __init__(self, connection, api_version=None):  # type: (Any, Optional[int]) -> None
        self.connection = connection
        self._api_version = api_version

    @classmethod
    def admin(cls):  # type: () -> UDM
        ...

    @classmethod
    def machine(cls):  # type: () -> UDM
        ...

    @classmethod
    def credentials(
        cls,
        identity,  # type: str
        password,  # type: str
        base=None,  # type: Optional[str]
        server=None,  # type: Optional[str]
        port=None,  # type: Optional[int]
    ):
        # type: (...) -> UDM
        ...

    def version(self, api_version):  # type: (int) -> UDM
        ...

    def get(self, name):  # type: (str) -> BaseModuleTV
        ...

    def obj_by_dn(self, dn):  # type: (str) -> BaseObjectTV
        ...

    @property
    def api_version(self):  # type: () -> int
        ...
