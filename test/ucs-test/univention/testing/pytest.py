#!/usr/bin/python3
# SPDX-FileCopyrightText: 2021-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""pytest runner for ucs-test"""


import argparse
import os


class PytestRunner:

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
            args.append('--junit-xml=%s' % (os.path.join(os.getcwd(), Junit().outdir, '%s.xml' % (testcase.uid,)),))
        if cls.options.verbose:
            args.append('-' + 'v' * cls.options.verbose)
        args.append('--continue-on-collection-errors')
        args.extend(('-c', '/usr/share/ucs-test/pytest.ini'))
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
        return test_case.exe.filename in ('/usr/bin/py.test-3', '/usr/bin/py.test', '/usr/bin/pytest-3', '/usr/bin/pytest', 'pytest', 'pytest-3', 'py.test', 'py.test-3', '/usr/share/ucs-test/playwright', '/usr/share/ucs-test/selenium-pytest')

    @classmethod
    def get_argument_group(cls, parser):
        """The option group for ucs-test-framework"""
        group = parser.add_argument_group('Additional pytest arguments')
        group.add_argument('--pytest-arg', action='append', default=[], help='Additional arguments passed to pytest. Skip leading dashs (-).')
        return group
