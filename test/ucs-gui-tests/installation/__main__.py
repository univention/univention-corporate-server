#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# UCS Installer Tests
#
# Copyright 2017 Univention GmbH
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

import os
import sys
import contextlib
import argparse
import subprocess
import ConfigParser

from vminstall import create_virtual_machine


class InstallerTests(object):

	def __init__(self, args):
		self.args = args
		self.i = 1
		self.ip_address = ''
		self.ip_master = ''
		self.password = ''

	def run(self):
		# TODO: screen dumps is static currently
		if not os.path.exists('screen_dumps'):
			os.makedirs('screen_dumps')
		if not os.path.exists('screen_dumps_master') and self.args.role not in ('master', 'basesystem'):
			os.makedirs('screen_dumps_master')

		vm_kwargs = {}
		managers = []
		if self.args.role not in ('master', 'basesystem'):
			self.ip_master = self.get_ip_address()
			vm_kwargs['dns_server'] = self.ip_master
			managers.append(create_virtual_machine(self.args.language, 'master', 'regular', self.args.server, self.args.iso_image, self.ip_master, 'screen_dumps_master'))

		self.ip_address = self.get_ip_address()
		managers.append(create_virtual_machine(self.args.language, self.args.role, self.args.environment, self.args.server, self.args.iso_image, self.ip_address, 'screen_dumps', **vm_kwargs))
		with contextlib.nested(*managers) as foo:
			vm, installer = foo.pop()
			self.password = installer.vm_config.password
			self.write_config()
			subprocess.call(['py.test', '--junitxml', self.args.junitxml] + self.args.tests)

		subprocess.call(['tar', '--remove-files', '-zcf', 'screen_dumps.tar.gz', 'screen_dumps'])
		if self.args.role not in ('master', 'basesystem'):
			subprocess.call(['tar', '--remove-files', '-zcf', 'screen_dumps_master.tar.gz', 'screen_dumps_master'])

	def get_ip_address(self):
		self.i += 1
		return '%s.%s' % (self.args.ip_range, self.i)

	def write_config(self):
		config = ConfigParser.RawConfigParser()
		config.add_section('General')
		cfg = {
			'language': self.args.language,
			'server': self.args.server,
			'iprange': self.args.ip_range,
			'isoimage': self.args.iso_image,
			'role': self.args.role,
			'environment': self.args.environment,
			'ip_address': self.ip_address,
			'master_ip': self.ip_master,
			'password': self.password,
		}
		for key, value in cfg.iteritems():
			config.set('General', key, value)
		with open('tests.cfg', 'wb') as fd:
			config.write(fd)

	@classmethod
	def main(cls, args):
		argparser = argparse.ArgumentParser()
		# FIXME: add help
		argparser.add_argument('--junitxml')
		argparser.add_argument('--language')
		argparser.add_argument('--server')
		argparser.add_argument('--ip-range')
		argparser.add_argument('--iso-image')
		argparser.add_argument('--role')
		argparser.add_argument('--environment')
		argparser.add_argument('tests', nargs='+')
		cls(argparser.parse_args(args)).run()


if __name__ == '__main__':
	InstallerTests.main(sys.argv[1:])
