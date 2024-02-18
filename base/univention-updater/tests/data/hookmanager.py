# For umc/python/updater/__init__.py::HookManager
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


def test_hook(*args, **kwargs):
    print('1ST_TEST_HOOK:', args, kwargs)
    return ('Result', 1)


def other_hook(*args, **kwargs):
    print('OTHER_HOOK:', args, kwargs)
    return 'Other result'


def register_hooks():
    return [
        ('test_hook', test_hook),
        ('pre_hook', other_hook),
    ]
