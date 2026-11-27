# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from pathlib import Path


def get_data_path(subdirectory: str, system_path: str) -> str:
    """Locate Debian-installed resources or fall back to wheel package data."""
    if Path(system_path).is_dir():
        return system_path
    return str(Path(__file__).with_name(subdirectory))
