import base64
import random
from logging import getLogger

from singleton_decorator import singleton

import univention.testing.ucr
import univention.uldap


ucr = univention.testing.ucr.UCSTestConfigRegistry()
ucr.load()
HOSTNAME = ucr.get("hostname")
DOMAIN_NAME = ucr.get("domainname")
DEFAULT_HOST = f"{HOSTNAME}.{DOMAIN_NAME}"


logger = getLogger(__name__)


@singleton
class TestData:
    def __init__(self):
        self._lo = univention.uldap.getMachineConnection()
        self._groups = self._lo.searchDn("univentionObjectType=groups/group")
        self._users = {
            "student": self._lo.searchDn("(&(univentionObjectType=users/user)(ucsschoolRole=student*))"),
            "teacher": self._lo.searchDn("(&(univentionObjectType=users/user)(ucsschoolRole=teacher*))"),
            "staff": self._lo.searchDn("(&(univentionObjectType=users/user)(ucsschoolRole=staff*))")
        }
        self._ous = self._lo.searchDn("univentionObjectType=container/ou")
        self._domains_controller_slave = self._lo.searchDn("univentionObjectType=computers/domaincontroller_slave")

    def random_group(self, only_dn=False, pop=False):
        dn = random.choice(self._groups)
        if pop:
            self._groups.remove(dn)
        return dn if only_dn else (self._lo.get(dn), dn)

    def random_user(self, only_dn=False, pop=False, role="student"):
        assert role in self._users, f"Unknown role {role!r}, must be one of {self._users.keys()}"
        dn = random.choice(self._users[role])
        if pop:
            self._users[role].remove(dn)
        return dn if only_dn else (self._lo.get(dn), dn)

    def random_ou(self, only_dn=False, pop=False):
        dn = random.choice(self._ous)
        if pop:
            self._ous.remove(dn)
        return dn if only_dn else (self._lo.get(dn), dn)

    def random_domain_controller_slave(self, only_dn=False, pop=False):
        dn = random.choice(self._domains_controller_slave)
        if pop:
            self._domains_controller_slave.remove(dn)
        return dn if only_dn else (self._lo.get(dn), dn)


def get_token(username: str, password: str) -> str:
    # Generate basic auth header
    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")
    return token
