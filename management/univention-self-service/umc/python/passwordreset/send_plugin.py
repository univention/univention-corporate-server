#
# Univention Password Self Service frontend base class
#
# SPDX-FileCopyrightText: 2015-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from univention.config_registry import ConfigRegistry
from univention.lib.i18n import Translation


_ = Translation('univention-self-service-passwordreset-umc').translate


class UniventionSelfServiceTokenEmitter:
    """base class"""

    def __init__(self, log):
        self.ucr = ConfigRegistry()
        self.ucr.load()
        self.data = {}
        self.log = log

    @staticmethod
    def send_method():
        return "????"

    @staticmethod
    def send_method_label():
        return _("????")

    @staticmethod
    def message_application():
        return 'password_reset'

    @staticmethod
    def is_enabled():
        ucr = ConfigRegistry()
        ucr.load()
        return ucr.is_true("umc/self-service/passwordreset/????/enabled")

    @property
    def udm_property(self):
        return "self-service-????"

    def password_reset_verified_recovery_email(self):
        return self.message_application() == "password_reset" and self.udm_property == "PasswordRecoveryEmail"

    @property
    def token_length(self):
        return 1024

    def set_data(self, data):
        self.data.update(data)

    def send(self):
        raise NotImplementedError("Implement me")
