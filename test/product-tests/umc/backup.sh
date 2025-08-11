#!/bin/bash
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

set -e -x

# shellcheck source=lib.sh
. product-tests/umc/lib.sh

run_umc_tests
