#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
# -*- coding: utf-8 -*-
## desc: Test the 'System diagnostic' module
## roles-not:
##  - basesystem
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Generator

import pytest
from playwright.sync_api import expect

import univention.testing.strings as uts
from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import plugins
from univention.testing.browser.lib import UMCBrowserTest
from univention.testing.browser.systemdiagnostics import SystemDiagnostic


_ = Translation('ucs-test-browser').translate

PLUGIN_DIR = Path(plugins.__file__).parent


@dataclass
class PluginData:
    title: str
    description: str
    test_action_label: str
    temp_file_name: Path
    plugin_path: Path


@pytest.fixture()
def plugin_data() -> Generator[PluginData, None, None]:
    p_data = create_diagnostics_plugin()

    yield p_data

    if p_data.plugin_path.exists():
        p_data.plugin_path.unlink()

    pyc_file = Path(f'{p_data}c')
    if pyc_file.exists():
        pyc_file.unlink()

    if p_data.temp_file_name.exists():
        p_data.temp_file_name.unlink()


def create_diagnostics_plugin() -> PluginData:
    plugin_path = get_plugin_path()
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.close()
    plugin_data = PluginData(
        '133_system_diagnostics title',
        '133_system_diagnostics description',
        'test_action label',
        Path(temp_file.name),
        plugin_path,
    )

    create_plugin(plugin_path, plugin_data)
    return plugin_data


def create_plugin(plugin_path: Path, plugin_data: PluginData):
    plugin = f"""
#!/usr/bin/python3
# -*- coding: utf-8 -*-

from univention.management.console.modules.diagnostic import Critical

title = '{plugin_data.title}'
description = '{plugin_data.description}'


def run(_umc_instance):
    with open('{plugin_data.temp_file_name}', 'r') as f:
        temp_file_content = f.read().strip()
    if temp_file_content == 'FAIL':
        raise Critical('{plugin_data.description}', buttons=[{{
            'action': 'test_action',
            'label': 'test_action label',
        }}])

def test_action(_umc_instance):
    print('test')


actions = {{
    'test_action': test_action,
}}
""".strip()

    with open(plugin_path, 'w') as fd:
        fd.write(plugin)


def get_plugin_path() -> Path:
    plugin_path = get_random_plugin_path()
    while plugin_path.exists():
        plugin_path = get_random_plugin_path()

    print(f'Test plugin path is {plugin_path}')

    return plugin_path


def get_random_plugin_path() -> Path:
    plugin_name = f'{uts.random_string(length=10, alpha=True, numeric=False)}.py'
    return PLUGIN_DIR / plugin_name


def test_system_diagnostics(umc_browser_test: UMCBrowserTest, plugin_data: PluginData):
    page = umc_browser_test.page

    system_diag = SystemDiagnostic(umc_browser_test)
    system_diag.navigate()

    expect(page.get_by_role('button', name=plugin_data.title)).to_be_hidden()

    with open(plugin_data.temp_file_name, 'w') as fd:
        fd.write('FAIL')

    system_diag.run_system_diagnostics()
    expect(page.get_by_role('button', name=plugin_data.title)).to_be_visible()
