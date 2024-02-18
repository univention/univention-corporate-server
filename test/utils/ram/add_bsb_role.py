#!/usr/bin/python3
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import multiprocessing
import time
from typing import Dict, List

import concurrent.futures

import univention.admin.uldap
from ucsschool.lib.roles import get_role_info
from univention.config_registry import ConfigRegistry


SEARCH_FILTER = "(&(ucsschoolRole=*)(univentionObjectType=users/user))"
SEARCH_ATTRS = ["ucsschoolRole"]
LDAP_WRITE_PARALLELISM = multiprocessing.cpu_count()


def update_roles_in_memory(dn: str, attrs: Dict[str, List[bytes]]) -> None:
    for role_b in attrs["ucsschoolRole"][:]:
        role_s = role_b.decode()
        role, _context_type, context = get_role_info(role_s)
        bsb_role = f"{role}:bsb:{context}".encode()
        if bsb_role not in attrs["ucsschoolRole"]:
            if "ucsschoolRoleOld" not in attrs:
                attrs["ucsschoolRoleOld"] = attrs["ucsschoolRole"].copy()
            attrs["ucsschoolRole"].append(bsb_role)


if __name__ == "__main__":
    lo, _ = univention.admin.uldap.getAdminConnection()
    ucr = ConfigRegistry()
    ucr.load()

    print(f"Searching for users and groups to modify with filter {SEARCH_FILTER!r}...")
    t0 = time.time()
    objs = lo.search(SEARCH_FILTER, attr=SEARCH_ATTRS)
    print(f"Found {len(objs)} objects to update in {time.time() - t0:.2f} seconds.")

    print("Updating roles in memory...")
    t0 = time.time()
    for dn, attrs in objs:
        update_roles_in_memory(dn, attrs)
    print(f"Updated roles in memory in {time.time() - t0:.2f} seconds.")

    ou_ds = f"ou=DEMOSCHOOL,{ucr['ldap/base']}"
    old_len = len(objs)
    objs = [(dn, attrs) for dn, attrs in objs if not dn.endswith(ou_ds) and "ucsschoolRoleOld" in attrs]
    print(f"Filtered out {old_len - len(objs)} object not to update.")

    print(f"Updating roles of {len(objs)} objects LDAP, using {LDAP_WRITE_PARALLELISM} threads...")
    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=LDAP_WRITE_PARALLELISM) as executor:
        for dn, attrs in objs:
            executor.submit(lo.modify, dn, [("ucsschoolRole", attrs["ucsschoolRoleOld"], attrs["ucsschoolRole"])])
    print(f"Updated roles in LDAP in {time.time() - t0:.2f} seconds.")
