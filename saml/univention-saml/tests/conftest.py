import sys
from types import ModuleType

import pytest

import univention


@pytest.fixture(autouse=True)
def fake_getent(mocker):
    mocker.patch("pwd.getpwnam").return_value.pw_uid = -1
    mocker.patch("grp.getgrnam").return_value.gr_gid = -1


class FakeSetUID(object):
    def __init__(self, uid):
        pass

    def __enter__(self):
        pass

    def __exit__(self, *args):
        pass

    def __call__(self, f):
        return f


listener = ModuleType("listener")
listener.SetUID = FakeSetUID  # type: ignore
listener.configRegistry = {}  # type: ignore
sys.modules["listener"] = listener

ud = ModuleType("univention.debug")
ud.debug = lambda mod, level, msg: None  # type: ignore
ud.LISTENER = -1  # type: ignore
ud.ERROR = 0  # type: ignore
ud.WARN = 1  # type: ignore
ud.PROCESS = 1  # type: ignore
ud.INFO = 3  # type: ignore
ud.ALL = 3  # type: ignore
sys.modules["univention.debug"] = ud
univention.debug = ud  # type: ignore

uni_cr = ModuleType("univention.config_registry")
sys.modules["univention.config_registry"] = uni_cr
univention.config_registry = uni_cr  # type: ignore


class FakeConfigRegistry(dict):
    def load(self):
        self.update({"ldap/base": "dc=base"})


@pytest.fixture
def fucr():
    return FakeConfigRegistry()


uni_cr_f = ModuleType("univention.config_registry.frontend")
uni_cr_f.ConfigRegistry = FakeConfigRegistry  # type: ignore
uni_cr_f.ucr_update = lambda ucr, changes: None  # type: ignore
sys.modules["univention.config_registry.frontend"] = uni_cr_f
uni_cr.frontend = uni_cr_f  # type: ignore
