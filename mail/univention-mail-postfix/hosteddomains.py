#!/usr/bin/python3
#
# Univention Mail Stack
#  listener module: mail domain configuration
#
# SPDX-FileCopyrightText: 2005-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import re

import univention.config_registry
import univention.debug

import listener


description = 'update mail/hosteddomains'
filter = '(objectClass=univentionMailDomainname)'


def handler(dn: str, new: dict[str, list[bytes]], old: dict[str, list[bytes]]) -> None:
    configRegistry = univention.config_registry.ConfigRegistry()
    configRegistry.load()

    old_hosteddomains = set(re.split('[ ]+', configRegistry.get('mail/hosteddomains', '')))
    hosteddomains = old_hosteddomains.copy()

    # remove old add new
    if old.get('cn'):
        hosteddomains.discard(old['cn'][0].decode('UTF-8'))
        univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "hosteddomains: removed %r" % old['cn'][0])
    if new.get('cn'):
        hosteddomains.add(new['cn'][0].decode('UTF-8'))
        univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "hosteddomains: added %r" % new['cn'][0])

    # if something changed then set UCR variable
    if old_hosteddomains != hosteddomains:
        try:
            listener.setuid(0)
            univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "hosteddomains: %s" % 'mail/hosteddomains=%s' % ' '.join(hosteddomains))
            univention.config_registry.handler_set(['mail/hosteddomains=%s' % ' '.join(hosteddomains)])
        finally:
            listener.unsetuid()
