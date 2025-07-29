# shellcheck shell=sh
# Univention Common Shell Library
#
# SPDX-FileCopyrightText: 2015-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

#
# ucs_check_license_csp checks the installed UCS license and returns
# an appropriate exitcode depending on the license status and license type.
# ucs_check_license_csp has to be called as user root.
#
# # ucs_check_license_csp ; echo $?
# CSP=True
# 0
#
# # ucs_check_license_csp ; echo $?
# CSP=False
# 10
#
ucs_check_license_csp () {
	python3 -m univention.lib.license_tools
}
