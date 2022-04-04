#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright 2020-2022 Univention GmbH
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

import pytest

from .conftest import import_lib_module

ucrLogrotate = import_lib_module("ucrLogrotate")


@pytest.fixture
def logrotate_ucr(mock_ucr):
	mock_ucr["logrotate/rotate"] = "weekly"
	mock_ucr["logrotate/rotate/count"] = "12"
	mock_ucr["logrotate/create"] = "640 root adm"
	mock_ucr["logrotate/missingok"] = "yes"
	mock_ucr["logrotate/compress"] = "yes"
	mock_ucr["logrotate/notifempty"] = "yes"
	return mock_ucr


class TestLogrotateConfig(object):
	def test_empty(self, mock_ucr):
		settings = ucrLogrotate.getLogrotateConfig("my-service", mock_ucr)
		assert settings["compress"] == "compress"
		assert settings["missingok"] == "missingok"
		assert settings["notifempty"] == "notifempty"
		assert len(settings) == 3

	def test_global(self, logrotate_ucr):
		settings = ucrLogrotate.getLogrotateConfig("my-service", logrotate_ucr)
		assert settings["rotate"] == "weekly"
		assert settings["rotate/count"] == "rotate 12"
		assert settings["create"] == "create 640 root adm"
		assert settings["compress"] == "compress"
		assert settings["missingok"] == "missingok"
		assert settings["notifempty"] == "notifempty"
		assert len(settings) == 6

	def test_global_modified(self, logrotate_ucr):
		logrotate_ucr["logrotate/compress"] = "off"
		logrotate_ucr["logrotate/missingok"] = "disabled"
		logrotate_ucr["logrotate/notifempty"] = "no"
		settings = ucrLogrotate.getLogrotateConfig("my-service", logrotate_ucr)
		assert settings["rotate"] == "weekly"
		assert settings["rotate/count"] == "rotate 12"
		assert settings["create"] == "create 640 root adm"
		assert len(settings) == 3

	def test_specific_rotate(self, logrotate_ucr):
		logrotate_ucr["logrotate/my-service/rotate"] = "daily"
		logrotate_ucr["logrotate/my-other-service/rotate"] = "monthly"
		settings = ucrLogrotate.getLogrotateConfig("my-service", logrotate_ucr)
		assert settings["rotate"] == "daily"
		assert settings["rotate/count"] == "rotate 12"
		assert settings["create"] == "create 640 root adm"
		assert settings["compress"] == "compress"
		assert settings["missingok"] == "missingok"
		assert settings["notifempty"] == "notifempty"
		assert len(settings) == 6

	def test_specific_rotate_count(self, logrotate_ucr):
		logrotate_ucr["logrotate/my-service/rotate/count"] = "4"
		logrotate_ucr["logrotate/my-other-service/rotate/count"] = "8"
		settings = ucrLogrotate.getLogrotateConfig("my-service", logrotate_ucr)
		assert settings["rotate"] == "weekly"
		assert settings["rotate/count"] == "rotate 4"
		assert settings["create"] == "create 640 root adm"
		assert settings["compress"] == "compress"
		assert settings["missingok"] == "missingok"
		assert settings["notifempty"] == "notifempty"
		assert len(settings) == 6

	def test_specific_create(self, logrotate_ucr):
		logrotate_ucr["logrotate/my-service/create"] = "660 root root"
		logrotate_ucr["logrotate/my-other-service/create"] = "640 nobody nogroup"
		settings = ucrLogrotate.getLogrotateConfig("my-service", logrotate_ucr)
		assert settings["rotate"] == "weekly"
		assert settings["rotate/count"] == "rotate 12"
		assert settings["create"] == "create 660 root root"
		assert settings["compress"] == "compress"
		assert settings["missingok"] == "missingok"
		assert settings["notifempty"] == "notifempty"
		assert len(settings) == 6

	def test_specific_compress(self, logrotate_ucr):
		logrotate_ucr["logrotate/my-service/compress"] = "no"
		logrotate_ucr["logrotate/my-other-service/compress"] = "yes"
		settings = ucrLogrotate.getLogrotateConfig("my-service", logrotate_ucr)
		assert settings["rotate"] == "weekly"
		assert settings["rotate/count"] == "rotate 12"
		assert settings["create"] == "create 640 root adm"
		assert settings["missingok"] == "missingok"
		assert settings["notifempty"] == "notifempty"
		assert len(settings) == 5

	def test_specific_missing_ok(self, logrotate_ucr):
		logrotate_ucr["logrotate/my-service/missingok"] = "no"
		logrotate_ucr["logrotate/my-other-service/missingok"] = "yes"
		settings = ucrLogrotate.getLogrotateConfig("my-service", logrotate_ucr)
		assert settings["rotate"] == "weekly"
		assert settings["rotate/count"] == "rotate 12"
		assert settings["create"] == "create 640 root adm"
		assert settings["compress"] == "compress"
		assert settings["notifempty"] == "notifempty"
		assert len(settings) == 5

	def test_specific_notifempty(self, logrotate_ucr):
		logrotate_ucr["logrotate/my-service/notifempty"] = "no"
		logrotate_ucr["logrotate/my-other-service/notifempty"] = "yes"
		settings = ucrLogrotate.getLogrotateConfig("my-service", logrotate_ucr)
		assert settings["rotate"] == "weekly"
		assert settings["rotate/count"] == "rotate 12"
		assert settings["create"] == "create 640 root adm"
		assert settings["compress"] == "compress"
		assert settings["missingok"] == "missingok"
		assert len(settings) == 5

	def test_specific_notifempty_modified(self, logrotate_ucr):
		logrotate_ucr["logrotate/notifempty"] = "no"
		logrotate_ucr["logrotate/my-service/notifempty"] = "yes"
		settings = ucrLogrotate.getLogrotateConfig("my-service", logrotate_ucr)
		assert settings["rotate"] == "weekly"
		assert settings["rotate/count"] == "rotate 12"
		assert settings["create"] == "create 640 root adm"
		assert settings["compress"] == "compress"
		assert settings["missingok"] == "missingok"
		assert settings["notifempty"] == "notifempty"
		assert len(settings) == 6
