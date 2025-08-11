#!/usr/bin/python3
# SPDX-FileCopyrightText: 2021-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Any

from univention.ldap_cache.cache import Cache, get_cache  # noqa: F401


def _extract_id_from_dn(dn: str) -> str:
    """
    We know that this is wrong in general. But to speed up things
    we do not use explode_dn from ldap.
    We use the knowledge about users/user, groups/group, computers/computer objects:
    Their uid / cn must not contain a "," or a "=".
    %timeit dn.split(",", 1)[0].split("=", 1)[1]
    => 300ns
    %timeit ldap.explode_dn(dn, 1)[0]
    => 8µs
    """  # noqa: RUF002
    return dn.split(",", 1)[0].split("=", 1)[1]


def groups_for_user(user_dn: str, consider_nested_groups: bool = True, cache: dict[str, set[str]] | None = None) -> list[str]:
    user_dn = user_dn.lower()
    if cache is None:
        _cache = get_cache()
        subcache = _cache.get_sub_cache('uniqueMembers').load()
        cache = {key: {val.lower() for val in values} for key, values in subcache.items()}
    search_for_dns = [user_dn]
    found: set[str] = set()
    while search_for_dns:
        search_for = search_for_dns.pop().lower()
        for member, dns in cache.items():
            if search_for in dns and member not in found:
                found.add(member)
                search_for_dns.append(member)
        if not consider_nested_groups:
            break
    return sorted(found)


def users_in_group(group_dn: str, consider_nested_groups: bool = True, readers: tuple[Any | None, Any | None] = (None, None), group_cache: dict[str, list[str]] = {}) -> list[str]:
    group_dn = group_dn.lower()
    cache = get_cache()
    member_uid_cache, unique_member_cache = (cache.get_sub_cache(name) for name in ['memberUids', 'uniqueMembers'])
    with member_uid_cache.reading(readers[0]) as member_uid_reader, unique_member_cache.reading(readers[1]) as unique_member_reader:
        ret: set[str] = set()
        members = unique_member_cache.get(group_dn, unique_member_reader)
        if not members:
            return []
        uids = member_uid_cache.get(group_dn, member_uid_reader) or []
        uids = {uid.lower() for uid in uids}
        for member in members:
            rdn = _extract_id_from_dn(member).lower()
            if rdn in uids:
                ret.add(member.lower())
            elif '%s$' % rdn in uids:
                continue
            else:
                if consider_nested_groups:
                    if member in group_cache:
                        ret.update(group_cache[member])
                    else:
                        members = users_in_group(member, consider_nested_groups, readers=(member_uid_reader, unique_member_reader), group_cache=group_cache)
                        group_cache[member] = members
                        ret.update(members)
        return sorted(ret)


def users_groups() -> dict[str, list[str]]:
    """
    Find all user-group relationship, including implicit ones:
    if Group1 have Group2 as a subgroup, all users from Group2
    are also considered members of Group1.
    """
    cache = get_cache()
    member_uid_cache, unique_member_cache = (cache.get_sub_cache(name) for name in ['memberUids', 'uniqueMembers'])

    group_users: dict[str, list[str]] = {}
    _group_cache: dict[str, list[str]] = {}
    with member_uid_cache.reading() as member_uid_reader, unique_member_cache.reading() as unique_member_reader:
        for group in unique_member_cache.keys():
            group_users[group] = users_in_group(group, readers=(member_uid_reader, unique_member_reader), group_cache=_group_cache)

    res: dict[str, set[str]] = {}
    for group, members in group_users.items():
        for member in members:
            groups = res.setdefault(member, set())
            groups.add(group)

    # return groups as sorted list
    return {_extract_id_from_dn(user): sorted(groups) for user, groups in res.items()}
