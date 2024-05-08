#!/usr/share/ucs-test/runner pytest-3 -s -vv --tb=native
## desc: Check Docker App mod_proxy configuration
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import pytest

from dockertest import Appcenter, tiny_app_apache


@pytest.mark.exposure('dangerous')
def test_app_modproxy(appcenter: Appcenter, app_name: str, app_version: str, ucr) -> None:
    """normal modproxy with HTTP and HTTPS."""
    app = tiny_app_apache(app_name, app_version)

    try:
        app.set_ini_parameter(
            WebInterface=f'/{app.app_name}',
            WebInterfacePortHTTP='80',
            WebInterfacePortHTTPS='443',
            AutoModProxy='True',
        )
        app.add_to_local_appcenter()
        appcenter.update()

        app.install()
        app.configure_tinyapp_modproxy()
        app.verify(joined=False)

        app.verify_basic_modproxy_settings_tinyapp()
        ucr.load()
        assert ucr.get(f'ucs/web/overview/entries/service/{app_name}/port_http') == '80'
        assert ucr.get(f'ucs/web/overview/entries/service/{app_name}/port_https') == '443'
    finally:
        app.uninstall()
        app.remove()


@pytest.mark.exposure('dangerous')
def test_app_modproxy_https(appcenter: Appcenter, app_name: str, app_version: str, ucr) -> None:
    """special mod proxy with disabled HTTP."""
    app = tiny_app_apache(app_name, app_version)

    try:
        app.set_ini_parameter(
            WebInterface=f'/{app.app_name}',
            WebInterfacePortHTTP='0',  # NO HTTP!
            WebInterfacePortHTTPS='80',  # ONLY HTTPS PUBLICLY!
            WebInterfaceProxyScheme='http',  # CONTAINER ONLY HAS HTTP (80) SUPPORT!
            AutoModProxy='True',
        )
        app.add_to_local_appcenter()
        appcenter.update()

        app.install()
        app.configure_tinyapp_modproxy()
        app.verify(joined=False)

        app.verify_basic_modproxy_settings_tinyapp(http=False, https=True)
        ucr.load()
        assert ucr.get(f'ucs/web/overview/entries/service/{app_name}/port_http') == ''
        assert ucr.get(f'ucs/web/overview/entries/service/{app_name}/port_https') == '443'
    finally:
        app.uninstall()
        app.remove()
