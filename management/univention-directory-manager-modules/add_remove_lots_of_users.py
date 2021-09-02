#!/usr/bin/python2.7

from __future__ import print_function
import datetime
import time
from univention.admin.uldap import getAdminConnection
from univention.config_registry import ConfigRegistry
from univention.udm import NoObject, UDM
import univention.admin.modules


lo, pos = getAdminConnection()
ucr = ConfigRegistry()
ucr.load()
ldap_base = ucr["ldap/base"]
udm = UDM.admin().version(0)
grp_mod = udm.get("groups/group")
base_grp_mod = univention.admin.modules.get("groups/group")
univention.admin.modules.init(lo, pos, base_grp_mod)

num_users_rounds = (10000, 50000, 100000)
grp_name = "testgr{}".format(datetime.date.today().strftime("%Y%m%d"))


class FakeLo(object):
    def __init__(self, get_result):
        self.get_result = get_result

    def get(self, *args, **kwargs):
        print("FakeLo.get() -> returning {} users".format(len(self.get_result.values()[0])))
        return self.get_result

    def modify(self, *args, **kwargs):
        print("FakeLo.modify() -> args repr {} chars long".format(len(repr(args)) + len(repr(kwargs))))
        return True


def delete_group(name):  # type: (str) -> None
    for group_dn in lo.searchDn("(&(univentionObjectType=groups/group)(cn={}))".format(name)):
        lo.delete(group_dn)
        print("Deleted group {!r}.".format(group_dn))
        break
    else:
        print("No group deleted, nothing found with name={!r}.".format(name))


def create_group(name):  # type: (str) -> str
    grp = grp_mod.new()
    grp.position = "cn=groups,{}".format(ldap_base)
    grp.props.name = name
    grp.save()
    print("Created group {!r}.".format(grp.dn))
    return grp.dn


for num_users in num_users_rounds:
    delete_group(grp_name)
    grp_dn = create_group(grp_name)
    users = [
        ("user{:05d}".format(num), "uid=user{:03d},cn=users,{}".format(num, ldap_base))
        for num in range(num_users)
    ]
    grp_obj = base_grp_mod.object(None, lo, pos, grp_dn)
    grp_obj.open()
    # mock LDAP access
    lo_ori = grp_obj.lo
    grp_obj.lo = FakeLo({"memberUid": [u[0] for u in users], "uniqueMember": [u[1] for u in users]})
    print("Removing a user from the group that has {} users...".format(len(users)))
    t0 = time.time()
    grp_obj.fast_member_remove([users[-1][1]], [users[-1][0]])
    t1 = time.time()
    grp_obj.lo = lo_ori
    diff = t1 - t0
    print("==========> Removed a user from a group with {} users in {:.3f} seconds ({}/s). <==========".format(
        len(users), diff, int(len(users) / diff))
    )

num_start_users = 10000

for num_users in num_users_rounds:
    delete_group(grp_name)
    grp_dn = create_group(grp_name)
    users0 = [
        ("startuser{:05d}".format(num), "uid=user{:03d},cn=users,{}".format(num, ldap_base))
        for num in range(num_start_users)
    ]
    users = [
        ("user{:05d}".format(num), "uid=user{:03d},cn=users,{}".format(num, ldap_base))
        for num in range(num_users)
    ]
    grp_obj = base_grp_mod.object(None, lo, pos, grp_dn)
    grp_obj.open()
    # mock LDAP access
    lo_ori = grp_obj.lo
    grp_obj.lo = FakeLo({"memberUid": [u[0] for u in users0], "uniqueMember": [u[1] for u in users0]})
    print("Adding {} users to the group that has already {} users with UDM...".format(len(users), len(users0)))
    t0 = time.time()
    grp_obj.fast_member_add([u[1] for u in users], [u[0] for u in users])
    t1 = time.time()
    grp_obj.lo = lo_ori
    diff = t1 - t0
    print("==========> Added {} users to the group in {:.3f} seconds ({}/s). <==========".format(
        len(users), diff, int(len(users) / diff))
    )

delete_group(grp_name)
