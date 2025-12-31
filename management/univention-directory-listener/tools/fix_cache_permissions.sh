#!/bin/sh -e
#
# SPDX-FileCopyrightText: 2020-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

cachedir=/var/lib/univention-directory-listener
for dir in "$cachedir" /var/lib/univention-ldap/listener; do
	find "$dir" ! -user listener -exec chown listener {} \;
done
