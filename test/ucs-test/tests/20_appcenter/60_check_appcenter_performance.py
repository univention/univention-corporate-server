#!/usr/share/ucs-test/runner python3
## desc: |
##  Check the performance for requests against the UMC appcenter.
## bugs: [38545, 39632]
## roles-not: [basesystem]
## packages:
##   - univention-management-console-module-appcenter
## exposure: safe
## tags: [appcenter, performance]

import time

from univention.appcenter import actions
from univention.testing import utils
from univention.testing.umc import Client


def main():
    print("Appcenter update starting")
    appcenter_update = actions.get_action('update')
    appcenter_update.call()

    print("Appcenter update done")
    max_time = 20.0
    request_query = ('appcenter/query', {'quick': True})

    print("Getting UMC connection")
    client = Client.get_test_connection()

    print("Start request to appcenter")
    start_time = time.monotonic()
    client.umc_command(*request_query)
    end_time = time.monotonic()
    print("Request finished")

    if end_time - start_time > max_time:
        utils.fail(f"The appcenter answered too slow\nThreshold is {max_time} sec; Appcenter replied in {end_time - start_time} sec.")
    else:
        print(f"Success: The appcenter answered in {end_time - start_time} sec.")


if __name__ == '__main__':
    main()
