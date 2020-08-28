#!/usr/share/ucs-test/runner /usr/bin/py.test -s
## desc: Check if requests with tracebacks are handled correctly
## roles:
##  - domaincontroller_master
## packages:
##  - univention-management-console
##  - univention-management-console-frontend
##  - ucs-test-umc-module
## exposure: dangerous


from __future__ import print_function
import json

import pytest

from univention.lib.umc import HTTPError

from univention.management.console.modules.ucstest import joinscript, unjoinscript


@pytest.mark.parametrize('path,expected_trace', [
	("ucstest/non_threaded_traceback", "raise NonThreadedError()\nNonThreadedError"),
	("ucstest/threaded_traceback", "raise ThreadedError()\nThreadedError"),
	("ucstest/traceback_as_thread_result", "Request: ucstest/traceback_as_thread_result\n\nThreadedError"),
])
def test_umc_tracebacks(Client, path, expected_trace):
	joinscript()
	try:
		umc_client = Client.get_test_connection()
		print("checking: {}".format(path))
		with pytest.raises(HTTPError) as exc:
			umc_client.umc_command(path)
		assert exc.value.status == 591, 'Wrong http return code'
		assert json.loads(exc.value.response.body)["traceback"].endswith(expected_trace), (json.loads(exc.value.response.body)["traceback"], expected_trace)
	finally:
		unjoinscript()


@pytest.mark.parametrize('path,expected_error', [
	("ucstest/umc_error_traceback", "This is an UMC Error"),
	("ucstest/umc_error_as_thread_result", "This is an UMC Error"),
])
def test_umc_errors(Client, path, expected_error):
	joinscript()
	try:
		umc_client = Client.get_test_connection()
		print("checking: {}".format(path))
		with pytest.raises(HTTPError) as exc:
			umc_client.umc_command(path)
		assert exc.value.status == 400, 'Wrong http return code'
		assert json.loads(exc.value.response.body)["message"] == expected_error, (json.loads(exc.value.response.body)["error"], expected_error)
		assert json.loads(exc.value.response.body)["traceback"] is None, (json.loads(exc.value.response.body)["traceback"], 'Traceback should be None (null')
	finally:
		unjoinscript()
