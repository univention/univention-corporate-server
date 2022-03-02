#!/usr/bin/python3
#
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 Univention GmbH
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

"""pytest runner for ucs-test"""

from __future__ import absolute_import

import os
import argparse


class PytestRunner(object):

	options = argparse.Namespace(inside=True)

	@classmethod
	def extend_command(cls, testcase, cmd):
		"""Add junit and other arguments to pytest"""
		if getattr(cls.options, 'inside', False):
			return cmd
		args = []
		if cls.options.dry:
			args.append('--collect-only')
		if cls.options.hold:
			args.append('--exitfirst')
		if cls.options.format == 'junit':
			from univention.testing.format.junit import Junit
			section = os.path.dirname(testcase.uid)
			args.append('--junit-xml=%s' % (os.path.join(os.getcwd(), Junit().outdir, '%s.xml' % (testcase.uid,)),))
			args.append('--junit-prefix=%s' % (section,))
		if cls.options.verbose:
			args.append('-' + 'v' * cls.options.verbose)
		args.append('--continue-on-collection-errors')
		# args.append('--strict')
		# args.append('--showlocals')
		# args.append('--full-trace')
		args.append('--tb=native')
		args.append('--color=auto')
		args.append('--confcutdir=/usr/share/ucs-test/')
		args.extend(('-%s' if len(arg) == 1 else '--%s') % (arg,) for arg in cls.options.pytest_arg)
		try:
			cmd.remove('--capture=no')
		except ValueError:
			pass
		try:
			cmd.remove('-s')
		except ValueError:
			pass
		cmd.extend(args)
		return cmd

	@classmethod
	def set_arguments(cls, options):
		"""store singleton CLI arguments globally"""
		cls.options = options

	@classmethod
	def is_pytest(self, test_case):
		"""indicates that the test case is a pytest test"""
		return test_case.exe.filename in ('/usr/bin/py.test-3', '/usr/bin/py.test', '/usr/bin/pytest-3', '/usr/bin/pytest', 'pytest', 'pytest-3', 'py.test', 'py.test-3')

	@classmethod
	def get_argument_group(cls, parser):
		"""The option group for ucs-test-framework"""
		group = parser.add_argument_group('Additional pytest arguments')
		group.add_argument('--pytest-arg', action='append', default=[], help='Additional arguments passed to pytest. Skip leading dashs (-).')
		return group
