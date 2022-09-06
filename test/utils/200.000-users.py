#!/usr/bin/python

import univention.admin.modules as modules
import univention.admin.uldap as uldap
from univention.config_registry import ConfigRegistry


lo, position = uldap.getAdminConnection()
ucr = ConfigRegistry()
ucr.load()
base = ucr.get('ldap/base')
number_of_users = 200000
# every 200th group is a big group containing all users -> 100
# every 350th group is a group that contains 3 nested groups -> 57
# every 880th group also contains a nested group as a nested group -> 22
number_of_groups = 20000
username = "testuser"
groupname = "testgroup"

modules.update()
users = modules.get('users/user')
modules.init(lo, position, users)
groups = modules.get('groups/group')
modules.init(lo, position, groups)
all_users = []
all_groups = []
group_member = {}

position.setDn('cn=users,%s' % (base,))
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
	all_users.append(dn)

position.setDn('cn=groups,%s' % (base,))
has_nested_group = []
for i in range(0, number_of_groups):
	name = "%s%s" % (groupname, i)
	group = groups.lookup(None, lo, "cn=%s" % name)
	new_members = group_member.get(i, [])
	nested_group = False
	if i and not i % 200:
		new_members = all_users
	if i and not i % 550:
		new_members = new_members + [all_groups[i - 1], all_groups[i - 2], all_groups[i - 3]]
		nested_group = True
	if i and not i % 880:
		new_members = new_members + [has_nested_group[:1][0]]
		nested_group = True
	if not group:
		group = groups.object(None, lo, position)
		group.open()
		group["name"] = name
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
