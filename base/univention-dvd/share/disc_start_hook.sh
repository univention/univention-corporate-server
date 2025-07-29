#!/bin/sh
#
# Univention DVD build settings
#
# SPDX-FileCopyrightText: 2014-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

exec run-parts -a "$1" -a "$2" -a "$3" -a "$4" -a "$5" /usr/share/univention-dvd/disc_start_hook.d/
