#!/usr/bin/python2.7
#
# Univention Portal
#
# Copyright 2020 Univention GmbH
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

from os import path

import pytest
from univentionunittests import import_module


@pytest.fixture
def mocked_portal_config(portal_config, request):
	reload(portal_config)
	test_path = request.fspath.dirname
	portal_config._CONF = path.join(test_path, "configs", "*.json")
	return portal_config


def test_load_config_success(mocked_portal_config):
	# Set up
	mocked_portal_config._DB = {"old": "value"}
	expected_config = {
			"port": 8090,
			"fqdn": "dataport.ucs",
			"url": "http://127.0.0.1:8090",
			"test": True
		}
	# Execute
	assert mocked_portal_config.load.never_loaded == True
	mocked_portal_config.load()
	assert mocked_portal_config.load.never_loaded == False
	assert mocked_portal_config._DB == expected_config


def test_load_config_error(mocker, mocked_portal_config):
	# Set up
	mocked_portal_config._DB = {"old": "value"}
	open_mock = mocker.patch.object(mocked_portal_config, "open", side_effect=EnvironmentError)
	# Execute
	assert mocked_portal_config.load.never_loaded == True
	mocked_portal_config.load()
	assert mocked_portal_config._DB == {}
	assert mocked_portal_config.load.never_loaded == True
	assert mocked_portal_config._DB == {}


def test_fetch_key(mocker, mocked_portal_config):
	# Set up
	def config_loaded():
		mocked_portal_config.load.never_loaded = False
	load_mock = mocker.patch.object(mocked_portal_config, 'load', side_effect=config_loaded)
	mocked_portal_config.load.never_loaded == True
	mocked_portal_config._DB = {
		"port": 443,
		"fqdn": "dataport.ucs"
	}
	# Execute
	assert mocked_portal_config.fetch("port") == 443
	assert mocked_portal_config.load.never_loaded == False
	assert mocked_portal_config.fetch("fqdn") == "dataport.ucs"
	with pytest.raises(KeyError):
		mocked_portal_config.fetch("no_key")
	load_mock.assert_called_once()
