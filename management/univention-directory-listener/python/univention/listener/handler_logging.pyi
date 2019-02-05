# -*- coding: utf-8 -*-
#
# Univention Directory Listener
#  PEP 484 type hints stub file
#
# Copyright 2017-2019 Univention GmbH
#
# http://www.univention.de/
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
# you and Univention.
#
# This program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

#
# Get a Python logging object below a listener module root logger.
# The new logging object can log to a stream or a file.
# The listener module root logger will log messages of all of its children
# additionally to the common listener.log.
#

#
# Code mostly copied and adapted from
# ucs-school-4.2/ucs-school-lib/python/models/utils.py
#

from __future__ import absolute_import
import grp
import pwd
import logging
from logging.handlers import TimedRotatingFileHandler
import univention.debug as ud
from univention.config_registry import ConfigRegistry
from typing import Any, Dict, IO, Optional, Type


__syslog_opened = False

class UniFileHandler(TimedRotatingFileHandler):
	def _open(self) -> IO[str]:
		...

class ModuleHandler(logging.Handler):
	LOGGING_TO_UDEBUG = None  # type: Dict[str, int]

	def __init__(self, level: int  = logging.NOTSET, udebug_facility: int = ud.LISTENER) -> None:
		...
	def emit(self, record: logging.LogRecord) -> None:
		...

FILE_LOG_FORMATS = dict()  # type: Dict[str, str]
CMDLINE_LOG_FORMATS = dict()  # type: Dict[str, str]
UCR_DEBUG_LEVEL_TO_LOGGING_LEVEL = dict()  # type: Dict[int, str]
LOG_DATETIME_FORMAT = ''  # type: str
_logger_cache = dict()  # type: Dict[str, logging.Logger]
_handler_cache = dict()  # type: Dict[str, UniFileHandler]
_ucr = ConfigRegistry()  # type: ConfigRegistry

def _get_ucr_int(ucr_key: str, default: Any) -> Any:
	...
def get_logger(name: str, path: Optional[str] = None) -> logging.Logger:
	...
def calculate_loglevel(name: str) -> str:
	...
def get_listener_logger(
		name: str,
		filename: str,
		level: Optional[str] = None,
		handler_kwargs: Optional[dict] = None,
		formatter_kwargs: Optional[dict] = None
) -> logging.Logger:
	fmt_kwargs = dict()  # type: Dict[str, Any]
	formatter_cls = logging.Formatter  # type: Type[logging.Formatter]
	_logger = logging.getLogger(name)  # type: logging.Logger
	return _logger
def _log_to_syslog(level: int, msg: str) -> None:
	...
def info_to_syslog(msg: str) -> None:
	...
