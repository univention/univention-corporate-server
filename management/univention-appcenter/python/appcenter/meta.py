#!/usr/bin/python3
#
# Univention App Center
#  Metaclass
#
# SPDX-FileCopyrightText: 2015-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#


class UniventionMetaInfo:
    pop = False
    save_as_list = False
    save_as_dict = False
    inheriting = True
    auto_set_name = False

    def _add_inheritace_info(self, klass, name):
        if self.inheriting:
            inheritance_info = getattr(klass, '_univention_meta_inheritance', set())
            inheritance_info.add(name)
            klass._univention_meta_inheritance = inheritance_info

    def set_name(self, name):
        name_attr = self.auto_set_name
        if name_attr is True:
            name_attr = 'name'
        setattr(self, name_attr, name)

    def contribute_to_class(self, klass, name):
        if self.auto_set_name:
            self.set_name(name)
        if self.save_as_list:
            if not hasattr(klass, self.save_as_list):
                self._add_inheritace_info(klass, self.save_as_list)
                setattr(klass, self.save_as_list, [])
            getattr(klass, self.save_as_list).append(self)
        if self.save_as_dict:
            if not hasattr(klass, self.save_as_dict):
                self._add_inheritace_info(klass, self.save_as_dict)
                setattr(klass, self.save_as_dict, {})
            getattr(klass, self.save_as_dict)[name] = self


class UniventionMetaClass(type):

    def __new__(mcs, name, bases, attrs):
        meta_infos = []
        for key, value in list(attrs.items()):
            if hasattr(value, 'contribute_to_class'):
                if value.pop:
                    attrs.pop(key)
                meta_infos.append((key, value))
        inheritance_info = set()
        for base in bases:
            if hasattr(base, '_univention_meta_inheritance'):
                for inheritance_name in base._univention_meta_inheritance:
                    inheritance_value = getattr(base, inheritance_name)
                    if isinstance(inheritance_value, dict):
                        attrs.setdefault(inheritance_name, {}).update(inheritance_value)
                    if isinstance(inheritance_value, list):
                        attrs.setdefault(inheritance_name, []).extend(inheritance_value)
                    inheritance_info.add(inheritance_name)
        attrs['_univention_meta_inheritance'] = inheritance_info
        new_cls = super().__new__(mcs, name, bases, attrs)
        for meta_info_name, meta_info in meta_infos:
            meta_info.contribute_to_class(new_cls, meta_info_name)
        return new_cls
