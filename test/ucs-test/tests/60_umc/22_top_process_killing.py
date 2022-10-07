#!/usr/share/ucs-test/runner pytest-3
## desc: Test the UMC backend process killing
## bugs: [34593, 38174]
## exposure: dangerous

import signal
import sys
from os import WNOHANG, WTERMSIG, fork, wait4
from time import sleep
import pytest

from psutil import Process, TimeoutExpired

from umc import UMCBase


class Test_UMCProcessKilling():
    MAX_PROCESS_TIME = 30  # seconds
    UMCBASE = None
    PROC = None

    @pytest.fixture(scope="class", autouse=True)
    def prepare_test(self):
        Test_UMCProcessKilling.UMCBASE = UMCBase()
        self.UMCBASE.create_connection_authenticate()

    def make_kill_request(self, signal, pids):
        """
        Applies the kill action with a signal 'signal' to the list of 'pids'
        provided by making a UMC request 'top/kill' with respective options.
        """
        self.UMCBASE.client.umc_command('top/kill', {'signal': signal, 'pid': pids})

    def query_process_exists(self, pid):
        """
        Checks if process with a provided 'pid' exists
        by making the UMC request 'top/query'.
        Returns True when exists.
        """
        return any(result['pid'] == pid and sys.executable in result['command'] for result in self.UMCBASE.client.umc_command('top/query').result)

    def force_process_kill(self):
        """
        Kills process with SIGKILL signal via psutil if not yet terminated.
        That is a clean-up action.
        """
        if self.PROC and self.PROC.is_running():
            print("Created process with pid '%s' was not terminated, "
                  "forcing kill using psutil" % self.PROC.pid)
            self.PROC.kill()

            try:
                # wait a bit for process to be killed
                self.PROC.wait(timeout=5)
            except TimeoutExpired as exc:
                print("Process with pid '%s' did not exit after forced KILL "
                      "via psutil: %r" % (self.PROC.pid, exc))

    def create_process(self, ignore_sigterm=False):
        """
        Initiates a simple test process that should be killed after by forking.
        Creates a psutil Process class to check running state
        before terminating. Also returns process id (pid).
        """
        pid = fork()
        if pid:  # parent
            Test_UMCProcessKilling.PROC = Process(pid)
            return pid
        else:  # child under test
            if ignore_sigterm:
                # the process should ignore 'SIGTERM'
                signal.signal(signal.SIGTERM, signal.SIG_IGN)
            sleep(self.MAX_PROCESS_TIME)
            sys.exit(0)

    @pytest.mark.parametrize('signame,ignore_signal', [
        ('SIGTERM', False),
        ('SIGKILL', False),
        ('SIGTERM', True)
    ])
    def test(self, signame, ignore_signal):
        """
        Creates a process;
        Check created process exist via UMC;
        Kills/Terminates process with a given 'signame' via UMC;
        Performs clean-up using psutil if needed.
        """
        print("\nTesting UMC process killing with signal '%s'" % signame)
        signum = getattr(signal, signame)
        try:
            pid = self.create_process(ignore_signal)
            assert self.query_process_exists(pid)

            self.make_kill_request(signame, [pid])  # a UMC request

            for i in range(self.MAX_PROCESS_TIME):
                if i:
                    sleep(1)
                child, exit_status, _res_usage = wait4(pid, WNOHANG)
                if child:
                    break

            print("Process Exit Status is: ", exit_status)
            exit_code = WTERMSIG(exit_status)

            if ignore_signal:
                # case 3:
                assert exit_code not in (signum, getattr(signal, 'SIGKILL'))
            else:
                # cases 1 and 2:
                assert exit_code == signum
                assert not self.query_process_exists(pid)  # a UMC request
        finally:
            self.force_process_kill()
