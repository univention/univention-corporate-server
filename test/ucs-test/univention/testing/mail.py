# -*- coding: utf-8 -*-
#
# UCS test
#
# Copyright 2013-2019 Univention GmbH
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
import time
import threading
import asyncore
from smtpd import DEBUGSTREAM, DebuggingServer, SMTPChannel, __version__


class UCSTest_Mail_Exception(Exception):

    """ Generic ucstest mail error """


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

    addr2fqdn = {}

    class ESMTPChannel(SMTPChannel):
        def __init__(self, server, conn, addr, fqdn=None):
            MailSink.addr2fqdn[addr] = fqdn
            SMTPChannel.__init__(self, server, conn, addr)

        def push(self, msg):
            # catch "220 $FQDN $VERSION" from SMTPChannel.__init__()
            try:
                new_fqdn = MailSink.addr2fqdn[self._SMTPChannel__addr]
                if msg == '220 %s %s' % (self._SMTPChannel__fqdn, __version__):
                    msg = '220 %s %s' % (new_fqdn, __version__)
            except KeyError:
                pass
            try:
                SMTPChannel.push(self, msg)
            except IndexError:
                # push sometimes fails with
                #
                # <type 'exceptions.IndexError'>:deque index out of range [/usr/lib/python2.7/asyncore.py|read|83]
                # [/usr/lib/python2.7/asyncore.py|handle_read_event|449]
                # [/usr/lib/python2.7/asynchat.py|handle_read|165]
                # [/usr/lib/python2.7/smtpd.py|found_terminator|163]
                # [/usr/lib/python2.7/smtpd.py|smtp_RCPT|251]
                # [/usr/lib/pymodules/python2.7/univention/testing/mail.py|push|74]
                # [/usr/lib/python2.7/smtpd.py|push|136]
                # [/usr/lib/python2.7/asynchat.py|push|193]
                # [/usr/lib/python2.7/asynchat.py|initiate_send|251]
                #
                # https://github.com/myano/jenni/issues/159 says "This is an inherent issue with multi-threading",
                # so just for testing, wait a moment and try angain
                time.sleep(3)
                SMTPChannel.push(self, msg)

        def smtp_EHLO(self, arg):
            # same code as smtp_HELO(), except /HELO/EHLO/ and changed FQDN
            if not arg:
                self.push('501 Syntax: EHLO hostname')
                return
            if self._SMTPChannel__greeting:
                self.push('503 Duplicate HELO/EHLO')
            else:
                self._SMTPChannel__greeting = arg
                try:
                    fqdn = MailSink.addr2fqdn[self._SMTPChannel__addr]
                except KeyError:
                    fqdn = self._SMTPChannel__fqdn
                self.push('250 %s' % fqdn)

        def smtp_HELO(self, arg):
            # change FQDN
            try:
                self._SMTPChannel__fqdn = MailSink.addr2fqdn[self._SMTPChannel__addr]
            except KeyError:
                pass
            SMTPChannel.smtp_HELO(self, arg)

    class EmlServer(DebuggingServer):
        target_dir = '.'
        number = 0
        filename = None

        def __init__(self, localaddr, remoteaddr, fqdn=None):
            DebuggingServer.__init__(self, localaddr, remoteaddr)
            self.fqdn = fqdn

        def handle_accept(self):
            pair = self.accept()
            if pair is not None:
                conn, addr = pair
                print >> DEBUGSTREAM, 'Incoming connection from %s' % repr(addr)
                channel = MailSink.ESMTPChannel(self, conn, addr, self.fqdn)

        def process_message(self, peer, mailfrom, rcpttos, data):
            DebuggingServer.process_message(self, peer, mailfrom, rcpttos, data)
            filename = self.filename or os.path.join(
                self.target_dir, '%s-%d.eml' % (time.strftime('%Y%m%d-%H%M%S'), self.number))
            with open(filename, 'a') as f:
                f.write('X-SmtpSink-Peer: %s\n' % repr(peer))
                f.write('X-SmtpSink-From: %s\n' % repr(mailfrom))
                f.write('X-SmptSink-To: %s\n' % repr(rcpttos))
                f.write(data)
                if self.filename:
                    f.write('\n\n')
            self.number += 1

    def __init__(self, address, port, filename=None, target_dir=None, fqdn=None):
        self.address = address
        self.port = port
        self.filename = filename
        if not target_dir:
            self.target_dir = '.'
        else:
            self.target_dir = target_dir
        self.thread = None
        self.do_run = False
        self.fqdn = fqdn

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_value, etraceback):
        self.stop()

    def start(self):
        self.do_run = True
        self.thread = threading.Thread(target=self.runner)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.do_run = False
        self.thread.join()

    def runner(self):
        print '*** Starting SMTPSink at %s:%s' % (self.address, self.port)
        sink = self.EmlServer((self.address, self.port), None, self.fqdn)
        sink.target_dir = self.target_dir
        sink.filename = self.filename
        while self.do_run:
            asyncore.loop(count=1, timeout=1)
        sink.close()
        print '*** SMTPSink at %s:%s stopped' % (self.address, self.port)


if __name__ == '__main__':
    import time
    # ms = MailSink('127.0.0.1', 12345, target_dir='/tmp/')
    ms = MailSink('127.0.0.1', 12345, filename='/tmp/sink.eml')
    print 'Starting sink'
    ms.start()
    print 'Waiting'
    time.sleep(45)
    print 'Stopping sink'
    ms.stop()
    print 'Waiting'
    time.sleep(10)
