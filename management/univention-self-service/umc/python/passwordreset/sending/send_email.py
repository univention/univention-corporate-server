#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Send a token to a user by email.
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2015-2023 Univention GmbH
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
from email.utils import formatdate

from six.moves.urllib_parse import quote

from univention.config_registry import ConfigRegistry
from univention.lib.i18n import Translation
from univention.management.console.modules.passwordreset.send_plugin import UniventionSelfServiceTokenEmitter


_ = Translation('univention-self-service-passwordreset-umc').translate


class SendEmail(UniventionSelfServiceTokenEmitter):

    def __init__(self, *args, **kwargs):
        super(SendEmail, self).__init__(*args, **kwargs)
        self.server = self.ucr.get("umc/self-service/passwordreset/email/server", "localhost")
        self.port = self.ucr.get_int("umc/self-service/passwordreset/email/server/port", 0)
        self.user = self.ucr.get("umc/self-service/passwordreset/email/server/user")
        self.ehlo = self.ucr.get("umc/self-service/passwordreset/email/server/ehlo")
        self.starttls = self.ucr.is_true("umc/self-service/passwordreset/email/server/starttls")

        if self.user:
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
        self.log("Sent mail with token to address {}.".format(self.data["address"]))

        return True
