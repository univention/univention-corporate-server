#!/usr/share/ucs-test/runner pytest-3 -s -vv --tb=native
## desc: Create and install a simple docker app
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import pytest

from univention.testing.utils import get_ldap_connection

from dockertest import Appcenter, tiny_app


@pytest.mark.exposure('dangerous')
def test_app_install(appcenter: Appcenter, app_name: str, app_version: str) -> None:
    app = tiny_app(app_name, app_version)
    try:
        app.add_to_local_appcenter()

        appcenter.update()

        app.install()

        app.verify(joined=False)

        lo = get_ldap_connection()
        print(lo.searchDn(filter=f'(&(cn={app_name[:5]}-*)(objectClass=univentionMemberServer)(!(aRecord=*))(!(macAddress=*)))', unique=True, required=True))
    finally:
        app.uninstall()
        app.remove()
