#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright 2011-2021 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.
"""
Common commands to manage Debian packages.
"""

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
