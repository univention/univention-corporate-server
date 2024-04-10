#!/usr/bin/python3
#
# Send a token to a user by email.
#
# SPDX-FileCopyrightText: 2015-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

#
#
# This is meant as an example. Please feel free to copy this file and adapt #
# it to your needs.                                                         #
#
#

#
#
# If the return code is other that True or an exception is raised and not   #
# caught, it is assumed that it was not possible to send the token to the   #
# user. The token is then deleted from the database.                        #
#
#

import email.charset
import os
import os.path
import smtplib
from email.mime.nonmultipart import MIMENonMultipart
from email.utils import formatdate, make_msgid
from urllib.parse import quote

from univention.config_registry import ConfigRegistry
from univention.lib.i18n import Translation
from univention.management.console.modules.passwordreset.send_plugin import UniventionSelfServiceTokenEmitter


_ = Translation('univention-self-service-passwordreset-umc').translate


class SendEmail(UniventionSelfServiceTokenEmitter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.server = self.ucr.get("umc/self-service/passwordreset/email/server", "localhost")
        self.port = self.ucr.get_int("umc/self-service/passwordreset/email/server/port", 0)
        self.user = self.ucr.get("umc/self-service/passwordreset/email/server/user")
        self.ehlo = self.ucr.get("umc/self-service/passwordreset/email/server/ehlo")
        self.starttls = self.ucr.is_true("umc/self-service/passwordreset/email/server/starttls")

        if self.user:
            self.password = os.getenv("SMTP_SECRET")
            if not self.password:
                secret_file = os.getenv("SMTP_SECRET_FILE")
                try:
                    with open(secret_file, 'r') as fd:
                        self.password = fd.readline().strip()
                except IOError:
                    self.log("SMTP_SECRET_FILE (%s) could not be read." % secret_file)
                    raise

        if (self.user or self.starttls) and not self.ehlo:
            hostname = self.ucr.get('hostname')
            domainname = self.ucr.get('domainname')
            self.ehlo = f"{hostname}.{domainname}"

    @staticmethod
    def send_method():
        return "email"

    @staticmethod
    def send_method_label():
        return _("Email")

    @staticmethod
    def is_enabled():
        ucr = ConfigRegistry()
        ucr.load()
        return ucr.is_true("umc/self-service/passwordreset/email/enabled")

    @property
    def udm_property(self):
        return "PasswordRecoveryEmail"

    @property
    def token_length(self):
        length = self.ucr.get("umc/self-service/passwordreset/email/token_length", 64)
        try:
            length = int(length)
        except ValueError:
            length = 64
        return length

    def send(self):
        path_ucr = self.ucr.get("umc/self-service/passwordreset/email/text_file")
        if path_ucr and os.path.exists(path_ucr):
            path = path_ucr
        else:
            path = "/usr/share/univention-self-service/email_bodies/email_body.txt"
        with open(path) as fp:
            txt = fp.read()

        fqdn = ".".join([self.ucr["hostname"], self.ucr["domainname"]])
        frontend_server = self.ucr.get("umc/self-service/passwordreset/email/webserver_address", fqdn)
        links = {
            'fqdn': fqdn,
            'domainname': self.ucr["domainname"],
            'link': f"https://{frontend_server}/univention/selfservice/#/selfservice/newpassword/",
            'tokenlink': "https://{fqdn}/univention/selfservice/#/selfservice/newpassword/?token={token}&username={username}".format(fqdn=frontend_server, username=quote(self.data["username"]), token=quote(self.data["token"])),
        }

        formatter_dict = self.data['user_properties']
        formatter_dict.update(links)
        formatter_dict['token'] = self.data['token']

        txt = txt.format(**formatter_dict)

        msg = MIMENonMultipart('text', 'plain', charset='utf-8')
        cs = email.charset.Charset("utf-8")
        cs.body_encoding = email.charset.QP
        msg["Subject"] = self.ucr.get("umc/self-service/passwordreset/email/subject", "Password reset")
        msg["Date"] = formatdate(localtime=True)
        msg["From"] = self.ucr.get("umc/self-service/passwordreset/email/sender_address", f"Password Reset Service <noreply@{fqdn}>")
        msg["To"] = self.data["address"]
        msg["Message-ID"] = make_msgid()
        msg.set_payload(txt, charset=cs)

        smtp = smtplib.SMTP(self.server, self.port)
        if self.starttls:
            smtp.ehlo(self.ehlo)
            smtp.starttls()
        if self.user:
            smtp.ehlo(self.ehlo)
            smtp.login(self.user, self.password)
        smtp.sendmail(msg["From"], self.data["address"], msg.as_string())
        smtp.quit()
        self.log("Sent mail with token to address %s.", self.data["address"])

        return True
