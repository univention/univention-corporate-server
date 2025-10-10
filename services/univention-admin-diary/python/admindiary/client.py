#!/usr/bin/python3
# SPDX-FileCopyrightText: 2019-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import logging
import os
import uuid
from collections.abc import Callable
from functools import partial, wraps
from getpass import getuser
from logging.handlers import SysLogHandler
from typing import Any, TypeVar

from univention.admindiary import DiaryEntry, get_events_to_reject, get_logger
from univention.admindiary.events import DiaryEvent


get_logger = partial(get_logger, 'client')

F = TypeVar('F', bound=Callable[..., Any])


def exceptionlogging(f: F) -> F:
    @wraps(f)
    def wrapper(*args, **kwds):
        try:
            return f(*args, **kwds)
        except Exception as exc:
            get_logger().exception('%s failed! %s' % (f.__name__, exc))
            return ''
    return wrapper  # type: ignore


class RsyslogEmitter:
    def __init__(self) -> None:
        self.handler: SysLogHandler | None = None

    def emit(self, entry: object) -> None:
        if self.handler is None:
            if os.path.exists('/dev/log'):
                self.handler = SysLogHandler(address='/dev/log', facility='user')
            else:
                get_logger().error('RsyslogEmitter().emit() failed: /dev/log does not exist, cannot emit entry (%s)' % (entry,))
                return
        record = logging.LogRecord('diary-rsyslogger', logging.INFO, None, None, 'ADMINDIARY: ' + str(entry), (), None, None)
        self.handler.emit(record)


emitter = RsyslogEmitter()


@exceptionlogging
def add_comment(message: str, context_id: str, username: str | None = None) -> int | None:
    event = DiaryEvent('COMMENT', {'en': message})
    return write_event(event, username=username, context_id=context_id)


@exceptionlogging
def write_event(event: DiaryEvent, args: dict[str, str] | None = None, username: str | None = None, context_id: str | None = None) -> int | None:
    args = args or {}
    return write(event.message, args, username, event.tags, context_id, event.name)


@exceptionlogging
def write(message: str, args: dict[str, str] | None = None, username: str | None = None, tags: list[str] | None = None, context_id: str | None = None, event_name: str | None = None) -> int | None:
    if username is None:
        username = getuser()
    if args is None:
        args = {}
    if tags is None:
        tags = []
    if context_id is None:
        context_id = os.environ.get('ADMINDIARY_CONTEXT') or str(uuid.uuid4())
    if event_name is None:
        event_name = 'CUSTOM'
    entry = DiaryEntry(username, message, args, tags, context_id, event_name)
    return write_entry(entry)


@exceptionlogging
def write_entry(entry: DiaryEntry) -> int | None:
    entry.assert_types()
    blocked_events = get_events_to_reject()
    if entry.event_name in blocked_events:
        get_logger().info('Rejecting %s' % entry.event_name)
        return None
    body = entry.to_json()
    emitter.emit(body)
    get_logger().debug('Successfully wrote %s. (%s)' % (entry.context_id, entry.event_name))
    return entry.context_id
