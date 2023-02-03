#!/usr/share/ucs-test/runner python3
## desc: Check squid restart without cache
## tags: [apptest]
## exposure: careful
## packages: [univention-squid]
## bugs: [33332, 35421]

import univention.testing.ucr as ucr_test
from univention.config_registry import handler_set
from univention.testing import utils

from essential.simplesquid import SimpleSquid


def main():
    fail = False
    squid = SimpleSquid()
    with ucr_test.UCSTestConfigRegistry():
        handler_set(['squid/cache=false'])
        squid.restart()
        fail = not squid.is_running(30)

    utils.wait_for_replication_and_postrun()
    squid.restart()

    if fail:
        utils.fail(f'squid/cache=false, {squid.basename} is not able to restart')


if __name__ == '__main__':
    main()
