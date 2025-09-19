#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Check if requests with tracebacks are handled correctly
## roles:
##  - domaincontroller_master
## packages:
##  - univention-management-console
##  - univention-management-console-frontend
##  - ucs-test-umc-module
## exposure: dangerous

import json
import re
import shlex

import pytest

from univention.lib.umc import HTTPError
from univention.management.console.modules.ucstest import joinscript, unjoinscript


ADR0010_EXT_REGEX = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3,6}\+\d{2}:\d{2}) +"
    r"(?P<level>\w+?) +(?P<raw>[^[].*|\[(?P<request_id>.*?)\] (?P<message>.+?)\t\| (?P<data>.*?))$",
)
PREFIX = 'Internal server error during "{request}".\nRequest: {request}\n\n'
LOGPREFIX = 'Internal server error: {request}'
TB_START = re.escape('Traceback (most recent call last):\n  File "/usr/lib/python3/dist-packages/univention/management/console/')

ERRORS = {
    "ucstest/non_threaded_traceback": re.compile(TB_START + 'base.py",.*in __error_handling.*' + re.escape('raise NonThreadedError()\nunivention.management.console.modules.ucstest.NonThreadedError') + '$', re.M | re.S),
    "ucstest/threaded_traceback": re.compile(TB_START + 'modules/decorators.py",.*in _run.*' + re.escape('raise ThreadedError()\nunivention.management.console.modules.ucstest.ThreadedError') + '$', re.M | re.S),
    "ucstest/traceback_as_thread_result": re.compile(re.escape('Traceback (most recent call last):\nunivention.management.console.modules.ucstest.ThreadedError') + '$'),
}


@pytest.mark.parametrize('path,expected_trace', list(ERRORS.items()), ids=['mainthread', 'thread', 'threadresult'])
def test_umc_tracebacks(Client, path, expected_trace):
    joinscript()
    try:
        umc_client = Client.get_test_connection()
        print(f"checking: {path}")
        with open('/var/log/univention/management-console-server.log') as server_log, open('/var/log/univention/management-console-module-ucstest.log') as module_log:
            server_log.seek(0, 2)
            module_log.seek(0, 2)
            with pytest.raises(HTTPError) as exc:
                umc_client.umc_command(path)
            server_log_text = parse_log(server_log.read())
            module_log_text = parse_log(module_log.read())
    finally:
        unjoinscript()

    assert exc.value.status == 591

    prefix = PREFIX.format(request=path)
    traceback = json.loads(exc.value.response.body)["traceback"]
    assert traceback.startswith(prefix)

    raw_traceback = traceback.removeprefix(prefix)
    assert raw_traceback.startswith('Traceback (most recent call last):\n')
    assert expected_trace.match(raw_traceback), (traceback, expected_trace)

    server_error = get_entry(server_log_text, 'Unexpected exception.')
    assert server_error['extended'] == traceback

    module_error = get_entry(module_log_text, LOGPREFIX.format(request=path))
    assert module_error['extended'] == raw_traceback

    fields = parse_logfmt(server_error['data'])
    assert fields['exc_info'] == traceback

    fields = parse_logfmt(module_error['data'])
    assert fields['exc_info'] == raw_traceback


def get_entry(log_text, indicator):
    return next((log for log in log_text if log.get('message') == indicator), None)


def parse_log(log_text):
    current = {}
    log_lines = []
    for line in log_text.splitlines():
        if match := ADR0010_EXT_REGEX.match(line):
            if current:
                log_lines.append(current)
            current = match.groupdict()
        else:
            current.setdefault('extended', []).append(line)
    if current:
        log_lines.append(current)
    for entry in log_lines:
        entry.pop('raw', None)
        if entry.get('extended'):
            entry['extended'] = '\n'.join(entry['extended'])
    return log_lines


def parse_logfmt(line: str) -> dict[str, str]:
    fields = {}
    for token in shlex.split(line):
        if "=" in token:
            k, v = token.split("=", 1)
            fields[k] = v.replace('\\n', '\n')
        else:
            fields[token] = ""
    return fields


@pytest.mark.parametrize('path,expected_error', [
    ("ucstest/umc_error_traceback", "This is an UMC Error"),
    ("ucstest/umc_error_as_thread_result", "This is an UMC Error"),
])
def test_umc_errors(Client, path, expected_error):
    joinscript()
    try:
        umc_client = Client.get_test_connection()
        print(f"checking: {path}")
        with pytest.raises(HTTPError) as exc:
            umc_client.umc_command(path)
        assert exc.value.status == 400, 'Wrong http return code'
        error = json.loads(exc.value.response.body)
        assert error["message"] == expected_error, (error["message"], expected_error)
        assert error["traceback"] is None, (error["traceback"], 'Traceback should be None (null')
    finally:
        unjoinscript()
