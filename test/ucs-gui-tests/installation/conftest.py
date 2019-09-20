#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# UCS Installer Tests
#
# Copyright 2017 Univention GmbH
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

from time import sleep
from vminstall.utils import copy_through_ssh, execute_through_ssh, remove_old_sshkey
import ConfigParser
import pytest

config = ConfigParser.SafeConfigParser()
config.read('tests.cfg')


@pytest.fixture(scope="session", autouse=True)
def execute_before_any_test():
	remove_old_sshkeys()
	copy_out_logs()
	# UCS will launch an apt process after each boot. To avoid problems with
	# tests that use apt themselves this sleep() waits until the automatically
	# started apt process ended.
	sleep(40)


def copy_out_logs():
	ip = config.get('General', 'ip_address')
	password = config.get('General', 'password')

	execute_through_ssh(password, 'cd /var; tar czf log.tar.gz log', ip)
	copy_through_ssh(password, 'root@%s:/var/log.tar.gz' % (ip), '.')


def remove_old_sshkeys():
	ip = config.get('General', 'ip_address')
	master_ip = config.get('General', 'master_ip')
	remove_old_sshkey(ip)
	if master_ip:
		remove_old_sshkey(master_ip)


@pytest.fixture
def language():
	return config.get('General', 'language')


@pytest.fixture
def server():
	return config.get('General', 'server')


@pytest.fixture
def iso_image():
	return config.get('General', 'isoimage')


@pytest.fixture
def environment():
	return config.get('General', 'environment')


@pytest.fixture
def role():
	return config.get('General', 'role')


@pytest.fixture
def master_ip():
	return config.get('General', 'master_ip')


@pytest.fixture
def ip_address():
	return config.get('General', 'ip_address')


@pytest.fixture
def password():
	return config.get('General', 'password')
