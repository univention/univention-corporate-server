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
from pyparsing import Word, alphas, Suppress, Combine, nums, string, Regex
from datetime import datetime
from admindiary_event_model import Event

class FileStorage(object):
	""" dummy example """
	def __init__(self, filename):
		self.filename = filename

	def __enter__(self):
		self.out = open(self.filename, "a")
		return self

	def __exit__(self, *args):
		self.out.close()

	def append(self, event):
		self.out.write(str(event) + "\n")
		# self.out.flush()

	def search(self, event):
		raise NotImplementedError

	def read(self, event):
		raise NotImplementedError

	def annotate(self, event):
		raise NotImplementedError


class SQLStorage(object):
	""" TODO """
	def __init__(self, filename):
		raise NotImplementedError

	def __enter__(self):
		return NotImplemented

	def __exit__(self, *args):
		raise NotImplementedError

	def append(self, event):
		raise NotImplementedError

	def search(self, event):
		raise NotImplementedError

	def read(self, event):
		raise NotImplementedError

	def annotate(self, event):
		raise NotImplementedError


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
		payload.setParseAction(lambda t: "".join(t)) ## json parsing happens in Event class

		self._pattern = timestamp("source_datetime") + hostname("source_hostname") + syslogtag + payload("serialized_event_dict")

	def deserialize(self, line):
		parsed = self._pattern.parseString(line)
		parsed_dict = parsed.asDict()
		# merge the nested dictionaries to return a simple structure
		rsyslog_event_dict = parsed_dict["serialized_event_dict"]
		rsyslog_event_dict["source_timestamp"] = parsed_dict["source_datetime"].strftime("%Y-%m-%d %H:%M:%S")
		rsyslog_event_dict["source_hostname"] = parsed_dict["source_hostname"]
		# and convert to Admin Diary object model
		return Event(rsyslog_event_dict)


def stdin_to_storage():
	rsyslog_transport = RsyslogTransport("ADMINDIARY:")

	with FileStorage("/tmp/1.log") as storage:
		while True:
			line = sys.stdin.readline()
			if not line:
				break
			event = rsyslog_transport.deserialize(line)
			storage.append(event)


if __name__ == "__main__":
	stdin_to_storage()
