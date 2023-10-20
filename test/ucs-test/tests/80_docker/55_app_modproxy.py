#!/usr/share/ucs-test/runner python3
## desc: Check Docker App mod_proxy configuration
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

from univention.testing.ucr import UCSTestConfigRegistry

from dockertest import Appcenter, get_app_name, get_app_version, tiny_app_apache


if __name__ == '__main__':
    with Appcenter() as appcenter:
        # normal modproxy
        app_name = get_app_name()
        app_version = get_app_version()
        ucr = UCSTestConfigRegistry()

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
            assert ucr.get(f'ucs/web/overview/entries/service/{app_name}/port_http') == '80', ucr.get(f'ucs/web/overview/entries/service/{app_name}/port_http')
            assert ucr.get(f'ucs/web/overview/entries/service/{app_name}/port_https') == '443', ucr.get(f'ucs/web/overview/entries/service/{app_name}/port_https')

        finally:
            app.uninstall()
            app.remove()

        # special mod proxy with disabled HTTP
        app_version = get_app_version()

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
            assert ucr.get(f'ucs/web/overview/entries/service/{app_name}/port_http') == '', ucr.get(f'ucs/web/overview/entries/service/{app_name}/port_http')
            assert ucr.get(f'ucs/web/overview/entries/service/{app_name}/port_https') == '443', ucr.get(f'ucs/web/overview/entries/service/{app_name}/port_https')

        finally:
            app.uninstall()
            app.remove()
