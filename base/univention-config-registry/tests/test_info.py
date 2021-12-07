#!/usr/bin/python3
"""Unit test for :py:mod:`univention.config_registry_info`"""
# pylint: disable-msg=C0103,E0611,R0904

from argparse import Namespace

import pytest

import univention.config_registry_info as ucri


@pytest.fixture
def variable():
	"""Complete UCR variable description."""
	v = ucri.Variable()
	v["description"] = "description"
	v["type"] = "type"
	v["categories"] = "categories"
	return v


@pytest.fixture
def category():
	"""Complete UCR category description."""
	c = ucri.Category()
	c["name"] = "name"
	c["icon"] = "icon"
	return c


class TestVariable(object):

	def test_unreg(self):
		v = ucri.Variable(registered=False)
		assert v.check() == []

	def test_incomplete(self):
		v = ucri.Variable()
		assert set(v.check()) == {'description', 'type', 'categories'}

	def test_empty(self):
		v = ucri.Variable()
		v["description"] = "description"
		v["type"] = ""
		assert set(v.check()) == {'type', 'categories'}

	def test_complete(self, variable):
		assert variable.check() == []


class TestCategory(object):

	def test_incomplete(self):
		c = ucri.Category()
		assert set(c.check()) == {'name', 'icon'}

	def test_empty(self):
		c = ucri.Category()
		c["name"] = "name"
		c["icon"] = ""
		assert c.check() == ['icon']

	def test_complete(self, category):
		assert category.check() == []


class TestConfigRegistryInfo(object):

	@pytest.fixture(autouse=True)
	def setup0(self, tmpdir, monkeypatch):
		"""Fake empty UCR info files."""
		base = tmpdir.mkdir("registry.info")
		monkeypatch.setattr(ucri.ConfigRegistryInfo, "BASE_DIR", str(base))
		categories = base.join(ucri.ConfigRegistryInfo.CATEGORIES)
		variables = base.join(ucri.ConfigRegistryInfo.VARIABLES)
		return Namespace(base=base, categories=categories, variables=variables)

	@pytest.fixture
	def setup(self, setup0):
		"""Fake populated UCR info files."""
		setup0.categories.mkdir()
		setup0.categories.join("a.cfg").write("[a]\nname[de]=Name\nname[en]=name\nicon=icon\n")
		setup0.categories.join("b.cfg").write("[b]\nname=name\n")
		setup0.variables.mkdir()
		setup0.variables.join("a.cfg").write("[a]\nDescription[de]=Description\nDescription[en]=description\nType=str\nDefault=default\nCategories=category\n\n")
		setup0.variables.join("b.cfg").write("[b]\nDescription=description\nType=int\n\n")
		setup0.variables.join("c.cfg").write("[key/.*]\nDescription=description\nType=str\nCategories=category\n\n")
		return setup0

	@pytest.fixture
	def info0(self, setup0):
		"""Empty registry info instance."""
		return ucri.ConfigRegistryInfo(install_mode=True)

	@pytest.fixture
	def info(self, setup):
		"""Registry info instance."""
		return ucri.ConfigRegistryInfo()

	def test_cri(self, info0):
		assert info0.check_categories() == {}
		assert info0.check_variables() == {}
		assert list(info0.get_categories()) == []

	def test_check_categories(self, info):
		assert info.check_categories() == {"b": ["icon"]}

	def test_check_variables(self, info):
		assert info.check_variables() == {"b": ["categories"]}

	def test_read_categories(self, info0, setup):
		info0.read_categories(str(setup.categories / "a.cfg"))
		assert sorted(info0.categories) == ["a"]

	def test_read_categorie_dups(self, info, setup):
		over = setup.categories.join("x.cfg")
		over.write("[B]\nname=other\n")
		info.read_categories(str(over))
		assert "B" not in info.categories
		assert info.categories["b"]["name"] == "name"

	def test_load_categories(self, info0, setup):
		info0.load_categories()
		assert sorted(info0.categories) == ["a", "b"]

	def test_load_categories_missing(self, info0):
		info0.load_categories()
		assert info0.categories == {}

	def test_pattern_sorter(self):
		data = [("key", "data"), ("key0", "data0"), ("key1", "")]
		assert sorted(data, key=ucri.ConfigRegistryInfo._pattern_sorter) == data

	def test_check_patterns_noucr(self, info0):
		info0.check_patterns()
		assert info0.variables == {}

	def test_check_patterns_explicit(self, info, variable):
		info._configRegistry = {"key": "val", "key/a": "a"}
		info.add_variable("key/a", variable)
		info.check_patterns()
		assert info.get_variable("key/a") is variable

	def test_check_patterns_term(self, info):
		info._configRegistry = {"key": "val", "key/a": "a"}
		info.check_patterns()
		assert info.variables["key/a"]

	@pytest.mark.parametrize("term,result", [
		("other", []),
		("key/a", ["key/.*"]),
		("^key", ["key/.*"]),
	])
	def test_describe_search_term(self, term, result, info):
		assert sorted(info.describe_search_term(term)) == result

	def test_write_customized(self, info, setup):
		info.write_customized()
		assert setup.variables.join(ucri.ConfigRegistryInfo.CUSTOMIZED).check(file=1)

	def test_write_variables_filename(self, info0, tmpdir):
		path = tmpdir / "a.cfg"
		assert info0._write_variables(filename=str(path))
		assert path.check(file=1)

	def test_write_variables_package(self, info0, setup):
		assert info0._write_variables(package="a")
		assert setup.variables.join("a.cfg").check(file=1)

	def test_write_variables_insufficient(self, info0):
		with pytest.raises(AttributeError):
			info0._write_variables()

	def test_write_variables_error(self, info0, tmpdir):
		assert not info0._write_variables(filename=str(tmpdir))

	def test_read_customized(self, info, setup):
		setup.variables.join(ucri.ConfigRegistryInfo.CUSTOMIZED).write("[b]\nType=str\n")
		info.read_customized()
		assert info.variables["b"]["Type"] == "str"

	def test_read_variables_filename(self, info0, setup):
		info0.read_variables(filename=str(setup.variables / "a.cfg"))
		assert info0.variables["a"]

	def test_read_variables_package(self, info0, setup):
		info0.read_variables(package="a")
		assert info0.variables["a"]

	def test_read_variables_insufficient(self, info0):
		with pytest.raises(AttributeError):
			info0.read_variables()

	@pytest.mark.parametrize("override,result", [
		(False, "int"),
		(True, "str"),
	])
	def test_read_variables_override(self, override, result, info, setup):
		over = setup.base.join("x.cfg")
		over.write("[b]\nType=str\n")
		info.read_variables(filename=str(over), override=override)
		assert info.variables["b"]["Type"] == result

	@pytest.mark.parametrize("registered_only", [False, True])
	@pytest.mark.parametrize("load_customized", [False, True])
	def test_load_variables(self, load_customized, registered_only, info, mocker):
		cp = mocker.patch.object(info, "check_patterns")
		rc = mocker.patch.object(info, "read_customized")
		info._configRegistry = {"a": "a", "c": "c", "key/a": "a"}

		info._load_variables(registered_only=registered_only, load_customized=load_customized)

		assert sorted(info.variables) == (["a", "b"] if registered_only else ["a", "b", "c", "key/a"])
		cp.assert_called_once_with()
		if load_customized:
			rc.assert_called_once_with()
		else:
			rc.assert_not_called()

	def test_load_variables_ignored(self, info0, setup0, mocker):
		rv = mocker.patch.object(info0, "read_variables")
		mocker.patch.object(info0, "check_patterns")

		setup0.variables.mkdir()
		setup0.variables.mkdir("sub").ensure("x.cfg")
		setup0.variables.ensure("y.bak")
		setup0.variables.ensure(ucri.ConfigRegistryInfo.CUSTOMIZED)
		cfg = setup0.variables.ensure("z.cfg")

		info0._load_variables(load_customized=False)

		rv.assert_called_once_with(str(cfg))

	def test_load_variables_missing(self, info0):
		info0._load_variables()
		assert info0.variables == {}

	def test_get_categories(self, info):
		assert sorted(info.get_categories()) == ["a", "b"]

	def test_get_category(self, info):
		assert info.get_category("a")

	def test_get_category_unknown(self, info0):
		assert info0.get_category("a") is None

	@pytest.mark.parametrize("category,result", [
		(None, ["a", "b"]),
		("category", ["a"]),
		("other", []),
	])
	def test_get_variables(self, category, result, info):
		assert sorted(info.get_variables(category)) == result

	def test_get_variable(self, info0):
		assert info0.get_variable("v") is None

	def test_add_variable(self, info0, variable):
		info0.add_variable("v", variable)
		assert info0.get_variable("v") is variable


def test_set_language():
	old = ucri._locale
	try:
		ucri.set_language("xx")
		assert ucri._locale == "xx"
		assert ucri.uit._locale == "xx"
	finally:
		ucri.set_language(old)
