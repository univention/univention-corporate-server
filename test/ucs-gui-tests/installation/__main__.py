#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# UCS Installer Tests
#
# Copyright 2017 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

import sys
import argparse
import subprocess
import ConfigParser


class InstallerTests(object):

	def __init__(self, args):
		self.language = args.language
		self.server = args.server
		self.args = args

	def run(self):
		# TODO: mkdir screen_dumps
		config = ConfigParser.RawConfigParser()
		config.add_section('General')
		config.set('General', 'language', self.language)
		config.set('General', 'server', self.server)
		with open('tests.cfg', 'wb') as fd:
			config.write(fd)
		subprocess.call(['py.test', '--junitxml', self.args.junitxml])

	@classmethod
	def main(cls, args):
		argparser = argparse.ArgumentParser()
		argparser.add_argument('--junitxml')
		argparser.add_argument('--language')
		argparser.add_argument('--server')
		cls(argparser.parse_args(args)).run()


if __name__ == '__main__':
	InstallerTests.main(sys.argv[1:])
