# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
import argparse
import logging
import pprint

import univention.admin.authorization
import univention.admin.modules
import univention.admin.uldap
import univention.logging
from univention.config_registry import ucr


univention.admin.modules.update()

univention.logging.basicConfig(level=logging.INFO)


def main(args):
    lo_admin, po = univention.admin.uldap.getAdminConnection()

    lo_user = univention.admin.uldap.access(base=ucr["ldap/base"])
    lo_user.bind(f'uid=ou2admin,cn=users,{ucr["ldap/base"]}', 'univention')

    univention.admin.authorization.Authorization.enable(lambda: lo_admin)
    lo_user = univention.admin.authorization.Authorization.inject_ldap_connection(lo_user)

    univention.admin.authorization.Authorization.enabled = False  # prevent early breakpoints
    for modname in {args.module, 'users/user', 'groups/group', 'container/cn', 'container/ou', 'container/dc'}:
        mod = univention.admin.modules.get(modname)
        univention.admin.modules.init(lo_user, po, mod)
    univention.admin.authorization.Authorization.enabled = True

    base = univention.admin.modules.get(args.base_module or args.module).object(None, lo_user, None, args.base)
    if args.permissions:
        evaluate_permissions(base)

    obj = univention.admin.modules.get(args.module).object(None, lo_user, None)
    objs = obj.lookup(None, lo_user, filter_s=args.filter, base=args.base, scope=args.scope)
    for child in objs:
        print('DN:', child.dn)
        for k, v in child.info.items():
            print(k, ':', v)
        print()
        print()


def evaluate_permissions(obj):
    actor, actor_roles = obj.authz._get_cached_user_roles(obj.lo)()
    print(obj.lo.binddn)
    print(actor)
    pprint.pprint(actor_roles)
    perms = obj.authz.engine.get_and_check_permissions(
        *obj.authz._get_data(obj.lo, obj),
        general_permissions_to_check=['udm:%s:read' % obj.module.replace('/', '-')],
        targeted_permissions_to_check=['udm:%s:read' % obj.module.replace('/', '-')],
    )
    print('permissions:')
    pprint.pprint(perms)
    print()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('module')
    parser.add_argument('--base')
    parser.add_argument('--base-module')
    parser.add_argument('--scope', default='sub')
    parser.add_argument('--filter', default='')
    parser.add_argument('--permissions', action='store_true')
    args = parser.parse_args()

    main(args)
