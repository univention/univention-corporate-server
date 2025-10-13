#!/usr/bin/python3
#
# Univention S4 Connector
#  dc sync
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from logging import getLogger

import ldap

import univention.admin.handlers.settings.sambadomain
from univention.logging import Structured
from univention.s4connector.s4 import decode_sid, format_escaped


log = Structured(getLogger("LDAP").getChild(__name__))


def _unixTimeInverval2seconds(unixTime):
    if not isinstance(unixTime, list):
        return unixTime

    if len(unixTime) != 2:
        log.warning('dc _unixTimeInverval2seconds: Not a valid time format: %s', unixTime)
        return 0

    if int(unixTime[0]) < 0:
        return 0

    if unixTime[1] == 'seconds':
        return int(unixTime[0])
    elif unixTime[1] == 'minutes':
        return int(unixTime[0]) * 60
    elif unixTime[1] == 'hours':
        return int(unixTime[0]) * 3600  # 60 * 60
    elif unixTime[1] == 'days':
        return int(unixTime[0]) * 86400  # 60 * 60 * 24
    else:
        log.warning('dc _unixTimeInverval2seconds: Not a valid time unit: %s', unixTime)
        return 0

# Time interval in S4 / AD is often 100-nanosecond intervals:
# http://msdn.microsoft.com/en-us/library/windows/desktop/ms676863%28v=vs.85%29.aspx


def _s2nano(seconds):
    return seconds * 10000000


def _nano2s(nanoseconds):
    return int(nanoseconds / 10000000)


def ucs2con(s4connector, key, object):

    log.debug('dc ucs2con: Object (%s): %s', object['dn'], object)
    s4base_dn, s4base_attr = s4connector.lo_s4.lo.search_s(s4connector.s4_ldap_base, ldap.SCOPE_BASE, '(objectClass=*)')[0]
    log.debug("dc ucs2con: S4 object: %r", s4base_dn)
    log.debug("dc ucs2con: S4 object: %r", s4base_attr)

    if b'univentionBase' in object['attributes'].get('objectClass'):
        # DC object → sync GPO
        if s4connector.configRegistry.is_true('connector/s4/mapping/gpo', True):
            ucs_val = object['attributes'].get('msGPOLink', [None])[0]  # msGPOLink is a single value
            s4_val = s4base_attr.get('msGPOLink')
            if ucs_val != s4_val:
                s4connector.lo_s4.lo.modify_s(s4connector.s4_ldap_base, [(ldap.MOD_REPLACE, 'gPLink', ucs_val)])

    elif b'sambaDomain' in object['attributes'].get('objectClass'):
        # Samba Domain object

        ml = []

        sync_times = [('sambaMaxPwdAge', 'maxPwdAge'), ('sambaMinPwdAge', 'minPwdAge'), ('sambaLockoutDuration', 'lockoutDuration')]
        for (ucs_attr, s4_attr) in sync_times:
            ucs_time = int(object['attributes'].get(ucs_attr, [0])[0])
            s4_time = _nano2s(int(s4base_attr.get(s4_attr, [0])[0]) * -1)

            log.debug('dc ucs2con: ucs_time (%s): %s', ucs_attr, ucs_time)
            log.debug('dc ucs2con: s4-time (%s): %s', s4_attr, s4_time)

            if ucs_time != s4_time:
                s4_time = str(_s2nano(ucs_time) * -1) if ucs_time > 0 else '0'
                ml.append((ldap.MOD_REPLACE, s4_attr, [s4_time.encode('ASCII')]))

        sync_integers = [('sambaPwdHistoryLength', 'pwdHistoryLength'), ('sambaMinPwdLength', 'minPwdLength'), ('univentionSamba4pwdProperties', 'pwdProperties')]
        for (ucs_attr, s4_attr) in sync_integers:
            ucs_val = object['attributes'].get(ucs_attr, b'0')
            s4_val = s4base_attr.get(s4_attr, [b'0'])[0]
            if ucs_val != s4_val:
                ml.append((ldap.MOD_REPLACE, s4_attr, ucs_val))

        if ml:
            log.debug('dc ucs2con: S4 object modlist: %s', ml)
            s4connector.lo_s4.lo.modify_s(s4connector.s4_ldap_base, ml)

    return True


def con2ucs(s4connector, key, object):

    log.debug('dc con2ucs: Object (%s): %s', object['dn'], object)

    # Search sambaDomainname object via sambaSID
    object_sid = decode_sid(object['attributes']['objectSid'][0])
    sambadomainnameObject = univention.admin.handlers.settings.sambadomain.lookup(None, s4connector.lo, format_escaped('sambaSID={0!e}', object_sid))

    if len(sambadomainnameObject) > 1:
        log.warning("dc con2ucs: Found more than one sambaDomainname object with sambaSID %r", object_sid)
    elif len(sambadomainnameObject) == 1:

        # Use the first sambaDomain
        sambadomainnameObject = sambadomainnameObject[0]

        # Do we modify this UCS object
        modify = False

        sync_times = [('maxPasswordAge', 'maxPwdAge'), ('minPasswordAge', 'minPwdAge'), ('lockoutDuration', 'lockoutDuration')]
        for (ucs_attr, s4_attr) in sync_times:
            ucs_time = _unixTimeInverval2seconds(sambadomainnameObject.get(ucs_attr, 0))
            s4_time = _nano2s(int(object['attributes'].get(s4_attr, [0])[0]) * -1)

            if ucs_time != s4_time:
                sambadomainnameObject[ucs_attr] = [str(s4_time), 'seconds']
                modify = True

        sync_integers = [('passwordHistory', 'pwdHistoryLength'), ('passwordLength', 'minPwdLength'), ('domainPwdProperties', 'pwdProperties')]
        for (ucs_attr, s4_attr) in sync_integers:
            ucs_val = sambadomainnameObject.get(ucs_attr, 0)
            s4_val = object['attributes'].get(s4_attr, [None])[0]
            if ucs_val != s4_val:
                sambadomainnameObject[ucs_attr] = s4_val.decode('UTF-8')
                modify = True

        if modify:
            sambadomainnameObject.modify()

    if s4connector.configRegistry.is_true('connector/s4/mapping/gpo', True):
        # Search DC object via ldap search

        dn, attr = s4connector.lo.search('objectClass=*', scope='base')[0]
        ml = []

        ucs_val = attr.get('msGPOLink')
        s4_val = object['attributes'].get('gPLink')

        if ucs_val != s4_val:
            if b'msGPO' not in attr.get('objectClass', []):
                ml.append(('objectClass', b'', b'msGPO'))

            ml.append(('msGPOLink', ucs_val, s4_val))

        if ml:
            s4connector.lo.modify(dn, ml)

    return True


def identify(dn, attr, canonical=0):
    return bool({b'univentionBase', b'sambaDomain'} & set(attr.get('objectClass', [])))
