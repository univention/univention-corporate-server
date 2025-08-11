#!/usr/bin/python3
# SPDX-FileCopyrightText: 2011-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Univention Lib Python module."""

__path__ = __import__('pkgutil').extend_path(__path__, __name__)

__all__ = ('I18N_Error', 'Locale', 'NullTranslation', 'Translation', 'get_lock', 'release_lock')

from univention.lib.i18n import I18N_Error, Locale, NullTranslation, Translation
from univention.lib.locking import get_lock, release_lock
