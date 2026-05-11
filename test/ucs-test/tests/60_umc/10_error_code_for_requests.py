#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Check if requests are answered with an error code after killing ucstest module
## roles:
##  - domaincontroller_master
## packages:
##  - univention-management-console
##  - univention-management-console-frontend
##  - ucs-test-umc-module
## exposure: dangerous

import http.client as httplib
import json
import ssl
import time

import psutil

from univention.testing.umc import Client


NUMBER_OF_CONNECTIONS = 8
RESPONSE_STATUS_CODES = (510, 511)


def kill_ucstest():
    search_mask = {'/usr/sbin/univention-management-console-module', '-m', 'ucstest'}
    for process in psutil.process_iter():
        if not (search_mask - set(process.cmdline())):
            print(f'Found module process {process.pid} {process.cmdline()!r} and killing it ...')
            process.kill()
            try:  # if kill did not succeed, terminate
                process.terminate()
            except psutil.NoSuchProcess:
                pass
    time.sleep(0.5)
    for process in psutil.process_iter():
        if not (search_mask - set(process.cmdline())):
            raise AssertionError(f'ERROR: ... module process {process.pid} {process.cmdline()!r} is still there, this should not happen!')


class AsyncClient(Client):

    def async_request(self, path):
        cookie = '; '.join(['='.join(x) for x in self.cookies.items()])
        headers = dict(self._headers, **{'Cookie': cookie, 'Content-Type': 'application/json'})
        headers['X-XSRF-Protection'] = self.cookies.get('UMCSessionId', '')
        connection = httplib.HTTPSConnection(self.hostname, timeout=10)
        print(f'*** POST to /univention/command/{path} with headers={headers!r}')
        connection.request('POST', '/univention/command/%s' % path, '{}', headers=headers)
        return connection


def test_error_code_for_requests(umc_allow_ucstest):
    print('Setting up the connections and sending requests...')
    connections = [
        AsyncClient.get_test_connection(timeout=10).async_request('ucstest/norespond')
        for i in range(NUMBER_OF_CONNECTIONS)
    ]
    time.sleep(2)

    print('Killing module process...')
    kill_ucstest()
    time.sleep(2)

    print('Verfying that requests are answered with an error code...')
    i = 0
    for i_connection in connections:
        try:
            response = i_connection.getresponse()
        except (TimeoutError, ssl.SSLError):
            print('ERROR: request timed out')
        else:
            body = response.read()
            print(f'*** RESPONSE Status={response.status} {response.reason}; body=\n{body!r}\n***')
            assert body, response
            assert response.status == 502, response.status
            assert response.reason in ('UMC-Server module process connection failed', 'Proxy Error'), response.reason
            if response.reason == 'UMC-Server module process connection failed':
                i += 1
            elif response.reason == 'Proxy Error':
                body = json.loads(body)
                assert 'Univention Management Console Server could not be reached' in body.get('message', ''), body
    assert i >= 1
