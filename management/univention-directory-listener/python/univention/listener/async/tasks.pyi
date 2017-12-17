# -*- coding: utf-8 -*-
#
# Univention Directory Listener
#  PEP 484 type hints stub file
#
# Copyright 2017 Univention GmbH
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

from __future__ import absolute_import
from celery import shared_task
from celery.signals import after_setup_task_logger, Signal
from univention.listener.async.listener_task import ListenerTask


@after_setup_task_logger.connect
def after_setup_task_logger_handler(sender: Signal = None, headers=None, body=None, **kwargs: str) -> None:
	...
@shared_task(base=ListenerTask, bind=True)
def async_listener_job(self: ListenerTask, filename: str, name: str) -> None:
	...
