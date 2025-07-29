#
# SPDX-FileCopyrightText: 2017-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


class ListenerModuleError(Exception):
    pass


class ListenerModuleConfigurationError(ListenerModuleError):
    pass


class ListenerModuleRuntimeError(ListenerModuleError):
    pass
