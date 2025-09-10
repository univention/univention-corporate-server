#!/usr/bin/python3
#
# Send a token to a user by email.
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

ucr = ConfigRegistry()
ucr.load()


class SendWithExternal(UniventionSelfServiceTokenEmitter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cmd = self.ucr.get("umc/self-service/passwordreset/external/command", "").split()
        if not self.cmd:
            raise ValueError("SendWithExternal: UCR umc/self-service/passwordreset/external/command must contain the path to the program to execute.")

    @staticmethod
    def send_method():
        return ucr.get("umc/self-service/passwordreset/external/method")

    @staticmethod
    def send_method_label():
        return ucr.get("umc/self-service/passwordreset/external/method_label", _("External"))

    @staticmethod
    def is_enabled():
        return ucr.is_true("umc/self-service/passwordreset/external/enabled")

    @property
    def udm_property(self):
        ucr.load()
        return ucr.get("umc/self-service/passwordreset/external/udm_property")

    @property
    def token_length(self):
        ucr.load()
        length = ucr.get("umc/self-service/passwordreset/external/token_length", 64)
        try:
            length = int(length)
        except ValueError:
            length = 64
        return length

    def send(self):
        env = os.environ.copy()
        env["selfservice_username"] = self.data["username"]
        env["selfservice_address"] = self.data["address"]
        env["selfservice_token"] = self.data["token"]

        #
        #
        # ATTENTION                                                                 #
        # The environment is inherited by all programs that are started by your     #
        # program. Your program should remove the token from its environment,       #
        # before starting any other program.                                        #
        #
        #

        self.log("Starting external program %s...", self.cmd)
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
