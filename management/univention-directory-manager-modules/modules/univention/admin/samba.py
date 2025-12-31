# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| samba related code"""

import string
from collections import OrderedDict


class acctFlags:
    """Samba Account Flags"""

    def __init__(self, flagstring=None, flags=None, fallbackflags=None):
        if flags is not None:
            self.__flags = OrderedDict(flags)
            return
        if not flagstring or not isinstance(flagstring, str) or len(flagstring) != 13:
            if fallbackflags is not None:
                self.__flags = OrderedDict(fallbackflags)
                return
            flagstring = '[U          ]'
        flags = {}
        flagstring = flagstring[1:-1]
        for letter in flagstring:
            if letter not in string.whitespace:
                flags[letter] = 1
        self.__flags = OrderedDict(flags)

    def __setitem__(self, key, value):
        self.__flags[key] = value

    def __getitem__(self, key):
        return self.__flags[key]

    def decode(self):
        flagstring = '['
        for flag, set in self.__flags.items():
            if set:
                flagstring = flagstring + flag
        while len(flagstring) < 12:
            flagstring += ' '
        flagstring += ']'
        return flagstring

    def set(self, flag):
        self[flag] = 1
        return self.decode()

    def unset(self, flag):
        self[flag] = 0
        return self.decode()
