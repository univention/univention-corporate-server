#!/usr/share/ucs-test/runner python3
## desc: Test update of mail/hosteddomains ucr variable
## tags: [apptest]
## exposure: dangerous
## packages:
##  - univention-mail-postfix

import random

import univention.testing.strings as uts
import univention.testing.ucr as ucr_test
import univention.testing.udm as udm_test
from univention.testing import utils


def main():
    with ucr_test.UCSTestConfigRegistry() as ucr:
        with udm_test.UCSTestUDM() as udm:
            domains = []
            for _ in range(5):
                maildomain = f'{uts.random_name()}.{uts.random_name()}.{uts.random_name()}'
                maildomain = "".join(random.choice([x.lower(), x.upper()]) for x in maildomain)
                udm.create_object(
                    'mail/domain',
                    position=f'cn=domain,cn=mail,{ucr["ldap/base"]}',
                    name=maildomain,
                )
                domains.append(maildomain.lower())
            ucr.load()
            registered = ucr.get('mail/hosteddomains')
            for maildomain in domains:
                if maildomain not in registered:
                    utils.fail(f'maildomain "{maildomain}" not registered in mail/hosteddomains ({registered})')
                udm.remove_object(
                    'mail/domain',
                    dn=f'cn={maildomain},cn=domain,cn=mail,{ucr["ldap/base"]}',
                )
                ucr.load()
                registered = ucr.get('mail/hosteddomains')
                if maildomain in registered:
                    utils.fail(f'maildomain "{maildomain}" is removed but still registered in mail/hosteddomains ({registered})')


if __name__ == '__main__':
    main()
