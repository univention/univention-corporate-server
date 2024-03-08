#!/usr/share/ucs-test/runner pytest-3 -s -vv --tb=native
## desc: Create and install a simple docker app with a simple dependency
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import pytest

from univention.testing.utils import get_ldap_connection

from dockertest import get_app_name, get_app_version, tiny_app


@pytest.mark.exposure('dangerous')
def test_app_install_with_required_app(appcenter):
    app_name = get_app_name()
    app_version = get_app_version()
    app2_name = get_app_name()
    app2_version = get_app_version()

    app = tiny_app(app_name, app_version)
    app2 = tiny_app(app2_name, app2_version)
    app.set_ini_parameter(RequiredAppsInDomain=app2_name)
    try:
        app.add_to_local_appcenter()
        app2.add_to_local_appcenter()

        appcenter.update()

        app.install()

        app.verify()
        app2.verify()

        lo = get_ldap_connection()
        print(lo.searchDn(filter=f'(&(cn={app_name[:5]}-*)(objectClass=univentionMemberServer)(!(aRecord=*))(!(macAddress=*)))', unique=True, required=True))
    finally:
        app2.uninstall()
        app.uninstall()
        app2.remove()
        app.remove()
