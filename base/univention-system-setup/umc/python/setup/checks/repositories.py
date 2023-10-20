import subprocess
from os import environ
from typing import Iterable, List, Tuple

import univention.config_registry
from univention.management.console.log import MODULE


UCR = univention.config_registry.ConfigRegistry()
UCR.load()

PROXY_MAP = {
    "http_proxy": 'proxy/http',
    "https_proxy": 'proxy/https',
    "no_proxy": 'proxy/no_proxy',
}


def get_unreachable_repository_servers() -> List[str]:
    UCR.load()

    servers = [
        UCR.get('repository/online/server'),
        UCR.get('repository/app_center/server'),
        'docker.software-univention.de',
    ]

    processes = start_curl_processes(servers)
    wait_for_processes_to_finish(processes)
    log_warnings_about_unreachable_repository_servers(zip(servers, processes))
    return [server for server, process in zip(servers, processes) if process.returncode != 0]


def start_curl_processes(servers: Iterable[str]) -> List[subprocess.Popen]:
    ENV = {
        envvar: UCR[ucrvar]
        for (envvar, ucrvar) in PROXY_MAP.items()
        if ucrvar in UCR
    }
    env = dict(environ, **ENV)
    return [
        subprocess.Popen(['curl', '--max-time', '10', server], env=env)
        for server in servers
    ]


def wait_for_processes_to_finish(processes: Iterable[subprocess.Popen]) -> None:
    for process in processes:
        process.wait()


def log_warnings_about_unreachable_repository_servers(servers_with_curl_processes: Iterable[Tuple[str, subprocess.Popen]]) -> None:
    for server, process in servers_with_curl_processes:
        if process.returncode != 0:
            MODULE.warn(
                # FIXME: When changing to Python 3 use process.args here.
                f"'curl --max-time 10 {server}' exited with returncode {process.returncode}.",
            )
