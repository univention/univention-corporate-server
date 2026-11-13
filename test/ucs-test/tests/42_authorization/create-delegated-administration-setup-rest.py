#!/usr/bin/python3
# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""Create setup for environment with delegated administration."""

import argparse

from univention.admin.rest.client import UDM, NotFound


USER_ROLE = 'udm:default-roles:domain-user'
ADMIN_ROLE = 'udm:default-roles:domain-administrator'
LDAP_BASE = 'dc=example,dc=com'

udm = ous = cns = users = groups = umc_policies = None

NUMBER_OF_OUS = 10
NUMBER_OF_USERS = 10
NUMBER_OF_GROUPS = 5

ALL_ADMIN_USERS = []
register_ldap_deny_user = ALL_ADMIN_USERS.append


def main(args):
    global LDAP_BASE, udm, ous, cns, users, groups, umc_policies
    LDAP_BASE = args.ldap_base
    GLOBAL_GROUPS = f'cn=groups,{LDAP_BASE}'

    udm = UDM.http(args.udm_rest_api, args.username, args.password)
    ous = udm.get('container/ou')
    cns = udm.get('container/cn')
    users = udm.get('users/user')
    groups = udm.get('groups/group')
    umc_policies = udm.get('policies/umc')

    api_access_group = create_or_modify_obj(groups, name='test-api-access', position=GLOBAL_GROUPS)
    create_or_modify_obj(groups, name='Domain Admins', position=GLOBAL_GROUPS, guardianMemberRoles=[ADMIN_ROLE])
    create_or_modify_obj(groups, name='Domain Users', position=GLOBAL_GROUPS, guardianMemberRoles=[USER_ROLE])
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


def create_or_modify_obj(module, identifying_property='name', position=None, **properties):
    try:
        objs = list(module.search('%s=%s' % (identifying_property, properties[identifying_property]), position=position or LDAP_BASE, scope='one', opened=True))
        if not objs:
            raise NotFound(None, None, None)
        assert len(objs) == 1, (properties, position, objs)
        obj = objs[0]
    except NotFound:
        obj = module.new(position)

    for key, value in properties.items():
        if isinstance(value, list):
            obj.properties[key].extend(value)
        else:
            obj.properties[key] = value
    obj.save(reload=True)
    return obj


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
        overridePWHistory=True,
        **props,
    )
    if policy:
        user.policies.setdefault('policies/umc', []).append(policy.dn)
    user.save()
    return user


def create_ou_structure(position, ouname, api_access_group, umc_policy):
    ou = create_or_modify_obj(ous, position=position, name=ouname)

    # user container
    cn_users = create_cn('users', ou.dn, userPath=True)
    # groups conainer
    cn_groups = create_cn('groups', ou.dn, groupPath=True)
    # computers container
    cn_computers = create_cn('computers', ou.dn, computerPath=True)
    # primary user group for ou
    primary_group = create_group(f'{ouname}-users', cn_groups.dn)
    # primary computer group for ou
    computers_group = create_group(f'{ouname}-computers', cn_computers.dn)
    # ou container with primary group setting
    ou.options['group-settings'] = True
    ou.properties['defaultGroup'] = primary_group.dn
    ou.properties['defaultClientGroup'] = computers_group.dn
    ou.save()

    # ou admin
    register_ldap_deny_user(create_user(
        f'{ouname}-admin',
        f'cn=users,{LDAP_BASE}',
        policy=umc_policy,
        groups=[api_access_group.dn],
        guardianRoles=[f'udm:default-roles:organizational-unit-admin&udm:contexts:position={ou.dn}'],
    ).dn)
    # Helpdesk Operator (helpdesk-operator)
    register_ldap_deny_user(create_user(
        f'{ouname}-helpdesk-operator',
        f'cn=users,{LDAP_BASE}',
        policy=umc_policy,
        groups=[api_access_group.dn],
        guardianRoles=[f'udm:default-roles:helpdesk-operator&udm:contexts:position={ou.dn}'],
    ).dn)
    # linux client manager user
    register_ldap_deny_user(create_user(
        f'{ouname}-clientmanager',
        f'cn=users,{LDAP_BASE}',
        policy=umc_policy,
        groups=[api_access_group.dn],
        guardianRoles=[f'udm:default-roles:linux-ou-client-manager&udm:contexts:position={ou.dn}'],
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
    parser.add_argument('ldap_base')
    parser.add_argument('--udm-rest-api', required=True)
    parser.add_argument('--username', required=True)
    parser.add_argument('--password', required=True)
    args = parser.parse_args()
    main(args)
