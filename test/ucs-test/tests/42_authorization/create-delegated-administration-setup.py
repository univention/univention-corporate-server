#!/usr/bin/python3
# SPDX-FileCopyrightText: 2024-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""create setup for environment with delegated administration"""

import argparse
from subprocess import check_call

from univention.config_registry import handler_set, ucr
from univention.lib.misc import custom_groupname
from univention.udm import UDM
from univention.udm.exceptions import NoObject


USER_ROLE = 'udm:default-roles:domain-user'
ADMIN_ROLE = 'udm:default-roles:domain-administrator'
LDAP_BASE = ucr['ldap/base']
GLOBAL_GROUPS = f'cn=groups,{LDAP_BASE}'

udm = UDM.admin().version(3)
ous = udm.get('container/ou')
cns = udm.get('container/cn')
users = udm.get('users/user')
groups = udm.get('groups/group')
umc_policies = udm.get('policies/umc')

NUMBER_OF_OUS = 10
NUMBER_OF_USERS = 10
NUMBER_OF_GROUPS = 5

ALL_ADMIN_USERS = []
register_ldap_deny_user = ALL_ADMIN_USERS.append


def main():
    api_access_group = create_or_modify_obj(groups, name='test-api-access', position=GLOBAL_GROUPS)
    create_or_modify_obj(groups, name=custom_groupname('Domain Admins', ucr), position=GLOBAL_GROUPS, guardianMemberRoles=[ADMIN_ROLE])
    create_or_modify_obj(groups, name=custom_groupname('Domain Users', ucr), position=GLOBAL_GROUPS, guardianMemberRoles=[USER_ROLE])
    umc_policy = create_or_modify_obj(
        umc_policies,
        name='organizational-unit-admins',
        position=f'cn=UMC,cn=policies,{LDAP_BASE}',
        allow=[f'cn=udm-all,cn=operations,cn=UMC,cn=univention,{LDAP_BASE}'],
    )

    kwargs = {'api_access_group': api_access_group, 'umc_policy': umc_policy}

    # create flat OU structure
    for i in range(1, NUMBER_OF_OUS + 1):
        create_ou_structure(LDAP_BASE, f'ou{i}', **kwargs)

    # create hierarchical OU structure
    dn = create_ou_structure(LDAP_BASE, 'bremen', **kwargs)
    dn = create_ou_structure(dn, 'steintor', **kwargs)
    dn = create_ou_structure(dn, 'education', **kwargs)
    create_ou_structure(dn, 'hr', **kwargs)

    ldap_acls_to_deny_access(ALL_ADMIN_USERS)
    create_permissions_and_privileges()
    activate_autorization_in_umc_and_udm_rest(api_access_group.dn)
    restart_services()


def create_permissions_and_privileges():
    check_call(
        ['bash', '-c', '''
time /usr/share/univention-directory-manager-tools/univention-configure-udm-authorization --store-local prune
time /usr/share/univention-directory-manager-tools/univention-configure-udm-authorization --store-local create-permissions
time /usr/share/univention-directory-manager-tools/univention-configure-udm-authorization --store-local create-default-roles
'''])


def activate_autorization_in_umc_and_udm_rest(api_access_dn):
    handler_set([
        'directory/manager/web/delegative-administration/enabled=true',
        'directory/manager/rest/delegative-administration/enabled=true',
        f'directory/manager/rest/authorized-groups/test-api-access={api_access_dn}',
    ])


def ldap_acls_to_deny_access(user_dns):
    aclfile = '/tmp/59-authz-udm-test-acl'
    with open(aclfile, 'w') as fh:
        fh.write(f'''@!@
user_dns = {user_dns!r}
print('# 59-authz-udm-test-acl')
print('access to *')
for dn in user_dns:
    print('     by dn.base="%s" none stop' % (dn,))
print('     by * +0 break')
@!@''')

    check_call([f'. /usr/share/univention-lib/ldap.sh && ucs_registerLDAPExtension --packagename ucs-test --packageversion 3 --ucsversionstart 5.2-2 --ucsversionend 5.99-0 --acl {aclfile}'], shell=True)


def restart_services():
    check_call([
        'systemctl', 'restart',
        'univention-management-console-server',
        'univention-directory-manager-rest',
        'slapd.service',
    ])


def create_or_modify_obj(module, identifying_property='name', position=None, **properties):
    try:
        objs = list(module.search('%s=%s' % (identifying_property, properties[identifying_property]), base=position or LDAP_BASE, scope='one'))
        if not objs:
            raise NoObject()
        assert len(objs) == 1, (properties, position, objs)
        obj = objs[0]
    except NoObject:
        obj = module.new()
        if position is not None:
            obj.position = position

    for key, value in properties.items():
        if isinstance(value, list):
            getattr(obj.props, key).extend(value)
        else:
            setattr(obj.props, key, value)
    return obj.save()


def create_cn(name, position, **props):
    return create_or_modify_obj(cns, position=position, name=name, **props)


def create_group(name, position, **props):
    return create_or_modify_obj(groups, position=position, name=name, **props)


def create_user(name, position, policy=None, **props):
    user = create_or_modify_obj(
        users, 'username', position,
        username=name,
        lastname=name,
        password='univention',
        overridePWHistory='1',
        **props,
    )
    if policy:
        user.policies['policies/umc'].append(policy.dn)
    user.save()
    return user


def create_ou_structure(position, ouname, api_access_group, umc_policy):
    ou = create_or_modify_obj(ous, position=position, name=ouname)

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
    register_ldap_deny_user(create_user(
        f'{ouname}-admin',
        f'cn=users,{LDAP_BASE}',
        policy=umc_policy,
        groups=[api_access_group.dn],
        guardianRoles=[f'udm:default-roles:organizational-unit-admin&udm:contexts:position={ou.dn.rstrip(LDAP_BASE)}'],
    ).dn)
    # Helpdesk Operator (helpdesk-operator)
    register_ldap_deny_user(create_user(
        f'{ouname}-helpdesk-operator',
        f'cn=users,{LDAP_BASE}',
        policy=umc_policy,
        groups=[api_access_group.dn],
        guardianRoles=[f'udm:default-roles:helpdesk-operator&udm:contexts:position={ou.dn.rstrip(LDAP_BASE)}'],
    ).dn)
    # linux client manager user
    register_ldap_deny_user(create_user(
        f'{ouname}-clientmanager',
        f'cn=users,{LDAP_BASE}',
        policy=umc_policy,
        groups=[api_access_group.dn],
        guardianRoles=[f'udm:default-roles:linux-ou-client-manager&udm:contexts:position={ou.dn.rstrip(LDAP_BASE)}'],
    ).dn)

    # user objects in ou
    user_dns = []
    for i in range(1, NUMBER_OF_USERS + 1):
        user = create_user(f'user{i}-{ouname}', cn_users.dn, guardianRoles=['udm:default-roles:dummyrole'])
        user_dns.append(user.dn)
    # group objects
    for i in range(1, NUMBER_OF_GROUPS + 1):
        create_group(f'group{i}-{ouname}', cn_groups.dn, users=user_dns)

    return ou.dn


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    main()
