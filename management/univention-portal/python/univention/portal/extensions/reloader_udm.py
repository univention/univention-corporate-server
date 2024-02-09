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

import importlib
import json
from imghdr import what
from urllib.parse import quote

from univention.portal.log import get_logger


logger = get_logger(__name__)


class PortalContentFetcherUDM:

    def __init__(self, portal_dn, assets_root):
        self._portal_dn = portal_dn
        self._assets_root = assets_root
        self.assets = []

    def fetch(self):
        udm_lib = importlib.import_module("univention.udm")
        try:
            udm = self._create_udm_client()
            portal_data = udm.get("portals/portal").get(self._portal_dn)
        except udm_lib.ConnectionError:
            get_logger("cache").warning("Could not establish UDM connection. Is the LDAP server accessible?")
            return None
        except udm_lib.UnknownModuleType:
            get_logger("cache").warning("UDM not up to date? Portal module not found.")
            return None
        except udm_lib.NoObject:
            get_logger("cache").warning("Portal %s not found", self._portal_dn)
            return None

        portal = self._extract_portal(portal_data)
        categories = self._extract_categories(udm, portal_data.props.categories)
        portal_categories = [category for dn, category in categories.items() if category["in_portal"]]
        user_links = portal_data.props.userLinks
        menu_links = portal_data.props.menuLinks
        folders = self._extract_folders(udm, portal_categories, user_links, menu_links)
        portal_folders = [folder for dn, folder in folders.items() if folder["in_portal"]]
        entries = self._extract_entries(udm, portal_categories, portal_folders, user_links, menu_links)
        announcements = self._extract_announcements(udm)

        return json.dumps(
            {
                "portal": portal,
                "categories": categories,
                "folders": folders,
                "entries": entries,
                "user_links": user_links,
                "menu_links": menu_links,
                "announcements": announcements,
            },
            sort_keys=True,
            indent=4,
        )

    def _create_udm_client(self):
        udm_lib = importlib.import_module("univention.udm")
        return udm_lib.UDM.machine(prefer_local_connection=True).version(3)

    def _extract_portal(self, portal_data):
        portal = {
            "dn": portal_data.dn,
            "showUmc": portal_data.props.showUmc,
            "logo": portal_data.props.logo,
            "background": portal_data.props.background,
            "name": portal_data.props.displayName,
            "defaultLinkTarget": portal_data.props.defaultLinkTarget,
            "ensureLogin": portal_data.props.ensureLogin,
            "categories": portal_data.props.categories,
        }

        portal_name = portal_data.props.name

        if portal["logo"]:
            portal["logo"] = self._collect_asset(portal_data.props.logo.raw, portal_name, "logos")

        if portal["background"]:
            portal["background"] = self._collect_asset(portal_data.props.background.raw, portal_name, "backgrounds")
        return portal

    @classmethod
    def _extract_categories(cls, udm, portal_categories):
        categories = {}

        for category in udm.get("portals/category").search():
            categories[category.dn] = {
                "dn": category.dn,
                "in_portal": category.dn in portal_categories,
                "display_name": category.props.displayName,
                "entries": category.props.entries,
            }

        return categories

    @classmethod
    def _extract_folders(cls, udm, portal_categories, user_links, menu_links):
        folders = {}

        for folder in udm.get("portals/folder").search():
            in_portal = (
                folder.dn in user_links
                or folder.dn in menu_links
                or any(folder.dn in category["entries"] for category in portal_categories)
            )
            folders[folder.dn] = {
                "dn": folder.dn,
                "in_portal": in_portal,
                "name": folder.props.displayName,
                "entries": folder.props.entries,
            }

        return folders

    def _extract_entries(self, udm, portal_categories, portal_folders, user_links, menu_links):
        entries = {}

        for entry in udm.get("portals/entry").search():
            if entry.dn in entries:
                continue
            in_portal = (
                entry.dn in user_links
                or entry.dn in menu_links
                or any(entry.dn in category["entries"] for category in portal_categories)
                or any(entry.dn in folder["entries"] for folder in portal_folders)
            )

            icon_url = None
            if entry.props.icon:
                icon_url = self._collect_asset(entry.props.icon.raw, entry.props.name, "entries")

            entries[entry.dn] = {
                "dn": entry.dn,
                "in_portal": in_portal,
                "name": entry.props.displayName,
                "description": entry.props.description,
                'keywords': entry.props.keywords,
                "icon_url": icon_url,
                "activated": entry.props.activated,
                "anonymous": entry.props.anonymous,
                "allowedGroups": entry.props.allowedGroups,
                "links": entry.props.link,
                "linkTarget": entry.props.linkTarget,
                "target": entry.props.target,
                "backgroundColor": entry.props.backgroundColor,
            }

        return entries

    @classmethod
    def _extract_announcements(cls, udm):
        udm_lib = importlib.import_module("univention.udm")
        announcements = {}

        try:
            announcement_module = udm.get("portals/announcement")
        except udm_lib.UnknownModuleType:
            announcement_module = None
        if not announcement_module:
            get_logger("cache").warning("UDM not up to date? Announcement module not found.")
            return announcements

        for announcement in announcement_module.search():
            announcements[announcement.dn] = {
                "dn": announcement.dn,
                "allowedGroups": announcement.props.allowedGroups,
                "name": announcement.props.name,
                "message": announcement.props.message,
                "title": announcement.props.title,
                "visibleFrom": str(announcement.props.visibleFrom),
                "visibleUntil": str(announcement.props.visibleUntil),
                "isSticky": announcement.props.isSticky,
                "needsConfirmation": announcement.props.needsConfirmation,
                "severity": announcement.props.severity,
            }

        return announcements

    def _collect_asset(self, content, name, dirname):
        name = name.replace(
            "/", "-",
        )  # name must not contain / and must be a path which can be accessed via the web!
        extension = what(None, content) or "svg"
        path = f"./icons/{quote(dirname)}/{quote(name)}.{quote(extension)}"
        self.assets.append((path, content))
        return path
