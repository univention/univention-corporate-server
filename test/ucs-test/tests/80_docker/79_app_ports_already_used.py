#!/usr/share/ucs-test/runner pytest-3 -s -vv --tb=native
## desc: Check the App installation if the next free port is already used
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import os
import socket

import pytest

from univention.testing.utils import get_ldap_connection

from dockertest import tiny_app_apache


def _open_port(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('', port))
    except OSError as msg:
        print(f'Bind failed. Error Code : {msg} {msg.errno} {os.strerror(msg.errno)}')
        return
    s.listen(10)
    print(f'Opened socket on port {port}')
    return s


@pytest.mark.exposure('dangerous')
def test_app_ports_already_used(appcenter):
    sockets = [_open_port(i) for i in range(40000, 40100)]

    app = tiny_app_apache()

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

        app.verify()

        app.configure_tinyapp_modproxy()
        app.verify_basic_modproxy_settings_tinyapp()

        lo = get_ldap_connection()
        print(lo.searchDn(filter=f'(&(cn={app.app_name[:5]}-*)(objectClass=univentionMemberServer)(!(aRecord=*))(!(macAddress=*)))', unique=True, required=True))
    finally:
        app.uninstall()
        app.remove()

    for s in sockets:
        if not s:
            continue
        s.close()
