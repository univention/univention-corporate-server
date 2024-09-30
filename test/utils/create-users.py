#!/usr/bin/python3
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""create some user/group objects for test environments"""

from argparse import ArgumentParser, Namespace

from univention.admin import modules, uldap
from univention.config_registry import ucr


def main(options: Namespace) -> None:

    lo, position = uldap.getAdminConnection()
    base = ucr['ldap/base']
    number_of_users = options.users
    # every 200th group is a big group containing all users -> 100
    # every 350th group is a group that contains 3 nested groups -> 57
    # every 880th group also contains a nested group as a nested group -> 22
    number_of_groups = options.groups
    username = "testuser"
    groupname = "testgroup"
    modules.update()
    users = modules.get('users/user')
    modules.init(lo, position, users)
    groups = modules.get('groups/group')
    modules.init(lo, position, groups)
    all_users: list[str] = []
    all_groups: list[str] = []
    group_member: dict[int, list[str]] = {}

    position.setDn('cn=users,%s' % (base,))
    for i in range(number_of_users):
        name = "%s%s" % (username, i)
        user = users.lookup(None, lo, "uid=%s" % name)
        if not user:
            user = users.object(None, lo, position)
            user.open()
            user["lastname"] = name
            user["password"] = "univention"
            user["username"] = name
            print('creating user %s' % name)
            dn = user.create()
        else:
            print('get user %s' % name)
            dn = user[0].dn
        if number_of_groups:
            gid = i % number_of_groups
            group_member.setdefault(gid, []).append(dn)
        all_users.append(dn)

    position.setDn('cn=groups,%s' % (base,))
    has_nested_group: list[str] = []
    for i in range(number_of_groups):
        name = "%s%s" % (groupname, i)
        group = groups.lookup(None, lo, "cn=%s" % name)
        new_members = group_member.get(i, [])
        nested_group = False
        if i and not i % 200:
            new_members = all_users
        if i and not i % 550:
            new_members = new_members + [all_groups[i - 1], all_groups[i - 2], all_groups[i - 3]]  # noqa: RUF005
            nested_group = True
        if i and not i % 880:
            new_members = [*new_members, has_nested_group[:1][0]]
            nested_group = True
        if not group:
            group = groups.object(None, lo, position)
            group.open()
            group["name"] = name
            role_name = name.replace(' ', '_').lower()
            group["guardianMemberRoles"] = ['app:ns:%s_role%s' % (role_name, i) for i in range(3)]
            if new_members:
                group["users"] = new_members
            print('creating group %s' % name)
            group.create()
            dn = group.dn
        else:
            group[0].open()
            group[0]["users"] = new_members
            print('modify group %s' % name)
            group[0].modify()
            dn = group[0].dn
        all_groups.append(dn)
        if nested_group:
            has_nested_group.append(dn)


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("-u", "--users", help="How many users to create", type=int, default=200000)
    parser.add_argument("-g", "--groups", help="How many groups to create", type=int, default=20000)
    options = parser.parse_args()
    main(options)
