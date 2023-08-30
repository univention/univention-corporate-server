#!/usr/share/ucs-test/runner python3
## desc: Create and install a simple UCS 4.4 docker app
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

from univention.testing.utils import get_ldap_connection

from dockertest import App, Appcenter, get_app_name, get_app_version


if __name__ == '__main__':
    with Appcenter() as appcenter:
        app_name = get_app_name()
        app_version = get_app_version()

        app = App(name=app_name, version=app_version, container_version='4.4')

        try:
            app.set_ini_parameter(
                DockerImage='docker-test.software-univention.de/ucs-appbox-amd64:4.4-8',
                DockerScriptSetup='/usr/sbin/app-setup')
            app.add_script(setup='#!/bin/sh\nrm /usr/lib/univention-install/18python-univention-directory-manager.inst')
            app.add_to_local_appcenter()

            appcenter.update()

            app.install()

            app.verify()

            lo = get_ldap_connection()
            print(lo.searchDn(filter='(&(cn=%s-*)(objectClass=univentionMemberServer)(!(aRecord=*))(!(macAddress=*)))' % app_name[:5], unique=True, required=True))
        finally:
            app.uninstall()
            app.remove()
