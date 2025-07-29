#!/usr/bin/python3
#
# Send a token to a user by email.
#
# SPDX-FileCopyrightText: 2020-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import email.charset
import os.path
import smtplib
from email.mime.nonmultipart import MIMENonMultipart
from email.utils import formatdate
from urllib.parse import quote

from univention.lib.i18n import Translation
from univention.management.console.modules.passwordreset.send_plugin import UniventionSelfServiceTokenEmitter


_ = Translation('univention-self-service-passwordreset-umc').translate


class VerifyEmail(UniventionSelfServiceTokenEmitter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.server = self.ucr.get("umc/self-service/account-verification/email/server", "localhost")

    @staticmethod
    def send_method():
        return "verify_email"

    @staticmethod
    def message_application():
        return 'email_verification'

    @staticmethod
    def is_enabled():
        return True
        #  For now this sending message is always enabled (unless we have for methods for sending verification tokens)
        #  ucr = ConfigRegistry()
        #  ucr.load()
        #  return ucr.is_true("umc/self-service/account-verification/email/enabled")

    @property
    def udm_property(self):
        return "PasswordRecoveryEmailVerified"

    @property
    def token_length(self):
        length = self.ucr.get("umc/self-service/account-verification/email/token_length", 64)
        try:
            length = int(length)
        except ValueError:
            length = 64
        return length

    def send(self):
        path_ucr = self.ucr.get("umc/self-service/account-verification/email/text_file")
        if path_ucr and os.path.exists(path_ucr):
            path = path_ucr
        else:
            path = "/usr/share/univention-self-service/email_bodies/verification_email_body.txt"
        with open(path) as fp:
            txt = fp.read()

        fqdn = ".".join([self.ucr["hostname"], self.ucr["domainname"]])
        frontend_server = self.ucr.get("umc/self-service/account-verification/email/webserver_address", fqdn)
        link = f"https://{frontend_server}/univention/selfservice/#/selfservice/verifyaccount/"
        tokenlink = "https://{fqdn}/univention/selfservice/#/selfservice/verifyaccount/?token={token}&username={username}&method={method}".format(
            fqdn=frontend_server,
            username=quote(self.data["username"]),
            token=quote(self.data["token"]),
            method=self.send_method(),
        )

        txt = txt.format(username=self.data["username"], token=self.data["token"], link=link, tokenlink=tokenlink)

        msg = MIMENonMultipart('text', 'plain', charset='utf-8')
        cs = email.charset.Charset("utf-8")
        cs.body_encoding = email.charset.QP
        msg["Subject"] = self.ucr.get("umc/self-service/account-verification/email/subject", "Account verification")
        msg["Date"] = formatdate(localtime=True)
        msg["From"] = self.ucr.get("umc/self-service/account-verification/email/sender_address", f"Account Verification Service <noreply@{fqdn}>")
        msg["To"] = self.data["address"]
        msg.set_payload(txt, charset=cs)

        smtp = smtplib.SMTP(self.server)
        smtp.sendmail(msg["From"], self.data["address"], msg.as_string())
        smtp.quit()
        self.log("Sent mail with token to address {}.".format(self.data["address"]))

        return True
