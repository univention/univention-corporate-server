#!/usr/bin/python3
# SPDX-FileCopyrightText: 2022-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import asyncio
import weakref

from .log import CORE


class _LogoutNotifiers:
    def __init__(self):
        self.__events = weakref.WeakValueDictionary()
        self.__lock = asyncio.Lock()

    async def get_or_set(self, session_id: str):
        async with self.__lock:
            event = self.__events.get(session_id, None)
            if event is None:
                event = asyncio.Event()
                weakref.finalize(event, lambda: CORE.debug("logout-sse event for session-id %s garbage collected", session_id))
                self.__events[session_id] = event
            return event

    def get(self, session_id: str):
        event = self.__events.get(session_id, None)
        return event


logout_notifiers: _LogoutNotifiers = _LogoutNotifiers()
