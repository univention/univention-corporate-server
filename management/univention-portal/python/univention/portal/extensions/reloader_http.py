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

from urllib.parse import urljoin, urlsplit

import requests

from univention.portal.extensions import reloader
from univention.portal.log import get_logger
from univention.portal.util import log_url_safe


logger = get_logger(__name__)


class HttpReloader(reloader.Reloader):
    """
    A reloader which updates a HTTP resource.

    The HTTP resource can also refer to assets which are linked from it.

    One use case is the portal data which is JSON and contains links to the
    icons of the Portal Entries. The reloader places those assets into a
    subpath of `assets_root`.
    """

    def __init__(self, url, assets_root):
        self._ensure_url_is_supported(url)
        self._ensure_url_is_supported(assets_root)
        self._url = url
        self._assets_root = assets_root

    def refresh(self, reason=None, content=None):
        class_name = self.__class__.__name__
        if not self._check_reason(reason):
            logger.info("Not refreshing cache, %s, reason: %s", class_name, reason)
            return False
        content, assets = self._generate_content()
        for path, asset_content in assets:
            asset_url = self._create_asset_url(path)
            self._write_content(asset_content, url=asset_url)
        return self._write_content(content, url=self._url)

    def _check_reason(self, reason=None):
        return reloader.check_reason_base(reason)

    def _generate_content(self):
        content_fetcher = self._create_content_fetcher()
        content = content_fetcher.fetch()
        return content, content_fetcher.assets

    def _create_asset_url(self, path):
        asset_url = urljoin(self._assets_root, path)
        if not asset_url.startswith(self._assets_root):
            raise ValueError('Value of "path" not allowed', path)
        return asset_url

    def _create_content_fetcher(self):
        """
        Subclasses shall implement this with a custom "fetcher".

        The "fetcher" is responsible to fetch the content from an external
        source and then returns the content to place into `self.url` together
        with optional assets.
        """
        raise NotImplementedError

    def _write_content(self, content, url):
        logger.debug("PUT asset to URL: %s", log_url_safe(url))
        # TODO: Append version information, "portal-listener/VERSION"
        headers = {"user-agent": "portal-listener"}
        result = requests.put(url=url, data=content, headers=headers)
        if result.status_code >= requests.codes.bad:
            logger.error("Upload of the image did fail: %s, %s", result.status_code, result.text)
            return False
        return True

    def _ensure_url_is_supported(self, url):
        url_parts = urlsplit(url)
        if url_parts.scheme not in ("http", "https"):
            raise ValueError('Invalid value for "url"', url)


class HttpPortalReloader(HttpReloader):

    def __init__(self, url, assets_root, portal_dn):
        logger.debug(
            "Initializing %s, url: %s, assets_root: %s, portal_dn: %s",
            self.__class__.__name__, log_url_safe(url), log_url_safe(assets_root), portal_dn)
        super().__init__(url, assets_root)
        self._portal_dn = portal_dn

    def _create_content_fetcher(self):
        return reloader.PortalContentFetcher(self._portal_dn, self._assets_root)

    def _check_reason(self, reason=None):
        return reloader.check_portal_reason(reason)


class HttpGroupsReloader(HttpReloader):

    def __init__(self, url, assets_root):
        logger.debug(
            "Initializing %s, url: %s, assets_root: %s",
            self.__class__.__name__, log_url_safe(url), log_url_safe(assets_root))
        super().__init__(url, assets_root)

    def _create_content_fetcher(self):
        return reloader.GroupsContentFetcher()

    def _check_reason(self, reason=None):
        return reloader.check_groups_reason(reason)
