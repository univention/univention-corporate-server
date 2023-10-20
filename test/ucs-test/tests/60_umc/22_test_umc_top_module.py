#!/usr/share/ucs-test/runner pytest-3
## desc: Test the UMC backend process killing
## bugs: [34593, 38174]
## exposure: dangerous

import contextlib
import signal
import sys
from os import WNOHANG, WTERMSIG, fork, wait4
from random import randint
from time import sleep

import pytest
from psutil import Process, TimeoutExpired, pid_exists

from univention.lib.umc import BadRequest


class Test_UMCTopModule:
    max_process_time = 30  # seconds
    proc = None

    def kill_process(self, signal, pid):
        """
        Applies the kill action with a signal 'signal' to the list of 'pids'
        provided by making a UMC request 'top/kill' with respective options.
        """
        self.client.umc_command('top/kill', {'signal': signal, 'pid': [pid]})

    def query_process_exists(self, pid):
        """
        Checks if process with a provided 'pid' exists
        by making the UMC request 'top/query'.
        Returns True when exists.
        """
        return any(result['pid'] == pid and sys.executable in result['command'] for result in self.client.umc_command('top/query', {'category': 'pid', 'filter': pid}).result)

    def force_process_kill(self):
        """
        Kills process with SIGKILL signal via psutil if not yet terminated.
        That is a clean-up action.
        """
        if self.proc and self.proc.is_running():
            print("Created process with pid '%s' was not terminated, "
                  "forcing kill using psutil" % self.proc.pid)
            self.proc.kill()

            try:
                # wait a bit for process to be killed
                self.proc.wait(timeout=5)
            except TimeoutExpired as exc:
                print("Process with pid '%s' did not exit after forced KILL "
                      "via psutil: %r" % (self.proc.pid, exc))

    @contextlib.contextmanager
    def create_process(self, ignore_sigterm=False):
        """
        Initiates a simple test process that should be killed after by forking.
        Creates a psutil Process class to check running state
        before terminating. Also returns process id (pid).
        """
        pid = fork()
        if pid:  # parent
            self.__class__.proc = Process(pid)
            yield pid
            self.force_process_kill()
            return

        if ignore_sigterm:
            # the process should ignore 'SIGTERM'
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
        sleep(self.max_process_time)
        pytest.exit(0)

    @pytest.mark.parametrize('signame,ignore_signal', [
        ('SIGTERM', False),
        ('SIGKILL', False),
        ('SIGTERM', True),
    ])
    def test_process_termination(self, signame, ignore_signal, Client):
        """
        Creates a process;
        Check created process exist via UMC;
        Kills/Terminates process with a given 'signame' via UMC;
        Performs clean-up using psutil if needed.
        """
        print(f"\nTesting UMC process killing with signal '{signame}'")
        signum = getattr(signal, signame)
        self.client = Client.get_test_connection()
        with self.create_process(ignore_signal) as pid:
            assert self.query_process_exists(pid)
            self.kill_process(signame, pid)  # a UMC request

            for i in range(self.max_process_time):
                if i:
                    sleep(1)
                child, exit_status, _res_usage = wait4(pid, WNOHANG)
                if child:
                    break

            print("Process Exit Status is: ", exit_status)
            exit_code = WTERMSIG(exit_status)

            if ignore_signal:
                assert exit_code == 0
            else:
                assert exit_code == signum
                assert not self.query_process_exists(pid)

    def test_error_handling_of_not_existing_process_termination(self, Client):
        self.client = Client.get_test_connection()
        pid = 0
        while True:
            pid = randint(2, 4194304)
            if not pid_exists(pid):
                break
        with pytest.raises(BadRequest, match=r'No process found with PID|Kein Prozess mit der PID'):
            self.kill_process('SIGKILL', pid)

    @pytest.mark.parametrize('pattern,category', [
        ('/sbin/init', 'all'),
        ('/sbin/init', 'command'),
        ('root', 'user'),
        (1, 'pid'),
    ])
    def test_process_query_single_process(self, pattern, category, Client):
        client = Client.get_test_connection()
        request = client.umc_command('top/query', {'pattern': pattern, 'category': category})
        assert request.result
        proc = request.result[0]
        assert all(key in proc for key in ('user', 'pid', 'cpu', 'mem', 'command'))
        assert proc['pid'] == 1 and proc['user'] == 'root' and proc['command'].startswith('/sbin/init')

    def test_process_query_response_structure(self, Client):
        client = Client.get_test_connection()
        request = client.umc_command('top/query', {'category': 'all'})
        assert request.result
        assert len(request.result) > 1
        assert all((key in result for key in ('user', 'pid', 'cpu', 'mem', 'command')) for result in request.result)
