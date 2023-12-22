#!/usr/bin/python3
#
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2021-2023 Univention GmbH
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

"""conftest plugin for pytest runner in ucs-test"""

from typing import Callable, TypeVar

import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser


_RT = TypeVar("_RT")
_F = Callable[..., _RT]  # Py3.10+: Callable[ParamSpec, _RT]


def pytest_addoption(parser: Parser) -> None:
    parser.addoption(
        "--ucs-test-tags-prohibited",
        action="append",
        metavar="TAG",
        default=[],
        help="Skip tests with this tag",
    )
    parser.addoption(
        "--ucs-test-tags-required",
        action="append",
        metavar="TAG",
        default=[],
        help="Only run tests with this tag",
    )
    parser.addoption(
        "--ucs-test-tags-ignore",
        action="append",
        metavar="TAG",
        default=[],
        help="Neither require nor prohibit this tag",
    )
    parser.addoption(
        "--ucs-test-default-tags",
        action="append",
        metavar="TAG",
        default=[],
        help="The tags for the entire test case, if the test function does not specify any",
    )
    parser.addoption(
        "--ucs-test-exposure",
        choices=('safe', 'careful', 'dangerous'),
        help="Run more dangerous tests",
    )
    parser.addoption(
        "--ucs-test-default-exposure",
        choices=('safe', 'careful', 'dangerous'),
        help="The exposure of the test",
    )


def pytest_configure(config: Config) -> None:
    config.addinivalue_line("markers", "slow: test case is slow")
    config.addinivalue_line("markers", "tags(name): tag a test case")
    config.addinivalue_line("markers", "roles(names): specify roles")
    config.addinivalue_line("markers", "exposure(exposure): run dangerous tests?")


def pytest_runtest_setup(item: pytest.Item) -> None:
    check_tags(item)
    check_roles(item)
    check_exposure(item)


def check_tags(item: pytest.Item) -> None:
    tags_required = set(item.config.getoption("--ucs-test-tags-required") or [])
    tags_prohibited = set(item.config.getoption("--ucs-test-tags-prohibited") or [])
    tags = {
        tag
        for mark in item.iter_markers(name="tags")
        for tag in mark.args
    } or set(item.config.getoption("--ucs-test-default-tags", []))

    prohibited = tags & tags_prohibited
    if prohibited:
        pytest.skip('De-selected by tag: %s' % (' '.join(prohibited),))
    elif tags_required:
        required = tags & tags_required
        if not required:
            pytest.skip('De-selected by tag: %s' % (' '.join(tags_required),))


def check_roles(item: pytest.Item) -> None:
    from univention.config_registry import ucr
    from univention.testing.data import CheckRoles
    roles_required = {
        role
        for mark in item.iter_markers(name="roles")
        for role in mark.args
    }
    roles_prohibited = {
        role
        for mark in item.iter_markers(name="roles_not")
        for role in mark.args
    }
    overlap = roles_required & roles_prohibited
    if overlap:
        roles = roles_required - roles_prohibited
    elif roles_required:
        roles = roles_required
    else:
        roles = set(CheckRoles.ROLES) - roles_prohibited

    if ucr['server/role'] not in roles:
        pytest.skip('Wrong role: %s not in (%s)' % (ucr['server/role'], ','.join(roles)))


def check_exposure(item: pytest.Item) -> None:
    from univention.testing.data import CheckExposure
    required_exposure = item.config.getoption("--ucs-test-exposure")
    if not required_exposure:
        return
    try:
        exposure = next(mark.args[0] for mark in item.iter_markers(name="exposure"))
    except StopIteration:
        exposure = item.config.getoption("--ucs-test-default-exposure", "safe")
    if CheckExposure.STATES.index(exposure) > CheckExposure.STATES.index(required_exposure):
        pytest.skip(f'Too dangerous: {exposure} > {required_exposure}')


def locale_available(*locales: str) -> Callable[[_F], _F]:  # Py3.10+: ParamSpec
    from univention.config_registry import ucr
    available = {locale.split(".")[0] for locale in ucr.get("locale", "").split()}
    required = set(locales) or {"de_DE", "en_US"}

    return pytest.mark.skipif(
        available < required,
        reason="Required locales are not available",
    )
