# Univention Portal
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2019-2024 Univention GmbH
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

import ipaddress
import re
from urllib.parse import urlparse

import tornado.web
from ldap.dn import str2dn

from univention.portal.extensions.cache_http import PortalFileCacheHTTP
from univention.portal.extensions.cache_object_storage import PortalFileCacheObjectStorage
from univention.portal.handlers.portal_resource import PortalResource


RE_FQDN = re.compile(
    r"(?=^.{4,253}$)(^((?!-)[a-zA-Z0-9-]{1,63}(?<!-)\.)+[a-zA-Z]{2,63}\.?$)",
)


class NavigationHandler(PortalResource):
    async def get(self, portal_name):
        portal = self.find_portal()
        if not portal:
            raise tornado.web.HTTPError(404)

        self._portal_lang = self.get_query_argument("language", "en-US").replace("-", "_")
        self._portal_base = self.get_query_argument(
            "base",
            self.reverse_abs_url("root", ()),
        ).rstrip("/")

        user = await portal.get_user(self)

        if isinstance(
            portal.portal_cache,
            (PortalFileCacheHTTP, PortalFileCacheObjectStorage),
        ):
            portal.refresh()

        visible_content = portal.get_visible_content(user, False)
        categories_content = portal.get_categories(visible_content)
        meta = portal.get_meta(visible_content, categories_content)
        entries = portal.portal_cache.get_entries()
        visible_entry_dns = portal._filter_entry_dns(
            entries.keys(),
            entries,
            user,
            False,
        )

        def get_category(category_dn):
            for category in categories_content:
                if category["dn"] == category_dn:
                    return category

        categories = []
        for category_dn, _ in meta["content"]:
            category_data = get_category(category_dn)
            if not category_data:
                continue

            category = {
                "identifier": str2dn(category_dn)[0][0][1],
                "display_name": self._choose_language(category_data["display_name"]),
                "entries": [
                    self._get_entry(entries[entry_dn], entry_dn)
                    for entry_dn in category_data["entries"]
                    if entry_dn in visible_entry_dns
                ],
            }

            if not category["entries"]:
                continue
            categories.append(category)

        navigation = {
            "categories": categories,
        }
        self.write(navigation)

    def _get_entry(self, entry_data, entry_dn):
        icon_url = entry_data["icon_url"] or None
        # most icons are referenced as ./portal/foo.svg
        if icon_url and icon_url.startswith("."):
            icon_url = icon_url[1:]
        icons = {self._portal_lang: [icon_url] if icon_url else []}

        links = {}
        for link in entry_data["links"]:
            links.setdefault(link["locale"], []).append(link["value"])

        return {
            "identifier": str2dn(entry_dn)[0][0][1],
            "icon_url": self._choose_url(
                icons,
                self._portal_base + "/univention/portal",
            ),
            "display_name": self._choose_language(entry_data["name"]),
            "link": self._choose_url(links, self._portal_base),
            "target": entry_data.get("target") or "_blank",
            "keywords": entry_data.get("keywords"),
        }

    def _choose_language(self, entry):
        return entry.get(self._portal_lang) or entry.get("en_US")

    def _choose_url(self, links, base):
        # rules:
        # - filter on the requested language otherwise fallback to en_US
        # - always fqdn before ip
        # - always https before http

        links = self._choose_language(links)
        if not links:
            return

        fqdn_links, ip_links, path_links = [], [], []
        for link in links:
            parsed = urlparse(link)
            try:
                ipaddress.ip_address(parsed.netloc)
            except ValueError:
                if RE_FQDN.search(parsed.netloc):
                    fqdn_links.append({"link": link, "parsed": parsed})
                else:
                    path_links.append({"link": base + link, "parsed": parsed})
            else:
                ip_links.append({"link": link, "parsed": parsed})

        def prefer_https(links):
            for linkdict in links:
                if linkdict["parsed"].scheme == "https":
                    return linkdict["link"]

            # if we are here, we had fqdn links but none https; return the first fqdn link from list
            return links[0]["link"]

        for links in (fqdn_links, ip_links, path_links):
            if links:
                return prefer_https(links)
