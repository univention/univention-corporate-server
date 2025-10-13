#!/usr/bin/python3
#
# Univention Common Python Library
#
# SPDX-FileCopyrightText: 2010-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| library for changing user pasword"""

from ldap.filter import filter_format

import univention.admin.modules
import univention.admin.uldap


univention.admin.modules.update()


def change(username, password):  # type: (str, str) -> None
    """
    Change the password of the given user

    >>> from univention.lib.password import change  # doctest: +SKIP
    >>> change('Administrator', 'secret12345')  # doctest: +SKIP
    >>> change('Administrator@DOMAIN.DE', 'secret12345')  # doctest: +SKIP
    """
    try:
        lo, pos = univention.admin.uldap.getAdminConnection()
    except Exception:
        lo, pos = univention.admin.uldap.getMachineConnection()

    module = univention.admin.modules._get('users/user')

    univention.admin.modules.init(lo, pos, module)

    if '@' in username:  # krb5Principal
        filter = filter_format('krb5PrincipalName=%s', [username])
    else:
        filter = filter_format('uid=%s', [username])
    objects = module.lookup(None, lo, filter, superordinate=None, unique=True, required=True, timeout=-1, sizelimit=0)

    # search was unique and required
    object = objects[0]

    object.open()
    object['password'] = str(password)
    object.modify()
