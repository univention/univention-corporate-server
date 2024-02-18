#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import subprocess
from os import environ
from pipes import quote
from typing import Iterable, Iterator, List, Tuple, cast

from univention.config_registry import ucr_live as UCR
from univention.management.console.log import MODULE


PROXY_MAP = {
    "http_proxy": 'proxy/http',
    "https_proxy": 'proxy/https',
    "no_proxy": 'proxy/no_proxy',
}


def get_unreachable_repository_servers() -> List[str]:
    """
    Start a process to check the reachability of important servers.

    Servers:
    * UCS repository server (`repository/online/server`)
    * App server (`repository/app_center/server`)
    * `docker.software-univention.de`

    :returns: List of URLs.
    """
    servers = [
        UCR.get('repository/online/server'),
        UCR.get('repository/app_center/server'),
        'docker.software-univention.de',
    ]

    processes = list(start_curl_processes(servers))
    wait_for_processes_to_finish(processes)
    log_warnings_about_unreachable_repository_servers(zip(servers, processes))
    return [server for server, process in zip(servers, processes) if process.returncode != 0]


def start_curl_processes(servers: Iterable[str]) -> Iterator[subprocess.Popen]:
    """
    Start a :command:`curl` process to check the reachability of important servers.process

    :param servers: List of URLs to check.
    :returns: List of processes.
    """
    ENV = {
        envvar: UCR[ucrvar]
        for (envvar, ucrvar) in PROXY_MAP.items()
        if ucrvar in UCR
    }
    env = dict(environ, **ENV)
    for server in servers:
        cmd = ['curl', '--max-time', '10', '--silent', '--show-error', '--head', server]
        yield subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)


def wait_for_processes_to_finish(processes: Iterable[subprocess.Popen]) -> None:
    """
    Wait until all processes have finished.

    :param processes: List of processes.
    """
    for process in processes:
        process.wait()


def log_warnings_about_unreachable_repository_servers(servers_with_curl_processes: Iterable[Tuple[str, subprocess.Popen]]) -> None:
    """
    Log a message for all failed processes.

    :param processes: List of 2-tuples (URL, process)
    """
    for server, process in servers_with_curl_processes:
        if process.returncode != 0:
            stdout, _strerr = process.communicate()
            MODULE.warn(
                "'%s' exited with returncode %s: %s" % (
                    " ".join(quote(arg) for arg in cast(Iterable[str], process.args)),
                    process.returncode,
                    stdout.decode(errors="replace"),
                ),
            )
