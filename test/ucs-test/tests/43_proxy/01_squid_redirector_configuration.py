#!/usr/share/ucs-test/runner python3
## desc: Check squid redirector written to config file
## tags: [apptest]
## exposure: safe
## bugs: [32429]
## packages: [univention-squid]

import univention.testing.ucr as ucr_test
from univention.config_registry import handler_set

from essential.simplesquid import SimpleSquid


def main():
    squid_guard_config = '/etc/squid/squidGuard.conf'
    squid_guard_path = '/usr/bin/squidGuard'
    squid = SimpleSquid()

    with ucr_test.UCSTestConfigRegistry():
        redirector = "pyredir"
        handler_set([f'squid/redirect={redirector}'])
        squid.redirector_is(redirector)

        redirector = "squidguard"
        handler_set([f'squid/redirect={redirector}'])
        squid.redirector_is(f"{squid_guard_path} -c {squid_guard_config}")


if __name__ == '__main__':
    main()
