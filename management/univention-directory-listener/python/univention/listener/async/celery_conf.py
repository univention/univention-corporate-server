# -*- coding: utf-8 -*-
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

from __future__ import absolute_import


__rabbit_mq_user = 'listener'
__rabbit_mq_pw = open('/etc/univention/rabbitmq_listener.secret', 'rb').read().strip()
__rabbit_mq_vhost = 'listener'


BROKER_URL = 'amqp://{}:{}@localhost:5672/{}'.format(__rabbit_mq_user, __rabbit_mq_pw, __rabbit_mq_vhost)
CELERYD_TASK_LOG_FORMAT = '[%(asctime)s: %(processName)s %(task_id)s] %(levelname)-8s %(module)s.%(funcName)s:%(lineno)d: %(message)s'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_EVENT_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'
CELERY_ENABLE_UTC = True
CELERY_TIMEZONE = 'Europe/Berlin'
