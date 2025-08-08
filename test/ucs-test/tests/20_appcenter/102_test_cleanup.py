#!/usr/share/ucs-test/runner python3
## desc: Test that the univentionAppInstalledOnServer attribute is cleaned up on removal of server
## roles: [domaincontroller_master, domaincontroller_backup]
## tags: [basic, apptest]
## bugs: [54892]
## packages: [univention-management-console-module-appcenter]
## exposure: dangerous

from dataclasses import dataclass

import pytest


@dataclass()
class DCInfo:
    fqdn: str
    dn: str
    module: str


@dataclass()
class AppInfo:
    installed_on: list[DCInfo]
    app_dn: str


def create_computer(module: str, random_string, ucr, udm, ldap_base) -> DCInfo:
    name = random_string()
    domainname = ucr.get('domainname')
    fqdn = f'{name}.{domainname}'
    dn = udm.create_object(module, name=name, domain=domainname, position=f'cn=dc,cn=computers,{ldap_base}')

    return DCInfo(fqdn, dn, module)


@pytest.fixture
def create_dcs(udm, random_string, ldap_base, ucr):
    modules = ['computers/domaincontroller_backup', 'computers/domaincontroller_master', 'computers/domaincontroller_slave', 'computers/memberserver']
    return [create_computer(module, random_string, ucr, udm, ldap_base) for module in modules]


@pytest.fixture
def create_app(create_dcs: list[DCInfo], udm, random_string):
    app_dn = udm.create_object('appcenter/app', id=random_string(), name=random_string(), version='1.0', server=[dc.fqdn for dc in create_dcs])

    return AppInfo(create_dcs, app_dn)


def test_univention_app_installed_on_server_cleaned_up(udm, create_app: AppInfo):
    expected = [dc_info.fqdn for dc_info in create_app.installed_on]
    for dc in create_app.installed_on:
        expected.remove(dc.fqdn)
        udm.remove_object(dc.module, dn=dc.dn)
        udm.verify_udm_object('appcenter/app', create_app.app_dn, {'server': expected})
