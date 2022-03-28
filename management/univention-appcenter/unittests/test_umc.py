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

import pytest

ANYTHING = object()


@pytest.fixture
def custom_apps_umc(custom_apps):
	custom_apps.load('unittests/inis/umc/')
	return custom_apps


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


class TestRiot(object):
	def test_resolve(self, mocked_ucr_appcenter, custom_apps_umc, appcenter_umc_instance, umc_request):
		umc_request.options = {'apps': ['riot'], 'action': 'install'}
		appcenter_umc_instance.resolve(umc_request)
		assert 'apps' in umc_request.result
		assert len(umc_request.result['apps']) == 1
		assert umc_request.result['apps'][0]['id'] == 'riot'
		assert 'autoinstalled' in umc_request.result
		assert [] == umc_request.result['autoinstalled']
		assert 'errors' in umc_request.result
		assert isinstance(umc_request.result['errors'], dict)
		assert 'warnings' in umc_request.result
		assert isinstance(umc_request.result['warnings'], dict)

	def test_dry_run(self, mocked_ucr_appcenter, custom_apps_umc, appcenter_umc_instance, umc_request, mocker):
		host = '{hostname}.{domainname}'.format(**mocked_ucr_appcenter)
		settings = {'riot/default/base_url': '/riot', 'riot/default/server_name': host}
		umc_request.options = {'apps': ['riot'], 'action': 'install', 'auto_installed': [], 'hosts': {'riot': host}, 'settings': {'riot': settings}, 'dry_run': True}
		mock = mocker.patch.object(appcenter_umc_instance, '_run_local_dry_run')
		mocker.patch.object(appcenter_umc_instance, '_run_local')
		mocker.patch.object(appcenter_umc_instance, '_run_remote_dry_run')
		mocker.patch.object(appcenter_umc_instance, '_run_remote')
		appcenter_umc_instance.run(umc_request)
		umc_request.progress(appcenter_umc_instance.progress)
		assert_called_with(mock, [(custom_apps_umc.find('riot'), 'install', settings, ANYTHING), {}])

	def test_run(self, mocked_ucr_appcenter, custom_apps_umc, appcenter_umc_instance, umc_request, mocker):
		host = '{hostname}.{domainname}'.format(**mocked_ucr_appcenter)
		settings = {'riot/default/base_url': '/riot', 'riot/default/server_name': host}
		umc_request.options = {'apps': ['riot'], 'action': 'install', 'auto_installed': [], 'hosts': {'riot': host}, 'settings': {'riot': settings}, 'dry_run': False}
		mocker.patch.object(appcenter_umc_instance, '_run_local_dry_run')
		mock = mocker.patch.object(appcenter_umc_instance, '_run_local')
		mocker.patch.object(appcenter_umc_instance, '_run_remote_dry_run')
		mocker.patch.object(appcenter_umc_instance, '_run_remote')
		appcenter_umc_instance.run(umc_request)
		umc_request.progress(appcenter_umc_instance.progress)
		assert_called_with(mock, [(custom_apps_umc.find('riot'), 'install', settings, ANYTHING), {}])


class TestKopano(object):
	def test_resolve(self, mocked_ucr_appcenter, custom_apps_umc, appcenter_umc_instance, umc_request):
		umc_request.options = {'apps': ['kopano-webapp'], 'action': 'install'}
		appcenter_umc_instance.resolve(umc_request)
		assert 'apps' in umc_request.result
		assert len(umc_request.result['apps']) == 2
		assert umc_request.result['apps'][0]['id'] == 'kopano-core'
		assert 'autoinstalled' in umc_request.result
		assert ['kopano-core'] == umc_request.result['autoinstalled']
		assert 'errors' in umc_request.result
		assert isinstance(umc_request.result['errors'], dict)
		assert 'warnings' in umc_request.result
		assert isinstance(umc_request.result['warnings'], dict)

	def test_dry_run(self, mocked_ucr_appcenter, custom_apps_umc, appcenter_umc_instance, umc_request, mocker):
		host = '{hostname}-fake.{domainname}'.format(**mocked_ucr_appcenter)
		localhost = '{hostname}.{domainname}'.format(**mocked_ucr_appcenter)
		umc_request.options = {'apps': ['kopano-webapp', 'kopano-core'], 'action': 'install', 'auto_installed': ['kopano-core'], 'hosts': {'kopano-webapp': localhost, 'kopano-core': host}, 'settings': {'kopano-core': {}, 'kopano-webapp': {}}, 'dry_run': True}
		mock1 = mocker.patch.object(appcenter_umc_instance, '_run_local_dry_run')
		mocker.patch.object(appcenter_umc_instance, '_run_local')
		mock2 = mocker.patch.object(appcenter_umc_instance, '_run_remote_dry_run')
		mocker.patch.object(appcenter_umc_instance, '_run_remote')
		appcenter_umc_instance.run(umc_request)
		umc_request.progress(appcenter_umc_instance.progress)
		assert_called_with(mock1, [(custom_apps_umc.find('kopano-webapp'), 'install', {}, ANYTHING), {}])
		assert_called_with(mock2, [(host, custom_apps_umc.find('kopano-core'), 'install', True, {}, ANYTHING), {}])

	def test_run(self, mocked_ucr_appcenter, custom_apps_umc, appcenter_umc_instance, umc_request, mocker):
		host = '{hostname}-fake.{domainname}'.format(**mocked_ucr_appcenter)
		localhost = '{hostname}.{domainname}'.format(**mocked_ucr_appcenter)
		umc_request.options = {'apps': ['kopano-webapp', 'kopano-core'], 'action': 'install', 'auto_installed': ['kopano-core'], 'hosts': {'kopano-webapp': localhost, 'kopano-core': host}, 'settings': {'kopano-core': {}, 'kopano-webapp': {}}, 'dry_run': False}
		mocker.patch.object(appcenter_umc_instance, '_run_local_dry_run')
		mock1 = mocker.patch.object(appcenter_umc_instance, '_run_local')
		mocker.patch.object(appcenter_umc_instance, '_run_remote_dry_run')
		mock2 = mocker.patch.object(appcenter_umc_instance, '_run_remote')
		appcenter_umc_instance.run(umc_request)
		umc_request.progress(appcenter_umc_instance.progress)
		assert_called_with(mock1, [(custom_apps_umc.find('kopano-webapp'), 'install', {}, ANYTHING), {}])
		assert_called_with(mock2, [(host, custom_apps_umc.find('kopano-core'), 'install', True, {}, ANYTHING), {}])


class TestUCSSchool(object):
	def test_resolve(self, mocked_ucr_appcenter, custom_apps_umc, appcenter_umc_instance, umc_request):
		umc_request.options = {'apps': ['ucsschool-kelvin-rest-api', 'ucsschool'], 'action': 'install'}
		appcenter_umc_instance.resolve(umc_request)
		assert 'apps' in umc_request.result
		assert len(umc_request.result['apps']) == 2
		assert umc_request.result['apps'][0]['id'] == 'ucsschool'
		assert 'autoinstalled' in umc_request.result
		assert [] == umc_request.result['autoinstalled']
		assert 'errors' in umc_request.result
		assert isinstance(umc_request.result['errors'], dict)
		assert 'warnings' in umc_request.result
		assert isinstance(umc_request.result['warnings'], dict)

	def test_dry_run(self, mocked_ucr_appcenter, custom_apps_umc, appcenter_umc_instance, umc_request, mocker):
		host = '{hostname}.{domainname}'.format(**mocked_ucr_appcenter)
		settings_ucsschool = {'ucsschool/join/create_demo': False}
		settings_kelvin = {'ucsschool/kelvin/access_tokel_ttl': 60, 'ucsschool/kelvin/log_level': 'DEBUG'}
		umc_request.options = {'apps': ['ucsschool', 'ucsschool-kelvin-rest-api'], 'action': 'install', 'auto_installed': [], 'hosts': {'ucsschool': host, 'ucsschool-kelvin-rest-api': host}, 'settings': {'ucsschool': settings_ucsschool, 'ucsschool-kelvin-rest-api': settings_kelvin}, 'dry_run': True}
		mock = mocker.patch.object(appcenter_umc_instance, '_run_local_dry_run')
		mocker.patch.object(appcenter_umc_instance, '_run_local')
		mocker.patch.object(appcenter_umc_instance, '_run_remote_dry_run')
		mocker.patch.object(appcenter_umc_instance, '_run_remote')
		appcenter_umc_instance.run(umc_request)
		umc_request.progress(appcenter_umc_instance.progress)
		assert_called_with(
			mock,
			[(custom_apps_umc.find('ucsschool'), 'install', settings_ucsschool, ANYTHING), {}],
			[(custom_apps_umc.find('ucsschool-kelvin-rest-api'), 'install', settings_kelvin, ANYTHING), {}],
		)

	def test_run(self, mocked_ucr_appcenter, custom_apps_umc, appcenter_umc_instance, umc_request, mocker):
		host = '{hostname}.{domainname}'.format(**mocked_ucr_appcenter)
		settings_ucsschool = {'ucsschool/join/create_demo': False}
		settings_kelvin = {'ucsschool/kelvin/access_tokel_ttl': 60, 'ucsschool/kelvin/log_level': 'DEBUG'}
		umc_request.options = {'apps': ['ucsschool', 'ucsschool-kelvin-rest-api'], 'action': 'install', 'auto_installed': [], 'hosts': {'ucsschool': host, 'ucsschool-kelvin-rest-api': host}, 'settings': {'ucsschool': settings_ucsschool, 'ucsschool-kelvin-rest-api': settings_kelvin}, 'dry_run': False}
		mocker.patch.object(appcenter_umc_instance, '_run_local_dry_run')
		mock = mocker.patch.object(appcenter_umc_instance, '_run_local')
		mocker.patch.object(appcenter_umc_instance, '_run_remote_dry_run')
		mocker.patch.object(appcenter_umc_instance, '_run_remote')
		appcenter_umc_instance.run(umc_request)
		umc_request.progress(appcenter_umc_instance.progress)
		assert_called_with(
			mock,
			[(custom_apps_umc.find('ucsschool'), 'install', settings_ucsschool, ANYTHING), {}],
			[(custom_apps_umc.find('ucsschool-kelvin-rest-api'), 'install', settings_kelvin, ANYTHING), {}],
		)
