#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Test passwordless login at SP with existing session at IdP
## tags: [saml]
## roles-not: [domaincontroller_master]
## join: true
## exposure: safe
## tags:
##  - skip_admember

import univention.admin.modules as udm_modules
from univention.testing import utils

import samltest


udm_modules.update()


def test_using_existing_session(saml_session):
    lo = utils.get_ldap_connection(admin_uldap=True)

    master = udm_modules.lookup('computers/domaincontroller_master', None, lo, scope='sub')
    master_hostname = "%s.%s" % (master[0]['name'], master[0]['domain'])
    try:
        saml_session.login_with_new_session_at_IdP()
        saml_session.test_logged_in_status()
        saml_session.target_sp_hostname = master_hostname
        saml_session.login_with_existing_session_at_IdP()
        saml_session.test_logged_in_status()
        print("Success: SSO with existing session is working")
    except samltest.SamlError as exc:
        utils.fail(str(exc))
