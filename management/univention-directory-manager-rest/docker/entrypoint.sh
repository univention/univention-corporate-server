#!/bin/bash
# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2026 Univention GmbH
#
# Run all executables in /entrypoint.d/ in lexical order, then exec the CMD.

set -euo pipefail

if [[ -d /entrypoint.d ]]; then
  for script in /entrypoint.d/*; do
    if [[ -x "${script}" ]]; then
      echo "[entrypoint] running ${script}"
      "${script}"
    fi
  done
fi

exec "$@"
