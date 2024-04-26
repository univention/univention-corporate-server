# SPDX-FileCopyrightText: 2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import datetime
import json
import logging
import os
import socket
import subprocess

import requests.packages.urllib3.util.connection as urllib3_cn
import urllib3
import utils
from locust import events, stats
from locust.runners import MasterRunner
from locust_jmeter_listener import JmeterListener


LOCUST_EXPECT_WORKERS = int(os.environ.get('EXPECT_WORKERS', '1'))
stats.MODERN_UI_PERCENTILES_TO_CHART = [0.66, 0.75, 0.80, 0.90, 0.95, 0.99]
stats.PERCENTILES_TO_STATISTICS = [0.66, 0.75, 0.80, 0.90, 0.95, 0.99]


def allowed_gai_family() -> socket.AddressFamily:
    """https://github.com/shazow/urllib3/blob/master/urllib3/util/connection.py"""
    family = socket.AF_INET
    # python requests tries IPv6 first, which can result in weird timings -> disable it for now
    # if urllib3_cn.HAS_IPV6:
    #     family = socket.AF_INET6 # force ipv6 only if it is available
    return family


urllib3_cn.allowed_gai_family = allowed_gai_family
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@events.init.add_listener
def on_locust_init(environment, **_kwargs):
    environment.stats.use_response_times_cache = True
    JmeterListener(environment, results_filename=f"/root/results_{datetime.datetime.now():%Y_%m_%d_%H_%M_%S}.csv")


@events.test_start.add_listener
def on_test_start(**kwargs) -> None:
    host_name = os.environ.get('HOSTNAME', None)
    if isinstance(kwargs['environment'].runner, MasterRunner) or not host_name:
        return

    try:
        worker_name = json.loads(subprocess.check_output(['curl', '-s', '--unix-socket', '/var/run/docker.sock', f'http://docker/containers/{host_name}/json']))
        worker_number = int(worker_name['Name'].rsplit('_', 1)[-1])
    except ValueError:
        worker_number = int(os.getenv('WORKER_NUMBER', '1'))

    total_n_users = utils.final_user
    users_per_worker = total_n_users // LOCUST_EXPECT_WORKERS
    utils.start_user = users_per_worker * (worker_number - 1)
    utils.current_user = utils.start_user
    utils.final_user = users_per_worker * worker_number
    logging.info(
        '%s', f'Worker {worker_number} of {LOCUST_EXPECT_WORKERS} with {users_per_worker} users from {users_per_worker * (worker_number - 1)} to {users_per_worker * worker_number}'
    )
