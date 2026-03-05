#!/usr/bin/python3
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from ipaddress import IPv4Network
from unittest.mock import MagicMock, patch


MODULE = 'univention.appcenter.docker'


@patch(f'{MODULE}.interfaces')
def test_get_host_networks_basic(mock_interfaces_mod):
    from univention.appcenter.docker import _get_host_networks

    iface = {'address': '172.16.54.1', 'netmask': '255.255.255.0'}
    mock_interfaces_mod.Interfaces.return_value.ipv4_interfaces = [('eth0', iface)]

    result = _get_host_networks()
    assert result == [IPv4Network('172.16.54.0/24')]


@patch(f'{MODULE}.interfaces')
def test_get_host_networks_multiple(mock_interfaces_mod):
    from univention.appcenter.docker import _get_host_networks

    iface1 = {'address': '172.16.2.1', 'netmask': '255.255.255.0'}
    iface2 = {'address': '10.0.0.5', 'netmask': '255.255.0.0'}
    mock_interfaces_mod.Interfaces.return_value.ipv4_interfaces = [
        ('eth0', iface1),
        ('eth1', iface2),
    ]

    result = _get_host_networks()
    assert result == [IPv4Network('172.16.2.0/24'), IPv4Network('10.0.0.0/16')]


@patch(f'{MODULE}.interfaces')
def test_get_host_networks_no_interfaces(mock_interfaces_mod):
    from univention.appcenter.docker import _get_host_networks

    mock_interfaces_mod.Interfaces.return_value.ipv4_interfaces = []

    result = _get_host_networks()
    assert result == []


@patch(f'{MODULE}.interfaces')
def test_get_host_networks_invalid_address(mock_interfaces_mod):
    from univention.appcenter.docker import _get_host_networks

    iface = {'address': 'not-an-ip', 'netmask': '255.255.255.0'}
    mock_interfaces_mod.Interfaces.return_value.ipv4_interfaces = [('eth0', iface)]

    result = _get_host_networks()
    assert result == []


def _make_docker_instance():
    """Create a Docker instance with a mocked app, without invoking __init__."""
    from univention.appcenter.docker import Docker

    instance = object.__new__(Docker)
    instance.app = MagicMock()
    instance.app.ucr_ip_key = 'appcenter/apps/testapp/ip'
    instance.app.id = 'testapp'
    instance.logger = MagicMock()
    return instance


@patch(f'{MODULE}.interfaces')
@patch(f'{MODULE}.docker_get_existing_subnets', return_value=[])
@patch(f'{MODULE}.Apps')
@patch(f'{MODULE}.ucr_get')
def test_get_app_network_skips_host_interface(mock_ucr_get, mock_apps, mock_subnets, mock_interfaces_mod):
    mock_ucr_get.side_effect = lambda key, default=None: {
        'appcenter/apps/testapp/ip': None,
        'appcenter/docker/compose/network': '172.16.1.1/16',
    }.get(key, default)
    mock_apps.return_value.get_all_apps.return_value = []

    iface = {'address': '172.16.2.1', 'netmask': '255.255.255.0'}
    mock_interfaces_mod.Interfaces.return_value.ipv4_interfaces = [('eth0', iface)]

    instance = _make_docker_instance()
    network = instance._get_app_network()

    assert network is not None
    assert network != IPv4Network('172.16.2.0/24')
    assert not network.overlaps(IPv4Network('172.16.2.0/24'))


@patch(f'{MODULE}.interfaces')
@patch(f'{MODULE}.docker_get_existing_subnets')
@patch(f'{MODULE}.Apps')
@patch(f'{MODULE}.ucr_get')
def test_get_app_network_skips_docker_and_host(mock_ucr_get, mock_apps, mock_subnets, mock_interfaces_mod):
    mock_ucr_get.side_effect = lambda key, default=None: {
        'appcenter/apps/testapp/ip': None,
        'appcenter/docker/compose/network': '172.16.1.1/16',
    }.get(key, default)
    mock_apps.return_value.get_all_apps.return_value = []
    mock_subnets.return_value = [IPv4Network('172.16.3.0/24')]

    iface = {'address': '172.16.2.1', 'netmask': '255.255.255.0'}
    mock_interfaces_mod.Interfaces.return_value.ipv4_interfaces = [('eth0', iface)]

    instance = _make_docker_instance()
    network = instance._get_app_network()

    assert network is not None
    assert not network.overlaps(IPv4Network('172.16.2.0/24'))
    assert not network.overlaps(IPv4Network('172.16.3.0/24'))


@patch(f'{MODULE}.interfaces')
@patch(f'{MODULE}.docker_get_existing_subnets', return_value=[])
@patch(f'{MODULE}.Apps')
@patch(f'{MODULE}.ucr_get')
def test_get_app_network_exhausted_by_host(mock_ucr_get, mock_apps, mock_subnets, mock_interfaces_mod):
    mock_ucr_get.side_effect = lambda key, default=None: {
        'appcenter/apps/testapp/ip': None,
        'appcenter/docker/compose/network': '172.16.1.1/16',
    }.get(key, default)
    mock_apps.return_value.get_all_apps.return_value = []

    # Host interface covers the entire /16 pool
    iface = {'address': '172.16.0.1', 'netmask': '255.255.0.0'}
    mock_interfaces_mod.Interfaces.return_value.ipv4_interfaces = [('eth0', iface)]

    instance = _make_docker_instance()
    network = instance._get_app_network()

    assert network is None
