#!/usr/bin/python3
#
# Univention AD Connector
#  Mapping functions for proxyAddresses
#
# SPDX-FileCopyrightText: 2016-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from logging import getLogger

from univention.logging import Structured


log = Structured(getLogger("LDAP").getChild(__name__))


def valid_mailaddress(val):
    # invalid is: <transport>:<address> iff <transport>.lower() != smtp
    if not val:
        return
    if isinstance(val, bytes):
        if b':' not in val:
            return val
        else:
            if val.lower().startswith(b'smtp:'):
                return val
    else:
        if ':' not in val:
            return val
        else:
            if val.lower().startswith('smtp:'):
                return val


def equal(values1, values2):
    """
    This is called in these two ways:
    1. in sync_from_ucs: values1 are mapped ucs and values2 are        con
    2. in __set_values:  values1 are        ucs and values2 are mapped con
    """
    log.trace("proxyAddesses: values1: %r", values1)
    log.trace("proxyAddesses: values2: %r", values2)
    values_normalized = []
    for values in (values1, values2):
        if not isinstance(values, list | tuple):
            values = [values]
        values_normalized.append(
            [v for v in map(valid_mailaddress, values) if v],
        )
    return set(values_normalized[0]) == set(values_normalized[1])


def to_proxyAddresses(s4connector, key, object):
    new_con_values = []
    ucs_values = object['attributes'].get('mailPrimaryAddress', [])
    mailPrimaryAddress = ucs_values[0] if ucs_values else None
    if mailPrimaryAddress:
        new_con_value = b'SMTP:' + mailPrimaryAddress
        new_con_values.append(new_con_value)
    for v in object['attributes'].get('mailAlternativeAddress', []):
        if v == mailPrimaryAddress:
            continue
        new_con_value = b'smtp:' + v
        new_con_values.append(new_con_value)
    return new_con_values


def to_mailPrimaryAddress(s4connector, key, object):
    for value in object['attributes'].get('proxyAddresses', []):
        if value.startswith(b'SMTP:'):
            return [value[5:]]
    return []


def to_mailAlternativeAddress(s4connector, key, object):
    new_ucs_values = []
    for value in object['attributes'].get('proxyAddresses', []):
        if value.startswith(b'smtp:'):
            new_ucs_values.append(value[5:])
    return new_ucs_values
