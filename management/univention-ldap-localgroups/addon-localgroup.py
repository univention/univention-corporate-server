# -*- coding: utf-8 -*-
#
# Copyright (C) 2004, 2005, 2006, 2007 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

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
