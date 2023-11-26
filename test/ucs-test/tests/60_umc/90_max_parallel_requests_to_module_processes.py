#!/usr/share/ucs-test/runner pytest-3
## desc: Test the global connection limit to module processes
## bugs: [56828]
## exposure: dangerous

import subprocess
import time
from multiprocessing import Process

import concurrent.futures
import pytest

from univention.lib.umc import BadGateway
from univention.management.console.modules.ucstest import joinscript, unjoinscript


@pytest.fixture(autouse=True)
def ucs_test_module_joined():
    joinscript()
    subprocess.check_call(["systemctl", "restart", "univention-management-console-server"])
    yield
    unjoinscript()


def pool_runner(func):
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(func) for i in range(100)]
        for future in concurrent.futures.as_completed(futures):
            print(future.result())


def test_max_parallel_requests_to_module_processes(Client):
    client = Client.get_test_connection()
    print("Open module processes")
    client.umc_command('ucstest/sleep', {'seconds': 1})
    client.umc_command('sysinfo/general')
    process_sleep = Process(target=pool_runner, args=(
        lambda: client.umc_command('ucstest/sleep', {'seconds': 10}).data, )
    )
    process_sleep.start()
    try:
        print("Wait for connections to be served")
        time.sleep(2)
        print("Check different module")
        process_sysinfo = Process(target=lambda: print(client.umc_command('sysinfo/general').data))
        process_sysinfo.start()
        process_sysinfo.join(timeout=5)
        if process_sysinfo.exitcode is None:
            process_sysinfo.terminate()
            raise TimeoutError()
        print("Module worked")
    finally:
        print("Cleanup")
        process_sleep.terminate()
        subprocess.check_call(["systemctl", "restart", "apache2"])
        subprocess.check_call(["systemctl", "restart", "univention-management-console-server"])


def test_module_process_can_be_reached_when_request_exceeds_initial_timeout(ucr, Client):
    client = Client.get_test_connection(language='en-US')
    subprocess.call(['pkill', '-f', 'univention-management-console-module.*-m.*ucstest'])
    assert client.umc_command('ucstest/sleep', {'seconds': 12}).data


def test_error_status_if_module_process_cannot_initialized_in_time(ucr, Client):
    """Test error handling works when module initialization takes more than 10 seconds (which is the timeout)"""
    ucr.handler_set(['ucstest/sleep-during-init=11'])
    client = Client.get_test_connection(language='en-US')
    subprocess.call(['pkill', '-f', 'univention-management-console-module.*-m.*ucstest'])
    assert client.umc_command('ucstest/sleep', {'seconds': 11}).data


def test_error_status_if_module_process_cannot_import_in_time(ucr, Client):
    """Test error handling works when module import takes more than 10 seconds (which is the timeout)"""
    ucr.handler_set(['ucstest/sleep-during-import=11'])
    subprocess.call(['pkill', '-f', 'univention-management-console-module.*-m.*ucstest'])
    client = Client.get_test_connection(language='en-US')
    with pytest.raises(BadGateway) as exc:
        client.umc_command('ucstest/sleep', {'seconds': 11})

    assert (
        "Connection to module process failed: ucstest: timeout exceeded" in exc.value.response.message
        or "Connection to module process failed: ucstest: HTTP 599: Recv failure: Connection reset by peer" in exc.value.response.message
    )
