#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test univention-keycloak
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import json
import os

import pytest
from utils import run_command

from univention.testing.strings import random_string
from univention.testing.utils import wait_for_listener_replication
from univention.udm.binary_props import Base64Bzip2BinaryProperty


@pytest.mark.skipif(not os.path.isfile("/etc/keycloak.secret"), reason="fails on hosts without keycloak.secret")
def test_create_oidc_client(keycloak_administrator_connection):
    """Creates and delete OIDC client in Keycloak"""
    client_id = 'foo-cli'
    args = ['univention-keycloak', 'oidc/rp', 'create', '--app-url=', client_id]
    run_command(args)
    keycloak_client_id = keycloak_administrator_connection.get_client_id(client_id)
    if not keycloak_client_id:
        raise RuntimeError(f'Failed to create {client_id} OIDC client')
    keycloak_administrator_connection.delete_client(keycloak_client_id)
    assert not keycloak_administrator_connection.get_client_id(client_id)


@pytest.mark.skipif(not os.path.isfile("/etc/keycloak.secret"), reason="fails on hosts without keycloak.secret")
def test_upgrade_config_status(keycloak_app_version):
    """no upgrade needed after installation"""
    upgrades = run_command(["univention-keycloak", "upgrade-config", "--json", "--get-upgrade-steps"])
    upgrades = json.loads(upgrades)
    assert not upgrades
    # no pending upgrades
    upgrades = run_command(["univention-keycloak", "domain-config", "--json", "--get"])
    upgrades = json.loads(upgrades)
    assert upgrades.get("domain_config_version")
    assert upgrades.get("domain_config_init")


@pytest.mark.skipif(not os.path.isfile("/etc/keycloak.secret"), reason="fails on hosts without keycloak.secret")
def test_upgrade_config_pending_upgrades(upgrade_status_obj):
    """
    remove domain config version and checks for updates
    there should be at least one update
    """
    data = json.loads(upgrade_status_obj.props.data.raw)
    del data["domain_config_version"]
    raw_value = json.dumps(data).encode("ascii")
    upgrade_status_obj.props.data = Base64Bzip2BinaryProperty("data", raw_value=raw_value)
    upgrade_status_obj.save()
    wait_for_listener_replication()
    pending_upgrades = run_command(["univention-keycloak", "upgrade-config", "--json", "--get-upgrade-steps"])
    pending_upgrades = json.loads(pending_upgrades)
    assert len(pending_upgrades) > 0


@pytest.mark.skipif(not os.path.isfile("/etc/keycloak.secret"), reason="fails on hosts without keycloak.secret")
def test_user_attribute_ldap_mapper(keycloak_administrator_connection):
    # create
    name = random_string()
    parent_id = keycloak_administrator_connection.get_components(query={"name": "ldap-provider", "type": "org.keycloak.storage.UserStorageProvider"})[0]["id"]
    run_command(["univention-keycloak", "user-attribute-ldap-mapper", "create", name])
    query = {"parent": parent_id, "type": "org.keycloak.storage.ldap.mappers.LDAPStorageMapper", "name": name}
    mapper = keycloak_administrator_connection.get_components(query=query)
    assert len(mapper) == 1
    mapper = mapper[0]
    assert mapper["providerId"] == "user-attribute-ldap-mapper"
    assert mapper["config"]["ldap.attribute"] == [name]
    assert mapper["config"]["user.model.attribute"] == [name]
    # get
    out = run_command(["univention-keycloak", "user-attribute-ldap-mapper", "get", "--json"])
    out = json.loads(out)
    assert name in out
    # delete
    run_command(["univention-keycloak", "user-attribute-ldap-mapper", "delete", name])
    mapper = keycloak_administrator_connection.get_components(query=query)
    assert len(mapper) == 0
