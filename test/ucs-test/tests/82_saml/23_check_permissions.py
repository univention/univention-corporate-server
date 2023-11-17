#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Checking for saml filesystem permissions
## tags: [saml]
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## apps:
##  - keycloak
## bugs: [38947]
## exposure: safe

from dataclasses import dataclass, field
from os import stat
from pathlib import Path

import pytest

from univention.config_registry import ucr


@dataclass
class Ownership:
    user: str
    group: str
    flags: str


@dataclass
class OwnershipTest:
    id: str  # test ID - used to display test information
    path: Path  # path to file/directory
    expected_ownership: Ownership  # expected ownership
    _ownership: Ownership = field(init=False, repr=False)  # actual ownership

    def __post_init__(self):
        flags = oct(stat(self.path).st_mode & 0o777)
        user = self.path.owner()
        group = self.path.group()
        self._ownership = Ownership(user=user, group=group, flags=flags)

    @property
    def ownership(self) -> Ownership:
        return self._ownership


def load_test_cases():
    sso_fqdn = ucr["ucs/server/sso/fqdn"]

    return [
        OwnershipTest(
            path=Path('/etc/idp-ldap-user.secret'),
            expected_ownership=Ownership(user='root', group='DC Backup Hosts', flags='0o640'),
            id='idp-ldap-user.secret',
        ),
        OwnershipTest(
            path=Path('/etc/simplesamlphp/authsources.php'),
            expected_ownership=Ownership(user='root', group='samlcgi', flags='0o640'),
            id='simplesaml-authsources',
        ),
        OwnershipTest(
            path=Path(f'/etc/simplesamlphp/{sso_fqdn}-idp-certificate.key'),
            expected_ownership=Ownership(user='root', group='samlcgi', flags='0o640'),
            id='simplesamlphp-private-key',
        ),
        OwnershipTest(
            path=Path(f'/etc/simplesamlphp/{sso_fqdn}-idp-certificate.crt'),
            expected_ownership=Ownership(user='root', group='samlcgi', flags='0o644'),
            id='simplesamlphp-certificate',
        ),
        OwnershipTest(
            path=Path('/etc/simplesamlphp/serviceprovider_enabled_groups.json'),
            expected_ownership=Ownership(user='samlcgi', group='samlcgi', flags='0o600'),
            id='simplesamlphp-group',
        ),
        OwnershipTest(
            path=Path('/var/lib/simplesamlphp/secrets.inc.php'),
            expected_ownership=Ownership(user='samlcgi', group='samlcgi', flags='0o640'),
            id='simplesamlphp-secrets',
        ),
        OwnershipTest(
            path=Path(f'/usr/share/univention-management-console/saml/idp/{sso_fqdn}.xml'),
            expected_ownership=Ownership(user='root', group='root', flags='0o644'),
            id=f'{sso_fqdn}.xml',
        ),
    ]


@pytest.mark.parametrize(
    'test_case',
    [pytest.param(test_case, id=test_case.id) for test_case in load_test_cases()],
)
def test_permissions(test_case: OwnershipTest):
    assert test_case.expected_ownership == test_case.ownership
