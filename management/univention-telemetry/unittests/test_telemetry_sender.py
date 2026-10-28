#!/usr/bin/python3
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import importlib.machinery
import importlib.util
import json
from pathlib import Path
from unittest.mock import Mock

import jsonschema
import pytest
import requests


_SCRIPT = Path(__file__).parent.parent / 'scripts' / 'univention-telemetry-sender'
_loader = importlib.machinery.SourceFileLoader('univention_telemetry_sender', str(_SCRIPT))
_spec = importlib.util.spec_from_loader('univention_telemetry_sender', _loader)
sender = importlib.util.module_from_spec(_spec)
_loader.exec_module(sender)


PROMETHEUS_TEXT = """\
# HELP nubus_ucs_version_info UCS version information
# TYPE nubus_ucs_version_info gauge
nubus_ucs_version_info{domain="example.com",errata="1234",license_uuid="test-uuid",patch="4",system_uuid="sys-uuid",ucs="5.2"} 1.0
# HELP nubus_n4k_version_info Nubus for Kubernetes version information
# TYPE nubus_n4k_version_info gauge
# HELP nubus_users_user_total Total number of UDM objects of type users/user
# TYPE nubus_users_user_total gauge
nubus_users_user_total{domain="example.com",license_uuid="test-uuid",platform="ucs"} 42.0
# HELP nubus_settings_license_users_limit_total Number of active users permitted by the installed license
# TYPE nubus_settings_license_users_limit_total gauge
nubus_settings_license_users_limit_total{domain="example.com",license_uuid="test-uuid",platform="ucs"} 100.0
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
                                                            "required": ["timeUnixNano", "asDouble", "attributes"],
                                                            "properties": {
                                                                "timeUnixNano": {"type": "string"},
                                                                "asDouble": {"oneOf": [{"type": "number"}, {"enum": ["Infinity", "-Infinity", "NaN"]}]},
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
    assert samples['nubus_ucs_version_info'] == expected


def test_parse_n4k_version():
    text = """\
# HELP nubus_n4k_version_info Nubus for Kubernetes version information
# TYPE nubus_n4k_version_info gauge
nubus_n4k_version_info{domain="example.com",license_uuid="n4k-uuid",major="1",minor="6",patch="1"} 1.0
"""
    expected = [
        {'labels': {'domain': 'example.com', 'license_uuid': 'n4k-uuid', 'major': '1', 'minor': '6', 'patch': '1'}, 'value': 1.0},
    ]
    samples = sender.parse_prometheus_text(text)
    assert samples['nubus_n4k_version_info'] == expected


def test_parse_user_count():
    expected = [
        {'labels': {'domain': 'example.com', 'license_uuid': 'test-uuid', 'platform': 'ucs'}, 'value': 42.0},
    ]
    samples = sender.parse_prometheus_text(PROMETHEUS_TEXT)
    assert samples['nubus_users_user_total'] == expected


def test_build_otlp_conforms_to_schema():
    samples = sender.parse_prometheus_text(PROMETHEUS_TEXT)
    payload = sender.build_otlp(samples, '1700000000000000000')
    jsonschema.validate(payload, OTLP_SCHEMA)


def test_build_otlp_nubus_ucs_version():
    expected = [{
        'name': 'nubus.ucs.version',
        'description': 'UCS version info per installation (value is always 1)',
        'unit': '1',
        'gauge': {'dataPoints': [{'timeUnixNano': '0', 'asDouble': 1.0, 'attributes': [
            {'key': 'license_uuid', 'value': {'stringValue': 'test-uuid'}},
            {'key': 'ucs', 'value': {'stringValue': '5.2'}},
            {'key': 'patch', 'value': {'intValue': '4'}},
            {'key': 'errata', 'value': {'intValue': '1234'}},
        ]}]},
    }]
    samples = sender.parse_prometheus_text(PROMETHEUS_TEXT)
    assert list(sender._build_otlp_nubus_ucs_version(samples['nubus_ucs_version_info'], '0')) == expected


def test_build_otlp_users_user_total():
    expected = [{
        'name': 'nubus.identities.active',
        'description': 'Count of non-deactivated users/user LDAP objects',
        'unit': '1',
        'gauge': {'dataPoints': [{'timeUnixNano': '0', 'asDouble': 42.0, 'attributes': [
            {'key': 'license_uuid', 'value': {'stringValue': 'test-uuid'}},
            {'key': 'platform', 'value': {'stringValue': 'ucs'}},
        ]}]},
    }]
    samples = sender.parse_prometheus_text(PROMETHEUS_TEXT)
    assert list(sender._build_otlp_users_user_total(samples['nubus_users_user_total'], '0')) == expected


def test_build_otlp_nubus_n4k_version():
    text = 'nubus_n4k_version_info{domain="x",license_uuid="u",major="1",minor="6",patch="1"} 1.0\n'
    expected = [{
        'name': 'nubus.n4k.version',
        'description': 'N4K version info per installation (value is always 1)',
        'unit': '1',
        'gauge': {'dataPoints': [{'timeUnixNano': '0', 'asDouble': 1.0, 'attributes': [
            {'key': 'license_uuid', 'value': {'stringValue': 'u'}},
            {'key': 'major', 'value': {'intValue': '1'}},
            {'key': 'minor', 'value': {'intValue': '6'}},
            {'key': 'patch', 'value': {'intValue': '1'}},
        ]}]},
    }]
    samples = sender.parse_prometheus_text(text)
    assert list(sender._build_otlp_nubus_n4k_version(samples['nubus_n4k_version_info'], '0')) == expected


@pytest.fixture(autouse=True)
def sleeps(monkeypatch):
    calls = []
    monkeypatch.setattr(sender.time, 'sleep', calls.append)
    return calls


def test_send_with_retry_succeeds_on_first_attempt(sleeps):
    session = Mock()
    session.post.return_value = Mock()

    sender.send_with_retry(session, {})

    assert session.post.call_count == 1
    assert sleeps == []


def test_send_with_retry_succeeds_on_third_attempt(sleeps):
    session = Mock()
    session.post.side_effect = [
        requests.ConnectionError('timeout'),
        requests.ConnectionError('timeout'),
        Mock(),
    ]

    sender.send_with_retry(session, {})

    assert session.post.call_count == 3
    assert sleeps == [sender.RETRY_DELAY] * 2


def test_send_with_retry_raises_after_all_attempts_fail():
    session = Mock()
    session.post.side_effect = requests.ConnectionError('timeout')

    with pytest.raises(requests.RequestException):
        sender.send_with_retry(session, {})

    assert session.post.call_count == 3


def test_send_with_retry_retries_on_http_error():
    session = Mock()
    response = Mock()
    response.raise_for_status.side_effect = requests.HTTPError('500')
    session.post.return_value = response

    with pytest.raises(requests.HTTPError):
        sender.send_with_retry(session, {})

    assert session.post.call_count == 3


def test_fetch_metrics_retries_until_success(sleeps):
    session = Mock()
    response = Mock(text='metrics')
    session.get.side_effect = [requests.ConnectionError('refused'), response]

    assert sender.fetch_metrics(session, 'secret') == 'metrics'

    assert session.get.call_count == 2
    assert sleeps == [sender.RETRY_DELAY]


def test_fetch_metrics_raises_after_all_attempts_fail():
    session = Mock()
    response = Mock()
    response.raise_for_status.side_effect = requests.HTTPError('503')
    session.get.return_value = response

    with pytest.raises(requests.HTTPError):
        sender.fetch_metrics(session, 'secret')

    assert session.get.call_count == 3


@pytest.mark.parametrize('value,expected', [
    (100.0, 100.0),
    (float('inf'), 'Infinity'),
    (float('-inf'), '-Infinity'),
    (float('nan'), 'NaN'),
])
def test_double_encodes_non_finite_values_as_strings(value, expected):
    assert sender._double(value) == expected


def test_build_otlp_unlimited_license_is_valid_json():
    text = PROMETHEUS_TEXT.replace('platform="ucs"} 100.0', 'platform="ucs"} +Inf')
    payload = sender.build_otlp(sender.parse_prometheus_text(text), '0')
    body = json.dumps(payload, allow_nan=False)
    jsonschema.validate(json.loads(body), OTLP_SCHEMA)
    assert '"asDouble": "Infinity"' in body


@pytest.mark.parametrize('ucr_values,expected', [
    ({}, {}),
    ({'proxy/http': 'http://proxy:3128'}, {'http': 'http://proxy:3128', 'https': 'http://proxy:3128'}),
    ({'proxy/https': 'http://tls-proxy:3128'}, {'https': 'http://tls-proxy:3128'}),
    (
        {'proxy/http': 'http://proxy:3128', 'proxy/https': 'http://tls-proxy:3128'},
        {'http': 'http://proxy:3128', 'https': 'http://tls-proxy:3128'},
    ),
])
def test_proxies_follow_ucr(ucr_values, expected):
    assert sender._proxies(ucr_values) == expected


def test_send_keeps_environment_proxy_when_ucr_has_none(monkeypatch):
    monkeypatch.setenv('HTTPS_PROXY', 'http://env-proxy:3128')
    session = requests.Session()
    settings = session.merge_environment_settings(sender.TELEMETRY_ENDPOINT, sender._proxies({}), None, None, None)
    assert settings['proxies']['https'] == 'http://env-proxy:3128'


def test_fetch_metrics_does_not_use_the_ucr_proxy():
    session = Mock()
    session.get.return_value = Mock(text='metrics')
    sender.fetch_metrics(session, 'secret')
    assert 'proxies' not in session.get.call_args.kwargs


def test_build_otlp_sends_the_metrics_that_are_present():
    text = 'nubus_users_user_total{domain="x",license_uuid="u",platform="ucs"} 7.0\n'
    payload = sender.build_otlp(sender.parse_prometheus_text(text), '0')
    metrics = payload['resourceMetrics'][0]['scopeMetrics'][0]['metrics']
    assert [metric['name'] for metric in metrics] == ['nubus.identities.active']


def test_build_otlp_raises_without_any_metrics():
    with pytest.raises(ValueError):
        sender.build_otlp({}, '0')
