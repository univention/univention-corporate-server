#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: test univention-policy-update-config-registry.py and nfsmounts.py
## exposure: dangerous
## tags: [udm]
## roles: [domaincontroller_master]
## packages:
##   - univention-base-files

import os
import subprocess
import tempfile

import univention.testing.strings as uts
import univention.testing.utils as utils


def test_policy_update_config_registry(udm, ucr):
	prefix = "ucs-test/base-files/policy-result/"
	registry = [(prefix + uts.random_string(), uts.random_string()) for _ in range(5)]
	registry_string_list = ["%s %s" % nu for nu in registry]

	# Create new policies/registry
	policy_name = "policy_" + uts.random_name()
	policy = udm.create_object('policies/registry', name=policy_name, registry=registry_string_list)
	utils.verify_ldap_object(policy, {'cn': [policy_name]})

	# Create new computer computers/domaincontroller_slave and attach the computer to the policy
	computer_name = "computer_" + uts.random_name()
	computer_passw = uts.random_string()
	slave_computer = udm.create_object('computers/domaincontroller_slave', name=computer_name, password=computer_passw, policy_reference=policy)

	script_path = "/usr/lib/univention-directory-policy/univention-policy-update-config-registry"
	with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as secret_file:
		command = [script_path, '-v', '-y', secret_file.name, slave_computer]
		os.fchmod(secret_file.fileno(), 0o600)
		secret_file.write(computer_passw)
		secret_file.flush()

		print("Executing: ", " ".join(command))
		print("Result:", subprocess.check_call(command))

		# Check that key values exists in UCR
		ucr.load()
		prefixed_ucr_keys = [(ucr_key, ucr_value) for ucr_key, ucr_value in ucr.items() if ucr_key.startswith(prefix)]
		assert sorted(prefixed_ucr_keys) == sorted(registry)
