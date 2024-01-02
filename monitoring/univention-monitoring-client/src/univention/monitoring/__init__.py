#!/usr/bin/python3
#
# Univention Monitoring Client
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2022-2024 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.
#

import argparse
import logging
import os.path
import subprocess
import sys

from prometheus_client import CollectorRegistry, Gauge, write_to_textfile

from univention.config_registry import ucr


NODE_EXPORTER_DIR = '/var/lib/prometheus/node-exporter/'


class Alert(object):
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
        stdout, stderr = proc.communicate()
        output = stdout.decode('UTF-8', 'replace') if stdout is not None else None
        return proc.returncode, output
