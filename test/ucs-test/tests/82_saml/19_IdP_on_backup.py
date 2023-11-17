#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Check whether idP is synchronized between DC Master and DC Backup.
## tags:
##  - saml
## bugs: [39479]
## roles: [domaincontroller_backup]
## join: true
## exposure: dangerous

import socket
import time

import univention.admin.modules as udm_modules
from univention.testing import utils

import samltest


udm_modules.update()


def test_idp_on_backup(saml_session):
    lo = utils.get_ldap_connection(admin_uldap=True)
    master = udm_modules.lookup('computers/domaincontroller_master', None, lo, scope='sub')
    master_hostname = "%s.%s" % (master[0]['name'], master[0]['domain'])
    master_ip = socket.gethostbyname(master_hostname)
    backup_ip = '127.0.0.1'

    try:
        with samltest.GuaranteedIdP(master_ip):
            saml_session.login_with_new_session_at_IdP()
            saml_session.test_logged_in_status()
            time.sleep(1)
        saml_session.target_sp_hostname = master_hostname
        with samltest.GuaranteedIdP(backup_ip):
            saml_session.login_with_existing_session_at_IdP()
            saml_session.test_logged_in_status()
    except samltest.SamlError as exc:
        utils.fail(str(exc))
