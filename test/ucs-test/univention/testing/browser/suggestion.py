#!/usr/bin/python3
#
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2023-2024 Univention GmbH
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

from __future__ import annotations

import shutil
from typing import TextIO

from univention.appcenter.app_cache import AppCenterCache, default_server


class AppCenterCacheTest:
    def __init__(self) -> None:
        cache = AppCenterCache.build(server=default_server())
        self.json_file: str = cache.get_cache_file(".suggestions.json")
        self.json_file_bak: str = cache.get_cache_file(".suggestions.bak.json")
        self.json_fd: TextIO | None = None
        shutil.move(self.json_file, self.json_file_bak)

    def write(self, txt: str, truncate: bool = False) -> None:
        if self.json_fd is None:
            self.json_fd = open(self.json_file, "w")

        if truncate:
            self.json_fd.truncate(0)

        self.json_fd.write(txt)
        self.json_fd.flush()

    def restore(self) -> None:
        if self.json_fd is not None:
            self.json_fd.close()
            shutil.move(self.json_file_bak, self.json_file)
