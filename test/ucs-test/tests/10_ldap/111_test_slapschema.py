#!/usr/share/ucs-test/runner python3
## desc: Check the diagnostic tool for missing schemas
## tags:
##  - schemas
##  - slapschema
## roles: [domaincontroller_master]
## bugs: [53455]
## exposure:

import importlib.machinery
import subprocess
import types
from subprocess import check_call

import pytest

from univention.config_registry import ucr
from univention.management.console.modules.diagnostic import Warning


loader = importlib.machinery.SourceFileLoader('62_check_slapschema', '/usr/lib/python3/dist-packages/univention/management/console/modules/diagnostic/plugins/62_check_slapschema.py')
check_slap = types.ModuleType(loader.name)
loader.exec_module(check_slap)


def setup_environment():
    # Install the package
    # Check if test user exist
    # Create test user if not exist
    print("Setting up the test environment ...")
    check_call(
        ['univention-install', '-y', 'univention-directory-manager-module-example'],
        stdout=subprocess.DEVNULL,
    )
    check_call(
        ['udm', 'test/ip_phone', 'create', '--set', 'name=test111', '--set', 'ip=1.2.3.4', '--set', 'priuser=test@slapschema'],
    )


def clean_environment():
    # Install dependencies to be able to use test/ip_phone module
    # Remove the test user
    # Uninstall the example package
    print("Cleaning the test environment ...")
    check_call(
        ['univention-install', '-y', 'univention-directory-manager-module-example'],
        stdout=subprocess.DEVNULL,
    )
    check_call(
        ['udm', 'test/ip_phone', 'remove', '--dn', "cn=test111,%(ldap/base)s" % ucr],
    )
    check_call(
        ['apt-get', '-y', 'remove', 'univention-directory-manager-module-example'],
        stdout=subprocess.DEVNULL,
    )


def remove_schema():
    # Remove the schema
    check_call(
        ['apt-get', '-y', 'remove', 'univention-directory-manager-module-example-schema'],
        stdout=subprocess.DEVNULL,
    )
    print("Removed schema")


def test_schema_is_present():
    check_slap.run(None)
    print("Test schema is present passed.")


def test_schema_is_not_present():
    with pytest.raises(Warning) as schemaInfo:
        check_slap.run(None)
    assert schemaInfo
    print("Test schema is not present passed.")


def main():
    setup_environment()
    test_schema_is_present()
    remove_schema()
    test_schema_is_not_present()
    clean_environment()


if __name__ == '__main__':
    main()
