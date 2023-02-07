#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Logrotation should trigger UMC components to reopen their logfiles
## packages:
##  - univention-management-console
##  - univention-management-console-frontend
## exposure: dangerous
## bugs: [38143, 37317]

import os
import os.path
from subprocess import PIPE, Popen, check_call
from time import sleep

import pytest


class LogrotateService:

    def __init__(self, service, logfile_pattern):
        self.service = service
        self.logfile_pattern = logfile_pattern
        self.old_stat = None

    @property
    def pgrep_pattern(self):
        return r'^/usr/bin/python3.*%s.*' % (self.service,)

    def pid(self):
        process = Popen(['pgrep', '-x', '-f', self.pgrep_pattern], stdout=PIPE)
        stdout, _stderr = process.communicate()
        assert not process.returncode
        pids = [int(pid) for pid in stdout.splitlines() if pid.strip()]
        assert len(pids) == 1
        return pids[0]

    def logfile(self):
        pid = self.pid()
        for file_ in os.listdir('/proc/%d/fd/' % (pid,)):
            file_ = os.path.join('/proc/%d/fd/' % (pid,), file_)
            if os.path.islink(file_) and os.readlink(file_).startswith(self.logfile_pattern):
                return file_
        print('No logfile for service %s found.' % (self.service,))

    def stat(self, logfile):
        assert logfile
        stat = os.stat(logfile)
        print(logfile, stat)
        return stat

    def service_restart(self):
        check_call(['systemctl', 'restart', os.path.basename(self.service)])
        sleep(2)  # give time to restart

    def pre(self):
        self.service_restart()
        self.old_stat = self.stat(self.logfile())

    def post(self):
        for i in range(10):
            if i:
                sleep(1)
            logfile = self.logfile()
            if not logfile:
                continue
            new_stat = self.stat(logfile)
            if not os.path.samestat(self.old_stat, new_stat):
                return
        raise AssertionError('Logrotate was executed, the service %s did not reopen the logfile %s.' % (self.service, logfile))


@pytest.mark.parametrize('service,logfile', [
    ('/usr/sbin/univention-management-console-server', '/var/log/univention/management-console-server.log'),
    ('/usr/sbin/univention-management-console-web-server', '/var/log/univention/management-console-web-server.log'),
])
def test_logrotation(service, logfile):
    service = LogrotateService(service, logfile)
    service.pre()
    check_call(['logrotate', '-v', '-f', '/etc/logrotate.d/univention-management-console'])
    service.post()
