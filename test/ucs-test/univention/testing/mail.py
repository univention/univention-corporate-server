# -*- coding: utf-8 -*-
#
# UCS test
#
# Copyright 2013-2019 Univention GmbH
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

from __future__ import print_function
import time
import os
import pwd
import subprocess


class MailSinkGuard(object):
	"""
	This class is a simple context manager that stops all attached mail sinks
	if the context is left.

	with MaiLSinkGuard() as msg:
		sink = MailSink(......)
		msg.add(sink)
		....use sink....
	"""
	def __init__(self):
		self.mail_sinks = set()  # type: Set[MailSink]

	def add(self, sink):   # type: (MailSink) -> None
		self.mail_sinks.add(sink)

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, etraceback):
		for mail_sink in self.mail_sinks:
			mail_sink.stop()


class MailSink(object):
	"""
	This class starts an SMTP sink on the specified address/port.
	Each incoming mail will be written to a single file if target_dir is used.
	To write all incoming mails into one file, use filename.

	>>> ms = MailSink('127.0.0.1', 12345, target_dir='/tmp/')
	>>> ms.start()
	<do some stuff>
	>>> ms.stop()

	>>> ms = MailSink('127.0.0.1', 12345, filename='/tmp/sinkfile.eml')
	>>> ms.start()
	<do some stuff>
	>>> ms.stop()

	>>> with MailSink('127.0.0.1', 12345, filename='/tmp/sinkfile.eml') as ms:
	>>> 	<do some stuff>
	"""
	def __init__(self, address, port, filename=None, target_dir=None, fqdn=None):
		self.address = address
		self.port = port
		self.filename = filename
		self.target_dir = target_dir
		self.process = None
		self.fqdn = fqdn

	def __enter__(self):
		self.start()
		return self

	def __exit__(self, exc_type, exc_value, etraceback):
		self.stop()

	def start(self):
		print('*** Starting SMTPSink at %s:%s' % (self.address, self.port))
		cmd = ['/usr/sbin/smtp-sink']  # use postfix' smtp-sink tool
		if self.filename is not None:
			cmd.extend(['-D', self.filename])
		elif self.target_dir is not None:
			cmd.extend(['-d', os.path.join(self.target_dir, '%Y%m%d-%H%M%S.')])
		else:
			cmd.extend(['-d', os.path.join('./%Y%m%d-%H%M%S.')])
		if self.fqdn:
			cmd.extend(['-h', self.fqdn])
		if os.geteuid() == 0:
			cmd.extend(['-u', pwd.getpwuid(os.getuid()).pw_name])
		cmd.append('{}:{}'.format(self.address, self.port))
		cmd.append('10')
		print('*** {!r}'.format(cmd))
		self.process = subprocess.Popen(cmd)

	def stop(self):
		if self.process is not None:
			self.process.terminate()
			time.sleep(1)
			self.process.kill()
			print('*** SMTPSink at %s:%s stopped' % (self.address, self.port))
			self.process = None


if __name__ == '__main__':
	# ms = MailSink('127.0.0.1', 12345, target_dir='/tmp/')
	ms = MailSink('127.0.0.1', 12345, filename='/tmp/sink.eml')
	print('Starting sink')
	ms.start()
	print('Waiting')
	time.sleep(25)
	print('Stopping sink')
	ms.stop()
	print('Waiting')
	time.sleep(5)
