#!/usr/bin/python3
#
# UCS Installer Tests
#
# SPDX-FileCopyrightText: 2017-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import configparser
from time import sleep

import pytest
from vminstall.utils import copy_through_ssh, execute_through_ssh, remove_old_sshkey


config = configparser.ConfigParser()
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
