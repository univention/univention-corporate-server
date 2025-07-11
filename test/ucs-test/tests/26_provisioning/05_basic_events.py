#!/usr/share/ucs-test/runner pytest-3 -s -l -vv --tb=native
## desc: Test create/modify/remove users in the Provisioning Stack
## tags: [provisioning]
## exposure: dangerous
## packages:
##   - python3-univention-provisioning-stack-listener

import json

import pytest
import requests

from univention.testing import utils



@pytest.fixture
def provisioning_url():
    return "http://localhost:7778/"


@pytest.fixture
def provisioning_admin_username():
    return "admin"


@pytest.fixture
def provisioning_admin_password():
    return json.load(open("/etc/provisioning-json.secrets"))["PROVISIONING_API_ADMIN_PASSWORD"]


@pytest.fixture
def subscription(provisioning_url, provisioning_admin_username, provisioning_admin_password):
    name = "01_basic"
    create_sub_json = {
        "name": name,
        "realms_topics": [
            {
                "realm": "udm",
                "topic": "users/user",
            },
        ],
        "request_prefill": False,
        "password": "univention",
    }
    requests.delete(provisioning_url + "v1/subscriptions/%s" % name, auth=(provisioning_admin_username, provisioning_admin_password))
    resp = requests.post(provisioning_url + "v1/subscriptions", json=create_sub_json, auth=(provisioning_admin_username, provisioning_admin_password))
    assert resp.status_code == 201
    return name


@pytest.fixture
def get_messages_and_ack(provisioning_url):
    def f(name):
        while ret := requests.get(provisioning_url + "v1/subscriptions/%s/messages/next?timeout=1" % name, auth=(name, "univention")).json():
            seq_num = ret["sequence_number"]
            yield ret
            stat_json = {
                "status": "ok",
            }
            requests.patch(provisioning_url + "v1/subscriptions/%s/messages/%s/status" % (name, seq_num), json=stat_json, auth=(name, "univention"))
    return f

def test_user_creation(udm, subscription, get_messages_and_ack):
    dn, _username = udm.create_user()

    messages = list(get_messages_and_ack(subscription))
    if len(messages) != 1:
        utils.fail(f"Expected 1 message after user creation, got {len(messages)}.")

    message = messages[0]
    assert message["body"]["old"] == {}, (
        f"Expected 'old' body to be empty, but got: {message['body']['old']}"
    )
    assert message["body"]["new"]["dn"] == dn, (
        f"Expected 'new.dn' to be '{dn}', but got '{message['body']['new'].get('dn')}'."
    )

def test_user_modification(udm, subscription, get_messages_and_ack):
    old_dn, _username = udm.create_user()

    # drain any creation messages
    for _ in get_messages_and_ack(subscription):
        pass

    new_description = "New description"
    udm.modify_object("users/user", dn=old_dn, description=new_description)

    messages = list(get_messages_and_ack(subscription))
    if len(messages) != 1:
        utils.fail(f"Expected 1 message after user modification, got {len(messages)}.")

    message = messages[0]
    assert message["body"]["old"]["properties"]["description"] is None, (
        f"Expected 'old.properties.description' to be None, but got: "
        f"{message['body']['old']['properties'].get('description')}"
    )
    assert message["body"]["new"]["properties"]["description"] == new_description, (
        f"Expected 'new.properties.description' to be '{new_description}', but got: "
        f"{message['body']['new']['properties'].get('description')}"
    )

def test_user_removal(udm, subscription, get_messages_and_ack):

    dn, username = udm.create_user()

    # drain initial messages, if any
    for _ in get_messages_and_ack(subscription):
        pass

    udm.remove_user(username)

    messages = list(get_messages_and_ack(subscription))
    if len(messages) != 1:
        utils.fail(f"Expected 1 message after user removal, got {len(messages)}.")

    message = messages[0]
    assert message["body"]["old"]["dn"] == dn, (
        f"Expected 'old.dn' to be '{dn}', but got '{message['body']['old'].get('dn')}'."
    )
    assert message["body"]["new"] == {}, (
        f"Expected 'new' body to be empty, but got: {message['body']['new']}"
    )