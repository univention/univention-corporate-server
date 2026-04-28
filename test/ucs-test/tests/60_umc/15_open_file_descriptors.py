#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Tests open file descriptors in UMC
## roles:
##  - domaincontroller_master
## bugs:
##  - 52274
##  - 59220
## packages:
##  - univention-directory-manager-tools
##  - univention-management-console
## exposure: dangerous

import math
import subprocess
from collections.abc import Callable
from time import sleep

import psutil
import pytest

from univention.lib.umc import Unauthorized
from univention.testing import ucr as _ucr
from univention.testing.ucr import UCSTestConfigRegistry
from univention.testing.udm import UCSTestUDM
from univention.testing.umc import Client


def pidof(name: str) -> int | None:
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        if p.info['name'] == name or any(name in arg for arg in p.info['cmdline']):
            return p.info['pid']
    return None


def lsof(pid: int) -> str:
    cmd = ["lsof", "-p", str(pid)]
    return subprocess.check_output(cmd).decode('utf-8')


def number_openfiles_type_stream(service: str) -> int:
    pid = pidof(service)
    open_files = lsof(pid).split('\n')
    return len([x for x in open_files if "type=STREAM" in x])


def get_limit_max_open_files(pid: int) -> tuple[int, int]:
    with open(f"/proc/{pid!s}/limits") as fh:
        for line in fh.readlines():
            print(line)
            if "Max open files" in line:
                parts = line.split()
                return int(parts[3]), int(parts[4])  # soft, hard
    raise RuntimeError("Limit not found")


def test_umc_http_max_open_file_descriptors(restart_umc_server: Callable):
    fd_max = 333
    try:
        with _ucr.UCSTestConfigRegistry() as ucr:
            ucr.handler_set([f'umc/http/max-open-file-descriptors={fd_max}'])
            restart_umc_server()
            pid = pidof("univention-management-console-server")
            limits = get_limit_max_open_files(pid)
            assert limits[0] == fd_max
            assert limits[1] == fd_max
    finally:
        restart_umc_server()


def test_open_files_after_failed_authentication(ucr: UCSTestConfigRegistry) -> None:
    client = Client()
    username = ucr.get('tests/domainadmin/account')
    open_files_start = number_openfiles_type_stream("univention-management-console-server")
    for i in range(10):
        with pytest.raises(Unauthorized):
            client.authenticate(username, 'dfdsfsdafsdfs')
    sleep(5)
    open_files_end = number_openfiles_type_stream("univention-management-console-server")
    assert math.isclose(open_files_start, open_files_end, abs_tol=1)


def test_open_files_after_password_change(udm: UCSTestUDM) -> None:
    password = "univention"
    _dn, username = udm.create_user(password=password)
    client = Client()
    client.authenticate(username, password)
    open_files_start = number_openfiles_type_stream("univention-management-console-server")
    for i in range(10):
        new_password = f"univention.99-{i}"
        options = {
            "password": {
                "password": f"{password}",
                "new_password": f"{new_password}",
            },
        }
        res = client.umc_set_password(options)
        assert res.status == 200
        password = new_password
    open_files_end = number_openfiles_type_stream("univention-management-console-server")
    assert math.isclose(open_files_start, open_files_end, abs_tol=1)
