#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv --tb=native
# desc: Test all variantes of UDM search filters
## exposure: dangerous
## roles: [domaincontroller_master]

import shlex

import pytest
from ldap.filter import filter_format

import univention.admin.modules


class Data:

    modules = {}

    def __enter__(self):
        from univention.testing import udm as _udm
        self.udm = _udm.UCSTestUDM().__enter__()
        return self

    def __exit__(self, etype, evalue, etraceback):
        try:
            self.udm.__exit__(etype, evalue, etraceback)
        except Exception as exc:
            print('Cannot cleanup UDM:', exc)

    def initialize_container(self):
        self.position = self.udm.create_with_defaults('container/ou')[0]

    def skip_non_addable_modules(self, module, property):
        if 'add' not in getattr(univention.admin.modules.get(module), 'operations', ['add']):
            pytest.skip('Module does not support creation')

    def skip_ignored_module(self, module, property):
        ignored_modules = {
            'users/self',
            'users/passwd',
            'shares/printergroup',
            'ms/gpipsec-filter',
            'ms/gpsi-class-store',
            'ms/gpipsec-negotiation-policy',
            'ms/gpsi-package-registration',
            'ms/gpwl-wired',
            'ms/gpipsec-isakmp-policy',
            'ms/gpipsec-policy',
            'ms/gpwl-wireless-blob',
            'ms/gpwl-wireless',
            'ms/gpsi-category-registration',
            'ms/gpipsec-nfa',
            'ms/domainpolicy',
        }
        if module in ignored_modules:
            pytest.skip('Module ignored')

        # debugging:
        # if module not in ('users/user',):
        #     pytest.skip('Module ignored')

    def skip_property_missing(self, module, property):
        if not self.modules[module].get(property):
            pytest.skip('Property was not set during automatic creation.')

    def initialize(self, module, property):
        if self.modules.setdefault(module, {}):
            return  # already created objects for this module

        # # create two objects, so we can verify a search filter doesn't match 2 objects
        # self.udm.create_with_defaults(module, position=self.position)
        dn, props = self.udm.create_with_defaults(module, position=self.position)

        mod = univention.admin.modules.get(module)
        for prop, value in props.items():
            if prop not in mod.property_descriptions:
                continue  # position, etc.
            self.modules[module][prop] = (dn, mod, value)


@pytest.fixture(autouse=True, scope='session')
def data():
    with Data() as d:
        d.initialize_container()
        yield d


class Test_UDMSearch(object):
    """Test all variantes of UDM search filters"""

    def pytest_generate_tests(self, metafunc):
        univention.admin.modules.update()
        modules = [
            (name, pname)
            for name, module in univention.admin.modules.modules.items()
            for pname in module.property_descriptions
            if not getattr(module, 'virtual', False)
        ]
        metafunc.parametrize('module,property', modules)

    def pytest_collection_modifyitems(self, config, items):
        for item in items:
            xfail_reason = self.should_xfail(item.callspec.params.get("module"), item.callspec.params.get("property"))
            if xfail_reason:
                item.add_marker(pytest.mark.xfail(reason=xfail_reason))

    @pytest.fixture(scope="module")
    def umc_client(self, Client):
        return Client.get_test_connection()

    def should_xfail(self, module, property):
        xfailed_properties = {
            'users/user': {
                # https://forge.univention.org/bugzilla/show_bug.cgi?id=53808
                'primaryGroup', 'disabled', 'locked', 'pwdChangeNextLogin', 'userexpiry', 'preferredDeliveryMethod', 'homeSharePath', 'sambaUserWorkstations',
            },
        }
        if module == 'users/user' and property == 'sambaLogonHours':
            return 'https://forge.univention.org/bugzilla/show_bug.cgi?id=53807'
        prop = univention.admin.modules.get(module).property_descriptions[property]
        if prop.multivalue and isinstance(prop.syntax, univention.admin.syntax.complex):
            return 'https://forge.univention.org/bugzilla/show_bug.cgi?id=51777'
        if property in xfailed_properties.get(module, set()):
            return 'Property currently broken'
        if property == 'data' and module in ('settings/data', 'settings/ldapacl', 'settings/ldapschema', 'settings/udm_hook', 'settings/udm_module', 'settings/udm_syntax'):
            return 'Binary search not supported'  # https://forge.univention.org/bugzilla/show_bug.cgi?id=53820
        return False

    def skip_property(self, module, property):
        skipped_properties = {
            'users/user': {'overridePWHistory', 'overridePWLength', 'password', 'unlock'},
            'kerberos/kdcentry': {'generateRandomPassword', 'password'},
            'computers/windows': {'ntCompatibility'},
        }
        if property in skipped_properties.get(module, set()):
            pytest.skip('Property is not searchable')

    def value_to_umc(self, module, property, value):
        if module == 'users/user':
            if property == 'umcProperty':
                return value.replace(' ', '=')
            elif property == 'homePostalAddress':
                return shlex.split(value)
        return value

    def value_to_udm_rest(self, module, property, value):
        return value

    def value_to_udm_cli(self, module, property, value):
        if module == 'users/user':
            if property == 'umcProperty':
                return value.replace(' ', '=')
        return value

    def create_or_skip(self, data, module, property):
        data.skip_non_addable_modules(module, property)
        data.skip_ignored_module(module, property)
        # data.skip_dontsearch(module, property)  # yes?
        self.skip_property(module, property)
        data.initialize(module, property)
        data.skip_property_missing(module, property)

        dn, mod, value = data.modules[module][property]
        if mod.property_descriptions[property].multivalue:
            value = value[0]

        return dn, mod, value

    def test_umc_module_ldap_directory_tree_search(self, data, module, property, umc_client):
        # TODO: search for *
        dn, mod, value = self.create_or_skip(data, module, property)

        dontsearch = mod.property_descriptions[property].dontsearch  # noqa: F841
        try:
            current_value = umc_client.umc_command('udm/get', [dn], 'navigation', print_request_data=False, print_response=False).result[0].get(property)  # noqa: F841
        except univention.lib.umc.BadRequest as exc:
            current_value = exc  # noqa: F841
        search_value = self.value_to_umc(module, property, value)

        objs = self.search_umc(umc_client, module, property, search_value, data.position)
        assert len(objs) == 1
        obj = objs[0]
        assert obj['$dn$'] == dn

    def search_umc(self, umc_client, module, property, search_value, position):
        return umc_client.umc_command(
            'udm/nav/object/query',
            {
                "hidden": True,
                "objectType": module,
                "objectProperty": property,
                "objectPropertyValue": search_value,
                "container": position,
            },
            'navigation',
        ).result

    def test_udm_cli_search(self, data, module, property, udm):
        # TODO: search for *
        dn, mod, value = self.create_or_skip(data, module, property)
        search_value = self.value_to_udm_cli(module, property, value)

        filter_s = filter_format('%s=%s', (property, search_value))
        objs = self.search_udm(udm, module, filter_s, data.position)
        assert len(objs) == 1
        obj = objs[0]
        assert obj[0] == dn

    def search_udm(self, udm, module, filter_s, position):
        return udm.list_objects(module, position=data.position, filter=filter_s)

    def _test_udm_rest_api_search(self, data, module, property):
        pass
