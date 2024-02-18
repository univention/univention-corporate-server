#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Management Console
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2006-2024 Univention GmbH
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

import warnings

from .definitions import (
    BAD_REQUEST, BAD_REQUEST_UNAUTH, MODULE_ERR, MODULE_ERR_COMMAND_FAILED, MODULE_ERR_INIT_FAILED, SUCCESS,
)
from .message import (
    MIMETYPE_HTML, MIMETYPE_JPEG, MIMETYPE_JSON, MIMETYPE_PLAIN, MIMETYPE_PNG, Message, Request, Response,
)
from .session import TEMPUPLOADDIR


warnings.warn('Importing code from obsolete univention.management.console.protocol. This is going to be removed without replacement in UCS 5.1.', DeprecationWarning, stacklevel=2)

__all__ = (
    'BAD_REQUEST',
    'BAD_REQUEST_UNAUTH',
    'MIMETYPE_HTML',
    'MIMETYPE_JPEG',
    'MIMETYPE_JSON',
    'MIMETYPE_PLAIN',
    'MIMETYPE_PNG',
    'MODULE_ERR',
    'MODULE_ERR_COMMAND_FAILED',
    'MODULE_ERR_INIT_FAILED',
    'SUCCESS',
    'TEMPUPLOADDIR',
    'Message',
    'Request',
    'Response',
)
