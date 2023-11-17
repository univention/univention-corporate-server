#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Test if SAML user was created successfully
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: safe
## tags:
##  - skip_admember

import pytest

from univention.testing import utils
from univention.testing.utils import LDAPObjectNotFound, LDAPObjectUnexpectedValue, LDAPObjectValueMissing


def test_saml_user(ucr):
    attrs = {
        'uid': ['sys-idp-user'],
        'objectClass': ['top', 'person', 'univentionPWHistory', 'simpleSecurityObject', 'uidObject', 'univentionObject'],
        'univentionObjectType': ['users/ldap'],
    }
    try:
        utils.verify_ldap_object('uid=sys-idp-user,cn=users,%s' % (ucr['ldap/base'],), attrs)
    except LDAPObjectNotFound:
        pytest.fail('No SAML user found')
    except (LDAPObjectValueMissing, LDAPObjectUnexpectedValue):
        pytest.fail('SAML user found, but some of the required attributes are wrong')
