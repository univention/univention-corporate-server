#!/usr/bin/python3
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import importlib.machinery
import importlib.util
from pathlib import Path
from unittest.mock import Mock, patch

import jsonschema
import pytest
import requests


_SCRIPT = Path(__file__).parent.parent / 'scripts' / 'univention-telemetry-sender'
_loader = importlib.machinery.SourceFileLoader('univention_telemetry_sender', str(_SCRIPT))
_spec = importlib.util.spec_from_loader('univention_telemetry_sender', _loader)
sender = importlib.util.module_from_spec(_spec)
_loader.exec_module(sender)


PROMETHEUS_TEXT = """\
# HELP version_ucs_info UCS version information
# TYPE version_ucs_info gauge
version_ucs_info{domain="example.com",errata="1234",license_uuid="test-uuid",patch="4",system_uuid="sys-uuid",ucs="5.2"} 1.0
# HELP version_n4k_info Nubus4Kubernetes version information
# TYPE version_n4k_info gauge
# HELP users_user_total Total number of UDM objects of type users/user
# TYPE users_user_total gauge
users_user_total{domain="example.com",license_uuid="test-uuid",platform="ucs"} 42.0
# HELP settings_license_users_limit_total Number of active users permitted by the installed license
# TYPE settings_license_users_limit_total gauge
settings_license_users_limit_total{domain="example.com",license_uuid="test-uuid",platform="ucs"} +Inf
"""

OTLP_SCHEMA = {
    "type": "object",
    "required": ["resourceMetrics"],
    "properties": {
        "resourceMetrics": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["resource", "scopeMetrics"],
                "properties": {
                    "resource": {
                        "type": "object",
                        "required": ["attributes"],
                        "properties": {
                            "attributes": {"$ref": "#/$defs/attributes"},
                        },
                    },
                    "scopeMetrics": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "required": ["scope", "metrics"],
                            "properties": {
                                "scope": {
                                    "type": "object",
                                    "required": ["name"],
                                    "properties": {"name": {"type": "string"}},
                                },
                                "metrics": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "required": ["name", "description", "unit", "gauge"],
                                        "properties": {
                                            "name": {"type": "string"},
                                            "description": {"type": "string"},
                                            "unit": {"type": "string"},
                                            "gauge": {
                                                "type": "object",
                                                "required": ["dataPoints"],
                                                "properties": {
                                                    "dataPoints": {
                                                        "type": "array",
                                                        "minItems": 1,
                                                        "items": {
                                                            "type": "object",
                                                            "required": ["timeUnixNano", "asInt", "attributes"],
                                                            "properties": {
                                                                "timeUnixNano": {"type": "string"},
                                                                "asInt": {"type": "string"},
                                                                "attributes": {"$ref": "#/$defs/attributes"},
                                                            },
                                                        },
                                                    },
                                                },
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
    },
    "$defs": {
        "attributes": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["key", "value"],
                "properties": {
                    "key": {"type": "string"},
                    "value": {
                        "type": "object",
                        "oneOf": [
                            {"required": ["stringValue"], "properties": {"stringValue": {"type": "string"}}},
                            {"required": ["intValue"], "properties": {"intValue": {"type": "string"}}},
                        ],
                    },
                },
            },
        },
    },
}


def test_parse_ucs_version():
    expected = [
        {'labels': {'domain': 'example.com', 'errata': '1234', 'license_uuid': 'test-uuid', 'patch': '4', 'system_uuid': 'sys-uuid', 'ucs': '5.2'}, 'value': 1.0},
    ]
    samples = sender.parse_prometheus_text(PROMETHEUS_TEXT)
    assert samples['version_ucs_info'] == expected


def test_parse_n4k_version():
    text = """\
# HELP version_n4k_info Nubus4Kubernetes version information
# TYPE version_n4k_info gauge
version_n4k_info{domain="example.com",license_uuid="n4k-uuid",major="1",minor="6",patch="1"} 1.0
"""
    expected = [
        {'labels': {'domain': 'example.com', 'license_uuid': 'n4k-uuid', 'major': '1', 'minor': '6', 'patch': '1'}, 'value': 1.0},
    ]
    samples = sender.parse_prometheus_text(text)
    assert samples['version_n4k_info'] == expected


def test_parse_user_count():
    expected = [
        {'labels': {'domain': 'example.com', 'license_uuid': 'test-uuid', 'platform': 'ucs'}, 'value': 42.0},
    ]
    samples = sender.parse_prometheus_text(PROMETHEUS_TEXT)
    assert samples['users_user_total'] == expected


def test_build_otlp_conforms_to_schema():
    samples = sender.parse_prometheus_text(PROMETHEUS_TEXT)
    payload = sender.build_otlp(samples, '1700000000000000000')
    jsonschema.validate(payload, OTLP_SCHEMA)


def test_ucs_version_metric():
    expected = [{
        'name': 'nubus.installation.ucs',
        'description': 'UCS version info per installation (value is always 1)',
        'unit': '1',
        'gauge': {'dataPoints': [{'timeUnixNano': '0', 'asInt': '1', 'attributes': [
            {'key': 'license_uuid', 'value': {'stringValue': 'test-uuid'}},
            {'key': 'ucs', 'value': {'stringValue': '5.2'}},
            {'key': 'patch', 'value': {'intValue': '4'}},
            {'key': 'errata', 'value': {'intValue': '1234'}},
        ]}]},
    }]
    samples = sender.parse_prometheus_text(PROMETHEUS_TEXT)
    assert list(sender._ucs_metrics(samples['version_ucs_info'], '0')) == expected


def test_user_metric():
    expected = [{
        'name': 'nubus.identities.active',
        'description': 'Count of non-deactivated users/user LDAP objects',
        'unit': '1',
        'gauge': {'dataPoints': [{'timeUnixNano': '0', 'asInt': '42', 'attributes': [
            {'key': 'license_uuid', 'value': {'stringValue': 'test-uuid'}},
            {'key': 'platform', 'value': {'stringValue': 'ucs'}},
        ]}]},
    }]
    samples = sender.parse_prometheus_text(PROMETHEUS_TEXT)
    assert list(sender._user_metrics(samples['users_user_total'], '0')) == expected


def test_n4k_metric():
    text = 'version_n4k_info{domain="x",license_uuid="u",major="1",minor="6",patch="1"} 1.0\n'
    expected = [{
        'name': 'nubus.installation.n4k',
        'description': 'N4K version info per installation (value is always 1)',
        'unit': '1',
        'gauge': {'dataPoints': [{'timeUnixNano': '0', 'asInt': '1', 'attributes': [
            {'key': 'license_uuid', 'value': {'stringValue': 'u'}},
            {'key': 'major', 'value': {'intValue': '1'}},
            {'key': 'minor', 'value': {'intValue': '6'}},
            {'key': 'patch', 'value': {'intValue': '1'}},
        ]}]},
    }]
    samples = sender.parse_prometheus_text(text)
    assert list(sender._n4k_metrics(samples['version_n4k_info'], '0')) == expected


def test_send_with_retry_succeeds_on_first_attempt():
    session = Mock()
    session.post.return_value = Mock()

    with patch.object(sender.time, 'sleep') as mock_sleep:
        sender.send_with_retry(session, {})

    assert session.post.call_count == 1
    mock_sleep.assert_not_called()


def test_send_with_retry_succeeds_on_third_attempt():
    session = Mock()
    session.post.side_effect = [
        requests.ConnectionError('timeout'),
        requests.ConnectionError('timeout'),
        Mock(),
    ]

    with patch.object(sender.time, 'sleep') as mock_sleep:
        sender.send_with_retry(session, {})

    assert session.post.call_count == 3
    assert mock_sleep.call_count == 2
    mock_sleep.assert_called_with(sender.RETRY_DELAY)


def test_send_with_retry_raises_after_all_attempts_fail():
    session = Mock()
    session.post.side_effect = requests.ConnectionError('timeout')

    with patch.object(sender.time, 'sleep'), pytest.raises(RuntimeError, match='3 send attempts failed'):
        sender.send_with_retry(session, {})

    assert session.post.call_count == 3


def test_send_with_retry_retries_on_http_error():
    session = Mock()
    response = Mock()
    response.raise_for_status.side_effect = requests.HTTPError('500')
    session.post.return_value = response

    with patch.object(sender.time, 'sleep'), pytest.raises(RuntimeError):
        sender.send_with_retry(session, {})

    assert session.post.call_count == 3
