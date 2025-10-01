# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
import random

import pytest

from univention.testing.active_directory import ActiveDirectorySettings, User
from univention.testing.udm import UCSTestUDM

from s4connector import connector_setup


@pytest.fixture
def active_directory_settings():
    return ActiveDirectorySettings(is_local_connect=True)


@pytest.fixture
def s4_connector():
    with connector_setup('sync') as connector:
        yield connector


@pytest.fixture
def ucs_user(udm: UCSTestUDM):
    dn, username = udm.create_user()

    yield {'dn': dn, 'username': username}

    udm.remove_user(username)


@pytest.fixture
def samba_user(active_directory_settings: ActiveDirectorySettings):
    user_api = User(active_directory_settings)
    samba_user = user_api.create(username=f'TestSyncLockedOut{random.randrange(1, 999)}', password='Univention.99')

    yield samba_user

    user_api.delete(username=samba_user.name)
