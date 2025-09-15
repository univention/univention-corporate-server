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

import pytest

from univention.lib.umc import HTTPError
from univention.management.console.modules.ucstest import joinscript, unjoinscript


@pytest.mark.parametrize('path,expected_trace', [
    ("ucstest/non_threaded_traceback", re.compile("raise NonThreadedError\\(\\)\n(univention.management.console.modules.ucstest.)?NonThreadedError", re.M)),
    ("ucstest/threaded_traceback", re.compile("raise ThreadedError\\(\\)\n(univention.management.console.modules.ucstest.)?ThreadedError", re.M)),
    ("ucstest/traceback_as_thread_result", re.compile("(univention.management.console.modules.ucstest.)?ThreadedError", re.M)),
])
def test_umc_tracebacks(Client, path, expected_trace):
    # this regex matches that the initial line of the traceback
    # log message includes the logfmter on the line of the initial logging
    # message
    error_line_regex = re.compile(
        # Structured Date + Log Level
        r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}\+\d{2}:\d{2}\ {4}ERROR '
        # Log-Message
        r'\[.*] Internal server error during ".*"\. \| '
        # Logfmt-Extras
        r'(pid=\d*\s|logname=[A-Z]+\s|func=.*\s|umcmodule=.*\s|requester_dn=".*"\s|requester_ip=\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s){4}',
    )
    # The traceback parts insure that the content of the traceback is correct
    traceback_parts = [
        [
            "Request: ucstest/non_threaded_traceback",
            "Traceback (most recent call last):", "raise exc.with_traceback(etraceback)",
            "function.__func__(self, request, *args, **kwargs)",
            "result = _multi_response(self, request)",
            "return function(self, request)",
            "return list(function(self, iterator, *nones))",
            "yield function(self, *args)",
            "raise NonThreadedError()",
        ],
        [
            "Request: ucstest/threaded_traceback",
            "Traceback (most recent call last):",
            "result = self._function(*args, **kwargs)  # type: Union[BaseException, _T]",
            "raise ThreadedError()",
        ],
        [
            "Request: ucstest/traceback_as_thread_result",
            "Traceback (most recent call last):",
        ],
    ]
    logfile = open('/var/log/univention/management-console-server.log')
    logfile.read()  # ensure we're at the end of the log-file before messages are written
    joinscript()
    try:
        umc_client = Client.get_test_connection()
        print(f"checking: {path}")
        with pytest.raises(HTTPError) as exc:
            umc_client.umc_command(path)
        assert exc.value.status == 591, 'Wrong http return code'
        traceback = json.loads(exc.value.response.body)["traceback"]
        assert expected_trace.search(traceback), (traceback, expected_trace)
    finally:
        unjoinscript()
        log_text = logfile.read()
        logfile.close()
        assert error_line_regex.match(log_text), f"Log Text doesn't have a line that matches the error regex: {error_line_regex}"
        assert expected_trace.search(log_text), (log_text, expected_trace)
        assert len([True for traceback_lines in traceback_parts if all(line in log_text for line in traceback_lines)]) == 1
        log_lines_with_trace = [line for line in log_text.replace('\\n', '').split('\n') if line]
        log_lines_without_trace = [line for line in log_lines_with_trace if 'ERROR' in line or 'PROCESS' in line]
        assert len(log_lines_without_trace) == 3
        assert len(log_lines_without_trace) < len(log_lines_with_trace)


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
