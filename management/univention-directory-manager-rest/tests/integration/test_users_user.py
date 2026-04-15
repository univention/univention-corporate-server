# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2023-2025 Univention GmbH
"""
Module providing integration tests for the UDM users/user objects.
"""
import urllib.parse

import requests


def test_users_user_get(session: requests.Session, udm_url: str, base_dn: str,
                        create_user):
    properties = create_user()

    dn = f"uid={properties['username']},cn=users,{base_dn}"
    url_users = urllib.parse.urljoin(udm_url, "users/user/")
    url_user = urllib.parse.urljoin(url_users, dn)

    conn = session.get(url_user)
    assert conn.status_code == requests.codes.ok, repr(conn.__dict__)
    result = conn.json()
    assert result["dn"] == dn
    for k, v in properties.items():
        if k == "password":
            continue
        assert result["properties"][k] == v


def test_users_user_post(
    session: requests.Session,
    udm_url: str,
    base_dn: str,
    delete_obj_after_test,
    random_user_properties,
):
    url_users = urllib.parse.urljoin(udm_url, "users/user/")
    properties = random_user_properties()
    dn = f"uid={properties['username']},cn=users,{base_dn}"
    delete_obj_after_test("users/user", dn)

    conn = session.post(url_users, json={"properties": properties})
    assert conn.status_code == requests.codes.created, repr(conn.__dict__)
    post_result = conn.json()
    new_dn = post_result["dn"]
    assert new_dn == dn
    new_uuid = post_result["uuid"]

    conn = session.get(f"{url_users}{new_dn}")
    assert conn.status_code == requests.codes.ok, repr(conn.__dict__)
    result = conn.json()
    assert result["dn"] == new_dn
    assert result["uuid"] == new_uuid
    for k, v in properties.items():
        if k == "password":
            continue
        assert result["properties"][k] == v


def test_users_user_patch(
    session: requests.Session,
    udm_url: str,
    base_dn: str,
    create_user,
    random_user_properties,
):
    properties = create_user()

    dn = f"uid={properties['username']},cn=users,{base_dn}"
    url_users = urllib.parse.urljoin(udm_url, "users/user/")
    url_user = urllib.parse.urljoin(url_users, dn)

    conn = session.get(url_user)
    assert conn.status_code == requests.codes.ok, repr(conn.__dict__)

    properties_new = random_user_properties()
    del properties_new["username"]
    del properties_new["password"]
    conn = session.patch(url_user, json={"properties": properties_new})
    assert conn.status_code == requests.codes.no_content, repr(conn.__dict__)

    conn = session.get(url_user)
    assert conn.status_code == requests.codes.ok, repr(conn.__dict__)
    result = conn.json()
    assert result["dn"] == dn
    for k, v in properties_new.items():
        assert result["properties"][k] == v


def test_users_user_put(
    session: requests.Session,
    udm_url: str,
    base_dn: str,
    create_user,
    random_user_properties,
):
    properties = create_user()

    dn = f"uid={properties['username']},cn=users,{base_dn}"
    url_users = urllib.parse.urljoin(udm_url, "users/user/")
    url_user = urllib.parse.urljoin(url_users, dn)

    conn = session.get(url_user)
    assert conn.status_code == requests.codes.ok, repr(conn.__dict__)
    result = conn.json()

    properties_new = random_user_properties()
    del properties_new["username"]
    del properties_new["password"]
    for k, v in properties_new.items():
        result["properties"][k] = v
    conn = session.put(url_user, json=result)
    assert conn.status_code == requests.codes.no_content, repr(conn.__dict__)

    conn = session.get(url_user)
    assert conn.status_code == requests.codes.ok, repr(conn.__dict__)
    result = conn.json()
    assert result["dn"] == dn
    for k, v in properties_new.items():
        assert result["properties"][k] == v


def test_users_user_delete(session: requests.Session, udm_url: str,
                           base_dn: str, create_user):
    properties = create_user()

    dn = f"uid={properties['username']},cn=users,{base_dn}"
    url_users = urllib.parse.urljoin(udm_url, "users/user/")
    url_user = urllib.parse.urljoin(url_users, dn)

    conn = session.get(url_user)
    assert conn.status_code == requests.codes.ok, repr(conn.__dict__)

    conn = session.delete(url_user)
    assert conn.status_code == requests.codes.no_content, repr(conn.__dict__)

    conn = session.get(url_user)
    assert conn.status_code == requests.codes.not_found, repr(conn.__dict__)
