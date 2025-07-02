#!/usr/bin/python3
# SPDX-FileCopyrightText: 2024-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""create setup for environment with delegated administration"""


from subprocess import check_call

from univention.config_registry import handler_set, ucr
from univention.udm import UDM
from univention.udm.exceptions import CreateError, NoObject


# create permissions and privileges
check_call(
    ['bash', '-c', '''
set -eux
date
/usr/share/univention-directory-manager-tools/univention-configure-udm-authorization --store-local prune
/usr/share/univention-directory-manager-tools/univention-configure-udm-authorization --store-local create-permissions
/usr/share/univention-directory-manager-tools/univention-configure-udm-authorization --store-local create-default-roles
date
'''])

# activate autorization in UMC and UDM-REST
handler_set(['directory/manager/web/delegative-administration/enabled=true', 'directory/manager/rest/delegative-administration/enabled=true'])
# TODO: how long do we need this? Do we need documentation?
# special LDAP ACL's to deny access for ouadmins
aclfile = '/tmp/59-authz-udm-test-acl'
with open(aclfile, 'w') as fh:
    fh.write('''@!@
ldap_base = configRegistry['ldap/base']

print('access to *')
for i in range(1, 11):
    print('     by dn.base="uid=ou%dadmin,cn=users,%s" none stop' % (i, ldap_base))
    print('     by dn.base="uid=ou%dhelpdesk-operator,cn=users,%s" none stop' % (i, ldap_base))
    print('     by dn.base="uid=ou%dclientmanager,cn=users,%s" none stop' % (i, ldap_base))
print('     by * +0 break')

@!@''')

cmd = [f'. /usr/share/univention-lib/ldap.sh && ucs_registerLDAPExtension --packagename ucs-test --packageversion 1 --ucsversionstart 5.2-2 --ucsversionend 5.99-0 --acl {aclfile}']
check_call(cmd, shell=True)

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

# domain-user role for Domain Users group
r = groups.search('name=Domain Users')
group = next(iter(r))
admin_role = 'udm:default-roles:domain-user'
if admin_role not in group.props.guardianMemberRoles:
    group.props.guardianMemberRoles.append(admin_role)
    group.save()

# domainadmins role for Domain Admins group
r = groups.search('name=Domain Admins')
group = next(iter(r))
admin_role = 'udm:default-roles:domain-administrator'
if admin_role not in group.props.guardianMemberRoles:
    group.props.guardianMemberRoles.append(admin_role)
    group.save()

# api access group
if api_access_grouplist := list(groups.search('name=test-api-access')):
    api_access_group = api_access_grouplist[0]
else:
    api_access_group = groups.new()
    api_access_group.props.name = 'test-api-access'
    api_access_group.save()

# ou's and users
number_of_ous = 10
number_of_users = 10
number_of_groups = 5


def create_cn(name, position, **props):
    cn = cns.new()
    cn.position = position
    cn.props.name = name
    cn.props.__dict__.update(**props)
    try:
        cn.save()
    except CreateError:
        cn = cns.get(f'cn={name},{position}')
    return cn


def create_group(name, position, **props):
    obj = groups.new()
    obj.position = position
    obj.props.name = name
    obj.props.__dict__.update(**props)
    try:
        obj.save()
    except CreateError:
        obj = groups.get(f'cn={name},{position}')
    return obj


def create_user(name, position, policy=None, **props):
    user = users.new()
    try:
        user = users.get(f'uid={name},{position}')
    except NoObject:
        user = users.new()
    user.position = position
    user.props.username = name
    user.props.lastname = name
    user.props.password = 'univention'
    user.props.overridePWHistory = '1'
    user.props.__dict__.update(**props)
    if policy:
        user.policies['policies/umc'].append(policy.dn)
    user.save()
    return user


def create_ou_structure(position, ouname):
    ou = ous.new()
    ou.position = position
    ou.props.name = ouname
    try:
        ou.save()
    except CreateError:
        ou = ous.get(f'ou={ouname},{position}')
    # user container
    cn_users = create_cn('users', ou.dn, userPath='1')
    # groups conainer
    cn_groups = create_cn('groups', ou.dn, groupPath='1')
    # computers container
    cn_computers = create_cn('computers', ou.dn, computerPath='1')
    # primary user group for ou
    primary_group = create_group(f'{ouname}-users', cn_groups.dn)
    # primary computer group for ou
    computers_group = create_group(f'{ouname}-computers', cn_computers.dn)
    # ou container with primary group setting
    ou.options.append('group-settings')
    ou.props.defaultGroup = primary_group.dn
    ou.props.defaultClientGroup = computers_group.dn
    ou.save()

    # ou admin
    create_user(
        f'{ouname}-admin',
        f'cn=users,{ldap_base}',
        policy=policy,
        groups=[api_access_group.dn],
        guardianRoles=[f'udm:default-roles:organizational-unit-admin&udm:contexts:position={ou.dn.rstrip(ldap_base)}'],
    )
    # Helpdesk Operator (helpdesk-operator)
    create_user(
        f'{ouname}-helpdesk-operator',
        f'cn=users,{ldap_base}',
        policy=policy,
        groups=[api_access_group.dn],
        guardianRoles=[f'udm:default-roles:helpdesk-operator&udm:contexts:position={ou.dn.rstrip(ldap_base)}'],
    )
    # linux client manager user
    create_user(
        f'{ouname}-clientmanager',
        f'cn=users,{ldap_base}',
        policy=policy,
        groups=[api_access_group.dn],
        guardianRoles=[f'udm:default-roles:linux-ou-client-manager&udm:contexts:position={ou.dn.rstrip(ldap_base)}'],
    )

    # user objects in ou
    user_dns = []
    for i in range(1, number_of_users + 1):
        user = create_user(f'user{i}-{ouname}', cn_users.dn, guardianRoles=['umc:udm:dummyrole'])
        user_dns.append(user.dn)
    # group objects
    for i in range(1, number_of_groups + 1):
        create_group(f'group{i}-{ouname}', cn_groups.dn, users=user_dns)


# create flat ou structure
for i in range(1, number_of_ous + 1):
    create_ou_structure(ldap_base, f'ou{i}')

# create hierarchical ou structure
create_ou_structure(ldap_base, 'bremen')
create_ou_structure(f'ou=bremen,{ldap_base}', 'steintor')
create_ou_structure(f'ou=steintor,ou=bremen,{ldap_base}', 'education')
create_ou_structure(f'ou=education,ou=steintor,ou=bremen,{ldap_base}', 'hr')
