#!/usr/bin/python3
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


def udm_resource_kind(object_type: str) -> str:
    object_type = object_type.replace(':', '-')
    return f'udm:module:{object_type}'


def udm_property_action(prop: str, action: str) -> str:
    prop = prop.replace(':', '-').replace('*', '-')
    action = action.replace(':', '-').replace('*', '-')
    return f'udm:property:{prop}:{action}'


def udm_property_action_wildcards(prop: str, action: str) -> str:
    prop = prop.replace(':', '-')
    action = action.replace(':', '-').replace('*', '-')
    return f'udm:property:{prop}:{action}'


def udm_object_action(action: str) -> str:
    action = action.replace(':', '-').replace('*', '-')
    return f'udm:object:{action}'
