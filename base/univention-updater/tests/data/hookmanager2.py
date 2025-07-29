# For umc/python/updater/__init__.py::HookManager
#
# SPDX-FileCopyrightText: 2024-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


def test_hook(*args, **kwargs):
    print('2ND_TEST_HOOK:', args, kwargs)
    return ('Result', 2)


def register_hooks():
    return [
        ('test_hook', test_hook),
    ]
