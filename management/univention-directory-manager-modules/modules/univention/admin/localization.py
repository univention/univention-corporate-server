# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""
|UDM| localization.

usage::

    translation = univention.admin.localization.translation()
    _ = translation.translate
"""

from univention.lib.i18n import Translation


translation = Translation

__all__ = ('translation',)
