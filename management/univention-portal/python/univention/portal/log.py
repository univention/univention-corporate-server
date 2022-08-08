#!/usr/bin/python3
#
# Univention Portal
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2020-2022 Univention GmbH
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
#

import logging
import sys


class ShortNameFormatter(logging.Formatter):
	shorten = "univention.portal"

	def format(self, record):
		record.short_name = record.name
		if record.short_name.startswith("%s." % self.shorten):
			record.short_name = record.short_name[len(self.shorten) + 1:]
		return super(ShortNameFormatter, self).format(record)


def setup_logger(logfile="/var/log/univention/portal.log", stream=True):
	logger = logging.getLogger("univention.portal")
	logger.setLevel(logging.DEBUG)
	if logfile is not None:
		log_format = "%(process)6d %(short_name)-12s %(asctime)s [%(levelname)8s]: %(message)s"
		log_format_time = "%y-%m-%d %H:%M:%S"
		formatter = ShortNameFormatter(log_format, log_format_time)
		handler = logging.FileHandler(logfile)
		handler.setFormatter(formatter)
		logger.addHandler(handler)
	if stream:
		handler = logging.StreamHandler(sys.stdout)
		logger.addHandler(handler)


def get_logger(name):
	logger = logging.getLogger("univention.portal")
	logger = logger.getChild(name)
	return logger
