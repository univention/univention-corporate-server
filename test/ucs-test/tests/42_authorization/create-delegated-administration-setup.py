#!/usr/bin/python3
# SPDX-FileCopyrightText: 2024-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""create setup for environment with delegated administration"""


from subprocess import check_call

from univention.config_registry import handler_set, ucr
from univention.udm import UDM
from univention.udm.exceptions import CreateError, NoObject


# TODO: add to documentation
# activate autorization in UMC and UDM-REST
handler_set(['umc/udm/delegation=true', 'directory/manager/rest/enable-delegative-administration=true'])

# TODO: remove once we are on 5.2-2
handler_set(['directory/manager/object-identifier/autogeneration=true'])
from univention.uldap import getRootDnConnection  # noqa: E402


lo = getRootDnConnection()
result = lo.search(filter='(&(objectClass=univentionObject)(!(univentionObjectIdentifier=*)))', attr=['entryUUID'])
for dn, attrs in result:
    lo.modify(dn, [('univentionObjectIdentifier', None, attrs.get('entryUUID'))])

# TODO: add to documentation
# enable UDM-REST for group used in tests
handler_set(['directory/manager/rest/authorized-groups/test-api-access=cn=test-api-access,cn=groups,dc=ucs,dc=test'])

check_call(['systemctl', 'restart', 'univention-management-console-server'])
check_call(['systemctl', 'restart', 'univention-directory-manager-rest'])

ldap_base = ucr["ldap/base"]

udm = UDM.admin().version(3)
ous = udm.get('container/ou')
cns = udm.get('container/cn')
users = udm.get('users/user')
groups = udm.get('groups/group')
policies = udm.get('policies/umc')

# enable umc udm for ouadmins (Domain Users)
if list(policies.search('name=organizational-unit-amdins')) == []:
    policy = policies.new()
    policy.position = f'cn=UMC,cn=policies,{ldap_base}'
    policy.props.name = 'organizational-unit-amdins'
    policy.props.allow.extend([
        # f'cn=udm-groups,cn=operations,cn=UMC,cn=univention,{ldap_base}',
        # f'cn=udm-users,cn=operations,cn=UMC,cn=univention,{ldap_base}',
        # f'cn=udm-syntax,cn=operations,cn=UMC,cn=univention,{ldap_base}',
        # f'cn=udm-mail,cn=operations,cn=UMC,cn=univention,{ldap_base}',
        f'cn=udm-all,cn=operations,cn=UMC,cn=univention,{ldap_base}',
    ])
    policy.save()
else:
    policy = next(policies.search('name=organizational-unit-amdins'))

# domainadmins role for Domain Admins group
r = groups.search('name=Domain Admins')
group = next(iter(r))

# api access group
if api_access_grouplist := list(groups.search('name=test-api-access')):
    api_access_group = api_access_grouplist[0]
else:
    api_access_group = groups.new()
    api_access_group.props.name = 'test-api-access'
    api_access_group.save()

admin_role = 'udm:default-roles:domain-administrator'
if admin_role not in group.props.guardianMemberRoles:
    group.props.guardianMemberRoles.append(admin_role)
    group.save()

# ou's and users
number_of_ous = 10
number_of_users = 10
number_of_groups = 5
for i in range(1, number_of_ous + 1):

    # ou, users, groups and computer container
    ou = ous.new()
    ou.position = ucr['ldap/base']
    ou.props.name = f'ou{i}'
    try:
        ou.save()
    except CreateError:
        pass

    # user container
    cn = cns.new()
    cn.position = f'ou=ou{i},{ldap_base}'
    cn.props.name = 'users'
    cn.props.userPath = "1"
    try:
        cn.save()
    except CreateError:
        pass

    # groups conainer
    cn = cns.new()
    cn.position = f'ou=ou{i},{ldap_base}'
    cn.props.name = 'groups'
    cn.props.groupPath = "1"
    try:
        cn.save()
    except CreateError:
        pass

    # computers container
    cn = cns.new()
    cn.position = f'ou=ou{i},{ldap_base}'
    cn.props.name = 'computers'
    cn.props.computerPath = '1'
    try:
        cn.save()
    except CreateError:
        pass

    # primary group for ou
    group = groups.new()
    group.position = f'cn=groups,ou=ou{i},{ldap_base}'
    group.props.name = f"ou{i}-users"
    try:
        group.save()
        print('create group ou?-users')
    except CreateError:
        pass

    # ou container with primary group setting
    ou = ous.get(f'ou=ou{i},{ldap_base}')
    ou.options.append('group-settings')
    ou.props.defaultGroup = f'cn=ou{i}-users,cn=groups,ou=ou{i},{ldap_base}'
    ou.save()

    # ou admin
    user = users.new()
    name = f'ou{i}admin'
    position = f'cn=users,{ldap_base}'
    try:
        user = users.get(f'uid={name},{position}')
    except NoObject:
        user = users.new()
    user.position = f'cn=users,{ldap_base}'
    user.props.username = f'ou{i}admin'
    user.props.lastname = f'ou{i}admin'
    user.props.password = 'univention'
    user.props.overridePWHistory = '1'
    user.props.guardianRoles = [
        f'umc:udm:ouadmin&umc:udm:ou=ou{i}',
        f'udm:default-roles:organizational-unit-admin&udm:contexts:ou=ou=ou{i}',
    ]
    user.policies['policies/umc'].append(policy.dn)
    if user.props.groups:
        user.props.groups.append(api_access_group.dn)
    else:
        user.props.groups = [api_access_group.dn]
    user.save()

    # linux client manager user
    user = users.new()
    name = f'ou{i}clientmanager'
    position = f'cn=users,{ldap_base}'
    try:
        user = users.get(f'uid={name},{position}')
    except NoObject:
        user = users.new()
    user.position = f'cn=users,{ldap_base}'
    user.props.username = f'ou{i}clientmanager'
    user.props.lastname = f'ou{i}clientmanager'
    user.props.password = 'univention'
    user.props.overridePWHistory = '1'
    user.props.guardianRoles = [f'umc:udm:linux-client-manager&umc:udm:ou=ou{i}']
    user.policies['policies/umc'].append(policy.dn)
    if user.props.groups:
        user.props.groups.append(api_access_group.dn)
    else:
        user.props.groups = [api_access_group.dn]
    user.save()

    # user objects in ou
    for j in range(1, number_of_users + 1):
        position = f'cn=users,ou=ou{i},{ldap_base}'
        name = f"user{j}-ou{i}"
        user = users.new()
        user.position = position
        user.props.username = name
        user.props.lastname = name
        user.props.password = 'univention'
        user.props.guardianRoles = ['umc:udm:dummyrole']
        try:
            user.save()
            print(f'create user {name} in {position}')
        except CreateError:
            pass

    # group objects in ou
    for j in range(1, number_of_users + 1):
        group = groups.new()
        group.position = f'cn=groups,ou=ou{i},{ldap_base}'
        group.props.name = f"group{j}-ou{i}"
        try:
            group.save()
            print(f'create group {name}')
        except CreateError:
            pass
