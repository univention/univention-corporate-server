#!/usr/share/ucs-test/runner python3
## desc: Spaces in mail addresses
## tags: [apptest]
## exposure: dangerous
## packages: [univention-mail-server]

import pytest

import univention.testing.strings as uts
import univention.testing.ucr as ucr_test
import univention.testing.udm as udm_test


EXPECTED_ERROR_MSG = 'Invalid syntax: Primary e-mail address (mailbox): Not a valid email address!'


def main():
    with ucr_test.UCSTestConfigRegistry() as ucr, udm_test.UCSTestUDM() as udm:
        fqdn = '%(hostname)s.%(domainname)s' % ucr
        mail_address = '%s @%s' % (uts.random_name(), ucr.get('domainname'))
        with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed) as exc:
            _userdn, _username = udm.create_user(
                set={
                    'password': 'univention',
                    'mailHomeServer': fqdn,
                    'mailPrimaryAddress': mail_address,
                },
            )
        assert EXPECTED_ERROR_MSG in str(exc.value), str(exc.value)


if __name__ == '__main__':
    main()
