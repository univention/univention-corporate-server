#!/usr/bin/python3
#
# Univention Portal
#
# SPDX-FileCopyrightText: 2020-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

import json
import os
from copy import deepcopy

from univention.portal import Plugin
from univention.portal.log import get_logger


class Cache(metaclass=Plugin):
    """
    Base class for Caching in general

    `get`: Gets the complete cache content.
    `refresh`: Refreshes the cache. Gets a "reason" to decide if this is
    really needed. The value "force" should be handled as if it is really
    needed.

    cache_file:
        Filename where the content is stored
    reloader:
        Class that handles the actual refresh
    """

    def __init__(self, cache_file, reloader=None):
        self._cache_file = cache_file
        self._reloader = reloader
        self._cache = {}
        self._loaded = False

    def get_id(self):
        try:
            stat = os.stat(self._cache_file)
            return str(stat.st_mtime)
        except (OSError):
            return ""

    def _load(self):
        get_logger("cache").info(f"loading cache file {self._cache_file}")
        try:
            with open(self._cache_file) as fd:
                self._cache = json.load(fd)
        except (OSError, ValueError):
            get_logger("cache").exception(f"Error loading {self._cache_file}")
        else:
            self._loaded = True

    def get(self):
        if not self._loaded or self.refresh():
            self._load()
        return self._cache

    def refresh(self, reason=None):
        if self._reloader:
            return self._reloader.refresh(reason=reason, content=self._cache)


class PortalFileCache(Cache):
    """
    Specialized cache for portal data. The implementation does not differ
    from that of a base cache, but it provides more specialized cache
    access methods that it needs in order to work with the Portal class.

    `get_user_links`
    `get_entries`
    `get_folders`
    `get_portal`
    `get_categories`
    `get_menu_links`
    `get_announcements`
    """

    def get_user_links(self):
        return deepcopy(self.get()["user_links"])

    def get_entries(self):
        return deepcopy(self.get()["entries"])

    def get_folders(self):
        return deepcopy(self.get()["folders"])

    def get_portal(self):
        return deepcopy(self.get()["portal"])

    def get_categories(self):
        return deepcopy(self.get()["categories"])

    def get_menu_links(self):
        return deepcopy(self.get()["menu_links"])

    def get_announcements(self):
        return deepcopy(self.get()["announcements"])


class GroupFileCache(Cache):
    """
    Caching class for groups.
    In fact it is just the same as the normal Cache and just here in case
    we want to get smarter at some point.
    """
