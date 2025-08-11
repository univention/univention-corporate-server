#!/usr/bin/python3
# SPDX-FileCopyrightText: 2020-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

import time

import pytest
from univentionunittests import import_module


class UMCTestRequest:
    _requests = {}

    def __init__(self, options):
        self.id = id(self)
        self.options = options
        self._requests[self.id] = self

    def save_result(self, result):
        if hasattr(self, 'result'):
            raise RuntimeError(f'Already saved result {self.result!r}. Cannot be called twice ({result!r})')
        self.result = result

    def expected_response(self, result):
        if not hasattr(self, 'result'):
            raise RuntimeError('No result for this request.')
        assert self.result == result
        del self._requests[self.id]

    def progress(self, func):
        progress_id = self.result['id']
        while True:
            request = UMCTestRequest({'progress_id': progress_id})
            func(request)
            result = request.result
            if result['finished']:
                self.result = result['result']
                break
            time.sleep(1)

    def __repr__(self):
        return f'<UMCTestRequest id={self.id!r} options={self.options!r}>'


def save_result_on_request(request_id, result, *args, **kwargs):
    umc_request = UMCTestRequest._requests[request_id]
    umc_request.save_result(result)


@pytest.fixture
def umc_request(request):
    if hasattr(request, "param"):
        return UMCTestRequest(request.param)
    else:
        return UMCTestRequest({})


@pytest.fixture
def instance(umc_module_class, mocker):
    mocker.patch.object(umc_module_class, 'finished', side_effect=save_result_on_request)
    mod = umc_module_class()
    mod.init()
    return mod


@pytest.fixture(scope='session')
def umc_module_class():
    return umc_module_class.umc_module.Instance


def pytest_addoption(parser):
    parser.addoption("--installed-umc", action="store_true", help="Test against installed UMC module (not src)")


def umc_requests(params):
    return pytest.mark.parametrize('umc_request', params, indirect=['umc_request'])


def import_umc_module(module_id, umc_src_path=None, set_umc_module_fixture=True):
    python_module_name = f'univention.management.console.modules.{module_id}'
    if umc_src_path is None:
        umc_src_path = 'umc/python/'
    use_installed = pytest.config.getoption('--installed-umc')
    module = import_module(module_id, umc_src_path, python_module_name, use_installed)
    if set_umc_module_fixture:
        umc_module_class.umc_module = module
    return module
