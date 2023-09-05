#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: check setting UCR variables
## packages:
##  - univention-management-console-module-ucr
## roles-not:
##  - basesystem
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

import subprocess
import tempfile
import time
from typing import IO

import pytest

from univention.lib.i18n import Translation
from univention.testing.browser.univentionconfigurationregistry import UniventionConfigurationRegistry


_ = Translation("ucs-test-browser").translate

SEARCHES = [
    {
        "pattern": "*tmpKey",
        "expected_results": 2,
    },
    {
        "pattern": "tmpKey",
        "expected_results": 4,
    },
    {
        "pattern": "*tmpDesc",
        "expected_results": 2,
    },
    {
        "pattern": "*tmpDesc*",
        "expected_results": 4,
    },
    {
        "pattern": "*tmpVal",
        "expected_results": 2,
    },
    {
        "pattern": "tmpVal*",
        "expected_results": 2,
    },
    {
        "pattern": "*tmpVal*",
        "expected_results": 4,
    },
    {
        "pattern": "tmpVal",
        "expected_results": 4,
    },
]


@pytest.fixture(autouse=True, scope="module")
def creating_testing_variables():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".cfg", dir="/etc/univention/registry.info/variables/") as registry_temp_file:
        create_testing_ucr_variables(registry_temp_file)
        yield


def test_ucr_module_category_filter(ucr_module: UniventionConfigurationRegistry):
    ucr_module.navigate()
    ucr_module.tester.fill_combobox(_("Category"), _("Base Settings"))
    search_result = len(ucr_module.get_ucr_module_search_results("tmpKey"))
    assert search_result == 2, f"Expected to get 2 results but got {search_result} when searching with a category"


def test_ucr_module_searches(ucr_module: UniventionConfigurationRegistry):
    ucr_module.navigate()

    for search in SEARCHES:
        search_results = ucr_module.get_ucr_module_search_results(search["pattern"])
        assert len(search_results) == search["expected_results"], f"Expected to get {search['expected_results']} results but got {len(search_results)}"


def test_ucr_module_set_variable(ucr_module: UniventionConfigurationRegistry):
    key = "umc_test/foo_tmpKey_bar"
    value = "testValue"
    ucr_module.navigate()
    ucr_module.search(key)
    ucr_module.set_variable(key, value)
    time.sleep(5)
    cli_search_result = ucr_cli_search_result(key)
    assert cli_search_result[key] == value, "Failed to set a variable via the UMC-UCR module"


def ucr_cli_search_result(pattern: str):
    search_results = subprocess.run(["ucr", "search", "--brief", "--all", pattern], check=True, stdout=subprocess.PIPE).stdout.decode("utf-8")
    search_results = search_results.split("\n")[:-1]
    result = {}
    for search_result in search_results:
        if ".*" in search_result:
            continue

        (key, value) = tuple(kv.strip() for kv in search_result.split(":", 1))
        if value == "<empty>":
            value = ""

        result[key] = value

    return result


def create_testing_ucr_variables(ucr_variable_file: IO[str]):
    ucr_variable_file.write(
        "[umc_test/foo_tmpKey]\n"
        "Description[de]=This is a test-description. foo_tmpDesc\n"
        "Description[en]=This is a test-description. foo_tmpDesc\n"
        "Type=str\n"
        "Categories=system-base\n"
        "\n"
        "[umc_test/tmpKey_foo]\n"
        "Description[de]=This is a test-description. tmpDesc_foo\n"
        "Description[en]=This is a test-description. tmpDesc_foo\n"
        "Type=str\n"
        "Categories=system-base\n"
        "\n"
        "[umc_test/foo_tmpKey_bar]\n"
        "Description[de]=This is a test-description. foo_tmpDesc_bar\n"
        "Description[en]=This is a test-description. foo_tmpDesc_bar\n"
        "Type=string\n"
        "Categories=service-software-management\n"
        "\n"
        "[umc_test/tmpKey]\n"
        "Description[de]=This is a test-description. tmpDesc\n"
        "Description[en]=This is a test-description. tmpDesc\n"
        "Type=str\n"
        "Categories=management-umc\n",
    )
    ucr_variable_file.flush()

    args = ["ucr", "set"] + [f"umc_test/{k}" for k in ["foo_tmpKey=foo_tmpVal", "tmpKey_foo=tmpVal_foo", "foo_tmpKey_bar=foo_tmpVal_bar", "tmpKey=tmpVal"]]
    subprocess.run(args, check=True)
