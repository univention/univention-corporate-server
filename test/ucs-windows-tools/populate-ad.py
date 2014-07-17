import sys
import time

sys.path.append("lib")

import winexe

winexe = winexe.WinExe()
winexe.options.add_option("--user-name", dest="user_name", default="vbsTestUser", help="prefix for the user name (vbsTestUser)")
winexe.options.add_option("--password", dest="password", default="univentionUCS3.2", help="the accounts password (univentionUCS3.2)")
winexe.options.add_option("--users", dest="users", type="int", help="number of users to create (10)", default=10)
winexe.options.add_option("--group-name", dest="group_name", default="vbsTestGroup", help="prefix for the group name (vbsTestGroup)")
winexe.options.add_option("--groups", dest="groups", type="int", help="number of users to create (10)", default=10)
winexe.check_options()

if winexe.opts.users > 0:
	winexe.winexec(
		"create-ad-users",
		winexe.opts.user_name,
		winexe.opts.password,
		winexe.opts.users)

if winexe.opts.groups > 0:
	winexe.winexec(
		"create-ad-groups",
		winexe.opts.group_name,
		winexe.opts.groups)

if winexe.opts.groups > 0 and winexe.opts.users > 0:
	winexe.winexec(
		"add-users-to-group",
		winexe.opts.user_name,
		winexe.opts.users,
		winexe.opts.group_name,
		winexe.opts.groups)

# check user login
if winexe.opts.users > 0:
	for i in range(1, winexe.opts.users + 1):
		userName = "%s%s" % (winexe.opts.user_name, i)
		winexe.check_user_login(userName, winexe.opts.password)

sys.exit(0)

