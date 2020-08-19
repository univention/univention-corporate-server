#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
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



def test_resolve(custom_apps, appcenter_umc_instance, get_action, umc_request, mocker):
	custom_apps.load('unittests/inis/umc/')
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
