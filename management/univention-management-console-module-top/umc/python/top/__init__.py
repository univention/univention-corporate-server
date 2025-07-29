#!/usr/bin/python3
#
# Univention Management Console
#  module: process overview
#
# SPDX-FileCopyrightText: 2011-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import time

import psutil

from univention.lib.i18n import Translation
from univention.management.console.log import MODULE
from univention.management.console.modules import Base, UMC_Error
from univention.management.console.modules.decorators import sanitize, simple_response
from univention.management.console.modules.sanitizers import (
    ChoicesSanitizer, IntegerSanitizer, ListSanitizer, PatternSanitizer,
)


_ = Translation('univention-management-console-module-top').translate


class Instance(Base):

    @sanitize(
        pattern=PatternSanitizer(default='.*'),
        category=ChoicesSanitizer(choices=['user', 'pid', 'command', 'all'], default='all'),
    )
    @simple_response
    def query(self, pattern, category='all'):
        processes = []
        for process in psutil.process_iter():
            try:
                cpu_time = process.cpu_times()
                proc = {
                    'timestamp': time.time(),
                    'cpu_time': cpu_time.user + cpu_time.system,
                    'user': process.username(),
                    'pid': process.pid,
                    'cpu': 0.0,
                    'mem': process.memory_percent(),
                    'command': ' '.join(process.cmdline() or []) or process.name(),
                }
            except psutil.NoSuchProcess:
                continue

            categories = [category]
            if category == 'all':
                categories = ['user', 'pid', 'command']
            if any(pattern.match(str(proc[cat])) for cat in categories):
                processes.append(proc)

        # Calculate correct cpu percentage
        time.sleep(1)
        for process_entry in processes:
            try:
                process = psutil.Process(process_entry['pid'])
                cpu_time = process.cpu_times()
            except psutil.NoSuchProcess:
                continue
            elapsed_time = time.time() - process_entry.pop('timestamp')
            elapsed_cpu_time = cpu_time.user + cpu_time.system - process_entry.pop('cpu_time')
            cpu_percent = (elapsed_cpu_time / elapsed_time) * 100
            process_entry['cpu'] = cpu_percent

        return processes

    @sanitize(
        signal=ChoicesSanitizer(choices=['SIGTERM', 'SIGKILL']),
        pid=ListSanitizer(IntegerSanitizer()),
    )
    @simple_response
    def kill(self, signal, pid):
        failed = []
        for pid_ in pid:
            try:
                process = psutil.Process(pid_)
                if signal == 'SIGTERM':
                    process.terminate()
                elif signal == 'SIGKILL':
                    process.kill()
            except psutil.NoSuchProcess as exc:
                failed.append(str(pid_))
                MODULE.error('Could not %s pid %s: %s' % (signal, pid_, exc))
        if failed:
            failed = ', '.join(failed)
            raise UMC_Error(_('No process found with PID %s') % (failed))
