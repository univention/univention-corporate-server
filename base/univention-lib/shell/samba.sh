# shellcheck shell=sh
# Univention Common Shell Library
#
# SPDX-FileCopyrightText: 2011-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

var_lib_samba_is_s4 () {
	test -e /var/lib/samba/private/secrets.ldb
}
