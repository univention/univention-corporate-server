# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Format UCS Test results as Jenkins report."""


import sys
from codecs import encode
from typing import IO
from xml.sax.saxutils import escape as escape_xml

from univention.testing.data import TestFormatInterface, TestResult


__all__ = ['Jenkins']


class Jenkins(TestFormatInterface):
    """
    Create Jenkins report.
    <https://wiki.jenkins-ci.org/display/JENKINS/Monitoring+external+jobs>
    """

    def __init__(self, stream: IO[str] = sys.stdout) -> None:
        super().__init__(stream)

    def end_test(self, result: TestResult) -> None:
        """Called after each test."""
        print('<run>', file=self.stream)
        try:
            mime, content = result.artifacts['stdout']
        except KeyError:
            pass
        else:
            print('<log encoding="hexBinary">%s</log>' % (encode(content.encode('UTF-8'), 'hex').decode('ASCII'),), file=self.stream)
        print('<result>%d</result>' % (result.result,), file=self.stream)
        print('<duration>%d</duration>' % (result.duration or -1,), file=self.stream)
        print('<displayName>%s</displayName>' % (escape_xml(result.case.uid),), file=self.stream)
        print('<description>%s</description>' % (escape_xml(result.case.description or ''),), file=self.stream)
        print('</run>', file=self.stream)
        super().end_test(result)

    def format(self, result: TestResult) -> None:
        """
        >>> from univention.testing.data import TestCase, TestEnvironment
        >>> te = TestEnvironment()
        >>> tc = TestCase('python/data.py')
        >>> tr = TestResult(tc, te)
        >>> tr.success()
        >>> Jenkins().format(tr)
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
