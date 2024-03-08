#!/usr/share/ucs-test/runner pytest-3 -s -vv --tb=native
## desc: Create and install a simple docker app without a Debian package (plain container app)
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import pytest

from univention.testing.utils import get_ldap_connection

from dockertest import tiny_app_apache


@pytest.mark.exposure('dangerous')
def test_app_without_package(appcenter):
    try:
        app = tiny_app_apache()
        app.set_ini_parameter(
            WebInterface=f'/{app.app_name}',
            WebInterfacePortHTTP='80',
            WebInterfacePortHTTPS='443',
            AutoModProxy='True',
        )
        app.add_to_local_appcenter()

        appcenter.update()

        app.install()

        app.verify()

        app.configure_tinyapp_modproxy()
        app.verify_basic_modproxy_settings_tinyapp()

        lo = get_ldap_connection()
        print(lo.searchDn(filter=f'(&(cn={app.app_name[:5]}-*)(objectClass=univentionMemberServer)(!(aRecord=*))(!(macAddress=*)))', unique=True, required=True))
    finally:
        app.uninstall()
        app.remove()
