#!/bin/sh
#
# Univention mail Postfix
#
# SPDX-FileCopyrightText: 2014-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

# (re)create DH keys
umask 022
openssl dhparam -out /etc/postfix/dh_512.pem.tmp -2 512 && mv /etc/postfix/dh_512.pem.tmp /etc/postfix/dh_512.pem
#openssl dhparam -out /etc/postfix/dh_1024.pem.tmp -2 1024 && mv /etc/postfix/dh_1024.pem.tmp /etc/postfix/dh_1024.pem
openssl dhparam -out /etc/postfix/dh_2048.pem.tmp -2 2048 && mv /etc/postfix/dh_2048.pem.tmp /etc/postfix/dh_2048.pem
chmod 644 /etc/postfix/dh_2048.pem /etc/postfix/dh_512.pem

invoke-rc.d postfix reload || true

exit 0
