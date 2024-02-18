# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Format UCS Test results as Test Anything Protocol report."""

import sys
from typing import IO

from univention.testing.data import TestEnvironment, TestFormatInterface, TestResult


__all__ = ['TAP']


class TAP(TestFormatInterface):
    """
    Create simple Test-Anything-Protocol report.
    <http://testanything.org/wiki/index.php/Main_Page>
    """

    def __init__(self, stream: IO[str] = sys.stdout) -> None:
        super().__init__(stream)

    def begin_run(self, environment: TestEnvironment, count: int = 1) -> None:
        """Called before first test."""
        super().begin_run(environment, count)
        print("1..%d" % (count,))

    def end_test(self, result: TestResult) -> None:
        """Called after each test."""
        if result.reason.eofs == "O":
            prefix = 'ok'
            suffix = ''
        elif result.reason.eofs == "S":
            prefix = 'not ok'
            suffix = ' # skip'
        else:
            prefix = 'not ok'
            suffix = ''
        print(f'{prefix} {result.case.uid}{suffix}', file=self.stream)
        super().end_test(result)

    def format(self, result: TestResult) -> None:
        """
        >>> from univention.testing.data import TestCase
        >>> te = TestEnvironment()
        >>> tc = TestCase('python/data.py')
        >>> tr = TestResult(tc, te)
        >>> tr.success()
        >>> TAP().format(tr)
        1..1
        """
        self.begin_run(result.environment)
        self.begin_section('')
        self.begin_test(result.case)
        self.end_test(result)
        self.end_section()
        self.end_run()


if __name__ == '__main__':
    import doctest
    doctest.testmod()
