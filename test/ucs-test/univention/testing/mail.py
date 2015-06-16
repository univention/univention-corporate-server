# -*- coding: utf-8 -*-
#
# UCS test
#
# Copyright 2013-2015 Univention GmbH
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

import os
import threading
import asyncore
from smtpd import SMTPServer


class UCSTest_Mail_Exception(Exception):
	""" Generic ucstest mail error """
	pass


class MailSink(object):
	"""
	This class starts an SMTP sink on the specified address/port.
	Each incoming mail will be written to a si

	>>> ms = MailSink('127.0.0.1', 12345, target_dir='/tmp/')
	>>> ms.start()
	<do some stuff>
	>>> ms.stop()

	>>> ms = MailSink('127.0.0.1', 12345, filename='/tmp/sinkfile.eml')
	>>> ms.start()
	<do some stuff>
	>>> ms.stop()
	"""
	class EmlServer(SMTPServer):
		target_dir = '.'
		number = 0
		filename = None

		def process_message(self, peer, mailfrom, rcpttos, data):
			if not self.filename:
				filename = os.path.join(self.target_dir, '%s-%d.eml' % (time.strftime('%Y%m%d-%H%M%S'), self.number))
			else:
				filename = self.filename
			with open(filename, 'a') as f:
				f.write('X-SmtpSink-Peer: %s\n' % repr(peer))
				f.write('X-SmtpSink-From: %s\n' % repr(mailfrom))
				f.write('X-SmptSink-To: %s\n' % repr(rcpttos))
				f.write(data)
				if self.filename:
					f.write('\n\n')
			self.number += 1

	def __init__(self, address, port, filename=None, target_dir=None):
		self.address = address
		self.port = port
		self.filename = filename
		if not target_dir:
			self.target_dir = '.'
		else:
			self.target_dir = target_dir
		self.thread = None
		self.do_run = False

	def start(self):
		self.do_run = True
		self.thread = threading.Thread(target=self.runner)
		self.thread.start()

	def stop(self):
		self.do_run = False
		self.thread.join()

	def runner(self):
		print '*** Starting SMTPSink at %s:%s' % (self.address, self.port)
		sink = self.EmlServer((self.address, self.port), None)
		sink.target_dir = self.target_dir
		sink.filename = self.filename
		while self.do_run:
			asyncore.loop(count=1, timeout=1)
		sink.close()
		print '*** SMTPSink at %s:%s stopped' % (self.address, self.port)

if __name__ == '__main__':
	import time
	#ms = MailSink('127.0.0.1', 12345, target_dir='/tmp/')
	ms = MailSink('127.0.0.1', 12345, filename='/tmp/sink.eml')
	print 'Starting sink'
	ms.start()
	print 'Waiting'
	time.sleep(45)
	print 'Stopping sink'
	ms.stop()
	print 'Waiting'
	time.sleep(10)
