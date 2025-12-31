#!/usr/bin/python3
#
# Univention Management Console
#  JSON helper classes, locale stuff etc.
#
# SPDX-FileCopyrightText: 2006-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


class JSON_Object:
    """
    Converts Python object into JSON compatible data
    structures. Types like lists, tuples and dictionary are converted
    directly. If none of these types matches the method tries to convert
    the attributes of the object and generate a dict to represent it.
    """

    def _json_list(self, obj):
        result = []
        for item in obj:
            if isinstance(item, JSON_Object):
                result.append(item.json())
            else:
                result.append(item)
        return result

    def _json_dict(self, obj):
        result = {}
        for key, value in obj.items():
            if isinstance(value, JSON_Object):
                result[key] = value.json()
            else:
                result[key] = value
        return result

    def json(self):
        if isinstance(self, list | tuple):
            return self._json_list(self)
        elif isinstance(self, dict):
            return self._json_dict(self)
        return self._json_dict(self.__dict__)


class JSON_List(list, JSON_Object):
    pass


class JSON_Dict(dict, JSON_Object):
    pass
