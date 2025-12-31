#!/bin/bash
#
# Univention Mail Postfix
#  call postmap on transport map and reload postfix
#
# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

postmap /etc/postfix/transport
