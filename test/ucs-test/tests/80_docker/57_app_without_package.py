#!/usr/share/ucs-test/runner python3
## desc: Create and install a simple docker app without a Debian package (plain container app)
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

from univention.testing.utils import get_ldap_connection

from dockertest import Appcenter, tiny_app_apache


if __name__ == '__main__':

    with Appcenter() as appcenter:
        try:
            app = tiny_app_apache()
            app.set_ini_parameter(
                WebInterface='/%s' % app.app_name,
                WebInterfacePortHTTP='80',
                WebInterfacePortHTTPS='443',
                AutoModProxy='True',
            )
            app.add_to_local_appcenter()

            appcenter.update()

            app.install()

            app.verify(joined=False)

            app.configure_tinyapp_modproxy()
            app.verify_basic_modproxy_settings_tinyapp()

            lo = get_ldap_connection()
            print(lo.searchDn(filter='(&(cn=%s-*)(objectClass=univentionMemberServer)(!(aRecord=*))(!(macAddress=*)))' % app.app_name[:5], unique=True, required=True))
        finally:
            app.uninstall()
            app.remove()
