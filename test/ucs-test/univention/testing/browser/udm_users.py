#!/usr/bin/python3
# SPDX-FileCopyrightText: 2023-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from dataclasses import dataclass


@dataclass
class User:
    username: str
    lastname: str
    password: str = 'univention'
    has_popup_after_login: bool = False


@dataclass
class Users:
    regular_user: User
    admin_user: User


def create_test_user(udm, lo) -> User:
    userdn = udm.create_user()[0]
    user_object = lo.get(userdn)

    return User(
        user_object['uid'][0].decode('utf-8'),
        user_object['sn'][0].decode('utf-8'),
    )
