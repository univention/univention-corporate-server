# -*- coding: utf-8 -*-
#
# Univention Scalix
#  listener module: synchronizing information between UCS and Scalix
#
# Copyright (C) 2006 Univention GmbH
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

import listener
import os, string
import univention.debug
import univention_baseconfig

name='scalix-user'
description='update scalix user information'
# attributes=['scalixHideUserEntry', 'scalixMailboxClass', 'scalixLimitMailboxSize', 'scalixLimitOutboundMail', 'scalixLimitInboundMail', 'scalixLimitNotifyUser', 'scalixScalixObject', 'scalixMailnode', 'scalixServerLanguage', 'scalixAdministrator', 'scalixMailboxAdministrator', 'scalixEmailAddress', 'member', 'dn', 'uid', 'objectClass', 'displayName', 'sn', 'givenname', 'initials', 'mail' 'cn', 'facsimileTelephoneNumber', 'homephone', 'street', 'st', 'telephoneNumber', 'title', 'c', 'company', 'departmentNumber', 'description', 'l', 'mobile', 'pager', 'physicalDeliveryOfficeName', 'postalCode', 'mailPrimaryAddress', 'mailAlternativeAddress', 'uniqueMember']
attributes=[]

filter='(scalixScalixObject=TRUE)'

def sync():
	try:
		listener.setuid(0)
		
		# ensure a utf-8-environment
		old_env=None
		if os.environ.has_key('LC_ALL'):
			old_env=os.environ['LC_ALL']
		os.environ['LC_ALL']='de_DE.UTF-8'

		baseConfig = univention_baseconfig.baseConfig()
		baseConfig.load()
		if baseConfig.has_key('scalix/omldapsync/parameter'):
			os.system("/opt/scalix/bin/omldapsync %s >>/var/log/univention/scalix-sync.log" % baseConfig['scalix/omldapsync/parameter'])
		else:
			os.system("/opt/scalix/bin/omldapsync -u ucs2scalix -S >> /var/log/univention/scalix-sync.log")

		if not old_env==None:
			os.environ['LC_ALL']=old_env
		else:
			del os.environ['LC_ALL']

	finally:
		listener.unsetuid()

def handler(dn, new, old):

	if old:
		sync ()
	elif new:
		sync ()

def initialize():
	pass

def clean():
	pass

def postrun():
	pass
