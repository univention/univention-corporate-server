#!/bin/sh
@%@UCRWARNING=# @%@
#
# SPDX-FileCopyrightText: 2016-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

@!@
for (typ, proto) in [('udp', 'udp'), ('tcp', 'tcp'), ('relp', 'tcp')]:
    port = configRegistry.get('syslog/input/%s' % (typ,))
    if port:
        print("# rsyslog %s" % (typ,))
        print("iptables --wait -A INPUT -p %s --dport %s -j ACCEPT" % (proto, port))
@!@
