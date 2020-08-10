#!/usr/bin/py.test
# -*- coding: utf-8 -*-

import sys
import importlib

import pytest


class UMCTestRequest(object):
	_requests = {}

	def __init__(self, options):
		self.id = id(self)
		self.options = options
		self._requests[self.id] = self

	def save_result(self, result):
		if hasattr(self, 'result'):
			raise RuntimeError('Already saved result {!r}. Cannot be called twice ({!r})'.format(self.result, result))
		self.result = result

	def expected_response(self, result):
		if not hasattr(self, 'result'):
			raise RuntimeError('No result for this request.')
		assert self.result == result
		del self._requests[self.id]

	def __repr__(self):
		return '<UMCTestRequest id={!r} options={!r}>'.format(self.id, self.options)


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


def import_umc_module(module_id, umc_src_path=None):
	umc_module_python_path = 'univention.management.console.modules.{}'.format(module_id)
	if pytest.config.getoption('--installed-umc'):
		module_name = umc_module_python_path
		# print('Testing against installed {}'.format(module_name))
	else:
		if umc_src_path is None:
			umc_src_path = 'umc/python/'
		if umc_src_path not in sys.path:
			sys.path.insert(1, umc_src_path)
		module_name = module_id
		# print('Testing against src {}'.format(module_name))
	module = importlib.import_module(module_name)
	umc_module_class.umc_module = module
	sys.modules[umc_module_python_path] = module
	return module
