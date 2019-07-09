#!/usr/bin/python

import univention.admin.objects
import univention.admin.modules as modules
import univention.admin.uldap as uldap
import univention.admin.config as config
import univention.config_registry

import random

lo, position = uldap.getAdminConnection()
co = config.config()
ucr = univention.config_registry.ConfigRegistry()
ucr.load()
base = ucr.get('ldap/base')
cusers = 5000
cgroups = 1050
cuseringroups = 50
cgroupsForTestUser = 50
username = "testuser"
groupname = "testgroup"

modules.update()
users = modules.get('users/user')
modules.init(lo, position, users)
groups = modules.get('groups/group')
modules.init(lo, position, groups)

for i in range(0, cusers):
	name = "%s%s" % (username, i)
	if not users.lookup(co, lo, "uid=%s" % name):
		user = users.object(co, lo, position)
		user.open()
		user["lastname"] = name
		user["password"] = "univention"
		user["username"] = name

for i in range(0, cgroups):
	name = "%s%s" % (groupname, i)
	if not groups.lookup(co, lo, "cn=%s" % name):
		group = groups.object(co, lo, position)
		group.open()
		group["name"] = name
		for u in random.sample(range(cusers), cuseringroups):
			group["users"].append("uid=%s%s,%s" % (username, u, base))

testuser = users.lookup(co, lo, "uid=%s%s" % (username, cusers - 1))
if testuser:
	t = testuser[0]
	t.open()
	for i in range(0, cgroupsForTestUser):
		dn = "cn=%s%s,%s" % (groupname, i, base)
		if dn not in t["groups"]:
			t["groups"].append(dn)
	t.modify()
