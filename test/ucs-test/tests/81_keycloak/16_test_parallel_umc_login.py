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
                    log.exception(f'Task {task_id} generated an exception: %r', e)
                log.error(f'Task {task_id} complete')

        elapsed_time = time.time() - start_time
        requests_per_second = num_requests / elapsed_time if elapsed_time > 0 else 0

        log.info(f'Total requests: {num_requests}')
        log.info(f'Successful: {success_count}')
        log.info(f'Failed: {failure_count}')
        log.info(f'Total time: {elapsed_time:.2f} seconds')
        log.info(f'Requests per second: {requests_per_second:.2f}')

        assert failure_count == 0
    finally:
        restart_umc_server()
