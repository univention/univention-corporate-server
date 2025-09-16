#!/usr/share/ucs-test/runner pytest-3 -s -l -v
## desc: Test parallel UMC oidc logins, see univention/dev/internal/team-nubus#1436
## tags: [keycloak, skip_admember]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import logging
import time

import concurrent.futures

from univention.testing.umc import ClientOIDC


log = logging.getLogger(__name__)


def login_logout(username, password, portal_fqdn):
    client = ClientOIDC()
    client.authenticate(username, password, portal_fqdn=portal_fqdn)
    client.logout()
    return True


def test_parallel_login_logout(admin_account, portal_config, restart_umc_server):
    num_requests = 100
    max_workers = 10
    success_count = 0
    failure_count = 0
    start_time = time.time()

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks and create a map of future to task_id
            future_to_task = {
                executor.submit(
                    login_logout,
                    admin_account.username,
                    admin_account.bindpw,
                    portal_config.fqdn,
                ): i for i in range(num_requests)
            }
            for future in concurrent.futures.as_completed(future_to_task):
                task_id = future_to_task[future]
                try:
                    success = future.result()
                    if success:
                        success_count += 1
                    else:
                        failure_count += 1
                except Exception as e:
                    failure_count += 1
                    log.exception('Task %s generated an exception: %r', task_id, e)
                log.error('Task %s complete', task_id)

        elapsed_time = time.time() - start_time
        requests_per_second = num_requests / elapsed_time if elapsed_time > 0 else 0

        log.info('Total requests: %s', num_requests)
        log.info('Successful: %s', success_count)
        log.info('Failed: %s', failure_count)
        log.info('Total time: %.2f seconds', elapsed_time)
        log.info('Requests per second: %.2f', requests_per_second)

        assert failure_count == 0
    finally:
        restart_umc_server()
