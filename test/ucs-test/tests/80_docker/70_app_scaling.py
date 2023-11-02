#!/usr/share/ucs-test/runner python3
## desc: Create and install multiple Docker Apps at once
## tags: [WIP,docker]
## timeout: 7200
## exposure: dangerous
## packages:
##   - docker.io

from dockertest import Appcenter, get_app_name, get_app_version, tiny_app_apache


DOCKER_APP_COUNT = 20


if __name__ == '__main__':
    with Appcenter() as appcenter:
        apps = []

        try:
            for i in range(DOCKER_APP_COUNT):
                app = tiny_app_apache(get_app_name(), get_app_version())
                app.set_ini_parameter(
                    WebInterface=f'/{app.app_name}',
                    WebInterfacePortHTTP='80',
                    WebInterfacePortHTTPS='443',
                    AutoModProxy='True',
                )
                app.add_to_local_appcenter()

                apps.append(app)

            appcenter.update()

            for i in range(DOCKER_APP_COUNT):
                apps[i].install()

            for i in range(DOCKER_APP_COUNT):
                apps[i].verify(joined=False)
                apps[i].configure_tinyapp_modproxy()
                apps[i].verify_basic_modproxy_settings_tinyapp()

        finally:
            for i in range(len(apps)):
                apps[i].uninstall()
                apps[i].remove()
