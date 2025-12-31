#!/usr/bin/python3
#
# Univention Management Console
#  UMC configuration
#
# SPDX-FileCopyrightText: 2011-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

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
SQL_POOL_SIZE_ENV_VAR = 'UMC_SQL_POOL_SIZE'
SQL_MAX_OVERFLOW_ENV_VAR = 'UMC_SQL_MAX_OVERFLOW'
SQL_POOL_TIMEOUT_ENV_VAR = 'UMC_SQL_POOL_TIMEOUT'
SQL_POOL_RECYCLE_ENV_VAR = 'UMC_SQL_POOL_RECYCLE'

SQL_URI_SETTINGS_NAME = 'sqlURI'
SQL_POOL_SIZE_SETTINGS_NAME = 'sqlPoolSize'
SQL_MAX_OVERFLOW_SETTINGS_NAME = 'sqlMaxOverflow'
SQL_POOL_TIMEOUT_SETTINGS_NAME = 'sqlPoolTimeout'
SQL_POOL_RECYCLE_SETTINGS_NAME = 'sqlPoolRecycle'

env_to_settings = {
    SQL_CONNECTION_ENV_VAR: (SQL_URI_SETTINGS_NAME, None),
    SQL_POOL_SIZE_ENV_VAR: (SQL_POOL_SIZE_SETTINGS_NAME, '5'),
    SQL_MAX_OVERFLOW_ENV_VAR: (SQL_MAX_OVERFLOW_SETTINGS_NAME, '10'),
    SQL_POOL_TIMEOUT_ENV_VAR: (SQL_POOL_TIMEOUT_SETTINGS_NAME, '30'),
    SQL_POOL_RECYCLE_ENV_VAR: (SQL_POOL_RECYCLE_SETTINGS_NAME, '-1'),
}
