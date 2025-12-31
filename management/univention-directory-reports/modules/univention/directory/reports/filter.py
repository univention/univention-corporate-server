#
# Univention Directory Reports
#  write an interpreted token structure to a file
#
# SPDX-FileCopyrightText: 2007-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import univention.admin.localization
import univention.admin.syntax as ua_syntax


translation = univention.admin.localization.translation('univention-directory-reports')
_ = translation.translate

__all__ = ['filter_add', 'filter_get']

_filters = []


def filter_add(types, func):
    _filters.append((types, func))


def filter_get(prop_type):
    for types, func in _filters:
        if isinstance(prop_type, types):
            return func
    return None


def _boolean_filter(prop, key, value):
    if value and value.lower() in ('1', 'yes', 'true'):
        # need to call str() here directly order to force a correct translation
        return (key, str(_('Yes')))
    else:
        # need to call str() here directly order to force a correct translation
        return (key, str(_('No')))


filter_add((ua_syntax.boolean, ua_syntax.TrueFalseUp, ua_syntax.TrueFalse, ua_syntax.TrueFalseUpper, ua_syntax.OkOrNot), _boolean_filter)


def _email_address(prop, key, value):
    if prop.multivalue:
        value = [r'\mbox{%s}' % val for val in value]
    else:
        value = r'\mbox{%s}' % value
    return (key, value)


filter_add((ua_syntax.emailAddress, ), _email_address)


def _samba_group_type(prop, key, value):
    # need to call str() directly in order to force a correct translation
    types = {
        '2': str(_('Domain Group')),
        '3': str(_('Local Group')),
        '5': str(_('Well-Known Group')),
    }
    if value in types.keys():
        value = types[value]
    return (key, value)


filter_add((ua_syntax.sambaGroupType, ), _samba_group_type)
