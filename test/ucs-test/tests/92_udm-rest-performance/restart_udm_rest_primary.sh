#!/bin/bash
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

set -e

echo univention > /tmp/univention
master=$(ucr get ldap/master)
univention-ssh /tmp/univention "root@$master" systemctl restart slapd.service
univention-ssh /tmp/univention "root@$master" systemctl restart univention-directory-manager-rest.service
sleep 5
