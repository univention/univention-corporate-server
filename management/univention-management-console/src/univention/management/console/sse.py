#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2022-2024 Univention GmbH
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

import asyncio
import weakref

from tornado.iostream import StreamClosedError

from .log import CORE
from .resource import Resource


class _LogoutNotifiers:
    def __init__(self):
        self.__events = weakref.WeakValueDictionary()
        self.__lock = asyncio.Lock()

    async def get_or_set(self, session_id: str):
        async with self.__lock:
            event = self.__events.get(session_id, None)
            if event is None:
                event = asyncio.Event()
                weakref.finalize(event, lambda: CORE.debug("logout-sse event for session-id %s garbage collected" % session_id))
                self.__events[session_id] = event
            return event

    def get(self, session_id: str):
        return self.__events.get(session_id, None)


async def wait_task(event):
    try:
        return await event.wait()
    except asyncio.CancelledError as e:
        raise e


class SSELogoutNotifer(Resource):
    requires_authentication = True
    wait_task = None
    cancelled = True

    async def wait(self, event: asyncio.Event):
        self.wait_task = asyncio.create_task(wait_task(event))
        try:
            ret = await self.wait_task
            self.cancelled = False
            return ret
        except asyncio.CancelledError:
            CORE.debug("logout-sse wait_task has been cancelled")

    async def get(self):
        self.set_header('content-type', 'text/event-stream')
        self.set_header('cache-control', 'no-cache')
        self.set_status(200)
        self.write("data:init\n\n")
        await self.flush()

        session_id = self.current_user.session_id
        self.for_session_id = session_id
        CORE.debug("logout-sse requested for session_id %s" % (session_id, ))

        event = await logout_notifiers.get_or_set(session_id)

        await self.wait(event)
        CORE.debug("logout-sse finished for session_id %s" % session_id)

        # the connection might have already been closed here, and we might not even have been logged out
        try:
            if not self.cancelled:
                self.write("data:logout\n\n")
            self.finish()
        except StreamClosedError:
            pass

    def on_connection_close(self):
        if self.wait_task is not None:
            CORE.debug("logout-sse connection closed by client and wait task still active. Cancelling")
            self.wait_task.cancel()

    def on_finish(self):
        if self.wait_task is not None and (not self.wait_task.cancelled() or not self.wait_task.done()):
            CORE.debug("logout-sse request finished but task not cancelled and not finished")
            self.wait_task.cancel()


logout_notifiers: _LogoutNotifiers = _LogoutNotifiers()
