#!/usr/share/ucs-test/runner pytest-3 -s -vv --tb=native
## desc: Create and install a simple docker app and check webinterface ports
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import pytest

from univention.config_registry import ConfigRegistry

from dockertest import get_app_version, tiny_app


@pytest.mark.exposure('dangerous')
def test_app_ports_webinterface(appcenter, app_name):
    webinterface_port_http = '8080'
    webinterface_port_https = '8443'

    for mod_proxy in [True, False]:
        app = tiny_app(app_name, get_app_version())
        try:
            app.set_ini_parameter(
                WebInterfacePortHTTP=webinterface_port_http,
                WebInterfacePortHTTPS=webinterface_port_https,
                AutoModProxy=str(mod_proxy),
                WebInterface=f'/{app_name}')
            app.add_to_local_appcenter()
            appcenter.update()
            app.install()

            ucr = ConfigRegistry()
            ucr.load()
            if mod_proxy:
                assert ucr.get(f'ucs/web/overview/entries/service/{app_name}/port_http') == '80'
                assert ucr.get(f'ucs/web/overview/entries/service/{app_name}/port_https') == '443'
            else:
                assert ucr.get(f'ucs/web/overview/entries/service/{app_name}/port_http') == webinterface_port_http
                assert ucr.get(f'ucs/web/overview/entries/service/{app_name}/port_https') == webinterface_port_https
        finally:
            app.uninstall()
            app.remove()
