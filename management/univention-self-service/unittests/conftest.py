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


import sys
import pytest
from six import get_method_self


@pytest.fixture
def mocked_conn(mocker, lo, pos):
	from univentionunittests.umc import import_umc_module
	selfservice = import_umc_module('passwordreset')
	mocker.patch.object(selfservice, 'get_admin_connection', return_value=[lo, pos])
	mocker.patch.object(selfservice, 'get_machine_connection', return_value=[lo, pos])
	import univention.management.console.ldap as umc_ldap
	mocker.patch.object(umc_ldap, '_getMachineConnection', return_value=[lo, pos])
	mocker.patch.object(umc_ldap, '_getAdminConnection', return_value=[lo, pos])
	yield
	get_method_self(umc_ldap.machine_connection).__dict__['_LDAP__ldap_connections'].clear()


@pytest.fixture
def selfservice_ucr(mocker, mocked_ucr):
	from univentionunittests.umc import import_umc_module
	from univention.config_registry import ConfigRegistry
	selfservice = import_umc_module('passwordreset')
	mocker.patch.object(selfservice, 'ucr', mocked_ucr)

	def inject_fake_ucr(self):
		self.clear()
		self.update(mocked_ucr.items)
	mocker.patch.object(ConfigRegistry, 'load', inject_fake_ucr)
	mocker.patch.object(ConfigRegistry, '__enter__', side_effect=ValueError("You may not save a faked UCR"))
	mocked_ucr['umc/self-service/enabled'] = 'yes'
	mocked_ucr['umc/self-service/passwordreset/email/enabled'] = 'yes'
	mocked_ucr['umc/self-service/account-deregistration/blacklist/groups'] = 'Administrators,Domain Admins'
	mocked_ucr['umc/self-service/account-deregistration/blacklist/users'] = ''
	mocked_ucr['umc/self-service/account-deregistration/whitelist/groups'] = 'Domain Users'
	mocked_ucr['umc/self-service/account-deregistration/whitelist/users'] = ''
	mocked_ucr['umc/self-service/passwordreset/blacklist/groups'] = 'Administrators,Domain Admins'
	mocked_ucr['umc/self-service/passwordreset/whitelist/groups'] = 'Domain Users'
	mocked_ucr['umc/self-service/profiledata/blacklist/groups'] = 'Administrators,Domain Admins'
	mocked_ucr['umc/self-service/profiledata/blacklist/users'] = ''
	mocked_ucr['umc/self-service/profiledata/whitelist/groups'] = 'Domain Users'
	mocked_ucr['umc/self-service/profiledata/whitelist/users'] = ''
	return mocked_ucr


@pytest.fixture
def selfservice_instance(umc_module_class, mocker):
	from univentionunittests.umc import import_umc_module, save_result_on_request
	selfservice = import_umc_module('passwordreset')
	send_plugin = import_umc_module('passwordreset.send_plugin', set_umc_module_fixture=False)
	mocker.patch.object(umc_module_class, 'finished', side_effect=save_result_on_request)
	mocker.patch.object(sys.modules[selfservice.get_sending_plugins.__module__], 'UniventionSelfServiceTokenEmitter', send_plugin.UniventionSelfServiceTokenEmitter)
	mod = umc_module_class()
	mod.init()
	return mod
