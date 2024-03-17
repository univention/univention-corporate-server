# TODO delete me

import argparse
import time
from random import sample

import dbus
import ldap

import univention.admin.uldap
from univention.admin.uexceptions import objectExists
from univention.config_registry import ConfigRegistry
from univention.udm import UDM


CACHE_BASE = 'cn=cache2,cn=internal'


class RolesTest:

    def __init__(self, opt):
        self.opt = opt

    def open_users(self, dns, roles=False, nested_groups=False, ldap_cache=False):
        for dn in dns:
            user = self.opt.users_mod.get(dn)
            if roles:
                if ldap_cache:
                    dn = f'cn={user.entry_uuid},{CACHE_BASE}'
                    roles = self.opt.connection.get(dn, attr=['postOfficeBox']).get('postOfficeBox')
                    user._orig_udm_object.info['guardianInheritedRoles'] = roles
                else:
                    user._orig_udm_object.open_guardian(nested_groups=nested_groups)
                assert len(user._orig_udm_object.info.get('guardianInheritedRoles', [])) > 290
            else:
                assert len(user._orig_udm_object.info.get('guardianInheritedRoles', [])) == 0

    def get_users(self, users=1):
        return [f'uid=testuser{x},cn=users,{self.opt.ucr["ldap/base"]}' for x in sample(range(1, 200000), users)]

    def clear_caches(self):
        self.restart_slapd()
        self.open_users(self.get_users(users=1))
        univention.admin.guardian_roles.get_group_role.cache_clear()
        univention.admin.guardian_roles.search_group_uniqueMembers.cache_clear()

    def run(self, users=100, **kwargs):
        t_total = 0
        reps = 3
        for i in range(reps):
            self.clear_caches()
            dns = self.get_users(users=users)
            t0 = time.time()
            self.open_users(dns, **kwargs)
            t_total += time.time() - t0
        print(f'open user - users:{users} {kwargs}: {t_total / reps}')

    def restart_slapd(self):
        sysbus = dbus.SystemBus()
        systemd1 = sysbus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1')
        manager = dbus.Interface(systemd1, 'org.freedesktop.systemd1.Manager')
        manager.RestartUnit('slapd.service', 'fail')
        time.sleep(5)


def tests(opt):
    test = RolesTest(opt)
    print('-- simple open --')
    test.run(users=1, roles=False)
    test.run(users=10, roles=False)
    test.run(users=100, roles=False)
    test.run(users=1000, roles=False)
    print('-- open with roles, ldap.get + udm cache --')
    test.run(users=1, roles=True)
    test.run(users=10, roles=True)
    test.run(users=100, roles=True)
    test.run(users=1000, roles=True)
    print('-- open with roles and nested groups, ldap.get + udm cache')
    test.run(users=1, roles=True, nested_groups=True)
    test.run(users=10, roles=True, nested_groups=True)
    test.run(users=100, roles=True, nested_groups=True)
    test.run(users=1000, roles=True, nested_groups=True)
    print('-- open with roles, ldap cache')
    test.run(users=1, roles=True, ldap_cache=True)
    test.run(users=10, roles=True, ldap_cache=True)
    test.run(users=100, roles=True, ldap_cache=True)
    test.run(users=1000, roles=True, ldap_cache=True)


def create_cache(opt):
    cn = ldap.dn.explode_rdn(CACHE_BASE, True)[0]
    try:
        opt.connection.add(CACHE_BASE, [('cn', cn.encode('UTF-8')), ('objectClass', b'organizationalRole')])
    except objectExists:
        pass
    for user in opt.users_mod.search('uid=*'):
        user._orig_udm_object.open_guardian(nested_groups=True)
        cache_dn = f'cn={user.entry_uuid},{CACHE_BASE}'
        try:
            opt.connection.delete(cache_dn)
        except ldap.NO_SUCH_OBJECT:
            pass
        changes = [
            ('cn', user.entry_uuid.encode('UTF-8')),
            ('objectClass', b'organizationalPerson'),
            ('sn', b'sn'),
            ('postOfficeBox', [x.encode('UTF-8') for x in user._orig_udm_object.info.get('guardianInheritedRoles', [])]),
        ]
        opt.connection.add(cache_dn, changes)
        print(cache_dn)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title="subcommands", description="valid subcommands", required=True, dest="command")
    p_tests = subparsers.add_parser("tests", help="run tests")
    p_tests.set_defaults(func=tests)
    p_cache = subparsers.add_parser("cache", help="build user<->roles LDAP cache")
    p_cache.set_defaults(func=create_cache)
    opt = parser.parse_args()
    ucr = ConfigRegistry()
    ucr.load()
    users_mod = UDM.machine().version(2).get('users/user')
    opt.ucr = ucr
    opt.users_mod = users_mod
    opt.connection = users_mod.connection
    opt.func(opt)


if __name__ == '__main__':
    main()
