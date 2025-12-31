#!/bin/sh
@%@UCRWARNING=# @%@
#
# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

## additional source port rule for netbios broadcast answers
iptables --wait -I INPUT 1 -p udp --sport 137 -j ACCEPT
