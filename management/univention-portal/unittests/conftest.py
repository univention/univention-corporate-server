#!/usr/bin/python3
#
# Univention Portal
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2020-2023 Univention GmbH
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

from importlib import reload
from os import path

import pytest


@pytest.fixture()
def dynamic_class():
    from univention import portal
    return portal.get_dynamic_classes


# Helper function fixtures


@pytest.fixture()
def patch_object_module(mocker):
    """Helper to patch module level library imports of an object or class"""

    def _(obj, module_name):
        return mocker.patch(f"{obj.__module__}.{module_name}")

    return _


@pytest.fixture()
def get_file_path(request):
    """Helper to get the absolute path of test files in the unittests directory"""
    unittest_path = request.fspath.dirname
    files_directory = "files"

    def _(file_name):
        return path.join(unittest_path, files_directory, file_name)

    return _


@pytest.fixture()
def mock_portal_config(mocker):
    """Returns a callable which can be used to inject configuration values."""
    from univention.portal import config

    reload(config)
    mocker.patch.object(config.load, "never_loaded", False)

    def _mock_portal_config(values):
        mocker.patch.object(config, "_DB", values)

    return _mock_portal_config


@pytest.fixture()
def mocked_portal_config(get_file_path):
    from univention.portal import config

    reload(config)
    config._CONF = get_file_path("config*.json")
    return config
