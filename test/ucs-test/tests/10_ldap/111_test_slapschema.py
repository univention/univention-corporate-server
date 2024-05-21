#!/usr/share/ucs-test/runner pytest-3
## desc: Check the diagnostic tool for missing schemas
## tags:
##  - schemas
##  - slapschema
## roles: [domaincontroller_master]
## bugs: [53455]
## exposure: dangerous

import importlib.machinery
import subprocess
import types
from contextlib import contextmanager, nullcontext
from subprocess import check_call
from typing import Iterator

import pytest

from univention.config_registry import ucr
from univention.management.console.modules.diagnostic import Warning
from univention.testing.utils import package_installed


EXAMPLE = 'univention-directory-manager-module-example'
SCHEMA = 'univention-directory-manager-module-example-schema'


loader = importlib.machinery.SourceFileLoader('62_check_slapschema', '/usr/lib/python3/dist-packages/univention/management/console/modules/diagnostic/plugins/62_check_slapschema.py')
check_slap = types.ModuleType(loader.name)
loader.exec_module(check_slap)


@contextmanager
def environment() -> Iterator[None]:
    check_call(['univention-install', '-y', EXAMPLE, SCHEMA], stdout=subprocess.DEVNULL)
    try:
        yield
    finally:
        check_call(['apt-get', '-y', 'purge', EXAMPLE, SCHEMA], stdout=subprocess.DEVNULL)


@contextmanager
def entry() -> Iterator[None]:
    check_call(['udm', 'test/ip_phone', 'create', '--set', 'name=test111', '--set', 'ip=1.2.3.4', '--set', 'priuser=test@slapschema'])
    yield None
    check_call(['udm', 'test/ip_phone', 'remove', '--dn', "cn=test111,%(ldap/base)s" % ucr])


def test():
    already_installed = package_installed(SCHEMA)

    with nullcontext() if already_installed else environment(), entry():
        check_slap.run(None)

    if already_installed:
        assert package_installed(SCHEMA)
    else:
        assert not package_installed(SCHEMA)
        with pytest.raises(Warning):
            check_slap.run(None)
