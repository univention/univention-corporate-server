#!/usr/bin/python3
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from types import SimpleNamespace
from unittest.mock import patch

import pytest


@pytest.mark.parametrize('value,expected', [(False, 'False'), (True, 'True')])
def test_list_setting_preserves_boolean_selection(value, expected):
    from univention.appcenter.settings import BoolSetting, ListSetting

    app = SimpleNamespace(docker=False)
    old_setting = BoolSetting(name='test/boolean-list')
    new_setting = ListSetting(name=old_setting.name, values=['True', 'False'])

    configuration = {}
    old_setting.set_value_together(app, value, configuration)
    stored_value = configuration['outside'][old_setting.name]
    with patch('univention.appcenter.settings.ucr_get', return_value=stored_value):
        assert new_setting.get_value(app) == expected
        upgrade_value = old_setting.get_value(app)

    configuration = {}
    new_setting.set_value_together(app, upgrade_value, configuration)
    assert configuration == {'outside': {new_setting.name: expected}}


def test_list_setting_keeps_other_lists_strict():
    from univention.appcenter.settings import ListSetting, SettingValueError

    setting = ListSetting(name='test/enum', values=['True', 'False', 'auto'])
    assert setting.sanitize_value(None, 'False') == 'False'
    for value in (False, 'false'):
        with pytest.raises(SettingValueError):
            setting.sanitize_value(None, value)
