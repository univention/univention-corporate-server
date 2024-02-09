#!/usr/bin/python3
#
# Univention Portal
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2020-2024 Univention GmbH
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
#


from copy import deepcopy

import requests

from univention.portal import Plugin
from univention.portal.log import get_logger
from univention.portal.util import log_url_safe


class CacheHTTP(metaclass=Plugin):
    """
    ucs_internal_url:
            The URL where the UCS internal portal/groups data are available.
    """

    def __init__(self, ucs_internal_url):
        self._ucs_internal_url = ucs_internal_url
        self._etag = None
        self._cache = {}

    def get_id(self):
        return self._etag

    def _load(self):
        get_logger("cache").info(
            f"loading data from {log_url_safe(self._ucs_internal_url)}",
        )

        # TODO: Append version to header, like "portal-server/VERSION"
        headers = {"user-agent": "portal-server"}
        if self._etag:
            headers["If-None-Match"] = self._etag

        try:
            response = requests.get(self._ucs_internal_url, headers=headers)
        except Exception:
            get_logger("cache").exception(
                "Error loading %s", log_url_safe(self._ucs_internal_url),
            )
            return

        if response.status_code == requests.codes.not_modified:
            get_logger("cache").info(
                "Not modified %s", log_url_safe(self._ucs_internal_url),
            )
            return
        elif response.status_code == requests.codes.unauthorized:
            get_logger("cache").error(
                "Cannot fetch %s. Unauthorized!", log_url_safe(self._ucs_internal_url),
            )
            return

        self._cache = response.json()
        self._etag = response.headers.get("ETag")
        get_logger("cache").info(
            "Loaded from %s, ETag: %s", log_url_safe(self._ucs_internal_url), self._etag,
        )

    def get(self):
        return self._cache

    def refresh(self, reason=None):
        self._load()


class PortalFileCacheHTTP(CacheHTTP):
    def __init__(self, ucs_internal_url):
        super().__init__(f"{ucs_internal_url}")

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
        # TODO: this needs special handling currently in the
        #       dev setup, since it relies on a connection to
        #       a UCS machine which might not have the latest
        #       portal with announcements installed.
        announcements = {}
        if "announcements" in self.get().keys():
            announcements = deepcopy(self.get()["announcements"])
        return announcements

    def refresh(self, reason=None):
        super().refresh(reason)


class GroupFileCacheHTTP(CacheHTTP):
    def __init__(self, ucs_internal_url):
        super().__init__(f"{ucs_internal_url}/groups")

    def refresh(self, reason=None):
        super().refresh(reason)
