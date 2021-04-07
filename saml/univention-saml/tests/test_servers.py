from os.path import devnull, dirname, join
from importlib.util import module_from_spec, spec_from_file_location
import sys

import pytest


DN = ""
ATTR = "univentionService"
SRV = "univention-saml"
FQHN = "hostname.domain"

LBASE = {
    "cn": [b"hostname"],
    "associatedDomain": [b"domain"],
}
LSRV = {
    "univentionService": [b"univention-saml"],
}
CERT = {
    "saml/idp/certificate/certificate": devnull,
    "saml/idp/certificate/privatekey": devnull
}


spec = spec_from_file_location("udl3", join(dirname(__file__), "../listener/univention-saml-servers.py"))
udl = module_from_spec(spec)
spec.loader.exec_module(udl)  # type: ignore
sys.modules["udl3"] = udl


class TestHandler(object):

    @pytest.fixture(autouse=True)
    def ucr(self, mocker, fucr):
        mocker.patch("udl3.ConfigRegistry").return_value = fucr
        return fucr

    @pytest.fixture(autouse=True)
    def update(self, mocker):
        return mocker.patch("udl3.ucr_update")

    @pytest.fixture(autouse=True)
    def call(self, mocker):
        return mocker.patch("udl3.call")

    def test_incomplete(self, update):
        udl.handler(DN, {}, {})
        update.assert_not_called()

    def test_base(self, update):
        udl.handler(DN, LBASE, {})
        update.assert_not_called()

    def test_add(self, update, ucr):
        new = dict(LBASE, **LSRV)
        udl.handler(DN, new, {})
        update.assert_called_once_with(ucr, {"ucs/server/saml-idp-server/hostname.domain": "hostname.domain"})

    def test_remove(self, update, ucr):
        udl.handler(DN, LBASE, LSRV)
        update.assert_called_once_with(ucr, {"ucs/server/saml-idp-server/hostname.domain": None})
