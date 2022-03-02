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
#


ANYTHING = object()


def assert_called_with(mock, *argss):
	assert mock.call_count == len(argss)
	for call, (args, kwargs) in zip(mock.call_args_list, argss):
		call = call.call_list()
		assert len(call[0][0]) == len(args)
		assert len(call[0][1]) == len(kwargs)
		for call_arg, assert_arg in zip(call[0][0], args):
			if assert_arg is ANYTHING:
				continue
			assert call_arg == assert_arg
		for key, assert_arg in kwargs.items():
			call_arg = call[0][1][key]
			if assert_arg is ANYTHING:
				continue
			assert call_arg == assert_arg


def test_install_two_apps(get_action, custom_apps, mocked_ucr, mocker):
	custom_apps.load('unittests/inis/dependencies')
	app1 = custom_apps.find('self-service')
	app2 = custom_apps.find('kopano-webapp')
	app3 = custom_apps.find('self-service-backend')
	app4 = custom_apps.find('kopano-core')
	for app in [app1, app2, app3, app4]:
		mocker.patch.object(app, 'is_installed', return_value=False)
	install = get_action('install')
	mock_do_it = mocker.patch.object(install, '_do_it')
	mock_send_information = mocker.patch.object(install, '_send_information')
	install.call(app=[app1, app2], noninteractive=True)
	assert_called_with(mock_send_information, ([app3, 200, None], {}), ([app1, 200, None], {}), ([app4, 200, None], {}), ([app2, 200, None], {}))
	assert_called_with(mock_do_it, ([app3, ANYTHING], {}), ([app1, ANYTHING], {}), ([app4, ANYTHING], {}), ([app2, ANYTHING], {}))
