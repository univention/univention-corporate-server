#!/usr/bin/python3
# SPDX-FileCopyrightText: 2022-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import argparse
from multiprocessing import managers

from setproctitle import getproctitle, setproctitle


proctitle = getproctitle()


class _SharedMemory(managers.SyncManager):

    started = False
    saml_state_cache = {}
    children = {}
    pkce = {}

    def dict(self):
        if self.started:
            return super().dict()
        return {}

    def namespace(self):
        if self.started:
            return self.Namespace()
        return argparse.Namespace()

    def start(self, *args, **kwargs):
        self.started = True
        setproctitle(proctitle + '   # multiprocessing manager')
        try:
            super().start(*args, **kwargs)
        finally:
            setproctitle(proctitle)

        # we must create the parent dictionary instance before forking but after python importing
        self.saml_state_cache = self.dict()
        self.children = self.dict()
        self.pkce = self.dict()


shared_memory = _SharedMemory()
