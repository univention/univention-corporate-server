#!/usr/bin/python3
#
# Send a token to a user using a text message service.
#
# SPDX-FileCopyrightText: 2015-2025 Univention GmbH
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

import os
import subprocess

from univention.config_registry import ConfigRegistry
from univention.lib.i18n import Translation
from univention.management.console.modules.passwordreset.send_plugin import UniventionSelfServiceTokenEmitter


_ = Translation('univention-self-service-passwordreset-umc').translate


class SendSMS(UniventionSelfServiceTokenEmitter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.cmd = self.ucr.get("umc/self-service/passwordreset/sms/command", "").split()
        if not self.cmd:
            raise ValueError("SendSMS: UCR umc/self-service/passwordreset/sms/command must contain the path to the program to execute.")

        self.country_code = self.ucr.get("umc/self-service/passwordreset/sms/country_code")
        if not self.country_code.isdigit():
            raise ValueError("SendSMS: UCR umc/self-service/passwordreset/sms/country_code must contain a number.")
        self.read_sms_secret()

    def read_sms_secret(self):
        self.password_file = self.ucr.get("umc/self-service/passwordreset/sms/password_file")
        if self.password_file is None:
            self.log("SendSMS: No sms secret file set")
            self.sms_username = ""
            self.sms_password = ""
            return

        try:
            with open(self.password_file) as pw_file:
                self.sms_username, self.sms_password = pw_file.readline().strip().split(":")
        except ValueError as ve:
            self.log("SendSMS: Format of sms secrets file ({}) is 'username:password'. Error: {}").format(self.password_file, ve)
            self.log("SendSMS: Format error in sms secrets file (%s): %s", self.password_file, ve)
            raise
        except OSError as e:
            self.log("SendSMS: Error reading sms secrets file (%s): %s", self.password_file, e)
            raise

    @staticmethod
    def send_method():
        return "mobile"

    @staticmethod
    def send_method_label():
        return _("Mobile number")

    @staticmethod
    def is_enabled():
        ucr = ConfigRegistry()
        ucr.load()
        return ucr.is_true("umc/self-service/passwordreset/sms/enabled")

    @property
    def udm_property(self):
        return "PasswordRecoveryMobile"

    @property
    def token_length(self):
        length = self.ucr.get("umc/self-service/passwordreset/sms/token_length", 12)
        try:
            length = int(length)
        except ValueError:
            length = 12
        return length

    def send(self):
        env = os.environ.copy()
        env["selfservice_username"] = self.data["username"]
        env["selfservice_address"] = self.data["address"]
        env["selfservice_token"] = self.data["token"]
        env["sms_country_code"] = self.country_code
        env["sms_username"] = self.sms_username
        env["sms_password"] = self.sms_password

        #
        #
        # ATTENTION                                                                 #
        # The environment is inherited by all programs that are started by your     #
        # program. Your program should remove the token from its environment,       #
        # before starting any other program.                                        #
        #
        #

        print(f"Starting external program {self.cmd}...")
        cmd_proc = subprocess.Popen(self.cmd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cmd_out, cmd_err = cmd_proc.communicate()
        cmd_out, cmd_err = cmd_out.decode('UTF-8', 'replace'), cmd_err.decode('UTF-8', 'replace')
        cmd_exit = cmd_proc.wait()

        if cmd_out:
            self.log("STDOUT of %s: %s", self.cmd, cmd_out)
        if cmd_err:
            self.log("STDERR of %s: %s", self.cmd, cmd_err)

        if cmd_exit == 0:
            return True
        else:
            raise Exception("Error sending token.")
