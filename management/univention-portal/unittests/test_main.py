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

from unittest import mock

import pytest

from univention.portal.log import get_logger
from univention.portal.main import start_app


def test_start_app_configures_port(mock_portal_config):
    mock_portal_config({"port": 1234, "enable_xheaders": False})
    app = mock.Mock()

    start_app(app)

    app.listen.assert_called_with(1234, xheaders=mock.ANY)


@pytest.mark.parametrize("enable_xheaders", [False, True])
def test_start_app_xheaders(enable_xheaders, mock_portal_config):
    mock_portal_config({"port": 1234, "enable_xheaders": enable_xheaders})
    app = mock.Mock()

    start_app(app)

    app.listen.assert_called_with(mock.ANY, xheaders=enable_xheaders)


def test_start_app_logs_message_regarding_xheaders(mocker, mock_portal_config):
    mock_portal_config({"port": 1234, "enable_xheaders": True})
    app = mock.Mock()
    info_mock = mocker.patch.object(get_logger("server"), "info")

    start_app(app)

    xheader_messages = [c for c in info_mock.call_args_list if _call_contains_xheaders(c)]
    assert xheader_messages


def _call_contains_xheaders(call):
    args = call[0]
    return "xheaders" in args[0]
