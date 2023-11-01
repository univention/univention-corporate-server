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
import os.path
import shutil
import tempfile
from imghdr import what
from pathlib import Path
from urllib.parse import quote

from univention.portal import Plugin, config
from univention.portal.log import get_logger


class Reloader(metaclass=Plugin):
    """
    Our base class for reloading

    The idea is that this class handles the reloading
    for caches.

    `refresh`: In fact the only method. Gets a "reason" so that it can
            decide that a refresh is not necessary. If it was necessary, it
            should return True

    A reason "force" should be treated as very important.
    If the reloader refreshed the content, the overlying cache will reload
    itself.
    """

    def refresh(self, reason=None):  # pragma: no cover
        pass


class MtimeBasedLazyFileReloader(Reloader):
    """
    Specialized class that reloads if a certain (cache) file was updated.
    So if a seconds process updated the file and this class is asked to
    reload, it just returns True. If the reason fits, it actually refreshes
    the content and writes it into the file.

    cache_file:
            Filename this object is responsible for
    """

    def __init__(self, cache_file):
        self._cache_file = cache_file
        self._mtime = self._get_mtime()

    def _get_mtime(self):
        try:
            return os.stat(self._cache_file).st_mtime
        except (OSError, AttributeError) as exc:
            get_logger("cache").warning(f"Unable to get mtime for {exc}")
            return 0

    def _file_was_updated(self):
        mtime = self._get_mtime()
        if mtime > self._mtime:
            self._mtime = mtime
            return True

    def _check_reason(self, reason, content=None):
        if reason is None:
            return False
        if reason == "force":
            return True

    def refresh(self, reason=None, content=None):
        if self._check_reason(reason, content=content):
            get_logger("cache").info("refreshing cache")
            fd = None
            try:
                fd = self._refresh()
            except Exception:
                get_logger("cache").exception("Error during refresh")
                # hopefully, we can still work with an older cache?
            else:
                if fd:
                    try:
                        os.makedirs(os.path.dirname(self._cache_file))
                    except OSError:
                        pass
                    shutil.move(fd.name, self._cache_file)
                    self._mtime = self._get_mtime()
                    return True
        return self._file_was_updated()

    def _refresh(self):  # pragma: no cover
        pass


class PortalReloaderUDM(MtimeBasedLazyFileReloader):
    """
    Specialized class that reloads a cache file with the content of a certain
    portal object using UDM. Reacts on reasons like "ldap:portal:<correct_dn>".

    portal_dn:
            DN of the portals/portal object
    cache_file:
            Filename this object is responsible for
    """

    def __init__(self, portal_dn, cache_file):
        super(PortalReloaderUDM, self).__init__(cache_file)
        self._portal_dn = portal_dn

    def _check_reason(self, reason, content=None):
        if super(PortalReloaderUDM, self)._check_reason(reason, content):
            return True
        if reason is None:
            return False
        reason_args = reason.split(":", 2)
        if len(reason_args) < 2:
            return False
        if reason_args[0] != "ldap":
            return False
        return reason_args[1] in ["portal", "category", "entry", "folder", "announcement"]

    def _refresh(self):
        udm_lib = importlib.import_module("univention.udm")
        try:
            udm = udm_lib.UDM.machine(prefer_local_connection=True).version(2)
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
        categories = self._extract_categories(udm, portal_data)
        user_links = portal_data.props.userLinks
        menu_links = portal_data.props.menuLinks
        folders = self._extract_folders(udm, portal_data, list(categories.values()))
        entries = self._extract_entries(udm, portal_data, list(categories.values()), list(folders.values()))
        announcements = self._extract_announcements(udm, portal_data)

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as fd:
            json.dump(
                {
                    "portal": portal,
                    "categories": categories,
                    "folders": folders,
                    "entries": entries,
                    "user_links": user_links,
                    "menu_links": menu_links,
                    "announcements": announcements,
                },
                fd,
                sort_keys=True,
                indent=4,
            )
            return fd

    @classmethod
    def _extract_portal(cls, portal_data):
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
            portal["logo"] = cls._write_image(portal_data.props.logo.raw, portal_name, "logos")
        if portal["background"]:
            portal["background"] = cls._write_image(portal_data.props.background.raw, portal_name, "backgrounds")
        return portal

    @classmethod
    def _extract_categories(cls, udm, portal):
        categories = {}
        for category in udm.get("portals/category").search():
            categories[category.dn] = {
                "dn": category.dn,
                "in_portal": category.dn in portal.props.categories,
                "display_name": category.props.displayName,
                "entries": category.props.entries,
            }
        return categories

    @classmethod
    def _extract_folders(cls, udm, portal, categories):
        folders = {}

        for folder in udm.get("portals/folder").search():
            in_portal = (
                folder.dn in portal.props.menuLinks
                or folder.dn in portal.props.userLinks
                or any(folder.dn in category["entries"] for category in categories if category["in_portal"])
            )
            folders[folder.dn] = {
                "dn": folder.dn,
                "in_portal": in_portal,
                "name": folder.props.displayName,
                "entries": folder.props.entries,
            }

        return folders

    @classmethod
    def _extract_entries(cls, udm, portal, categories, folders):
        entries = {}

        for entry in udm.get("portals/entry").search():
            if entry.dn in entries:
                continue
            in_portal = (
                entry.dn in portal.props.menuLinks
                or entry.dn in portal.props.userLinks
                or any(entry.dn in category["entries"] for category in categories if category["in_portal"])
                or any(entry.dn in folder["entries"] for folder in folders if folder["in_portal"])
            )
            icon_url = None
            if entry.props.icon:
                icon_url = cls._write_image(entry.props.icon.raw, entry.props.name, "entries")

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
    def _extract_announcements(cls, udm, portal):
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

    @classmethod
    def _write_image(cls, image, name, dirname):
        assets_root = Path(config.fetch("assets_root"))

        try:
            name = name.replace(
                "/", "-",
            )  # name must not contain / and must be a path which can be accessed via the web!
            extension = what(None, image) or "svg"
            path = assets_root / "icons" / dirname / f"{name}.{extension}"
            path.write_bytes(image)
        except (OSError, TypeError):
            get_logger("img").exception("Error saving image for %s" % name)
        else:
            return f"./icons/{quote(dirname)}/{quote(name)}.{extension}"


class GroupsReloaderLDAP(MtimeBasedLazyFileReloader):
    """
    Specialized class that reloads a cache file with the content of group object
    in LDAP. Reacts on the reason "ldap:group".

    .. warnings:: As of 4.0.7-8 we use univention-group-membership-cache to
    obtain groups user belongs to; but we cannot change the constructor kwargs
    because customers may have added entries to
    /usr/share/univention-portal/portals.json that still uses them.

    ldap_uri:
            URI for the LDAP connection, e.g. "ldap://ucs:7369"
    binddn:
            The bind dn for the connection, e.g. "cn=ucs,cn=computers,..."
    password_file:
            Filename that holds the password for the binddn, e.g. "/etc/machine.secret"
    ldap_base:
            Base in which the groups are searched in. E.g., "dc=base,dc=com" or "cn=groups,ou=OU1,dc=base,dc=com"
    cache_file:
            Filename this object is responsible for
    """

    def __init__(self, ldap_uri, binddn, password_file, ldap_base, cache_file):
        super(GroupsReloaderLDAP, self).__init__(cache_file)

    def _check_reason(self, reason, content=None):
        if super(GroupsReloaderLDAP, self)._check_reason(reason, content):
            return True
        if reason is None:
            return False
        if reason.startswith("ldap:group"):
            return True

    def _refresh(self):
        from univention.ldap_cache.frontend import users_groups

        users = users_groups()
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as fd:
            json.dump(users, fd, sort_keys=True, indent=4)
        return fd
