#!/usr/bin/python3
# SPDX-FileCopyrightText: 2021-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import json
from multiprocessing import managers

from setproctitle import getproctitle, setproctitle


proctitle = getproctitle()


class _SharedMemory(managers.SyncManager):

    children = {}
    queue = {}
    search_sessions = {}
    authenticated = {}

    def start(self, *args, **kwargs):
        setproctitle(proctitle + '   # multiprocessing manager')
        try:
            super().start(*args, **kwargs)
        finally:
            setproctitle(proctitle)

        # we must create the parent dictionary instance before forking but after Python importing
        self.children = self.dict()
        self.queue = self.dict()
        self.search_sessions = self.dict()
        self.authenticated = self.dict()


shared_memory = _SharedMemory()


class JsonEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, managers.DictProxy):
            return dict(o)
        if isinstance(o, managers.ListProxy):
            return list(o)
        raise TypeError(f'Object of type {type(o).__name__} is not JSON serializable')
