# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
import ldap
import pytest

from univention.testing.active_directory import ActiveDirectorySettings
from univention.testing.ucr import UCSTestConfigRegistry

from adconnector import _Connector, connector_setup


@pytest.fixture
def active_directory_settings(ucr: UCSTestConfigRegistry) -> ActiveDirectorySettings:
    return ActiveDirectorySettings(
        host=ucr.get('connector/ad/ldap/host'),
        admin_username=ldap.dn.explode_rdn(ucr.get('connector/ad/ldap/binddn'), notypes=True)[0],
        admin_password=open(ucr.get('connector/ad/ldap/bindpw')).read(),
    )


@pytest.fixture
def ad_connector():
    with connector_setup('sync'):
        connector = _Connector()
        yield connector
