#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  UMC configuration
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2011-2024 Univention GmbH
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
Configuration
=============

Global configuration variables and objects for the UMC server.

This module provides a global :class:`!ConfigRegistry` instance *ucr*
some constants that are used internally.
"""
import univention.config_registry


ucr = univention.config_registry.ConfigRegistry()
ucr.load()


def get_int(variable, default):
    return ucr.get_int(variable, default)


SERVER_DEBUG_LEVEL = ucr.get_int('umc/server/debug/level', 2)
SERVER_MAX_CONNECTIONS = ucr.get_int('umc/server/max-connections', 100)

MODULE_COMMAND = '/usr/sbin/univention-management-console-module'

MODULE_DEBUG_LEVEL = ucr.get_int('umc/module/debug/level', 2)
MODULE_INACTIVITY_TIMER = ucr.get_int('umc/module/timeout', 600) * 1000

SQL_CONNECTION_ENV_VAR = 'UMC_SQL_CONNECTION_URI'
