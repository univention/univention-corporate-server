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


import json
from io import StringIO
from unittest.mock import Mock, patch

import boto3
import pytest
from botocore.response import StreamingBody
from botocore.stub import Stubber


UCS_INTERNAL_PATH = "portal-data"
PORTAL_DATA_KEYS = [
    "portal",
    "entries",
    "folders",
    "categories",
    "user_links",
    "menu_links",
]
PORTAL_DATA = {key: key for key in PORTAL_DATA_KEYS}
GROUPS_DATA = {"username": ["list", "of", "groups"]}


@pytest.mark.parametrize(
    "class_name",
    [
        "CacheObjectStorage",
        "PortalFileCacheObjectStorage",
        "GroupFileCacheObjectStorage",
    ],
)
def test_import(class_name, dynamic_class):
    assert dynamic_class(class_name)


@pytest.mark.parametrize(
    "class_name,path,data,data_keys",
    [
        (
            "PortalFileCacheObjectStorage",
            f"{UCS_INTERNAL_PATH}/portal",
            PORTAL_DATA,
            PORTAL_DATA_KEYS,
        ),
        ("GroupFileCacheObjectStorage", f"{UCS_INTERNAL_PATH}/groups", GROUPS_DATA, []),
    ],
)
@patch(
    "univention.portal.extensions.cache_object_storage.get_object_storage_client",
    Mock(return_value=boto3.client("s3")),
)
def test_portal_file_cache_object_storage(
    dynamic_class,
    class_name,
    path,
    data,
    data_keys,
):
    file_cache_object_storage = dynamic_class(
        class_name,
    )(
        path,
        "http://stub_endpoint",
        "stub_bucket",
        "stub_user",
        "stub_pass",
    )

    body_encoded = json.dumps(data)

    body = StreamingBody(StringIO(body_encoded), len(body_encoded))
    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": 200,
            "HTTPHeaders": {
                "accept-ranges": "bytes",
                "content-length": len(body_encoded),
                "content-type": "application/json",
            },
            "RetryAttempts": 0,
        },
        "AcceptRanges": "bytes",
        "ContentLength": len(body_encoded),
        "ContentType": "application/json",
        "Body": body,
    }

    with Stubber(file_cache_object_storage._object_storage_client) as stubber:
        stubber.add_response(
            "get_object",
            response,
            {"Bucket": file_cache_object_storage._bucket, "Key": path},
        )
        file_cache_object_storage.refresh()

    assert file_cache_object_storage.get() == data
    for item in data_keys:
        assert item == getattr(file_cache_object_storage, f"get_{item}")()
