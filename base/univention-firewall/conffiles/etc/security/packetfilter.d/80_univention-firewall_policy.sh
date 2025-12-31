#!/bin/sh
@%@UCRWARNING=# @%@
#
# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

# set default policy for incoming traffic
@!@
policy = configRegistry.get('security/packetfilter/defaultpolicy', 'ACCEPT').upper()
if policy == 'REJECT':
    print('# "REJECT" is no valid default policy - changing default policy to "DROP" and')
    print('# adding final "REJECT" rule in INPUT queue.')
    print('iptables --wait -A INPUT -j REJECT')
    print('ip6tables --wait -A INPUT -j REJECT')
    policy = 'DROP'
print('iptables --wait -P INPUT %s' % policy)
print('iptables --wait -P OUTPUT ACCEPT')
print('ip6tables --wait -P INPUT %s' % policy)
print('ip6tables --wait -P OUTPUT ACCEPT')
@!@
