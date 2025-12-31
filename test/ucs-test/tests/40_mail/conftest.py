# SPDX-FileCopyrightText: 2013-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import pytest

import univention.testing.ucr as ucr_test

from essential.mail import random_email


@pytest.fixture
def fqdn():
    with ucr_test.UCSTestConfigRegistry() as ucr:
        return '%(hostname)s.%(domainname)s' % ucr


@pytest.fixture
def user_addr():
    return random_email()
