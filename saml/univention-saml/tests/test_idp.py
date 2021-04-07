from os.path import dirname, join
from importlib.util import module_from_spec, spec_from_file_location
import sys

import pytest


DN = "id=default-saml-idp,cn=univention,dc=base"
ATTR = "LdapGetAttributes"
UCRV = "saml/idp/ldap/get_attributes"

spec = spec_from_file_location("udl2", join(dirname(__file__), "../listener/univention-saml-idp-config.py"))
udl = module_from_spec(spec)
spec.loader.exec_module(udl)  # type: ignore
sys.modules["udl2"] = udl


class TestHandler(object):

    @pytest.fixture
    def ucr(self, mocker, fucr):
        mocker.patch("udl2.ConfigRegistry").return_value = fucr
        return fucr

    @pytest.fixture
    def update(self, mocker):
        return mocker.patch("udl2.ucr_update")

    def test_change_other(self, update):
        udl.handler("cn=other", {ATTR: [b"new"]}, {})
        update.assert_not_called()

    def test_default(self, ucr, update):
        udl.handler(DN, {}, {})
        update.assert_called_once_with(ucr, {UCRV: None})

    def test_custom(self, ucr, update):
        dn = "cn=other"
        ucr["saml/idp/configobject"] = dn
        udl.handler(dn, {ATTR: [b"new"]}, {})
        update.assert_called_once_with(ucr, {UCRV: "'new'"})

    def test_add(self, ucr, update):
        udl.handler(DN, {ATTR: [b"new"]}, {})
        update.assert_called_once_with(ucr, {UCRV: "'new'"})

    def test_modify(self, ucr, update):
        udl.handler(DN, {ATTR: [b"new"]}, {ATTR: [b"old"]})
        update.assert_called_once_with(ucr, {UCRV: "'new'"})

    def test_delete(self, ucr, update):
        udl.handler(DN, {}, {ATTR: [b"old"]})
        update.assert_called_once_with(ucr, {UCRV: None})
