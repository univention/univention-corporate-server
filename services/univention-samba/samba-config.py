# -*- coding: utf-8 -*-
#
# Univention Samba
#  listener module: manages samba configuration
#
# Copyright (C) 2001, 2002, 2003, 2004, 2005, 2006 Univention GmbH
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


name='samba-config'
description='Create configuration for Samba shares'
filter='(objectClass=univentionSambaConfig)'
atributes=[]

def handler(dn, new, old):
	listener.setuid(0)
	try:
		if new:
			if new.has_key('univentionSambaPasswordHistory') and new['univentionSambaPasswordHistory']:
				os.system('/usr/bin/pdbedit -P "password history" -C %s' % int(new['univentionSambaPasswordHistory'][0]))
			if new.has_key('univentionSambaMinPasswordLength') and new['univentionSambaMinPasswordLength']:
				os.system('/usr/bin/pdbedit -P "min password length" -C "%s"' % int(new['univentionSambaMinPasswordLength'][0]))
			if new.has_key('univentionSambaMinPasswordAge') and new['univentionSambaMinPasswordAge']:
				os.system('/usr/bin/pdbedit -P "minimum password age" -C "%s"' %int(new['univentionSambaMinPasswordAge'][0]))
			if new.has_key('univentionSambaBadLockoutAttempts') and new['univentionSambaBadLockoutAttempts']:
				os.system('/usr/bin/pdbedit -P "bad lockout attempt" -C "%s"' %int(new['univentionSambaBadLockoutAttempts'][0]))
			if new.has_key('univentionSambaLogonToChangePW') and new['univentionSambaLogonToChangePW']:
				os.system('/usr/bin/pdbedit -P "user must logon to change password" -C "%s"' %int(new['univentionSambaLogonToChangePW'][0]))
			if new.has_key('univentionSambaMaxPasswordAge') and new['univentionSambaMaxPasswordAge']:
				os.system('/usr/bin/pdbedit -P "maximum password age" -C "%s"' %int(new['univentionSambaMaxPasswordAge'][0]))
			if new.has_key('univentionSambaLockoutDuration') and new['univentionSambaLockoutDuration']:
				os.system('/usr/bin/pdbedit -P "lockout duration" -C "%s"' %int(new['univentionSambaLockoutDuration'][0]))
			if new.has_key('univentionSambaResetCountMinutes') and new['univentionSambaResetCountMinutes']:
				os.system('/usr/bin/pdbedit -P "reset count minutes" -C "%s"' %int(new['univentionSambaResetCountMinutes'][0]))
			if new.has_key('univentionSambaDisconnectTime') and new['univentionSambaDisconnectTime']:
				os.system('/usr/bin/pdbedit -P "disconnect time" -C "%s"' %int(new['univentionSambaDisconnectTime'][0]))
			if new.has_key('univentionSambaRefuseMachinePWChange') and new['univentionSambaRefuseMachinePWChange']:
				os.system('/usr/bin/pdbedit -P "refuse machine password change" -C "%s"' %int(new['univentionSambaRefuseMachinePWChange'][0]))
		else:
			if old.has_key('univentionSambaPasswordHistory') and old['univentionSambaPasswordHistory']:
				os.system('/usr/bin/pdbedit -P "password history" -C 0')
			if old.has_key('univentionSambaMinPasswordLength') and old['univentionSambaMinPasswordLength']:
				os.system('/usr/bin/pdbedit -P "min password length" -C 0')
			if old.has_key('univentionSambaMinPasswordAge') and old['univentionSambaMinPasswordAge']:
				os.system('/usr/bin/pdbedit -P "minimum password age" -C 0')
			if old.has_key('univentionSambaBadLockoutAttempts') and old['univentionSambaBadLockoutAttempts']:
				os.system('/usr/bin/pdbedit -P "bad lockout attempt" -C 0')
			if old.has_key('univentionSambaLogonToChangePW') and old['univentionSambaLogonToChangePW']:
				os.system('/usr/bin/pdbedit -P "user must logon to change password" -C "%s"' %int(old['univentionSambaLogonToChangePW'][0]))
			if old.has_key('univentionSambaMaxPasswordAge') and old['univentionSambaMaxPasswordAge']:
				os.system('/usr/bin/pdbedit -P "maximum password age" -C "%s"' %int(old['univentionSambaMaxPasswordAge'][0]))
			if old.has_key('univentionSambaLockoutDuration') and old['univentionSambaLockoutDuration']:
				os.system('/usr/bin/pdbedit -P "lockout duration" -C "%s"' %int(old['univentionSambaLockoutDuration'][0]))
			if old.has_key('univentionSambaResetCountMinutes') and old['univentionSambaResetCountMinutes']:
				os.system('/usr/bin/pdbedit -P "reset count minutes" -C "%s"' %int(old['univentionSambaResetCountMinutes'][0]))
			if old.has_key('univentionSambaDisconnectTime') and old['univentionSambaDisconnectTime']:
				os.system('/usr/bin/pdbedit -P "disconnect time" -C "%s"' %int(old['univentionSambaDisconnectTime'][0]))
			if old.has_key('univentionSambaRefuseMachinePWChange') and old['univentionSambaRefuseMachinePWChange']:
				os.system('/usr/bin/pdbedit -P "refuse machine password change" -C "%s"' %int(old['univentionSambaRefuseMachinePWChange'][0]))
	finally:
		listener.unsetuid()

def postrun():
	listener.setuid(0)
	try:
		if listener.baseConfig.has_key('samba/ha/master') and listener.baseConfig['samba/ha/master']:
			initscript='/etc/heartbeat/resource.d/samba'
		else:
			initscript='/etc/init.d/samba'
		os.spawnv(os.P_WAIT, initscript, ['samba', 'reload'])
	finally:
		listener.unsetuid()
