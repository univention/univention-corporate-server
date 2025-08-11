#!/bin/bash
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

set -e

# shellcheck disable=SC1091
. scenarios/veyon/utils-veyon.sh

destroy_veyon_aws_instances
