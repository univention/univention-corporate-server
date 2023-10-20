#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2019-2023 Univention GmbH
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

import json
import logging
from datetime import datetime
from socket import gethostname
from typing import Dict, List  # noqa: F401

import six

from univention.config_registry import ConfigRegistry


ucr = ConfigRegistry()
ucr.load()

LOG_FILE = '/var/log/univention/admindiary.log'


def get_events_to_reject() -> "List[str]":
    ucrv = 'admin/diary/reject'
    blocked_events = ucr.get(ucrv)
    if blocked_events:
        return blocked_events.split()
    return []


class _ShortNameFormatter(logging.Formatter):
    shorten = 'univention.admindiary'

    def format(self, record: "logging.LogRecord") -> str:
        record.short_name = record.name
        if record.short_name.startswith(f'{self.shorten}.'):
            record.short_name = record.short_name[len(self.shorten) + 1:]
        return super(_ShortNameFormatter, self).format(record)


def _setup_logger() -> "logging.Logger":
    base_logger = logging.getLogger('univention.admindiary')
    if not _setup_logger._setup:
        base_logger.setLevel(logging.INFO)
        log_format = '%(process)6d %(short_name)-12s %(asctime)s [%(levelname)8s]: %(message)s'
        log_format_time = '%y-%m-%d %H:%M:%S'
        formatter = _ShortNameFormatter(log_format, log_format_time)
        try:
            handler = logging.FileHandler(LOG_FILE)
            handler.setFormatter(formatter)
            base_logger.addHandler(handler)
        except EnvironmentError:
            pass
        _setup_logger._setup = True
    return base_logger


_setup_logger._setup = False


def get_logger(name: str) -> "logging.Logger":
    base_logger = _setup_logger()
    logger = base_logger.getChild(name)
    log_level = ucr.get(f'admin/diary/logging/{name}')
    if log_level:
        log_level = logging.getLevelName(log_level)
        if isinstance(log_level, int):
            logger.setLevel(log_level)
        else:
            logger.warning(f'Cannot use log level {log_level}. Call ucr set admin/diary/logging/{name}=DEBUG (for example)')
    return logger


class DiaryEntry(object):
    def __init__(self, username: str, message: str, args: "Dict[str, str]", tags: "List[str]", context_id: str, event_name: str) -> None:
        self.username = username
        self.hostname = gethostname()
        self.message = message
        self.args = args
        self.timestamp = datetime.now()
        self.tags = tags
        self.context_id = context_id
        self.event_name = event_name

    def assert_types(self) -> None:
        if not isinstance(self.username, six.string_types):
            raise TypeError(f'DiaryEntry() argument "username" has to be "string", but is: {type(self.username)} ({self.username})')
        if not isinstance(self.hostname, six.string_types):
            raise TypeError(f'DiaryEntry().hostname has to be "string", but is: {type(self.hostname)} ({self.hostname})')
        if not isinstance(self.args, dict) or not all(isinstance(key, six.string_types) and isinstance(value, six.string_types) for key, value in self.args.items()):
            raise TypeError(f'DiaryEntry() argument "args" has to be "dict of string/string", but is: {type(self.args)} ({self.args})')
        if self.message is not None:
            if not isinstance(self.message, dict) or not all(isinstance(key, six.string_types) and isinstance(value, six.string_types) for key, value in self.message.items()):
                raise TypeError(f'DiaryEntry() argument "message" has to be "dict of string/string", but is: {type(self.message)} ({self.message})')
            for locale, message in self.message.items():
                try:
                    message.format(**self.args)
                except Exception:
                    raise TypeError('DiaryEntry() argument "message" (%s, %r) has wrong format for given args (%r).', locale, message, self.args)
        if not isinstance(self.timestamp, datetime):
            raise TypeError('DiaryEntry().timestamp has to be "datetime"')
        if not isinstance(self.tags, list) or not all(isinstance(tag, six.string_types) for tag in self.tags):
            raise TypeError(f'DiaryEntry() argument "tags" have to be "list of string", but is: {type(self.tags)} ({self.tags})')
        if not isinstance(self.context_id, six.string_types):
            raise TypeError(f'DiaryEntry() argument "context_id" has to be "string", but is: {type(self.context_id)} ({self.context_id})')
        if not isinstance(self.event_name, six.string_types):
            raise TypeError(f'DiaryEntry() argument "event" name has to be "string", but is: {type(self.event_name)} ({self.event_name})')

    def to_json(self) -> str:
        attrs = {
            'username': self.username,
            'hostname': self.hostname,
            'message': self.message,
            'args': self.args,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S%z'),
            'tags': self.tags,
            'context_id': self.context_id,
            'event': self.event_name,
            'type': 'Entry v1',
        }
        return json.dumps(attrs)

    @classmethod
    def from_json(cls, body: str) -> "DiaryEntry":
        json_body = json.loads(body)
        entry = cls(json_body['username'], json_body['message'], json_body['args'], json_body['tags'], json_body['context_id'], json_body['event'])
        entry.timestamp = datetime.strptime(json_body['timestamp'], '%Y-%m-%d %H:%M:%S')
        entry.hostname = json_body['hostname']
        entry.assert_types()
        return entry
