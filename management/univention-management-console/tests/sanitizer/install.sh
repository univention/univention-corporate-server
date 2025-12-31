#!/bin/bash
#
# Univention
#  testscript for the UMC sanitizer
#
# SPDX-FileCopyrightText: 2012-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

install -d /usr/lib/python3/dist-packages/univention/management/console/modules/sanitize/

install -m755 __init__.py /usr/lib/python3/dist-packages/univention/management/console/modules/sanitize/__init__.py
install -m644 sanitize.xml /usr/share/univention-management-console/modules/

. /usr/share/univention-lib/umc.sh
umc_operation_create "sanitize-all" "sanitizer" "" "sanitize/*"
umc_policy_append "default-umc-all" "sanitize-all"
