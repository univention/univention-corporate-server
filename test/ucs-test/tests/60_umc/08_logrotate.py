#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Logrotation should trigger UMC components to reopen their logfiles
## packages:
##  - univention-management-console
##  - univention-management-console-frontend
## exposure: dangerous
## bugs: [38143, 37317]

import os
import os.path
from subprocess import check_call, check_output
from time import sleep


class Test_LogrotationReload:

    SERVICE = '/usr/sbin/univention-management-console-server'
    LOGFILE = '/var/log/univention/management-console-server.log'

    def pid(self):
        pids = [int(pid) for pid in check_output(['pgrep', '-x', '-f', r'^/usr/bin/python3.*%s.*' % (self.SERVICE,)]).decode('UTF-8').splitlines() if pid.strip()]
        assert len(pids) == 1
        return pids[0]

    def logfiles(self):
        pid = self.pid()
        for file_ in os.listdir('/proc/%d/fd/' % (pid,)):
            file_ = os.path.join('/proc/%d/fd/' % (pid,), file_,)
            if os.path.islink(file_) and os.readlink(file_) == self.LOGFILE:
                yield file_

    def stat(self, logfile,):
        assert logfile
        stat = os.stat(logfile)
        print(logfile, stat,)
        return stat

    def test_logrotation(self):
        self.service_restart()
        old_stats = [self.stat(logfile) for logfile in self.logfiles()]
        assert len(old_stats) == 2

        check_call(['logrotate', '-v', '-f', '/etc/logrotate.d/univention-management-console'])

        for i in range(10):
            if i:
                sleep(1)
            logfiles = list(self.logfiles())
            if not logfiles:
                continue
            new_stats = [self.stat(logfile) for logfile in logfiles]
            assert len(new_stats) == 2

            assert not os.path.samestat(old_stats[0], new_stats[0],)
            assert not os.path.samestat(old_stats[0], new_stats[1],)

    def service_restart(self):
        check_call(['systemctl', 'restart', os.path.basename(self.SERVICE)])
        sleep(2)  # give time to restart
