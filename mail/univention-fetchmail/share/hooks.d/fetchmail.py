# SPDX-FileCopyrightText: 2023-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import json

from univention.admin.hook import AttributeHook, simpleHook


def map_value(value, encoding=()):
    ret = []
    for elem in value:
        entry = []
        for param in elem:
            entry.append(param if isinstance(param, str) else param.decode())
        ret.append(json.dumps(entry).encode(*encoding))
    return ret


def unmap_value(value, encoding=()):
    try:
        entries = [json.loads(v) for v in value]
    except ValueError:
        # try the previous format. This should only happen once as
        # the next time the values will be already json formatted (#56008).
        entries = [[w.strip('"') for w in v.decode(*encoding).split('";"')] for v in value]
    return entries


if AttributeHook.version < 3:
    class FetchMailSingleHook(AttributeHook):
        version = 2
        udm_attribute_name = 'FetchMailSingle'
        ldap_attribute_name = 'univentionFetchmailSingle'

        def map_attribute_value_to_ldap(self, value):
            return map_value(value)

        def map_attribute_value_to_udm(self, value):
            return unmap_value(value)

    class FetchMailMultiHook(AttributeHook):
        version = 2
        udm_attribute_name = 'FetchMailMulti'
        ldap_attribute_name = 'univentionFetchmailMulti'

        def map_attribute_value_to_ldap(self, value):
            return map_value(value)

        def map_attribute_value_to_udm(self, value):
            return unmap_value(value)
else:
    class FetchMailSingleHook(simpleHook):

        map = staticmethod(map_value)
        unmap = staticmethod(unmap_value)

    class FetchMailMultiHook(simpleHook):

        map = staticmethod(map_value)
        unmap = staticmethod(unmap_value)
