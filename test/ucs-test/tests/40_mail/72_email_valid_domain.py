#!/usr/share/ucs-test/runner python3
## desc: Email domain validity
## tags: [apptest]
## exposure: dangerous
## packages: [univention-mail-postfix]

import univention.testing.strings as uts
import univention.testing.ucr as ucr_test
import univention.testing.udm as udm_test
from univention.testing import utils


# UCS syntax (primaryEmailAddressValidDomain) and OX app syntax checks
EXPECTED_ERROR_MSGS = (
    "The domain part of the primary mail address is not in list of configured mail domains",
    "The mail address' domain does not match any mail domain object.",
)


def main():
    with ucr_test.UCSTestConfigRegistry() as ucr, udm_test.UCSTestUDM() as udm:
        fqdn = '%(hostname)s.%(domainname)s' % ucr
        test_domain = f'{uts.random_name()}.com'
        mail_address = f'{uts.random_name()}@{test_domain}'
        try:
            udm.create_user(
                set={
                    'password': 'univention',
                    'mailHomeServer': fqdn,
                    'mailPrimaryAddress': mail_address,
                },
            )
            utils.fail(f'UDM accepted domain {test_domain!r}, which is not in the list of configured mail domains.')
        except udm_test.UCSTestUDM_CreateUDMObjectFailed as exc:
            if any(error_msg in str(exc) for error_msg in EXPECTED_ERROR_MSGS):
                print(f"OK: expected error happened: {exc}")
            else:
                utils.fail(f'User creation failed because of unexpected error: {exc}')


if __name__ == '__main__':
    main()
