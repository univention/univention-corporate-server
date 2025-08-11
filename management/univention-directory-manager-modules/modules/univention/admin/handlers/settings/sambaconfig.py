# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for samba config"""

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
import univention.admin.password
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate


def logonToChangePWMap(udm_value):
    """
    'User must logon to change PW' behaves like an integer (at least
    to us), but must be stored as either 0 (allow) or 2 (disallow)
    """
    if (udm_value == "1"):
        return b"2"
    else:
        return b"0"


def logonToChangePWUnmap(ldap_value):

    if (ldap_value[0] == b"2"):
        return "1"
    else:
        return "2"


module = 'settings/sambaconfig'
childs = False
# since samba 3.0.30 and UCS 2.1 the domain configuration for samba will be stored in the samba domain object
operations = ['edit', 'remove', 'search', 'move']
short_description = _('Settings: Samba Configuration')
object_name = _('Samba Configuration')
object_name_plural = _('Samba Configuration settings')
long_description = ''
options = {
    'default': univention.admin.option(
        short_description=short_description,
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
        identifies=True,
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
lookup_filter = object.lookup_filter
identify = object.identify
