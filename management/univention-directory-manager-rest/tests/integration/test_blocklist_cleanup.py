# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

import hashlib
import os
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from univention.admin.rest.client import UnprocessableEntity


@pytest.mark.skip
def test_blocklist_cleanup(udm_rest_api_client, create_user, udm_url, pytestconfig, delete_obj_after_test):
    properties = create_user(with_univentionObjectIdentifier=True)
    blocklist_list_module = udm_rest_api_client.get('blocklists/list')

    blocklist_list_obj = blocklist_list_module.new()
    blocklist_list_obj_props = {
        'name': 'test-blocklist',
        'retentionTime': '1m',
        'blockingProperties': [
            {
                'module': 'users/user',
                'property': 'firstname',
            },
        ],
    }
    blocklist_list_obj.properties.update(blocklist_list_obj_props)
    blocklist_list_obj.position = 'cn=blocklists,cn=internal'
    blocklist_list_obj.save()
    delete_obj_after_test('blocklists/list', blocklist_list_obj.dn)

    blocklist_entry_module = udm_rest_api_client.get('blocklists/entry')
    blocklist_entry_valid_seconds = 5
    blocklist_entry_value_until = datetime.now(timezone.utc) + timedelta(seconds=blocklist_entry_valid_seconds)
    blocklist_entry_value_sha = hashlib.sha256('test-value'.encode('utf-8')).hexdigest()
    blocklist_entry_obj_props = {
        'value': f'cn=sha256:{blocklist_entry_value_sha}',
        'blockedUntil': blocklist_entry_value_until.strftime('%Y%m%d%H%M%SZ'),
        'originUniventionObjectIdentifier': properties['uuid'],
    }

    blocklist_entry_obj = blocklist_entry_module.new()
    blocklist_entry_obj.properties.update(blocklist_entry_obj_props)
    blocklist_entry_obj.position = blocklist_list_obj.dn
    blocklist_entry_obj.save()
    blocklist_entry_obj_dn = blocklist_entry_obj.dn

    assert blocklist_entry_module.get(blocklist_entry_obj_dn)

    time.sleep(blocklist_entry_valid_seconds)

    blocklist_clean_script_file = Path('docker') / 'blocklist-cleanup' / 'blocklist_clean_expired.py'

    python_cmd = shutil.which('python3')
    assert python_cmd

    username = pytestconfig.getoption('--username')
    password = pytestconfig.getoption('--password')
    with tempfile.NamedTemporaryFile() as fd:
        fd.write(password.encode('UTF-8'))
        fd.flush()
        env_vars = os.environ | {
            'UDM_API_URL': udm_url,
            'UDM_API_USER': username,
            'UDM_API_PASSWORD_FILE': fd.name,
        }
        subprocess.run([python_cmd, blocklist_clean_script_file], check=True, env=env_vars)

    with pytest.raises(UnprocessableEntity):
        blocklist_entry_module.get(blocklist_entry_obj_dn)
