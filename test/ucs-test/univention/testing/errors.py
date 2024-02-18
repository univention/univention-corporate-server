# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""UCS Test errors."""
__all__ = ['TestConditionError', 'TestError']


class TestError(Exception):
    """General test error."""


class TestConditionError(Exception):
    """Error during prepaation for test."""

    def __iter__(self):
        return self.tests.__iter__()

    @property
    def tests(self):
        """Return failed tests."""
        return self.args[0]


if __name__ == '__main__':
    import doctest
    doctest.testmod()
