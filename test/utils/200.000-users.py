#!/usr/bin/python

import univention.admin.modules as modules
import univention.admin.uldap as uldap
from univention.config_registry import ConfigRegistry


lo, position = uldap.getAdminConnection()
ucr = ConfigRegistry()
ucr.load()
base = ucr.get('ldap/base')
number_of_users = 200000
number_of_groups = 200
username = "testuser"
groupname = "testgroup"

modules.update()
users = modules.get('users/user')
modules.init(lo, position, users)
groups = modules.get('groups/group')
modules.init(lo, position, groups)

group_member = {}
for i in range(0, number_of_users):
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
    group = i % number_of_groups
    if not group_member.get(group):
        group_member[group] = []
    group_member[group].append(dn)

for i in range(0, number_of_groups):
    name = "%s%s" % (groupname, i)
    group = groups.lookup(None, lo, "cn=%s" % name)
    if not group:
        group = groups.object(None, lo, position)
        group.open()
        group["name"] = name
        if group_member.get(i):
            group["users"] = group_member[i]
        print('creating group %s' % name)
        group.create()
    else:
        group[0].open()
        group[0]["users"] = group_member[i]
        print('modify group %s' % name)
        group[0].modify()
