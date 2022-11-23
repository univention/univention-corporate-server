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
    ('udm_users_user_locust_user.py', 'UsersUserGet', '/users/user/', '2m', 0.5, 2000),
    ('udm_users_user_locust_user.py', 'UsersUserPost', '/users/user/', '2m', 0.5, 2000),
    ('udm_users_user_locust_user.py', 'UsersUserAddGet', '/users/user/add', '2m', 0.5, 2000),
    ('udm_users_user_locust_user.py', 'UsersUserDnGet', '/users/user/{dn}', '2m', 0.5, 2000),
    ('udm_users_user_locust_user.py', 'UsersUserDnDeleteStudent', '/users/user/{dn_student}', '2m', 0.5, 2000),
    ('udm_users_user_locust_user.py', 'UsersUserDnDeleteTeacher', '/users/user/{dn_teacher}', '2m', 0.5, 2000),
    ('udm_users_user_locust_user.py', 'UsersUserDnDeleteStaff', '/users/user/{dn_staff}', '2m', 0.5, 2000),
    ('udm_users_user_locust_user.py', 'UsersUserDnPut', '/users/user/{dn}', '2m', 0.5, 2000),
    ('udm_users_user_locust_user.py', 'UsersUserDnPatch', '/users/user/{dn}', '2m', 0.5, 2000),
    ('udm_groups_group_locust_user.py', 'GroupsGroupGet', '/groups/group/', '2m', 0.5, 2000),
    ('udm_groups_group_locust_user.py', 'GroupsGroupPost', '/groups/group/', '2m', 0.5, 2000),
    ('udm_groups_group_locust_user.py', 'GroupsGroupAddGet', '/groups/group/add', '2m', 0.5, 2000),
    ('udm_groups_group_locust_user.py', 'GroupsGroupDnGet', '/groups/group/{dn}', '2m', 0.5, 2000),
    ('udm_groups_group_locust_user.py', 'GroupsGroupDnDelete', '/groups/group/{dn}', '2m', 0.5, 2000),
    ('udm_groups_group_locust_user.py', 'GroupsGroupDnPut', '/groups/group/{dn}', '2m', 0.5, 2000),
    ('udm_groups_group_locust_user.py', 'GroupsGroupDnPatch', '/groups/group/{dn}', '2m', 0.5, 2000),
    ('udm_container_ou_locust_user.py', 'ContainerOuGet', '/container/ou/', '2m', 0.5, 2000),
    ('udm_container_ou_locust_user.py', 'ContainerOuPost', '/container/ou/', '2m', 0.5, 2000),
    ('udm_container_ou_locust_user.py', 'ContainerOuAddGet', '/container/ou/add', '2m', 0.5, 2000),
    ('udm_container_ou_locust_user.py', 'ContainerOuDnGet', '/container/ou/{dn}', '2m', 0.5, 2000),
    ('udm_container_ou_locust_user.py', 'ContainerOuDnDelete', '/container/ou/{dn}', '2m', 0.5, 2000),
    ('udm_container_ou_locust_user.py', 'ContainerOuDnPut', '/container/ou/{dn}', '2m', 0.5, 2000),
    ('udm_container_ou_locust_user.py', 'ContainerOuDnPatch', '/container/ou/{dn}', '2m', 0.5, 2000),
    ('udm_computers_domaincontroller_slave_locust_user.py', 'ComputersDomaincontrollerSlaveGet', '/computers/domaincontroller_slave/', '2m', 0.5, 2000),
    ('udm_computers_domaincontroller_slave_locust_user.py', 'ComputersDomaincontrollerSlavePost', '/computers/domaincontroller_slave/', '2m', 0.5, 2000),
    ('udm_computers_domaincontroller_slave_locust_user.py', 'ComputersDomaincontrollerSlaveAddGet', '/computers/domaincontroller_slave/add', '2m', 0.5, 2000),
    ('udm_computers_domaincontroller_slave_locust_user.py', 'ComputersDomaincontrollerSlaveDnGet', '/computers/domaincontroller_slave/{dn}', '2m', 0.5, 2000),
    ('udm_computers_domaincontroller_slave_locust_user.py', 'ComputersDomaincontrollerSlaveDnDelete', '/computers/domaincontroller_slave/{dn}', '2m', 0.5, 2000),
    ('udm_computers_domaincontroller_slave_locust_user.py', 'ComputersDomaincontrollerSlaveDnPut', '/computers/domaincontroller_slave/{dn}', '2m', 0.5, 2000),
    ('udm_computers_domaincontroller_slave_locust_user.py', 'ComputersDomaincontrollerSlaveDnPatch', '/computers/domaincontroller_slave/{dn}', '2m', 0.5, 2000),
])
def test_udm_performance(run_test, check_failure_count, check_rps, check_95_percentile, locust_file, locust_user_class, url_name, locust_run_time, rps, time_95_percentile):
    result_file_base_path = os.path.join(RESULT_DIR, "udm-" + locust_user_class)
    run_test(locust_file, locust_user_class, locust_run_time, result_file_base_path)
    check_failure_count(result_file_base_path)
    check_rps(result_file_base_path, url_name, rps)
    check_95_percentile(result_file_base_path, url_name, time_95_percentile)
