#!/usr/bin/python3
#
# Univention Management Console
#  Univention Directory Manager Module
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2023 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.
"""
Testing wrapper arount the UDM REST API client
- Tracks modifications and reverts changes when cleanup() is called
- Prevents modifications of objects that were created outside the test session.
"""

from typing import Optional, cast

from unittest.mock import patch

from univention.admin.rest.client import UDM, Module, Object, Response


class CannotModifyExistingObjectException(Exception):
    # TODO: Add more info
    pass


@patch('univention.admin.rest.client.Module', new='TestModule')
class TestUDM(UDM):

    def __init__(self, uri: str, username: str, password: str, *args, **kwargs) -> None:
        super().__init__(uri, username, password, *args, **kwargs)

        self._cleanup = {}

    def modules(self, name=None):
        self.load()
        for module in self.client.resolve_relations(self.entry, 'udm:object-modules'):
            for module_info in self.client.get_relations(module, 'udm:object-types', name):
                yield TestModule(self, module_info['href'], module_info['name'], module_info['title'])

    def set_cleanup(self, object_type: str, dn: Optional[str]) -> None:
        assert dn, "Tried to set cleanup for an object with empty dn, this might be a bug in this testing wrapper"
        self._cleanup.setdefault(object_type, []).append(dn)

    def remove_cleanup(self, object_type: str, dn: Optional[str]) -> None:
        assert dn, "Tried to unset cleanup for an object with empty dn, this might be a bug in this testing wrapper"
        self._cleanup[object_type].remove(dn)

    def assert_test_object(self, object_type: str, dn: Optional[str]):
        """In a test context, only object that were created during the test can be modified or deleted."""
        assert dn, "Tried to check the status for an object with empty dn, this might be a bug in this testing wrapper"
        if not self._cleanup.get(dn):
            raise CannotModifyExistingObjectException(dn)

    def cleanup(self) -> None:
        for key, value in self._cleanup.items():
            print(key, value)


# This is probably no longer needed!
@patch('univention.admin.rest.client.Object', new='TestObject')
class TestModule(Module):

    def __init__(self, udm: TestUDM, uri: str, name: str, title: str, *args, **kwargs) -> None:
        super().__init__(udm, uri, name, title, *args, **kwargs)


class TestObject(Object):

    def __init__(self, udm: UDM, representation, etag=None, last_modified=None, *args, **kwargs) -> None:
        super().__init__(udm, representation, etag, last_modified, *args, **kwargs)
        self.udm = cast(TestUDM, self.udm)
        # self.udm.set_cleanup(self.object_type, self.dn)

    def save(self, reload: bool = True) -> Response:
        if not self.dn:
            result = self._create(reload)
            self.udm.set_cleanup(self.object_type, self.dn)
            return result

        self.udm.assert_test_object(self.object_type, self.dn)
        return self._modify(reload)

    def delete(self, remove_referring: bool = False) -> str:
        self.udm.assert_test_object(self.object_type, self.dn)
        # Why is result an empty string? not bytes btw!
        result = super().delete(remove_referring=remove_referring)
        self.udm.remove_cleanup(self.object_type, self.dn)
        return result

    def move(self, position: str) -> None:
        self.udm.assert_test_object(self.object_type, self.dn)
        old_module = self.object_type
        old_dn = self.dn
        super().move(position)
        self.udm.remove_cleanup(old_module, old_dn)
        self.udm.set_cleanup(self.object_type, self.dn)
