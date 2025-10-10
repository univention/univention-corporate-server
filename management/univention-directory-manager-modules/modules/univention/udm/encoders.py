# SPDX-FileCopyrightText: 2018-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""En/Decoders for object properties."""

from __future__ import annotations

import datetime
import logging
import sys
import time
from typing import TYPE_CHECKING, Any

import lazy_object_proxy

import univention.admin.modules
from univention.admin.syntax import sambaGroupType
from univention.admin.uexceptions import valueInvalidSyntax

from .binary_props import Base64BinaryProperty, Base64Bzip2BinaryProperty
from .exceptions import NoObject, UnknownModuleType
from .udm import UDM


if TYPE_CHECKING:
    from collections.abc import Callable


__dn_list_property_encoder_class_cache = {}
__dn_property_encoder_class_cache = {}


class BaseEncoder:
    static = False  # whether to create an instance or use a class/static method

    def __init__(self, property_name: str | None = None, *args: Any, **kwargs: Any) -> None:
        self.property_name = property_name

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.property_name})'

    def encode(self, value: Any | None = None) -> Any | None:
        raise NotImplementedError()

    def decode(self, value: Any | None = None) -> Any | None:
        raise NotImplementedError()


class Base64BinaryPropertyEncoder(BaseEncoder):
    static = False

    def decode(self, value: str | None = None) -> Base64BinaryProperty | None:
        if value:
            return Base64BinaryProperty(self.property_name, value)
        else:
            return value

    def encode(self, value: Base64BinaryProperty | None = None) -> str | None:
        if value:
            if not isinstance(value, Base64BinaryProperty):
                value = Base64BinaryProperty(self.property_name, raw_value=value)
            return value.encoded
        else:
            return value


class Base64Bzip2BinaryPropertyEncoder(BaseEncoder):
    static = False

    def decode(self, value: str | None = None) -> Base64Bzip2BinaryProperty | None:
        if value:
            return Base64Bzip2BinaryProperty(self.property_name, value)
        else:
            return value

    def encode(self, value: Base64Bzip2BinaryProperty | None = None) -> str | None:
        if value:
            return value.encoded
        else:
            return value


class DatePropertyEncoder(BaseEncoder):
    static = True

    @staticmethod
    def decode(value: str | None = None) -> datetime.date | None:
        if value:
            return datetime.date(*time.strptime(value, '%Y-%m-%d')[0:3])
        else:
            return value

    @staticmethod
    def encode(value: datetime.date | None = None) -> str | None:
        if value:
            return value.strftime('%Y-%m-%d')
        else:
            return value


class DisabledPropertyEncoder(BaseEncoder):
    static = True

    @staticmethod
    def decode(value: str | None = None) -> bool:
        return value == '1'

    @staticmethod
    def encode(value: bool | None = None) -> str:
        return '1' if value else '0'


class HomePostalAddressPropertyEncoder(BaseEncoder):
    static = True

    @staticmethod
    def decode(value: list[list[str]] | None = None) -> list[dict[str, str]] | None:
        if value:
            return [{'street': v[0], 'zipcode': v[1], 'city': v[2]} for v in value]
        else:
            return value

    @staticmethod
    def encode(value: list[dict[str, str]] | None = None) -> list[list[str]] | None:
        if value:
            return [[v['street'], v['zipcode'], v['city']] for v in value]
        else:
            return value


class ListOfListOflTextToDictPropertyEncoder(BaseEncoder):
    static = True

    @staticmethod
    def decode(value: list[list[str]] | None = None) -> dict[str, str] | None:
        if value is None:
            return value
        return dict(value)

    @staticmethod
    def encode(value: dict[str, str] | None = None) -> list[list[str]] | None:
        if value:
            return [[k, v] for k, v in value.items()]
        else:
            return value


class MultiLanguageTextAppcenterPropertyEncoder(BaseEncoder):
    static = True

    @staticmethod
    def decode(value: list[str] | None = None) -> dict[str, str] | None:
        if value:
            res = {}
            for s in value:
                lang, txt = s.split(' ', 1)
                lang = lang.strip('[]')
                res[lang] = txt
            return res
        else:
            return value

    @staticmethod
    def encode(value: dict[str, str] | None = None) -> list[str] | None:
        if value:
            return [f'[{k}] {v}' for k, v in value.items()]
        else:
            return value


class SambaGroupTypePropertyEncoder(BaseEncoder):
    static = True
    choices = dict(sambaGroupType.choices)
    choices_reverted = {v: k for k, v in sambaGroupType.choices}

    @classmethod
    def decode(cls, value: list[str] | None = None) -> str | None:
        try:
            return cls.choices[value]
        except KeyError:
            return value

    @classmethod
    def encode(cls, value: str | None = None) -> list[str] | None:
        try:
            return cls.choices_reverted[value]
        except KeyError:
            return value


class SambaLogonHoursPropertyEncoder(BaseEncoder):
    static = True
    _weekdays = ('Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat')

    @classmethod
    def decode(cls, value: list[int] | None = None) -> list[str] | None:
        if value:
            return [f'{cls._weekdays[dow]} {hour}-{hour + 1}' for dow, hour in (divmod(v, 24) for v in value)]
        else:
            return value

    @classmethod
    def encode(cls, value: list[str] | None = None) -> list[int] | None:
        if value:
            try:
                values = [v.split() for v in value]
                return [cls._weekdays.index(w) * 24 + int(h.split('-', 1)[0]) for w, h in values]
            except (IndexError, ValueError):
                raise valueInvalidSyntax('One or more entries in sambaLogonHours have invalid syntax.').with_traceback(sys.exc_info()[2])
        else:
            return value


class StringCaseInsensitiveResultLowerBooleanPropertyEncoder(BaseEncoder):
    static = True
    result_case_func = 'lower'
    false_string = 'false'
    true_string = 'true'

    @classmethod
    def decode(cls, value: str | None = '') -> bool:
        return isinstance(value, str) and value.lower() == cls.true_string

    @classmethod
    def encode(cls, value: bool | None = None) -> str:
        assert cls.result_case_func in ('lower', 'upper')
        if value:
            return getattr(cls.true_string, cls.result_case_func)()
        else:
            return getattr(cls.false_string, cls.result_case_func)()


class StringCaseInsensitiveResultUpperBooleanPropertyEncoder(StringCaseInsensitiveResultLowerBooleanPropertyEncoder):
    result_case_func = 'upper'


class StringIntBooleanPropertyEncoder(BaseEncoder):
    static = True

    @staticmethod
    def decode(value: str | None = None) -> bool:
        return value == '1'

    @staticmethod
    def encode(value: bool | None = None) -> str:
        if value:
            return '1'
        else:
            return '0'


class StringIntPropertyEncoder(BaseEncoder):
    static = False

    def decode(self, value: str | None = None) -> int | None:
        if value in ('', None):
            return None
        else:
            try:
                return int(value)
            except ValueError:
                raise valueInvalidSyntax(f'Value of {self.property_name!r} must be an int (is {value!r}).').with_traceback(sys.exc_info()[2])

    @staticmethod
    def encode(value: int | None = None) -> str | None:
        if value is None:
            return value
        else:
            return str(value)


class StringListToList(BaseEncoder):
    static = True
    separator = ' '

    @classmethod
    def decode(cls, value: str | None = None) -> list[str] | None:
        if value:
            return value.split(cls.separator)
        else:
            return value

    @classmethod
    def encode(cls, value: list[str] | None = None) -> str | None:
        if value:
            return cls.separator.join(value)
        else:
            return value


class DnListPropertyEncoder(BaseEncoder):
    """
    Given a list of DNs, return the same list with an additional member
    ``objs``. ``objs`` is a lazy object that will become the list of UDM
    objects the DNs refer to, when accessed.

    :py:func:`dn_list_property_encoder_for()` will dynamically produce
    subclasses of this for every UDM module required.
    """

    static = False
    udm_module_name = ''

    class DnsList(list):
        # a list with an additional member variable
        objs = None

        def __deepcopy__(self, memodict=None):
            return list(self)

    class MyProxy(lazy_object_proxy.Proxy):
        # overwrite __repr__ for better navigation in ipython
        def __repr__(self, __getattr__: Callable[[object, str], object] = object.__getattribute__) -> str:
            return super(DnListPropertyEncoder.MyProxy, self).__str__()

    def __init__(self, property_name: str | None = None, connection: Any | None = None, api_version: int | None = None, *args: Any, **kwargs: Any) -> None:
        assert connection is not None, 'Argument "connection" must not be None.'
        assert api_version is not None, 'Argument "api_version" must not be None.'
        super().__init__(property_name, *args, **kwargs)
        self._udm = UDM(connection, api_version)

    def _list_of_dns_to_list_of_udm_objects(self, value):
        udm_module = None
        res = []
        for dn in value:
            try:
                if self.udm_module_name == 'auto':
                    obj = self.udm.obj_by_dn(dn)
                else:
                    if not udm_module:
                        udm_module = self.udm.get(self.udm_module_name)
                    obj = udm_module.get(dn)
            except UnknownModuleType as exc:
                logging.getLogger('ADMIN').warning('%s', exc)
            except NoObject as exc:
                logging.getLogger('ADMIN').warning('%s', exc)
            else:
                res.append(obj)
        return res

    def decode(self, value: list[str] | None = None) -> list[str] | None:
        if value is None:
            value = []
        assert hasattr(value, '__iter__'), f'Value is not iterable: {value!r}'
        new_list = self.DnsList(value)
        new_list.objs = self.MyProxy(lambda: self._list_of_dns_to_list_of_udm_objects(value))
        return new_list

    @staticmethod
    def encode(value: list[str] | None = None) -> list[str] | None:
        try:
            del value.objs
        except AttributeError:
            pass
        return value

    @property
    def udm(self) -> object:
        return self._udm


class PoliciesEncoder(BaseEncoder):
    static = False

    def __init__(self, property_name: str | None = None, connection: Any | None = None, api_version: int | None = None, module_name: str | None = None, *args: Any, **kwargs: Any) -> None:
        assert connection is not None, 'Argument "connection" must not be None.'
        assert api_version is not None, 'Argument "api_version" must not be None.'
        super().__init__(property_name, *args, **kwargs)
        self._udm = UDM(connection, api_version)
        self.module_name = module_name

    def decode(self, value: Any | None = None) -> dict[Any, list[Any]]:
        policies = {}
        policy_modules = univention.admin.modules.policyTypes(self.module_name)
        if not policy_modules and self._udm.get(self.module_name)._orig_udm_module.childs:  # container, which allows every policy-type
            policy_modules = [x for x in univention.admin.modules.modules if x.startswith('policies/') and x != 'policies/policy']

        for policy_module in policy_modules:
            policies.setdefault(policy_module, [])

        for policy_dn in value or []:
            policy_module = self._udm.obj_by_dn(policy_dn)._udm_module.name
            if policy_module not in policies:
                continue
            policies[policy_module].append(policy_dn)

        return policies

    def encode(self, value: dict[Any, list[Any]] | None = None) -> list[Any]:
        if value:
            return [y for x in value.values() for y in x]
        else:
            return []


class CnameListPropertyEncoder(DnListPropertyEncoder):
    """
    Given a list of CNAMEs, return the same list with an additional member
    ``objs``. ``objs`` is a lazy object that will become the list of UDM
    objects the CNAMEs refer to, when accessed.
    """

    udm_module_name = 'dns/alias'

    def _list_of_dns_to_list_of_udm_objects(self, value):
        udm_module = self.udm.get(self.udm_module_name)
        return [list(udm_module.search(f'relativeDomainName={cname}'))[0] for cname in value]  # noqa: RUF015


class DnsEntryZoneAliasListPropertyEncoder(DnListPropertyEncoder):
    """
    Given a list of dnsEntryZoneAlias entries, return the same list with an
    additional member ``objs``. ``objs`` is a lazy object that will become
    the list of UDM objects the dnsEntryZoneAlias entries refer to, when
    accessed.
    """

    udm_module_name = 'dns/alias'

    def _list_of_dns_to_list_of_udm_objects(self, value):
        udm_module = self.udm.get(self.udm_module_name)
        return [udm_module.get(f'relativeDomainName={v[2]},{v[1]}') for v in value]


class DnsEntryZoneForwardListMultiplePropertyEncoder(DnListPropertyEncoder):
    """
    Given a list of dnsEntryZoneForward entries, return the same list with an
    additional member ``objs``. ``objs`` is a lazy object that will become
    the list of UDM objects the dnsEntryZoneForward entries refer to, when
    accessed.
    """

    udm_module_name = 'dns/forward_zone'

    @staticmethod
    def _itemgetter(value):
        return value[0]

    def _list_of_dns_to_list_of_udm_objects(self, value):
        udm_module = self.udm.get(self.udm_module_name)
        return [udm_module.get(self._itemgetter(v)) for v in value]


class DnsEntryZoneForwardListSinglePropertyEncoder(DnsEntryZoneForwardListMultiplePropertyEncoder):
    """
    Given a list of dnsEntryZoneForward entries, return the same list with an
    additional member ``objs``. ``objs`` is a lazy object that will become
    the list of UDM objects the dnsEntryZoneForward entries refer to, when
    accessed.
    """

    udm_module_name = 'dns/forward_zone'

    @staticmethod
    def _itemgetter(value):
        return value


class DnsEntryZoneReverseListMultiplePropertyEncoder(DnsEntryZoneForwardListMultiplePropertyEncoder):
    """
    Given a list of dnsEntryZoneReverse entries, return the same list with an
    additional member ``objs``. ``objs`` is a lazy object that will become
    the list of UDM objects the dnsEntryZoneReverse entries refer to, when
    accessed.
    """

    udm_module_name = 'dns/reverse_zone'

    @staticmethod
    def _itemgetter(value):
        return value[0]


class DnsEntryZoneReverseListSinglePropertyEncoder(DnsEntryZoneReverseListMultiplePropertyEncoder):
    """
    Given a list of dnsEntryZoneReverse entries, return the same list with an
    additional member ``objs``. ``objs`` is a lazy object that will become
    the list of UDM objects the dnsEntryZoneReverse entries refer to, when
    accessed.
    """

    udm_module_name = 'dns/reverse_zone'

    @staticmethod
    def _itemgetter(value):
        return value


class DnPropertyEncoder(BaseEncoder):
    """
    Given a DN, return a string object with the DN and an additional member
    ``obj``. ``obj`` is a lazy object that will become the UDM object the DN
    refers to, when accessed.

    :py:func:`dn_property_encoder_for()` will dynamically produce
    subclasses of this for every UDM module required.
    """

    static = False
    udm_module_name = ''

    class DnStr(str):  # noqa: SLOT000
        # a string with an additional member variable
        obj = None

        def __deepcopy__(self, memodict=None):
            return str(self)

    class MyProxy(lazy_object_proxy.Proxy):
        # overwrite __repr__ for better navigation in ipython
        def __repr__(self, __getattr__: Callable[[object, str], object] = object.__getattribute__) -> str:
            return super(DnPropertyEncoder.MyProxy, self).__str__()

    def __init__(self, property_name: str | None = None, connection: Any = None, api_version: int | None = None, *args: Any, **kwargs: Any) -> None:
        assert connection is not None, 'Argument "connection" must not be None.'
        assert api_version is not None, 'Argument "api_version" must not be None.'
        super().__init__(property_name, *args, **kwargs)
        self._udm = UDM(connection, api_version)

    def _dn_to_udm_object(self, value: Any) -> Any | None:
        try:
            if self.udm_module_name == 'auto':
                return self.udm.obj_by_dn(value)
            else:
                udm_module = self.udm.get(self.udm_module_name)
                return udm_module.get(value)
        except UnknownModuleType as exc:
            logging.getLogger('ADMIN').error('%s', exc)
        except NoObject as exc:
            logging.getLogger('ADMIN').warning('%s', exc)
        return None

    def decode(self, value: str | None = None) -> str | None:
        if value in (None, ''):
            return None
        new_str = self.DnStr(value)
        if value:
            new_str.obj = self.MyProxy(lambda: self._dn_to_udm_object(value))
        return new_str

    @staticmethod
    def encode(value: str | None = None) -> str | None:
        try:
            del value.obj
        except AttributeError:
            pass
        return value

    @property
    def udm(self) -> UDM:
        return self._udm


def _classify_name(name: str) -> str:
    mod_parts = name.split('/')
    return ''.join(f'{mp[0].upper()}{mp[1:]}' for mp in mod_parts)


def dn_list_property_encoder_for(udm_module_name: str) -> type[DnListPropertyEncoder]:
    """
    Create a (cached) subclass of DnListPropertyEncoder specific for each UDM
    module.

    :param str udm_module_name: name of UDM module (e.g. `users/user`) or
            `auto` if auto-detection should be done. Auto-detection requires one
            additional LDAP-query per object (still lazy though)!
    :return: subclass of DnListPropertyEncoder
    """
    if udm_module_name not in __dn_list_property_encoder_class_cache:
        cls_name = f'DnListPropertyEncoder{_classify_name(udm_module_name)}'
        specific_encoder_cls = type(cls_name, (DnListPropertyEncoder,), {})
        specific_encoder_cls.udm_module_name = udm_module_name  # type: ignore[attr-defined]
        __dn_list_property_encoder_class_cache[udm_module_name] = specific_encoder_cls
    return __dn_list_property_encoder_class_cache[udm_module_name]


def dn_property_encoder_for(udm_module_name: str) -> type[DnPropertyEncoder]:
    """
    Create a (cached) subclass of DnPropertyEncoder specific for each UDM
    module.

    :param str udm_module_name: name of UDM module (e.g. `users/user`) or
            `auto` if auto-detection should be done. Auto-detection requires one
            additional LDAP-query per object (still lazy though)!
    :return: subclass of DnPropertyEncoder
    """
    if udm_module_name not in __dn_property_encoder_class_cache:
        cls_name = f'DnPropertyEncoder{_classify_name(udm_module_name)}'
        specific_encoder_cls = type(cls_name, (DnPropertyEncoder,), {})
        specific_encoder_cls.udm_module_name = udm_module_name  # type: ignore[attr-defined]
        __dn_property_encoder_class_cache[udm_module_name] = specific_encoder_cls
    return __dn_property_encoder_class_cache[udm_module_name]
