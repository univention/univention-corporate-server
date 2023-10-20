#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: test UCR policy is applied to host
## exposure: dangerous
## tags: [udm]
## roles: [domaincontroller_master]
## packages:
##   - univention-base-files

import os
import subprocess
import tempfile

import univention.testing.strings as uts
from univention.testing import utils


def test_policy_update_config_registry(udm, ucr):
    PREFIX = "ucs-test/base-files/policy-result/"
    registry = [(PREFIX + uts.random_string(), uts.random_string()) for _ in range(5)]
    registry_string_list = ["%s %s" % nu for nu in registry]

    # Create new policies/registry
    policy_name = "policy_" + uts.random_name()
    policy = udm.create_object('policies/registry', name=policy_name, registry=registry_string_list)
    utils.verify_ldap_object(policy, {'cn': [policy_name]})

    # Create new computer computers/domaincontroller_slave and attach the computer to the policy
    computer_name = "computer_" + uts.random_name()
    computer_passw = uts.random_string()
    slave_computer = udm.create_object('computers/domaincontroller_slave', name=computer_name, password=computer_passw, policy_reference=policy)

    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as secret_file:
        os.fchmod(secret_file.fileno(), 0o600)
        secret_file.write(computer_passw)
        secret_file.flush()

        command = [
            "/usr/lib/univention-directory-policy/univention-policy-update-config-registry",
            '-v',
            '-y', secret_file.name,
            slave_computer,
        ]
        print("Executing: ", " ".join(command))
        print("Result:", subprocess.check_call(command))

    # Check that key values exists in UCR
    ucr.load()
    prefixed_ucr_keys = [(ucr_key, ucr_value) for ucr_key, ucr_value in ucr.items() if ucr_key.startswith(PREFIX)]
    assert sorted(prefixed_ucr_keys) == sorted(registry)
