#!/usr/share/ucs-test/runner pytest-3 -s -l -v
## desc: Test passing environment variables to the Keycloak container via keycloak/environment/*
## tags: [keycloak, skip_admember]
## roles: [domaincontroller_master]
## exposure: dangerous

import json
import os

import pytest
from utils import run_command

from univention.config_registry.frontend import ucr_update


PREFIX = 'keycloak/environment/'

VALID = {
    'UCS_TEST_KC_ENV_SIMPLE': 'univention',
    'UCS_TEST_KC_ENV_SPECIAL': 'a b: "c" #d \'e\' {f} [g], h=i',
    'UCS_TEST_KC_ENV_UNICODE': 'Grüße äöü ß',
    '_ucs_test_kc_env_lower': 'lower',
}
INVALID = {
    '1UCS_TEST_KC_ENV_DIGIT': 'digit',
    'UCS-TEST-KC-ENV-DASH': 'dash',
    'UCS_TEST_KC_ENV/NESTED': 'nested',
}
# KC_FEATURES is read by Keycloak itself, the result is visible in the server info
FEATURE = {'KC_FEATURES': 'ssf'}


def configure_keycloak() -> None:
    # runs configure_host: re-renders the compose file, recreates the
    # container, waits until it is healthy and re-imports the UCS CA
    run_command(['univention-app', 'configure', 'keycloak'])


def container_env() -> dict[str, str]:
    out = run_command(['docker', 'inspect', '--format', '{{json .Config.Env}}', 'keycloak'])
    return {name: value for name, _, value in (entry.partition('=') for entry in json.loads(out))}


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_environment_expert_settings(ucr_proper, keycloak_admin_connection, is_keycloak):
    """
    Test that keycloak/environment/<NAME> UCR variables are passed as
    environment variables to the Keycloak container, that invalid names are
    ignored and that the variables are removed again after unsetting them.
    """
    variables = {f'{PREFIX}{name}': value for name, value in {**VALID, **INVALID, **FEATURE}.items()}
    ucr_proper.load()
    original = {key: ucr_proper.get(key) for key in variables}
    ucr_update(ucr_proper, variables)
    try:
        configure_keycloak()
        env = container_env()

        for name, value in VALID.items():
            assert env.get(name) == value, f'{name} not passed correctly to the container'
        for name, value in INVALID.items():
            assert name not in env, f'invalid variable name {name} passed to the container'
            assert value not in env.values(), f'value of invalid variable name {name} passed to the container'

        # the variables from the compose file are kept
        assert env.get('KC_HTTP_PORT') == '8180'
        assert env.get('KEYCLOAK_ADMIN') == 'admin'

        # Keycloak uses the variable
        assert env.get('KC_FEATURES') == FEATURE['KC_FEATURES']
        features = {feature['name'].lower(): feature['enabled'] for feature in keycloak_admin_connection.get_server_info()['features']}
        assert features.get('ssf') is True, 'feature from KC_FEATURES not enabled'

        # unset variables are removed from the container
        ucr_update(ucr_proper, dict.fromkeys(variables))
        configure_keycloak()
        env = container_env()
        for name in [*VALID, *FEATURE]:
            assert name not in env, f'{name} still passed to the container after unset'
    finally:
        ucr_proper.load()
        if original != {key: ucr_proper.get(key) for key in variables}:
            ucr_update(ucr_proper, original)
            configure_keycloak()
