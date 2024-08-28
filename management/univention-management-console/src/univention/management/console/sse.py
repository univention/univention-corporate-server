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
                weakref.finalize(event, lambda: CORE.debug("logout-sse event for session-id %s garbage collected" % session_id))
                self.__events[session_id] = event
            return event

    def get(self, session_id: str):
        event = self.__events.get(session_id, None)
        return event


logout_notifiers: _LogoutNotifiers = _LogoutNotifiers()
