#!/usr/bin/python3
# SPDX-FileCopyrightText: 2023-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


import shutil
from typing import TextIO

from univention.appcenter.app_cache import AppCenterCache, default_server


class AppCenterCacheTest:
    def __init__(self) -> None:
        cache = AppCenterCache.build(server=default_server())
        self.json_file: str = cache.get_cache_file('.suggestions.json')
        self.json_file_bak: str = cache.get_cache_file('.suggestions.bak.json')
        self.json_fd: TextIO | None = None
        shutil.move(self.json_file, self.json_file_bak)

    def write(self, txt: str, truncate: bool = False) -> None:
        if self.json_fd is None:
            self.json_fd = open(self.json_file, 'w')

        if truncate:
            self.json_fd.truncate(0)

        self.json_fd.write(txt)
        self.json_fd.flush()

    def restore(self) -> None:
        if self.json_fd is not None:
            self.json_fd.close()
            shutil.move(self.json_file_bak, self.json_file)
