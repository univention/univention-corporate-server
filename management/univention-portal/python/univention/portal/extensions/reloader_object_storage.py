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

import mimetypes
import pathlib
from urllib.parse import urlsplit

import requests
from botocore.exceptions import EndpointConnectionError

from univention.portal.extensions import reloader
from univention.portal.log import get_logger
from univention.portal.util import get_object_storage_client


logger = get_logger(__name__)


class ObjectStorageReloader(reloader.Reloader):
    """
    A reloader which updates an object storage resource.

    One use case is the portal data which is JSON and contains links to the
    icons of the Portal Entries. The reloader places those assets into a
    subpath of `assets_root_path`.

    Because of the way the portal extensions are loaded, keep in mind the
    build arguments are specified in `portals.json`.
    """

    def __init__(
        self,
        json_path,
        assets_root_path,
        object_storage_endpoint,
        bucket,
        access_key_id,
        secret_access_key,
    ):
        self._object_storage_endpoint = object_storage_endpoint
        self._bucket = bucket
        self._access_key_id = access_key_id
        self._secret_access_key = secret_access_key

        self._assets_root_path = assets_root_path
        self._json_path = json_path

        self._ensure_object_storage_endpoint_is_supported(object_storage_endpoint)
        self._object_storage_client = get_object_storage_client(
            object_storage_endpoint,
            access_key_id,
            secret_access_key,
        )

    def refresh(self, reason=None, content=None):
        class_name = self.__class__.__name__
        if not self._check_reason(reason):
            logger.info("Not refreshing cache, %s, reason: %s", class_name, reason)
            return False
        content, assets = self._generate_content()
        for path, asset_content in assets:
            asset_absolute_path = self._create_asset_absolute_path(path)
            self._write_content(
                asset_content,
                asset_absolute_path,
                mimetypes.guess_type(asset_absolute_path)[0],
            )
        return self._write_content(content, self._json_path, "application/json")

    def _check_reason(self, reason=None):
        return reloader.check_reason_base(reason)

    def _generate_content(self):
        content_fetcher = self._create_content_fetcher()
        content = content_fetcher.fetch()
        return content, content_fetcher.assets

    def _create_asset_absolute_path(self, path):
        return str(pathlib.Path(self._assets_root_path, path))

    def _create_content_fetcher(self):
        """
        Subclasses shall implement this with a custom "fetcher".

        The "fetcher" is responsible to fetch the content from an external
        source and then returns the content to place into `self.url` together
        with optional assets.
        """
        raise NotImplementedError

    def _write_content(self, content, asset_absolute_path, content_type):
        logger.debug(
            "Writing asset to bucket %s on path: %s",
            self._bucket,
            asset_absolute_path,
        )
        try:
            result = self._object_storage_client.put_object(
                Body=content,
                Bucket=self._bucket,
                Key=asset_absolute_path,
                ContentType=content_type,
            )
        except EndpointConnectionError:
            logger.error(
                "Could not connect to object storage server at %s",
                self._object_storage_endpoint,
            )
            return
        if result["ResponseMetadata"]["HTTPStatusCode"] >= requests.codes.bad:
            logger.error(
                "Upload of the asset did fail with status_code %s",
                result["ResponseMetadata"]["HTTPStatusCode"],
            )
            return False
        return True

    def _ensure_object_storage_endpoint_is_supported(self, url):
        url_parts = urlsplit(url)
        if url_parts.scheme not in ("http", "https"):
            raise ValueError('Invalid value for "url"', url)


class ObjectStoragePortalReloader(ObjectStorageReloader):
    def __init__(
        self,
        json_path,
        assets_root_path,
        portal_dn,
        object_storage_endpoint,
        bucket,
        access_key_id,
        secret_access_key,
    ):
        logger.debug(
            "Initializing %s, in bucket %s at %s, assets_root_path: %s, portal_dn: %s",
            self.__class__.__name__,
            bucket,
            json_path,
            assets_root_path,
            portal_dn,
        )
        super().__init__(
            json_path,
            assets_root_path,
            object_storage_endpoint,
            bucket,
            access_key_id,
            secret_access_key,
        )
        self._portal_dn = portal_dn

    def _create_content_fetcher(self):
        # TODO: assets_root_path is not used in PortalContentFetcher, drop
        return reloader.PortalContentFetcher(self._portal_dn, self._assets_root_path)

    def _check_reason(self, reason=None):
        return reloader.check_portal_reason(reason)


class ObjectStorageGroupsReloader(ObjectStorageReloader):
    def __init__(
        self,
        json_path,
        assets_root_path,
        object_storage_endpoint,
        bucket,
        access_key_id,
        secret_access_key,
    ):
        logger.debug(
            "Initializing %s, in: %s, assets_root_path: %s",
            self.__class__.__name__,
            json_path,
            assets_root_path,
        )
        super().__init__(
            json_path,
            assets_root_path,
            object_storage_endpoint,
            bucket,
            access_key_id,
            secret_access_key,
        )

    def _create_content_fetcher(self):
        return reloader.GroupsContentFetcher()

    def _check_reason(self, reason=None):
        return reloader.check_groups_reason(reason)
