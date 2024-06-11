#!/usr/share/ucs-test/runner python3
## desc: Test basic schema registration
## tags:
##  - ldapextensions
##  - apptest
## roles:
##  - domaincontroller_master
## roles-not:
##  - basesystem
## packages:
##  - python3-univention-lib
## exposure: dangerous
## bugs: [57279]

import subprocess
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from pathlib import Path
from shlex import quote
from tempfile import mkdtemp

import ldap
from retrying import retry

from univention.config_registry import ucr
from univention.management.console.modules import diagnostic
from univention.testing.strings import random_int
from univention.testing.utils import fail


attribute_id = random_int() + random_int() + random_int() + random_int() + random_int()
SCHEMA_NAME = 'univention-corporate-client.schema'
DIAGNOSTIC_PLUGIN = '60_old_schema_registration'

SCHEMA = '''
attributetype ( 1.3.6.1.4.1.10176.200.10999.%(attribute_id)s NAME 'univentionFreeAttribute%(attribute_id)s'
    DESC ' unused custom attribute %(attribute_id)s '
    EQUALITY caseExactMatch
    SUBSTR caseIgnoreSubstringsMatch
    SYNTAX 1.3.6.1.4.1.1466.115.121.1.15 )
''' % {'attribute_id': attribute_id}


@contextmanager
def schema_file() -> Iterator[Path]:
    tmp = Path(mkdtemp())
    schema = tmp / SCHEMA_NAME
    schema.write_text(SCHEMA)
    try:
        yield schema
    finally:
        schema.unlink()
        tmp.rmdir()


@contextmanager
def register_schema(schema: Path) -> Iterator[None]:
    installed = Path("/var/lib/univention-ldap/local-schema") / SCHEMA_NAME
    assert not installed.exists(), f"Schema '{installed}' already exists"
    subprocess.check_call(['sh', '-x', '-c', f'. /usr/share/univention-lib/ldap.sh && ucs_registerLDAPSchema {quote(schema.as_posix())}'])
    try:
        yield
    finally:
        with suppress(FileNotFoundError):
            installed.unlink()  # Py3.8+: missing_ok=True
        subprocess.check_call(["ucr", "commit", "/etc/ldap/slapd.conf"])
        subprocess.check_call(["systemctl", "restart", "slapd.service"])


@retry(retry_on_exception=ldap.SERVER_DOWN, stop_max_attempt_number=ucr.get_int('ldap/client/retry/count', 15) + 1)
def __fetch_schema_from_uri(ldap_uri: str):
    return ldap.schema.subentry.urlfetch(ldap_uri)


def fetch_schema_from_ldap_master():
    ldap_uri = 'ldap://%(ldap/master)s:%(ldap/master/port)s' % ucr
    return __fetch_schema_from_uri(ldap_uri)


def test() -> None:
    with schema_file() as sfile, register_schema(sfile):
        # start the diagnostic check
        old_schema_registration = diagnostic.Plugin(DIAGNOSTIC_PLUGIN)
        result = old_schema_registration.execute(None)
        assert not result['success'], 'old schema not detected'
        assert {'action': 'register_schema', 'label': 'Register Schema files'} in result['buttons'], 'repair button not shown'

        # repair button
        old_schema_registration.execute(None, action='register_schema')  # FIXME: check for errors? -> Bug #57279
        assert old_schema_registration.module.udm_schema_obj_exists(SCHEMA_NAME)

        try:
            # check if schema is registered properly now
            schema = fetch_schema_from_ldap_master()
            attribute_identifier = "( 1.3.6.1.4.1.10176.200.10999.%(attribute_id)s NAME 'univentionFreeAttribute%(attribute_id)s" % {'attribute_id': attribute_id}

            for attribute_entry in schema[1].ldap_entry().get('attributeTypes'):
                if attribute_entry.startswith(attribute_identifier):
                    print('The schema entry was found: %s' % attribute_entry)
                    break
            else:
                fail('The attribute was not found: univentionFreeAttribute%(attribute_id)s' % {'attribute_id': attribute_id})
        finally:
            subprocess.check_call(['sh', '-x', '-c', f'. /usr/share/univention-lib/ldap.sh && ucs_unregisterLDAPExtension --schema {quote(sfile.stem)}'])


test()

# vim: set ft=python :
