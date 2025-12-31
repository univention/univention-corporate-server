#!/usr/bin/python3
#
# Univention Monitoring Client
#
# SPDX-FileCopyrightText: 2022-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

import argparse
import logging
import os.path
import subprocess
import sys

from prometheus_client import CollectorRegistry, Gauge, write_to_textfile

from univention.config_registry import ucr


NODE_EXPORTER_DIR = '/var/lib/prometheus/node-exporter/'


class Alert:
    """Execute alert plugin"""

    def __init__(self, args):
        self.args = args
        self.log = logging.getLogger(self.args.prog)
        self.default_labels = {'instance': '%(hostname)s.%(domainname)s' % ucr}
        self._registry = CollectorRegistry()

    @classmethod
    def main(cls):
        parser = argparse.ArgumentParser(description=cls.__doc__)
        parser.add_argument('-v', '--verbose', action='store_true', help='Add debug output')
        args = parser.parse_args()
        args.prog = parser.prog
        plugin = parser.prog
        if args.verbose:
            logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

        if ucr.is_true('monitoring/plugin/%s/disabled' % (plugin,)):
            return

        self = cls(args)
        self.write_metrics()
        write_to_textfile(os.path.join(NODE_EXPORTER_DIR, '%s.prom' % (plugin,)), self._registry)

    def write_metrics(self):
        pass

    def write_metric(self, metric_name, value, doc=None, **labels):
        labels = dict(self.default_labels, **labels)
        g = Gauge(metric_name, doc or self.__doc__ or '', labelnames=list(labels), registry=self._registry)
        g.labels(**labels).set(value)

    def exec_command(self, *args, **kwargs):
        kwargs.setdefault('stdout', subprocess.PIPE)
        kwargs.setdefault('stderr', subprocess.DEVNULL)
        proc = subprocess.Popen(*args, **kwargs)
        stdout, _stderr = proc.communicate()
        output = stdout.decode('UTF-8', 'replace') if stdout is not None else None
        return proc.returncode, output
