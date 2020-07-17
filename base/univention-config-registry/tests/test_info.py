#!/usr/bin/python
"""Unit test for :py:mod:`univention.config_registry_info`"""
# pylint: disable-msg=C0103,E0611,R0904
import pytest

import univention.config_registry_info as ucri


def test_variable():
	v = ucri.Variable()
	assert set(v.check()) == {'description', 'type', 'categories'}


def test_category():
	c = ucri.Category()
	assert set(c.check()) == {'name', 'icon'}


class TestConfigRegistryInfo(object):

	def test_cri(self):
		cri = ucri.ConfigRegistryInfo(True)
		assert cri.check_categories() == {}
		assert cri.check_variables() == {}
		assert list(cri.get_categories()) == []

	@pytest.mark.skip
	def test_read_categories(self):
		pass

	@pytest.mark.skip
	def test_load_categories(self):
		pass

	@pytest.mark.skip
	def test_check_patterns(self):
		pass

	@pytest.mark.skip
	def test_describe_search_term(self):
		pass

	@pytest.mark.skip
	def test_write_customized(self):
		pass

	@pytest.mark.skip
	def test_read_customized(self):
		pass

	@pytest.mark.skip
	def test_get_category(self):
		pass

	@pytest.mark.skip
	def test_get_variables(self):
		pass

	@pytest.mark.skip
	def test_get_variable(self):
		pass

	@pytest.mark.skip
	def test_add_variable(self):
		pass
