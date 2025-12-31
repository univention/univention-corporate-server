#!/usr/bin/python3
# SPDX-FileCopyrightText: 2011-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""Common commands to manage Debian packages."""

from univention.config_registry import ConfigRegistry


configRegistry = ConfigRegistry()
configRegistry.load()

cmd_update = configRegistry.get('update/commands/update', 'apt-get update')
"""Update package cache."""

cmd_show = configRegistry.get('update/commands/show', 'apt-cache show')
"""Show package information."""

cmd_upgrade = configRegistry.get(
    'update/commands/upgrade',
    'apt-get -o DPkg::Options::=--force-confold -o DPkg::Options::=--force-overwrite -o DPkg::Options::=--force-overwrite-dir --trivial-only=no --assume-yes --quiet=1 upgrade')
"""Upgrade only installed packages"""
cmd_upgrade_sim = configRegistry.get(
    'update/commands/upgrade/simulate',
    'apt-get -o DPkg::Options::=--force-confold -o DPkg::Options::=--force-overwrite -o DPkg::Options::=--force-overwrite-dir --trivial-only=no --assume-yes --quiet=1 -s upgrade')
"""Simulate upgrade only installed packages"""

cmd_dist_upgrade = configRegistry.get(
    'update/commands/distupgrade',
    'apt-get -o DPkg::Options::=--force-confold -o DPkg::Options::=--force-overwrite -o DPkg::Options::=--force-overwrite-dir --trivial-only=no --assume-yes --quiet=1 dist-upgrade')
"""Upgrade system, may install new packages to satisfy dependencies"""
cmd_dist_upgrade_sim = configRegistry.get(
    'update/commands/distupgrade/simulate',
    'apt-get -o DPkg::Options::=--force-confold -o DPkg::Options::=--force-overwrite -o DPkg::Options::=--force-overwrite-dir --trivial-only=no --assume-yes --quiet=1 -s dist-upgrade')
"""Simulate upgrade system, may install new packages to satisfy dependencies"""

cmd_install = configRegistry.get(
    'update/commands/install',
    'apt-get -o DPkg::Options::=--force-confold -o DPkg::Options::=--force-overwrite -o DPkg::Options::=--force-overwrite-dir --trivial-only=no --assume-yes --quiet=1 install')
"""Install packages"""

cmd_remove = configRegistry.get('update/commands/remove', 'apt-get --yes remove')
"""Remove packages"""

cmd_config = configRegistry.get('update/commands/configure', 'dpkg --configure -a')
"""Configure all pending packages"""

del ConfigRegistry
del configRegistry
