#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test UCS telemetry sender script
## tags: [udm, apptest]
## roles: [domaincontroller_master]
## exposure: safe
## packages:
##   - univention-directory-manager-tools

import importlib.machinery
import importlib.util
from unittest.mock import Mock, patch

import jsonschema
import pytest
import requests


SCRIPT_PATH = '/usr/share/univention-directory-manager-tools/univention-telemetry-sender'
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

_loader = importlib.machinery.SourceFileLoader('univention_telemetry_sender', SCRIPT_PATH)
_spec = importlib.util.spec_from_loader('univention_telemetry_sender', _loader)
sender = importlib.util.module_from_spec(_spec)
_loader.exec_module(sender)


def test_parse_ucs_version():
    samples = sender.parse_prometheus_text(PROMETHEUS_TEXT)
    assert len(samples['version_ucs_info']) == 1
    labels = samples['version_ucs_info'][0]['labels']
    assert labels['license_uuid'] == 'test-uuid'
    assert labels['ucs'] == '5.2'
    assert labels['patch'] == '4'
    assert labels['errata'] == '1234'


def test_parse_n4k_version():
    text = """\
# HELP version_n4k_info Nubus4Kubernetes version information
# TYPE version_n4k_info gauge
version_n4k_info{domain="example.com",license_uuid="n4k-uuid",major="1",minor="6",patch="1"} 1.0
"""
    samples = sender.parse_prometheus_text(text)
    assert len(samples['version_n4k_info']) == 1
    labels = samples['version_n4k_info'][0]['labels']
    assert labels['license_uuid'] == 'n4k-uuid'
    assert labels['major'] == '1'
    assert labels['minor'] == '6'
    assert labels['patch'] == '1'


def test_parse_user_count():
    samples = sender.parse_prometheus_text(PROMETHEUS_TEXT)
    assert len(samples['users_user_total']) == 1
    assert samples['users_user_total'][0]['value'] == 42
    assert samples['users_user_total'][0]['labels']['license_uuid'] == 'test-uuid'
    assert samples['users_user_total'][0]['labels']['platform'] == 'ucs'


def test_build_otlp_conforms_to_schema():
    samples = sender.parse_prometheus_text(PROMETHEUS_TEXT)
    payload = sender.build_otlp(samples, '1700000000000000000')
    jsonschema.validate(payload, OTLP_SCHEMA)


def test_build_otlp_ucs_metric():
    samples = sender.parse_prometheus_text(PROMETHEUS_TEXT)
    payload = sender.build_otlp(samples, '1700000000000000000')

    resource_attrs = {a['key']: a['value'] for a in payload['resourceMetrics'][0]['resource']['attributes']}
    assert resource_attrs['service.name']['stringValue'] == sender.SERVICE_NAME

    metrics = {metric['name']: metric for metric in payload['resourceMetrics'][0]['scopeMetrics'][0]['metrics']}
    assert 'nubus.installation.ucs' in metrics

    dp = metrics['nubus.installation.ucs']['gauge']['dataPoints'][0]
    assert dp['asInt'] == '1'
    assert dp['timeUnixNano'] == '1700000000000000000'

    attrs = {a['key']: a['value'] for a in dp['attributes']}
    assert attrs['license_uuid']['stringValue'] == 'test-uuid'
    assert attrs['ucs']['stringValue'] == '5.2'
    assert attrs['patch']['intValue'] == '4'
    assert attrs['errata']['intValue'] == '1234'


def test_build_otlp_identities_metric():
    samples = sender.parse_prometheus_text(PROMETHEUS_TEXT)
    metrics = {metric['name']: metric for metric in sender.build_otlp(samples, '0')['resourceMetrics'][0]['scopeMetrics'][0]['metrics']}
    assert 'nubus.identities.active' in metrics

    dp = metrics['nubus.identities.active']['gauge']['dataPoints'][0]
    assert dp['asInt'] == '42'

    attrs = {a['key']: a['value'] for a in dp['attributes']}
    assert attrs['license_uuid']['stringValue'] == 'test-uuid'
    assert attrs['platform']['stringValue'] == 'ucs'


def test_build_otlp_n4k_metric():
    text = 'version_n4k_info{domain="x",license_uuid="u",major="1",minor="6",patch="1"} 1.0\n'
    samples = sender.parse_prometheus_text(text)
    metrics = {metric['name']: metric for metric in sender.build_otlp(samples, '0')['resourceMetrics'][0]['scopeMetrics'][0]['metrics']}
    assert 'nubus.installation.n4k' in metrics

    attrs = {a['key']: a['value'] for a in metrics['nubus.installation.n4k']['gauge']['dataPoints'][0]['attributes']}
    assert attrs['license_uuid']['stringValue'] == 'u'
    assert attrs['major']['intValue'] == '1'
    assert attrs['minor']['intValue'] == '6'
    assert attrs['patch']['intValue'] == '1'


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


def test_send_with_retry_raises_on_http_error():
    session = Mock()
    response = Mock()
    response.raise_for_status.side_effect = requests.HTTPError('500')
    session.post.return_value = response

    with patch.object(sender.time, 'sleep'), pytest.raises(RuntimeError):
        sender.send_with_retry(session, {})
