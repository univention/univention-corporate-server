#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Checking for saml filesystem permissions
## tags: [saml]
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
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
    must_exist: bool

    def __post_init__(self):
        if not self.path.exists():
            self._ownership = None
            return
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
            must_exist=True,
        ),
        OwnershipTest(
            path=Path('/etc/simplesamlphp/authsources.php'),
            expected_ownership=Ownership(user='root', group='samlcgi', flags='0o640'),
            id='simplesaml-authsources',
            must_exist=True,
        ),
        OwnershipTest(
            path=Path(f'/etc/simplesamlphp/{sso_fqdn}-idp-certificate.key'),
            expected_ownership=Ownership(user='root', group='samlcgi', flags='0o640'),
            id='simplesamlphp-private-key',
            must_exist=True,
        ),
        OwnershipTest(
            path=Path(f'/etc/simplesamlphp/{sso_fqdn}-idp-certificate.crt'),
            expected_ownership=Ownership(user='root', group='samlcgi', flags='0o644'),
            id='simplesamlphp-certificate',
            must_exist=True,
        ),
        OwnershipTest(
            path=Path('/var/lib/simplesamlphp/secrets.inc.php'),
            expected_ownership=Ownership(user='samlcgi', group='samlcgi', flags='0o640'),
            id='simplesamlphp-secrets',
            must_exist=True,
        ),
        OwnershipTest(
            path=Path(f'/usr/share/univention-management-console/saml/idp/{sso_fqdn}.xml'),
            expected_ownership=Ownership(user='root', group='root', flags='0o644'),
            id=f'{sso_fqdn}.xml',
            must_exist=True,
        ),
        OwnershipTest(
            path=Path('/etc/simplesamlphp/serviceprovider_enabled_groups.json'),
            expected_ownership=Ownership(user='samlcgi', group='samlcgi', flags='0o600'),
            id='simplesamlphp-group',
            must_exist=False,
        ),
    ]


@pytest.mark.parametrize(
    'test_case',
    [pytest.param(test_case, id=test_case.id) for test_case in load_test_cases()],
)
def test_permissions(test_case: OwnershipTest):
    if not test_case.must_exist and test_case.ownership is None:
        return
    assert test_case.expected_ownership == test_case.ownership
