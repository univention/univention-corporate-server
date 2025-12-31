#
# Univention Directory Reports
#  write an interpreted token structure to a file
#
# SPDX-FileCopyrightText: 2007-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import codecs
import os

from .tokens import AttributeToken, DateToken, PolicyToken, QueryToken, ResolveToken, TextToken


class Output:

    def __init__(self, tokens, filename=None, fd=None):
        self._tokens = tokens
        self._filename = filename
        self._fd = fd

    def _create_dir(self):
        if not os.path.isdir(os.path.dirname(self._filename)):
            os.makedir(self.path, mode=0o700)

    def open(self):
        if self._fd:
            return
        self._create_dir()
        self._fd = codecs.open(self._filename, 'wb', encoding='utf8')

    def close(self):
        if self._fd:
            self._fd.close()
        self._fd = None

    def write(self, tokens=[]):
        if not self._fd:
            return
        if not tokens:
            tokens = self._tokens
        for token in tokens:
            if isinstance(token, TextToken):
                self._fd.write(str(token.data))
            elif isinstance(token, ResolveToken | QueryToken):
                if len(token):
                    self.write(token)
            elif isinstance(token, DateToken | AttributeToken | PolicyToken):
                self._fd.write(token.value)
