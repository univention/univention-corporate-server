#
# SPDX-FileCopyrightText: 2018-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


import univention.admin.modules


def get_all_udm_module_names() -> list[str]:
    """
    Get the names of all installed UDM modules.

    :return: list with UDM module names
    """
    univention.admin.modules.update()
    return sorted(mod for mod in univention.admin.modules.modules)
