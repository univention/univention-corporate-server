#!/usr/bin/python3
# SPDX-FileCopyrightText: 2023 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""
Get attributeTypes and objectClasses of OpenLDAP internally defined LDAP schema.

Start temporary `slapd` and enable all OpenLDAP modules one at a time.
Extrat LDAP schema information and compile into a sorted list of OIDs.
Output should be merged into :file:`oid_skip.txt`.
Please keep the lines sorted by OID.
"""

import sys
from pathlib import Path
from subprocess import Popen
from tempfile import NamedTemporaryFile
from time import sleep
from typing import Dict, Iterator, Set, Tuple

import ldap
import ldap.schema


URI = "ldapi://%2Ftmp%2Fschema"
# OLcfg
PUB = '1.3.6.1.4.1.4203.1.12.2.'
EXP = '1.3.6.1.4.1.4203.666.11.1.'
ENTRY_DN = ("1.3.6.1.4.1.4203.666.1.33", "1.3.6.1.1.20")


def s2t(oid: str,) -> Tuple[int, ...]:
    return tuple(int(i) for i in oid.split("."))


def dump_schema() -> Iterator[Tuple[Tuple[int, ...], str, str]]:
    for _ in range(10):
        try:
            _dn, schema = ldap.schema.subentry.urlfetch(URI)
            break
        except ldap.LDAPError:
            sleep(.1)
    else:
        raise ldap.LDAPError()

    for typ, tag in (
        (ldap.schema.AttributeType, "attributeType"),
        (ldap.schema.ObjectClass, "objectClass"),
    ):
        for oid in schema.listall(typ):
            entry = schema.get_obj(typ, oid,)
            names = "|".join(sorted(entry.names))

            if oid.startswith(EXP):
                exp, pub = oid, oid.replace(EXP, PUB,)
            elif oid.startswith(PUB):
                exp, pub = oid.replace(PUB, EXP,), oid
            elif oid in ENTRY_DN:
                exp, pub = ENTRY_DN
            else:
                yield s2t(oid), f"{oid:35}", f"{tag}.{names}"
                continue

            yield s2t(pub), f"{pub:35}  {exp:35}", f"{tag}.{names}"


def walk_modules() -> Iterator[str]:
    yield ""
    for mod in Path("/usr/lib/ldap").glob("*.so"):
        yield mod.stem


def main() -> None:
    schema: Dict[Tuple[int, ...], Tuple[str, str, Set[str]]] = {}

    for i, mod in enumerate(walk_modules()):
        if sys.stderr.isatty():
            print(f"\r{i}: {mod}", end="\r", file=sys.stderr,)

        with NamedTemporaryFile("w") as tmp:
            tmp.write(f"moduleload {mod}.so" if mod else "")
            tmp.flush()

            cmd = ["slapd", "-f", tmp.name, "-d", "0", "-h", URI]
            proc = Popen(cmd)
            try:
                for key, line, name in dump_schema():
                    _, _, mods = schema.setdefault(key, (line, name, set()),)
                    if "" not in mods:
                        mods.add(mod)
            finally:
                proc.kill()

    print("# new official OpenLDAP 2.4 OID        old Experimental OpenLDAP 2.3 OID")
    for _key, (line, name, mods) in sorted(schema.items()):
        mod = f"{','.join(sorted(mods))}: " if mods - {""} else ""
        print(f"{line}  # {mod}{name}")


if __name__ == "__main__":
    main()
