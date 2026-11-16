#!/usr/bin/python3
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

from argparse import ArgumentParser, Namespace

import pytest


INSTALLED = '1.0'
INTERMEDIATE = '2.0'
LATEST = '3.0'
OLDER = '0.9'


@pytest.fixture
def upgrade(get_action, custom_apps, mocked_ucr_appcenter, mocker, import_appcenter_module):
    """An upgrade action whose apps come from a test cache and which never touches the system."""
    app_module = import_appcenter_module('app')
    app_cache = import_appcenter_module('app_cache')
    cache = Namespace(get_ucs_version=lambda: '5.2', get_server=lambda: 'https://appcenter.test')
    custom_apps._test_cache = cache  # App only keeps a weak reference to its cache

    def add_app(app_id, version, installed=False, docker=False):
        docker_attrs = {'docker_image': 'image', 'docker_allowed_images': []} if docker else {}
        app = app_module.App({}, cache, id=app_id, version=version, component_id=f'{app_id}_{version}', install_permissions=False, **docker_attrs)
        mocker.patch.object(app, 'is_installed', return_value=installed)
        custom_apps._test_apps.append(app)

    for app_id in ('app', 'other'):
        add_app(app_id, OLDER)
        add_app(app_id, INSTALLED, installed=True)
        add_app(app_id, INTERMEDIATE)
        add_app(app_id, LATEST)
    add_app('uninstalled', INSTALLED)
    for version in (OLDER, INSTALLED, LATEST):
        add_app('docker', version, installed=version == INSTALLED, docker=True)

    def find_by_string(app_string):
        app_id, app_version, _ucs_version, _server = app_cache.Apps.split_app_string(app_string)
        return custom_apps.find(app_id, app_version=app_version)

    mocker.patch.object(app_cache.Apps, 'find_by_string', side_effect=find_by_string)
    action = get_action('upgrade')()
    mocker.patch.object(action, 'do_it', return_value=True)
    return action


def parse(action, *argv):
    """Parses like scripts/univention-app, which registers every action as a subparser."""
    parser = ArgumentParser()
    action.setup_parser(parser.add_subparsers().add_parser('upgrade'))
    return parser.parse_args(['upgrade', '--noninteractive', *argv])


def targets(action):
    """The (id, version) pairs that main() handed over for upgrading, None if it upgraded nothing."""
    if not action.do_it.called:
        return None
    return [(app.id, app.version) for app in action.do_it.call_args[0][0].app]


def test_explicit_installed_version_is_a_successful_noop(upgrade):
    assert upgrade.main(parse(upgrade, f'app={INSTALLED}')) is True
    assert targets(upgrade) is None


def test_no_version_selects_the_latest_candidate(upgrade):
    assert upgrade.main(parse(upgrade, 'app')) is True
    assert targets(upgrade) == [('app', LATEST)]


@pytest.mark.parametrize('version', [INTERMEDIATE, LATEST])
def test_explicit_newer_version_is_the_target(upgrade, version):
    assert upgrade.main(parse(upgrade, f'app={version}')) is True
    assert targets(upgrade) == [('app', version)]


def test_explicit_older_version_is_rejected(upgrade):
    assert upgrade.main(parse(upgrade, f'app={OLDER}')) is False
    assert targets(upgrade) is None


def test_explicit_version_of_uninstalled_app_is_not_reported_as_installed(upgrade):
    assert upgrade.main(parse(upgrade, f'uninstalled={INSTALLED}')) is False
    assert targets(upgrade) is None


def test_only_matching_apps_are_skipped(upgrade):
    assert upgrade.main(parse(upgrade, f'app={INSTALLED}', f'other={INTERMEDIATE}')) is True
    assert targets(upgrade) == [('other', INTERMEDIATE)]


def test_rejected_app_fails_but_does_not_block_the_others(upgrade):
    assert upgrade.main(parse(upgrade, f'app={OLDER}', f'other={INTERMEDIATE}')) is False
    assert targets(upgrade) == [('other', INTERMEDIATE)]


def test_only_master_packages_still_selects_the_latest_candidate(upgrade):
    assert upgrade.main(parse(upgrade, '--only-master-packages', f'app={INSTALLED}')) is True
    assert targets(upgrade) == [('app', LATEST)]


def test_programmatic_call_with_the_installed_app_selects_the_latest_candidate(upgrade, custom_apps):
    args = upgrade._build_namespace(app=[custom_apps.find('app')], noninteractive=True)
    assert upgrade.main(args) is True
    assert targets(upgrade) == [('app', LATEST)]


def test_programmatic_call_can_request_an_explicit_version(upgrade, custom_apps):
    args = upgrade._build_namespace(app=[custom_apps.find('app')], noninteractive=True, apps_with_explicit_version={'app'})
    assert upgrade.main(args) is True
    assert targets(upgrade) is None


def test_other_actions_keep_the_plain_app_argument(get_action, imported_appcenter_modules, import_appcenter_module):
    actions = import_appcenter_module('actions')
    for name in ('install', 'remove'):
        parser = ArgumentParser()
        get_action(name)().setup_parser(parser)
        app_argument = next(action for action in parser._actions if action.dest == 'app')
        assert type(app_argument) is actions.StoreAppAction


def test_force_is_hidden_from_help(upgrade):
    parser = ArgumentParser()
    upgrade.setup_parser(parser)
    assert '--force' not in parser.format_help()


def test_explicit_older_version_of_docker_app_is_rejected_without_force(upgrade):
    assert upgrade.main(parse(upgrade, f'docker={OLDER}')) is False
    assert targets(upgrade) is None


def test_force_makes_an_older_version_of_docker_app_the_target(upgrade):
    args = parse(upgrade, '--force', f'docker={OLDER}')
    assert upgrade.main(args) is True
    assert targets(upgrade) == [('docker', OLDER)]
    # App.check() would otherwise refuse the older version
    assert args.skip_checks == ['must_have_candidate']


def test_force_keeps_skipping_all_checks(upgrade):
    args = parse(upgrade, '--skip-checks', '--force', f'docker={OLDER}')
    assert upgrade.main(args) is True
    assert args.skip_checks == []


def test_force_with_the_installed_version_is_a_successful_noop(upgrade):
    assert upgrade.main(parse(upgrade, '--force', f'docker={INSTALLED}')) is True
    assert targets(upgrade) is None


def test_force_without_version_selects_the_latest_candidate(upgrade):
    assert upgrade.main(parse(upgrade, '--force', 'docker')) is True
    assert targets(upgrade) == [('docker', LATEST)]


def test_force_is_refused_for_older_version_of_package_app(upgrade):
    # apt does not downgrade packages, only the registered app version would change
    assert upgrade.main(parse(upgrade, '--force', f'app={OLDER}')) is False
    assert targets(upgrade) is None


@pytest.fixture
def docker_upgrade_mode(upgrade, custom_apps, mocker, import_appcenter_module):
    """_docker_upgrade_mode() of the installed Docker app, all versions use the same image."""
    docker_upgrade = import_appcenter_module('actions.docker_upgrade')
    app_module = import_appcenter_module('app')
    mocker.patch.object(docker_upgrade.Start, 'call', return_value=True)
    mocker.patch.object(docker_upgrade, 'get_action')
    mocker.patch.object(app_module.App, 'get_docker_image_name', return_value='image')
    mocker.patch.object(upgrade, '_execute_container_script', return_value=None)  # no update_available script
    upgrade.old_app = custom_apps.find('docker', app_version=INSTALLED)

    def mode(version, force=False):
        upgrade._allow_downgrade = force
        mode, detail = upgrade._docker_upgrade_mode(custom_apps.find('docker', app_version=version))
        return mode or None, detail
    return mode


@pytest.mark.parametrize('force', [False, True])
def test_newer_version_with_the_same_image_upgrades_the_app(docker_upgrade_mode, force):
    assert docker_upgrade_mode(LATEST, force) == ('app', LATEST)


def test_older_version_with_the_same_image_is_nothing_to_upgrade_without_force(docker_upgrade_mode):
    assert docker_upgrade_mode(OLDER) == (None, None)


def test_force_installs_older_version_with_the_same_image(docker_upgrade_mode):
    assert docker_upgrade_mode(OLDER, force=True) == ('app', OLDER)


@pytest.mark.parametrize('force', [False, True])
def test_installed_version_is_nothing_to_upgrade(docker_upgrade_mode, force):
    assert docker_upgrade_mode(INSTALLED, force) == (None, None)
