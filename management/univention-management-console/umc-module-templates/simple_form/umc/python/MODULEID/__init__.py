#!/usr/bin/python3
#
# Univention Management Console
#  MODULEDESC
#
# SPDX-FileCopyrightText: 2012-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import email.charset
import smtplib
from email.mime.nonmultipart import MIMENonMultipart

from univention.lib.i18n import Translation
from univention.management.console.base import Base
from univention.management.console.log import MODULE
# from univention.management.console.config import ucr
from univention.management.console.modules.decorators import sanitize, simple_response
from univention.management.console.modules.sanitizers import StringSanitizer


_ = Translation('PACKAGENAME').translate


class Instance(Base):

    def init(self):
        # this initialization method is called when the
        # module process is started and the configuration from the
        # UMC server is completed
        super().init()

    def configuration(self, request):
        """Returns a directionary of initial values for the form."""
        self.finished(request.id, {
            'sender': request.username + '@example.com',
            'subject': 'Test mail from PACKAGENAME',
            'recipient': 'test@example.com',
        })

    @sanitize(
        sender=StringSanitizer(required=True),
        recipient=StringSanitizer(required=True),
        subject=StringSanitizer(required=True),
        message=StringSanitizer(required=True),
    )
    @simple_response
    def send(self, sender, recipient, subject, message):
        def _send_thread(self, request):
            MODULE.info('sending mail: thread running')

            msg = MIMENonMultipart('text', 'plain', charset='utf-8')
            cs = email.charset.Charset("utf-8")
            cs.body_encoding = email.charset.QP
            msg["Subject"] = subject
            msg["From"] = sender
            msg["To"] = recipient
            msg.set_payload(message, charset=cs)

            server = smtplib.SMTP('localhost')
            server.set_debuglevel(0)
            server.sendmail(sender, recipient, msg.as_string())
            server.quit()
            return True

        MODULE.info('sending mail: starting thread')
        return _send_thread
