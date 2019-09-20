# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for samba config
#
# Copyright 2004-2019 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.handlers
import univention.admin.password
import univention.admin.allocators
import univention.admin.localization

translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate


def logonToChangePWMap(val):
	"""
	'User must logon to change PW' behaves like an integer (at least
	to us), but must be stored as either 0 (allow) or 2 (disallow)
	"""

	if (val == "1"):
		return "2"
	else:
		return "0"


def logonToChangePWUnmap(val):

	if (val[0] == "2"):
		return "1"
	else:
		return "2"


module = 'settings/sambaconfig'
childs = 0
# since samba 3.0.30 and UCS 2.1 the domain configuration for samba will be stored in the samba domain object
operations = ['edit', 'remove', 'search', 'move']
short_description = _('Settings: Samba Configuration')
object_name = _('Samba Configuration')
object_name_plural = _('Samba Configuration settings')
long_description = ''
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionSambaConfig'],
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Configuration Name'),
		long_description='',
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
		required=True,
		identifies=True
	),
	'passwordLength': univention.admin.property(
		short_description=_('Password Length'),
		long_description='',
		syntax=univention.admin.syntax.integer,
	),
	'passwordHistory': univention.admin.property(
		short_description=_('Password History'),
		long_description='',
		syntax=univention.admin.syntax.integer,
	),
	'minPasswordAge': univention.admin.property(
		short_description=_('Minimum Password Age'),
		long_description='',
		syntax=univention.admin.syntax.UNIX_TimeInterval,
	),
	'badLockoutAttempts': univention.admin.property(
		short_description=_('Bad Lockout Attempts'),
		long_description='',
		syntax=univention.admin.syntax.integer,
	),
	'logonToChangePW': univention.admin.property(
		short_description=_('User must Logon to Change Password'),
		long_description='',
		syntax=univention.admin.syntax.boolean,
	),
	'maxPasswordAge': univention.admin.property(
		short_description=_('Maximum Password Age'),
		long_description='',
		syntax=univention.admin.syntax.UNIX_TimeInterval,
	),
	'lockoutDuration': univention.admin.property(
		short_description=_('Lockout Duration Minutes'),
		long_description='',
		syntax=univention.admin.syntax.UNIX_TimeInterval,
	),
	'resetCountMinutes': univention.admin.property(
		short_description=_('Reset Count Minutes'),
		long_description='',
		syntax=univention.admin.syntax.integer,
	),
	'disconnectTime': univention.admin.property(
		short_description=_('Disconnect Time'),
		long_description='',
		syntax=univention.admin.syntax.UNIX_TimeInterval,
	),
	'refuseMachinePWChange': univention.admin.property(
		short_description=_('Refuse Machine Password Change'),
		long_description='',
		syntax=univention.admin.syntax.boolean,
	),
}

layout = [
	Tab(_('General'), _('Basic values'), layout=[
		Group(_('General Samba configuration settings'), layout=[
			"name",
			["passwordLength", "passwordHistory"],
			["minPasswordAge", "maxPasswordAge"],
			["badLockoutAttempts", "lockoutDuration"],
			["resetCountMinutes", "logonToChangePW"],
			["disconnectTime", "refuseMachinePWChange"],
		]),
	]),
]


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('passwordLength', 'univentionSambaMinPasswordLength', None, univention.admin.mapping.ListToString)
mapping.register('passwordHistory', 'univentionSambaPasswordHistory', None, univention.admin.mapping.ListToString)
mapping.register('minPasswordAge', 'univentionSambaMinPasswordAge', univention.admin.mapping.mapUNIX_TimeInterval, univention.admin.mapping.unmapUNIX_TimeInterval)
mapping.register('maxPasswordAge', 'univentionSambaMaxPasswordAge', univention.admin.mapping.mapUNIX_TimeInterval, univention.admin.mapping.unmapUNIX_TimeInterval)
mapping.register('badLockoutAttempts', 'univentionSambaBadLockoutAttempts', None, univention.admin.mapping.ListToString)
mapping.register('logonToChangePW', 'univentionSambaLogonToChangePW', logonToChangePWMap, logonToChangePWUnmap)
mapping.register('lockoutDuration', 'univentionSambaLockoutDuration', univention.admin.mapping.mapUNIX_TimeInterval, univention.admin.mapping.unmapUNIX_TimeInterval)
mapping.register('resetCountMinutes', 'univentionSambaResetCountMinutes', None, univention.admin.mapping.ListToString)
mapping.register('disconnectTime', 'univentionSambaDisconnectTime', univention.admin.mapping.mapUNIX_TimeInterval, univention.admin.mapping.unmapUNIX_TimeInterval)
mapping.register('refuseMachinePWChange', 'univentionSambaRefuseMachinePWChange', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module

	@classmethod
	def unmapped_lookup_filter(cls):
		return univention.admin.filter.conjunction('&', [
			univention.admin.filter.expression('objectClass', 'univentionSambaConfig'),
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('objectClass', 'univentionDomain')]),
		])


lookup = object.lookup
identify = object.identify
