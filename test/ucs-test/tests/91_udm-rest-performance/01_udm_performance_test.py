#!/usr/share/ucs-test/runner /usr/bin/pytest-3 -l -v
## -*- coding: utf-8 -*-
## desc: check performance of udm
## tags: [univention-drirectory-manager-modules]
## exposure: dangerous
import copy
import os

import pytest
from conftest import DEFAULT_HOST, ENV_LOCUST_DEFAULTS, LOCUST_FILES_DIR, RESULT_DIR, set_locust_environment_vars


@pytest.fixture(scope="module")
def create_result_dir():
    if not os.path.exists(RESULT_DIR):
        os.makedirs(RESULT_DIR)


@pytest.fixture(scope="module")
def run_test(execute_test, verify_test_sent_requests, create_result_dir):
    def _run_test(locust_file, locust_user_class, locust_run_time, result_file_base_path):
        LOCUST_FILE_PATH = os.path.join(LOCUST_FILES_DIR, locust_file)
        LOCUST_ENV_VARIABLES = copy.deepcopy(ENV_LOCUST_DEFAULTS)
        LOCUST_ENV_VARIABLES["LOCUST_RUN_TIME"] = locust_run_time
        set_locust_environment_vars(LOCUST_ENV_VARIABLES)
        execute_test(LOCUST_FILE_PATH, locust_user_class, result_file_base_path, 'https://' + DEFAULT_HOST)
        verify_test_sent_requests(result_file_base_path)
    return _run_test


@pytest.mark.parametrize("locust_file, locust_user_class, url_name, locust_run_time, rps, time_95_percentile", [
    ('udm_computers_domaincontroller_slave_locust_user.py', 'ComputersDomaincontrollerSlaveGet', '/univention/udm/computers/domaincontroller/slave', '1m', 0.5, 2000),
    ('udm_computers_domaincontroller_slave_locust_user.py', 'ComputersDomaincontrollerSlavePost', '/univention/udm/computers/domaincontroller/slave', '1m', 0.5, 2000),
    ('udm_computers_domaincontroller_slave_locust_user.py', 'ComputersDomaincontrollerSlaveAddGet', '/univention/udm/computers/domaincontroller/slave/add', '1m', 0.5, 2000),
    ('udm_computers_domaincontroller_slave_locust_user.py', 'ComputersDomaincontrollerSlaveDnGet', '/univention/udm/computers/domaincontroller/slave/dn', '1m', 0.5, 2000),
    ('udm_computers_domaincontroller_slave_locust_user.py', 'ComputersDomaincontrollerSlaveDnDelete', '/univention/udm/computers/domaincontroller/slave/dn', '1m', 0.5, 2000),
    ('udm_computers_domaincontroller_slave_locust_user.py', 'ComputersDomaincontrollerSlaveDnPut', '/univention/udm/computers/domaincontroller/slave/dn', '1m', 0.5, 2000),
    ('udm_computers_domaincontroller_slave_locust_user.py', 'ComputersDomaincontrollerSlaveDnPatch', '/univention/udm/computers/domaincontroller/slave/dn', '1m', 0.5, 2000),
    ('udm_container_ou_locust_user.py', 'ContainerOuGet', '/univention/udm/container/ou', '1m', 0.5, 2000),
    ('udm_container_ou_locust_user.py', 'ContainerOuPost', '/univention/udm/container/ou', '1m', 0.5, 2000),
    ('udm_container_ou_locust_user.py', 'ContainerOuAddGet', '/univention/udm/container/ou/add', '1m', 0.5, 2000),
    ('udm_container_ou_locust_user.py', 'ContainerOuDnGet', '/univention/udm/container/ou/dn', '1m', 0.5, 2000),
    ('udm_container_ou_locust_user.py', 'ContainerOuDnDelete', '/univention/udm/container/ou/dn', '1m', 0.5, 2000),
    ('udm_container_ou_locust_user.py', 'ContainerOuDnPut', '/univention/udm/container/ou/dn', '1m', 0.5, 2000),
    ('udm_container_ou_locust_user.py', 'ContainerOuDnPatch', '/univention/udm/container/ou/dn', '1m', 0.5, 2000),
    ('udm_groups_group_locust_user.py', 'GroupsGroupGet', '/univention/udm/groups/group', '1m', 0.5, 2000),
    ('udm_groups_group_locust_user.py', 'GroupsGroupPost', '/univention/udm/groups/group', '1m', 0.5, 2000),
    ('udm_groups_group_locust_user.py', 'GroupsGroupAddGet', '/univention/udm/groups/group/add', '1m', 0.5, 2000),
    ('udm_groups_group_locust_user.py', 'GroupsGroupDnGet', '/univention/udm/groups/group/dn', '1m', 0.5, 2000),
    ('udm_groups_group_locust_user.py', 'GroupsGroupDnDelete', '/univention/udm/groups/group/dn', '1m', 0.5, 2000),
    ('udm_groups_group_locust_user.py', 'GroupsGroupDnPut', '/univention/udm/groups/group/dn', '1m', 0.5, 2000),
    ('udm_groups_group_locust_user.py', 'GroupsGroupDnPatch', '/univention/udm/groups/group/dn', '1m', 0.5, 2000),
    ('udm_users_user_locust_user.py', 'UsersUserGet', '/univention/udm/users/user', '1m', 0.5, 2000),
    ('udm_users_user_locust_user.py', 'UsersUserPost', '/univention/udm/users/user', '1m', 0.5, 2000),
    ('udm_users_user_locust_user.py', 'UsersUserAddGet', '/univention/udm/users/user/add', '1m', 0.5, 2000),
    ('udm_users_user_locust_user.py', 'UsersUserDnGet', '/univention/udm/users/user/dn', '1m', 0.5, 2000),
    ('udm_users_user_locust_user.py', 'UsersUserDnDelete', '/univention/udm/users/user/dn', '1m', 0.5, 2000),
    ('udm_users_user_locust_user.py', 'UsersUserDnPut', '/univention/udm/users/user/dn', '1m', 0.5, 2000),
    ('udm_users_user_locust_user.py', 'UsersUserDnPatch', '/univention/udm/users/user/dn', '1m', 0.5, 2000),
])
def test_udm_performance(run_test, check_failure_count, check_rps, check_95_percentile, locust_file, locust_user_class, url_name, locust_run_time, rps, time_95_percentile):
    result_file_base_path = os.path.join(RESULT_DIR, "udm-" + locust_user_class)
    run_test(locust_file, locust_user_class, locust_run_time, result_file_base_path)
    check_failure_count(result_file_base_path)
    check_rps(result_file_base_path, url_name, rps)
    check_95_percentile(result_file_base_path, url_name, time_95_percentile)
