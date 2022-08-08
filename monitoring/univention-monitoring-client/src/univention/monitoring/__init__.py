#!/usr/bin/python3
#
# Univention Monitoring Client
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2022 Univention GmbH
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
import re
import subprocess
import sys

from univention.config_registry import ucr

NODE_EXPORTER_DIR = '/var/lib/prometheus/node-exporter/'
RE_INVALID_LABEL = re.compile('[{"=}]')


def quote(string):
	return string.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')


class Alert(object):
	"""Execute alert plugin"""

	def __init__(self, args):
		self.args = args
		self.log = logging.getLogger(self.args.prog)
		self.default_labels = {'instance': '%(hostname)s.%(domainname)s' % ucr}
		self._fd = None

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
		with open(os.path.join(NODE_EXPORTER_DIR, '%s.prom' % (plugin,)), 'w') as self._fd:
			self.write_metrics()

	def write_metrics(self):
		pass

	def write_metric(self, metric_name, value, **labels):
		labels = dict(self.default_labels, **labels)
		label_str = '{%s}' % ','.join(
			'%s="%s"' % (RE_INVALID_LABEL.sub('', key), quote(val))
			for key, val in labels.items()
		) if labels else ''

		value = '%d' % (value,) if isinstance(value, int) else '%f' % (value,)
		self._fd.write('%s%s %s\n' % (metric_name, label_str, value))

	def exec_command(self, *args, **kwargs):
		kwargs.setdefault('stdout', subprocess.PIPE)
		kwargs.setdefault('stderr', subprocess.DEVNULL)
		proc = subprocess.Popen(*args, **kwargs)
		stdout, stderr = proc.communicate()
		output = stdout.decode('UTF-8', 'replace') if stdout is not None else None
		return proc.returncode, output
