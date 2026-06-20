#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: |
##  Check the UMC query command with a custom INI file.
## roles-not: [basesystem]
## packages:
##   - univention-management-console-module-appcenter
## tags: [appcenter]
## exposure: safe
## bugs: [44768]

import os

import pytest

import univention.testing.strings as str_test
import univention.testing.ucr as ucr_test
from univention import config_registry
from univention.appcenter.app_cache import AppCache
from univention.testing.umc import Client

import appcentertest as app_test


README_TYPES = (
    'README',
    'README_INSTALL',
    'README_POST_INSTALL',
    'README_UPDATE',
    'README_POST_UPDATE',
    'README_UNINSTALL',
    'README_POST_UNINSTALL',
)

RATINGS = (
    'VendorSupported',
    'EditorsAward',
    'PopularityAward',
)


@pytest.fixture(scope='module', autouse=True)
def appcenter_umc_test_mode():
    with ucr_test.UCSTestConfigRegistry():
        config_registry.handler_set(['appcenter/umc/update/always=false'])
        app_test.restart_umc()
        yield
        app_test.restart_umc()


@pytest.fixture
def app_prefix():
    cache = AppCache()
    cache.clear_cache()

    prefix = f'{cache.get_cache_dir()}/testapp_{str_test.random_name()}'
    created_files = []

    def write_file(suffix, content):
        path = f'{prefix}.{suffix}'
        created_files.append(path)
        with open(path, 'w') as fd:
            fd.write(content)

    write_file('ini', '''
[Application]
ID=test_app
Code=00
Name=Test App
Version=11
License=freemium
Description=Test App [EN]

[de]
Description=Test App [DE]
''')

    for readme in README_TYPES:
        for lang in ('EN', 'DE'):
            write_file(f'{readme}_{lang}', f'--{readme}_{lang}--')

    yield prefix, write_file

    for path in created_files:
        if os.path.exists(path):
            os.unlink(path)


def get_app_from_umc(lang='en_US'):
    client = Client.get_test_connection(language=lang)
    apps = client.umc_command(
        'appcenter/query',
        print_response=False,
        print_request_data=False,
    ).result

    matches = [app for app in apps if app['id'] == 'test_app']
    assert matches, 'The test app does not occur in the list of queried apps!'
    return matches[0]


@pytest.mark.parametrize('lang,suffix', [
    ('en_US', 'EN'),
    ('de_DE', 'DE'),
])
def test_umc_query_app_localized_ini_and_readme(app_prefix, lang, suffix):
    app = get_app_from_umc(lang)

    expected_data = {
        'id': 'test_app',
        'code': '00',
        'name': 'Test App',
        'version': '11',
        'license': 'freemium',
        'description': f'Test App [{suffix}]',
    }

    for key, expected_value in expected_data.items():
        assert app[key] == expected_value

    for readme in README_TYPES:
        expected_value = f'--{readme}_{suffix}--'
        assert app[readme.lower()] == expected_value


@pytest.mark.parametrize('ratings', [
    (RATINGS[0], RATINGS[2]),
    (RATINGS[1],),
    (RATINGS[0], RATINGS[1], RATINGS[2]),
])
def test_umc_query_app_ratings(app_prefix, ratings):
    _prefix, write_file = app_prefix

    meta = '[Application]\n'
    for rating in ratings:
        meta += f'{rating}=1\n'

    write_file('meta', meta)

    app = get_app_from_umc()
    actual_ratings = {
        rating['name']
        for rating in app.get('rating', [])
        if rating['value'] == 1
    }

    assert actual_ratings == set(ratings)
