#!/usr/bin/python3
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""create setup for environment with delegated administration"""


from subprocess import check_call

from univention.config_registry import handler_set, ucr
from univention.udm import UDM
from univention.udm.exceptions import CreateError, NoObject


# activate delegated administration
handler_set(['umc/udm/delegation=true'])
check_call(['service', 'univention-management-console-server', 'restart'])

udm = UDM.admin().version(2)
ous = udm.get('container/ou')
cns = udm.get('container/cn')
users = udm.get('users/user')
groups = udm.get('groups/group')
policies = udm.get('policies/umc')

# enable umc udm for ouadmins (Domain Users)
# FIXME: not for everybody, just for ouadmins
r = policies.search('name=default-umc-users')
policy = next(iter(r))
ops = [
    f'cn=udm-groups,cn=operations,cn=UMC,cn=univention,{ucr["ldap/base"]}',
    f'cn=udm-users,cn=operations,cn=UMC,cn=univention,{ucr["ldap/base"]}',
    f'cn=udm-syntax,cn=operations,cn=UMC,cn=univention,{ucr["ldap/base"]}',
    f'cn=udm-mail,cn=operations,cn=UMC,cn=univention,{ucr["ldap/base"]}',
]

for op in ops:
    if op not in policy.props.allow:
        policy.props.allow.append(op)
policy.save()

# domainadmins role for Domain Admins group
r = groups.search('name=Domain Admins')
group = next(iter(r))
admin_role = 'umc:udm:domainadmin'
if admin_role not in group.props.guardianMemberRoles:
    group.props.guardianMemberRoles.append(admin_role)
    group.save()

# ou's and users
number_of_ous = 10
number_of_users = 10
for i in range(1, number_of_ous + 1):

    # ou and users, groups container
    ou = ous.new()
    ou.position = ucr['ldap/base']
    ou.props.name = f'ou{i}'
    ou.props.userPath = "1"
    ou.props.groupPath = "1"
    try:
        ou.save()
    except CreateError:
        pass
    cn = cns.new()
    cn.position = f'ou=ou{i},{ucr["ldap/base"]}'
    cn.props.name = 'users'
    cn.props.userPath = "1"
    try:
        cn.save()
    except CreateError:
        pass
    cn = cns.new()
    cn.position = f'ou=ou{i},{ucr["ldap/base"]}'
    cn.props.name = 'groups'
    cn.props.groupPath = "1"
    try:
        cn.save()
    except CreateError:
        pass

    # ou admin
    user = users.new()
    name = f'ou{i}admin'
    position = f'cn=users,{ucr["ldap/base"]}'
    try:
        user = users.get(f'uid={name},{position}')
    except NoObject:
        user = users.new()
    user.position = f'cn=users,{ucr["ldap/base"]}'
    user.props.username = f'ou{i}admin'
    user.props.lastname = f'ou{i}admin'
    user.props.password = 'univention'
    user.props.overridePWHistory = '1'
    user.props.guardianRoles = [f'umc:udm:ouadmin&umc:udm:ou=ou{i}']
    user.save()

    # user objects in ou
    for j in range(1, number_of_users + 1):
        # position = f'cn=users,ou=ou{i},{ucr["ldap/base"]}'
        position = f'ou=ou{i},{ucr["ldap/base"]}'
        name = f"user{j}-ou{i}"
        user = users.new()
        user.position = position
        user.props.username = name
        user.props.lastname = name
        user.props.password = 'univention'
        try:
            user.save()
            print(f'creat user {name} in {position}')
        except CreateError:
            pass
