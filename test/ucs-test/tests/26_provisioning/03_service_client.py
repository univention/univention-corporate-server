#!/usr/share/ucs-test/runner pytest-3 -s -l -vv --tb=native
## desc: Test the Provisioning Service subscription client lifecycle
## tags: [provisioning]
## exposure: dangerous
## roles: [domaincontroller_master]
## packages:
##  - univention-provisioning-service-client
## apps:
##  - provisioning-service

# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2026 Univention GmbH

import json
import os
import stat
import subprocess

import requests

from univention.config_registry import ucr


CLIENT = "/usr/sbin/univention-provisioning-service-client"
ADMIN_CREDENTIAL_FILE = "/etc/provisioning-secrets.json"


def run_client(*arguments):
    return subprocess.run(
        [CLIENT, *arguments],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_subscription_lifecycle_uses_managed_limited_credential(tmp_path):
    primary = ucr.get("ldap/master")
    base_url = f"https://{primary}/univention/provisioning"
    subscriptions_url = f"{base_url}/v1/subscriptions"
    name = f"ucs-test-service-client-{ucr.get('hostname')}"
    definition = json.dumps(
        {
            "name": name,
            "realms_topics": [{"realm": "udm", "topic": "users/user"}],
            "request_prefill": False,
        }
    )
    admin_password = json.load(open(ADMIN_CREDENTIAL_FILE, encoding="utf-8"))["PROVISIONING_API_ADMIN_PASSWORD"]
    auth = ("admin", admin_password)
    subscription_dir = tmp_path / "runtime-secrets"
    subscription_dir.mkdir(mode=0o700)
    subscription_file = subscription_dir / "subscription.json"

    requests.delete(f"{subscriptions_url}/{name}", auth=auth)
    try:
        created = run_client(
            "subscribe",
            "--provisioning-server",
            primary,
            "--subscription-file",
            os.fspath(subscription_file),
            "--generate-password",
            "--force",
            "--json",
            definition,
        )
        assert created.returncode == 0, created.stderr
        assert admin_password not in created.stdout + created.stderr

        metadata = subscription_file.stat()
        assert stat.S_IMODE(metadata.st_mode) == 0o600
        record = json.loads(subscription_file.read_text(encoding="utf-8"))
        assert record["state"] == "active"
        assert record["subscription"]["name"] == name
        assert record["password"] != admin_password

        response = requests.get(f"{subscriptions_url}/{name}", auth=(name, record["password"]))
        assert response.status_code == 200

        # Reusing an active record must not need the administrator password.
        reused = run_client(
            "subscribe",
            "--provisioning-server",
            primary,
            "--subscription-file",
            os.fspath(subscription_file),
            "--admin-credential-file",
            "/does/not/exist",
            "--generate-password",
            "--json",
            definition,
        )
        assert reused.returncode == 0, reused.stderr
        assert "reused" in reused.stdout

        # A normal removal also authenticates only with the limited secret.
        removed = run_client(
            "unsubscribe",
            "--provisioning-server",
            primary,
            "--subscription-file",
            os.fspath(subscription_file),
            "--admin-credential-file",
            "/does/not/exist",
        )
        assert removed.returncode == 0, removed.stderr
        assert not subscription_file.exists()
        assert name not in {item["name"] for item in requests.get(subscriptions_url, auth=auth).json()}
    finally:
        requests.delete(f"{subscriptions_url}/{name}", auth=auth)
