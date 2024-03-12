#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2018-2024 Univention GmbH
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
# you and Univention.
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

"""Base classes for (simplified) UDM modules and objects."""


import copy
import pprint
from collections.abc import Iterable, Iterator, Mapping
from typing import TYPE_CHECKING, Any, NamedTuple, Self, cast

from ldap.filter import filter_format

from .exceptions import MultipleObjects, NoObject
from .plugins import Plugin


LdapMapping = NamedTuple('LdapMapping', [('ldap2udm', Mapping[str, str]), ('udm2ldap', Mapping[str, str])])


class BaseObjectProperties:
    """Container for |UDM| properties."""

    def __init__(self, udm_obj: 'BaseObject') -> None:
        self._udm_obj = udm_obj

    def __repr__(self) -> str:
        return '{}({})'.format(
            self.__class__.__name__,
            pprint.pformat({k: v for k, v in self.__dict__.items() if not str(k).startswith('_')}, indent=2),
        )

    def __deepcopy__(self, memo: dict) -> Any:
        id_self = id(self)
        if not memo.get(id_self):
            memo[id_self] = {}
            for k, v in self.__dict__.items():
                if k == '_udm_obj':
                    continue
                memo[id_self][k] = copy.deepcopy(v)
        return memo[id_self]


class BaseObject:
    r"""
    Base class for |UDM| object classes.

    Usage:

    *   Creation of instances is always done through
        :py:meth:`BaseModule.new`, :py:meth:`BaseModule.get` or :py:meth:`BaseModule.search`.

    *   Modify an object::

          user.props.firstname = 'Peter'
          user.props.lastname = 'Pan'
          user.save()

    *   Move an object::

          user.position = 'cn=users,ou=Company,dc=example,dc=com'
          user.save()

    *   Delete an object::

          obj.delete()

    After saving a :py:class:`BaseObject`, it is :py:meth:`.reload`\ ed
    automatically because UDM hooks and listener modules often add, modify or
    remove properties when saving to LDAP. As this involves LDAP, it can be
    disabled if the object is not used afterwards and performance is an issue::

        user_mod.meta.auto_reload = False
    """

    udm_prop_class = BaseObjectProperties

    def __init__(self) -> None:
        """
        Don't instantiate a :py:class:`BaseObject` directly. Use
        :py:meth:`BaseModule.get()`, :py:meth:`BaseModule.new()` or
        :py:meth:`BaseModule.search()`.
        """
        self.dn = ''
        self.props: BaseObjectProperties | None = None
        self.options: list[str] = []
        self.policies: list[str] = []
        self.position = ''
        self.superordinate: str | None = None
        self._udm_module: BaseModule | None = None

    def __repr__(self) -> str:
        return '{}({!r}, {!r})'.format(
            self.__class__.__name__,
            self._udm_module.name if self._udm_module else '<not initialized>',
            self.dn,
        )

    def reload(self) -> Self:
        """
        Refresh object from LDAP.

        :return: self
        """
        raise NotImplementedError()

    def save(self) -> Self:
        """
        Save object to LDAP.

        :return: self
        :raises univention.udm.exceptions.MoveError: when a move operation fails
        """
        raise NotImplementedError()

    def delete(self, remove_childs: bool = False) -> None:
        """
        Remove the object (and optionally its child nodes) from the LDAP database.

        :param bool remove_childs: if there are UDM objects below this objects DN, recursively remove
                them before removing this object
        """
        raise NotImplementedError()


class BaseModuleMetadata:
    """Base class for UDM module meta data."""

    auto_open = True
    r"""Whether |UDM| objects should be ``open()``\ ed."""
    auto_reload = True
    r"""Whether |UDM| objects should be ``reload()``\ ed after saving."""

    def __init__(self, meta: 'BaseModule.Meta') -> None:
        self.supported_api_versions: Iterable[int] = getattr(meta, "supported_api_versions", [])
        self.suitable_for: Iterable[str] = getattr(meta, "suitable_for", [])
        self.used_api_version: int | None = None
        self._udm_module: BaseModule | None = None

    def __repr__(self) -> str:
        return '{}({})'.format(
            self.__class__.__name__,
            ', '.join(f'{k}={v!r}' for k, v in self.__dict__.items() if not str(k).startswith('_')),
        )

    def instance(self, udm_module: 'BaseModule', api_version: int) -> Self:
        cpy = copy.deepcopy(self)
        cpy._udm_module = udm_module
        cpy.used_api_version = api_version
        return cpy

    @property
    def identifying_property(self) -> str:
        """
        UDM property of which the mapped LDAP attribute is used as first
        component in a DN, e.g. `username` (LDAP attribute `uid`) or `name`
        (LDAP attribute `cn`).
        """
        raise NotImplementedError()

    def lookup_filter(self, filter_s: str | None = None) -> str:
        """
        Filter the UDM module uses to find its corresponding LDAP objects.

        This can be used in two ways:

        * get the filter to find all objects::

              myfilter_s = obj.meta.lookup_filter()

        * get the filter to find a subset of the corresponding LDAP objects
          (`filter_s` will be combined with `&` to the filter for all objects)::

              `myfilter = obj.meta.lookup_filter('(|(givenName=A*)(givenName=B*))')`

        :param str filter_s: optional LDAP filter expression
        :return: an LDAP filter string
        """
        raise NotImplementedError()

    @property
    def mapping(self) -> LdapMapping:
        """
        UDM properties to LDAP attributes mapping and vice versa.

        :return: a namedtuple containing two mappings: a) from UDM property to
                LDAP attribute and b) from LDAP attribute to UDM property
        """
        raise NotImplementedError()


class ModuleMeta(Plugin):
    udm_meta_class = BaseModuleMetadata

    if TYPE_CHECKING:
        meta: BaseModuleMetadata = None

    def __new__(mcs: type[Self], name: str, bases: tuple[type, ...], attrs: dict[str, Any]) -> Self:
        meta = attrs.pop('Meta', None)
        new_cls_meta = mcs.udm_meta_class(meta)
        new_cls = cast(ModuleMeta, super().__new__(mcs, name, bases, attrs))
        new_cls.meta = new_cls_meta
        return new_cls


class BaseModule(metaclass=ModuleMeta):
    r"""
    Base class for UDM module classes. UDM modules are basically UDM object
    factories.

    Usage:

    0.  Get module using::

            user_mod = UDM.admin/machine/credentials().version(2).get('users/user')

    1.  Create fresh, not yet saved BaseObject::

            new_user = user_mod.new()

    2.  Load an existing object::

            group = group_mod.get('cn=test,cn=groups,dc=example,dc=com')
            group = group_mod.get_by_id('Domain Users')

    3.  Search and load existing objects::

            dc_slaves = dc_slave_mod.search(filter_s='cn=s10*')
            campus_groups = group_mod.search(base='ou=campus,dc=example,dc=com')

    4.  Load existing object(s) without ``open()``\ ing them::

            user_mod.meta.auto_open = False
            user = user_mod.get(dn)
            user.props.groups == []
    """

    _udm_object_class = BaseObject
    _udm_module_meta_class = BaseModuleMetadata

    class Meta:
        supported_api_versions: Iterable[int] = []
        suitable_for: Iterable[str] = []

    def __init__(self, name: str, connection: Any, api_version: int) -> None:
        self.connection = connection
        self.name = name
        self.meta = self.meta.instance(self, api_version)  # type: ignore[has-type]

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.name!r})'

    def new(self, superordinate: str | BaseObject | None = None) -> BaseObject:
        """
        Create a new, unsaved :py:class:`BaseObject` object.

        :param superordinate: DN or UDM object this one references as its
                superordinate (required by some modules)
        :return: a new, unsaved BaseObject object
        """
        raise NotImplementedError()

    def get(self, dn: str) -> BaseObject:
        """
        Load |UDM| object from |LDAP|.

        :param str dn: |DN| of the object to load.
        :return: an existing :py:class:`BaseObject` instance.
        :raises univention.udm.exceptions.NoObject: if no object is found at `dn`
        :raises univention.udm.exceptions.WrongObjectType: if the object found at `dn` is not of type :py:attr:`self.name`
        """
        raise NotImplementedError()

    def get_by_id(self, id: str) -> BaseObject:
        """
        Load |UDM| object from |LDAP| by searching for its ID.

        This is a convenience function around :py:meth:`search()`.

        :param str id: ID of the object to load (e.g. username (uid) for users/user,
                name (cn) for groups/group etc.)
        :return: an existing :py:class:`BaseObject` object.
        :raises univention.udm.exceptions.NoObject: if no object is found with ID `id`
        :raises univention.udm.exceptions.MultipleObjects: if more than one object is found with ID `id`
        """
        filter_s = filter_format(f'{self.meta.identifying_property}=%s', (id,))
        res = list(self.search(filter_s))
        if not res:
            raise NoObject(f'No object found for {filter_s!r}.', module_name=self.name)
        elif len(res) > 1:
            raise MultipleObjects(
                f'Searching in module {self.name!r} with identifying_property {self.meta.identifying_property!r} (filter: {filter_s!r}) returned {len(res)} objects.', module_name=self.name)
        return res[0]

    def search(self, filter_s: str = '', base: str = '', scope: str = 'sub', sizelimit: int = 0) -> Iterator[BaseObject]:
        """
        Get all |UDM| objects from |LDAP| that match the given filter.

        :param str filter_s: LDAP filter (only object selector like `uid=foo`
                required, `objectClasses` will be set by the |UDM| module)
        :param str base: |LDAP| search base.
        :param str scope: |LDAP| search scope, e.g. `base` or `sub` or `one`.
        :param int sizelimit: |LDAP| size limit for searched results.
        :return: iterator of :py:class:`BaseObject` objects
        """
        raise NotImplementedError()
