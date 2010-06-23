# -*- coding: utf-8 -*-
#
# Copyright 2004-2010 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

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
