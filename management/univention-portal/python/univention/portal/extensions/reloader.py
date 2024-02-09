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

import os.path
import shutil
import tempfile

from univention.portal import Plugin, config
from univention.portal.extensions.reloader_content import GroupsContentFetcher, PortalContentFetcher
from univention.portal.log import get_logger


logger = get_logger("cache")


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

    def refresh(self, reason, content=None):  # pragma: no cover
        raise NotImplementedError()


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
        logger.debug("init, %s, cache_file %s", self.__class__.__name__, cache_file)
        self._cache_file = cache_file
        self._mtime = self._get_mtime()
        self._assets_root = config.fetch("assets_root")

    def _get_mtime(self):
        try:
            return os.stat(self._cache_file).st_mtime
        except (EnvironmentError, AttributeError) as exc:
            get_logger("cache").warning(f"Unable to get mtime for {exc}")
            return 0

    def _file_was_updated(self):
        mtime = self._get_mtime()
        if mtime > self._mtime:
            self._mtime = mtime
            return True

    def _check_reason(self, reason, content=None):
        return check_reason_base(reason)

    def refresh(self, reason=None, content=None):
        class_name = self.__class__.__name__
        if not self._check_reason(reason, content=content):
            logger.info("Not refreshing cache, %s, reason: %s", class_name, reason)
            return self._file_was_updated()

        logger.info("Refreshing cache, %s, reason: %s", class_name, reason)
        try:
            content, assets = self._refresh()
        except Exception:
            get_logger("cache").exception("Error during refresh")
        else:
            for path, asset_content in assets:
                path = os.path.normpath(path)
                full_path = os.path.join(self._assets_root, path)
                self._write(full_path, asset_content)
            return self._write(self._cache_file, content)

        return self._file_was_updated()

    def _refresh(self):  # pragma: no cover
        pass

    def _write(self, path, content):
        logger.debug("Writing file %s", path)

        fd = None
        try:
            fd = self._write_to_tmp_file(content)
        except Exception:
            get_logger("cache").exception("Error during refresh")
            # hopefully, we can still work with an older cache?
        else:
            if fd:
                try:
                    os.makedirs(os.path.dirname(path))
                except EnvironmentError:
                    pass
                shutil.move(fd.name, path)
                self._mtime = self._get_mtime()
                return True

    def _write_to_tmp_file(self, content):
        mode = "w"
        if isinstance(content, bytes):
            mode = "wb"
        with tempfile.NamedTemporaryFile(mode=mode, delete=False) as fd:
            fd.write(content)
            return fd


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
        return check_portal_reason(reason)

    def _refresh(self):
        content_fetcher = PortalContentFetcher(self._portal_dn, self._assets_root)
        content = content_fetcher.fetch()
        return (content, content_fetcher.assets)


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
        super().__init__(cache_file)

    def _check_reason(self, reason, content=None):
        return check_groups_reason(reason)

    def _refresh(self):
        logger.debug("Refreshing groups cache")
        return GroupsContentFetcher().fetch()


def check_reason_base(reason):
    if reason is None:
        return False
    if reason == "force":
        return True


def check_groups_reason(reason):
    if check_reason_base(reason):
        return True
    if reason is None:
        return False
    if reason.startswith("ldap:group"):
        return True
    return False


def check_portal_reason(reason):
    if check_reason_base(reason):
        return True
    if reason is None:
        return False
    reason_args = reason.split(":", 2)
    if len(reason_args) < 2:
        return False
    if reason_args[0] != "ldap":
        return False
    return reason_args[1] in ["portal", "category", "entry", "folder", "announcement"]
