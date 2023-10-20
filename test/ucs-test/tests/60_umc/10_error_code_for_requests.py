#!/usr/share/ucs-test/runner python3
## desc: Check if requests are answered with an error code after killing ucstest module
## roles:
##  - domaincontroller_master
## packages:
##  - univention-management-console
##  - univention-management-console-frontend
##  - ucs-test-umc-module
## exposure: dangerous

import http.client as httplib
import socket
import ssl
import subprocess
import time

import psutil

from univention.management.console.modules.ucstest import joinscript, unjoinscript
from univention.testing import utils
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


def restart_web_server():
    subprocess.call(['systemctl', 'restart', 'univention-management-console-server', 'apache2'])


class AsyncClient(Client):

    def async_request(self, path):
        cookie = '; '.join(['='.join(x) for x in self.cookies.items()])
        headers = dict(self._headers, **{'Cookie': cookie, 'Content-Type': 'application/json'})
        headers['X-XSRF-Protection'] = self.cookies.get('UMCSessionId', '')
        connection = httplib.HTTPSConnection(self.hostname, timeout=10)
        print(f'*** POST to /univention/command/{path} with headers={headers!r}')
        connection.request('POST', f'/univention/command/{path}', '{}', headers=headers)
        return connection


def main():
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
    success = True
    for i_connection in connections:
        try:
            response = i_connection.getresponse()
            print(f'*** RESPONSE Status={response.status} {response.reason}; body=\n{response.read()!r}\n***')
            if response.status != 502 or response.reason != 'UMC-Server module process connection failed':
                print(f'ERROR: Unexpected status of response {response.status} {response.reason} (expected 502)')
                success = False
        except (socket.timeout, ssl.SSLError):
            print('ERROR: request timed out')

    if not success:
        utils.fail('ERROR: Requests are not answered with an error code')


if __name__ == '__main__':
    joinscript()
    try:
        main()
    finally:
        restart_web_server()
        unjoinscript()
