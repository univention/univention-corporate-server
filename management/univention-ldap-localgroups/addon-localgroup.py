name='addon-localgroup'
description='prints changes from univentionLocalGroup into File'
filter='(objectClass=univentionLocalGroup)'
attributes=['univentionLocalGroupMember','uniqueMember']

import listener
import os
import sys
import univention.debug
import types
import string

def rm_uperm(User,Group):
	##Get root Permissions
	listener.setuid(0)
	for singl_user in User:
		for singl_group in Group:
			start_of_uname=string.find(singl_user,"=")
			end_of_uname=string.find(singl_user,",")
			os.system("gpasswd -d %s %s"%(singl_user[start_of_uname+1:end_of_uname], singl_group))
	listener.unsetuid()

def wr_uperm(User, Group):
	##Get root Permissions
	listener.setuid(0)
	for singl_user in User:
		for singl_group in Group:
			start_of_uname=string.find(singl_user,"=")
			end_of_uname=string.find(singl_user,",")
			os.system("gpasswd -a %s %s"%(singl_user[start_of_uname+1:end_of_uname], singl_group))
	listener.unsetuid()


def handler(dn, new, old):
	##If Object changed:
	if new and old:
			if new.has_key('univentionLocalGroupMember'):
				if old.has_key('univentionLocalGroupMember'):
					if old.has_key('uniqueMember'):
						rm_uperm(old['uniqueMember'], old['univentionLocalGroupMember'])
				wr_uperm(new['uniqueMember'], new['univentionLocalGroupMember'])
			else:
				rm_uperm(old['uniqueMember'], old['univentionLocalGroupMember'])
				
	#If Listener Module is initialised:
	if new and not old:
		if new.has_key('uniqueMember'):
			if new.has_key('univentionLocalGroupMember'):
				wr_uperm(new['uniqueMember'], new['univentionLocalGroupMember'])
