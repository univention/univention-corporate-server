#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2010-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Univention common Python library for :command:`logrotate` configuration files."""


from univention.config_registry import ConfigRegistry


def _getBoolDefault(varGlobal: str, varLocal: str, settings: dict[str, str], configRegistry: ConfigRegistry) -> None:
    """
    Get default value of type boolean.

    :param str varGlobal: The |UCR| variable name of the global setting.
    :param str varLocal: The |UCR| variable name of the service specific setting.
    :param dict settings: A mapping, where the configuration is stored in.
    :param ConfigRegistry configRegistry: An |UCR| instance.
    """
    configName = varGlobal.rsplit("/", 1)[-1]
    if configRegistry.is_true(varGlobal, True):
        settings[configName] = configName
    if configRegistry.is_false(varLocal) and settings.get(configName):
        del settings[configName]
    if configRegistry.is_true(varLocal, False):
        settings[configName] = configName


def getLogrotateConfig(name: str, configRegistry: ConfigRegistry) -> dict[str, str]:
    """
    Build aggregated configuration for log file rotation.

    :param str name: The name of the log file or service.
    :param ConfigRegistry configRegistry: An |UCR| instance.
    :returns: A dictionary containing the merged configuration.
    :rtype: dict

    >>> ucr = ConfigRegistry()
    >>> ucr.load()
    >>> conf = getLogrotateConfig('service', ucr)
    """
    settings = {}

    for var in ["logrotate/", "logrotate/" + name + "/"]:

        if configRegistry.get(var + "rotate"):
            settings["rotate"] = configRegistry[var + "rotate"]
        if configRegistry.get(var + "rotate/count"):
            settings["rotate/count"] = "rotate " + configRegistry[var + "rotate/count"]
        if configRegistry.get(var + "create"):
            settings["create"] = "create " + configRegistry[var + "create"]

    _getBoolDefault("logrotate/missingok", "logrotate/" + name + "/missingok", settings, configRegistry)
    _getBoolDefault("logrotate/compress", "logrotate/" + name + "/compress", settings, configRegistry)
    _getBoolDefault("logrotate/notifempty", "logrotate/" + name + "/notifempty", settings, configRegistry)

    return settings
