#!/usr/share/ucs-test/runner pytest-3 -s -l -vv --tb=native
## desc: Test create/modify/remove users in the Provisioning Stack
## tags: [provisioning]
## exposure: dangerous
## packages:
##   - python3-univention-provisioning-stack-listener

import json

import pytest
import requests


@pytest.fixture
def provisioning_url():
    return "http://localhost:7778/"


@pytest.fixture
def provisioning_admin_username():
    return "admin"


@pytest.fixture
def provisioning_admin_password():
    return json.load(open("/etc/provisioning-json.secrets"))["ADMIN_NATS_PASSWORD"]


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
    i = 0
    for message in get_messages_and_ack(subscription):
        i += 1
        assert message["body"]["old"] == {}
        assert message["body"]["new"]["dn"] == dn
    assert i == 1


def test_user_modification(udm, subscription, get_messages_and_ack):
    old_dn, _username = udm.create_user()
    for message in get_messages_and_ack(subscription):
        pass
    new_description = "New description"
    udm.modify_object("users/user", dn=old_dn, description=new_description)
    i = 0
    for message in get_messages_and_ack(subscription):
        i += 1
        assert message["body"]["old"]["properties"]["description"] is None
        assert message["body"]["new"]["properties"]["description"] == new_description
    assert i == 1


def test_user_removal(udm, subscription, get_messages_and_ack):
    dn, username = udm.create_user()
    for message in get_messages_and_ack(subscription):
        pass
    udm.remove_user(username)
    i = 0
    for message in get_messages_and_ack(subscription):
        i += 1
        assert message["body"]["old"]["dn"] == dn
        assert message["body"]["new"] == {}
    assert i == 1
