#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2019 Univention GmbH
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
# <http://www.gnu.org/licenses/>.

"""
 * Backend library classes and methods
 * Wenn called as __main__ it acts as rsyslog plugin
"""

import sys
from datetime import datetime

from pyparsing import Word, alphas, Suppress, Combine, nums, string, Regex

from univention.admindiary import DiaryEntry
from univention.admindiary.backend import add


class RsyslogTransport(object):
	def __init__(self, syslogtag):
		ints = Word(nums)
		# timestamp
		month = Word(string.ascii_uppercase, string.ascii_lowercase, exact=3)
		day   = ints
		hour  = Combine(ints + ":" + ints + ":" + ints)

		timestamp = month + day + hour
		# Convert timestamp to datetime
		year = str(datetime.now().year)
		timestamp.setParseAction(lambda t: datetime.strptime(year + ' ' + ' '.join(t), '%Y %b %d %H:%M:%S'))

		# hostname
		hostname = Word(alphas + nums + "_-.")

		# syslogtag
		syslogtag = Suppress(syslogtag)

		# message
		payload = Regex(".*")
		payload.setParseAction(lambda t: "".join(t))  # json parsing happens in Event class

		self._pattern = timestamp("source_datetime") + hostname("source_hostname") + syslogtag + payload("serialized_event_dict")

	def deserialize(self, line):
		parsed = self._pattern.parseString(line)
		parsed_dict = parsed.asDict()
		# merge the nested dictionaries to return a simple structure
		rsyslog_event_dict = parsed_dict["serialized_event_dict"]
		# and convert to Admin Diary object model
		entry = DiaryEntry.from_json(rsyslog_event_dict)
		return entry


def stdin_to_storage():
	rsyslog_transport = RsyslogTransport("ADMINDIARY:")

	while True:
		line = sys.stdin.readline()
		if not line:
			break
		entry = rsyslog_transport.deserialize(line)
		add(entry)


if __name__ == "__main__":
	stdin_to_storage()
