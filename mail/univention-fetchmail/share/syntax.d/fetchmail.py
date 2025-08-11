# SPDX-FileCopyrightText: 2023-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import univention.admin.localization
from univention.admin.syntax import IMAP_POP3, boolean, complex, select, string, userPasswd  # noqa: A004


_ = univention.admin.localization.translation("univention.admin.fetchmail").translate


class FetchMailSingle(complex):
    """Syntax for single drop fetchmail configuration."""

    subsyntaxes = [
        (_('Remote Server'), string), (_('Protocol'), IMAP_POP3),
        (_('Remote Username'), string), (_('Password'), userPasswd),
        (_('Use SSL'), boolean), (_('Keep on remote server'), boolean),
    ]

    subsyntax_names = ('server', 'protocol', 'remote username', 'password', 'ssl', 'keep')
    all_required = True

    def get_widget_options(self, udm_property):
        descr = complex.get_widget_options(self, udm_property)
        descr['rowLabelsVisibility'] = 'allRows'
        return descr

    @classmethod
    def parse(cls, texts, minn=None):
        if texts and not any(texts):
            return None
        return super(cls, cls).parse(texts, minn)


class FetchmailEnvelope(select):
    """Syntax for fetchmail envelope options."""

    name = 'FetchmailEnvelope'
    choices = [
        ('Envelope-To', 'Envelope-To'),
        ('X-Envelope-To', 'X-Envelope-To'),
        ('X-Original-To', 'X-Original-To'),
        ('X-RCPT-To', 'X-RCPT-To'),
        ('Delivered-To', 'Delivered-To'),
    ]


class FetchMailMulti(complex):
    """Syntax for multi drop fetchmail configuration."""

    subsyntaxes = [
        (_('Remote Server'), string), (_('Protocol'), IMAP_POP3),
        (_('Remote Username'), string), (_('Password'), userPasswd),
        (_('Local Domain Names'), string), (_('Virtual Qmail Prefix'), string),
        (_('Envelope Header'), FetchmailEnvelope), (_('Use SSL'), boolean), (_('Keep on remote server'), boolean),
    ]

    subsyntax_names = ('server', 'protocol', 'remote username', 'password', 'Local Domain Name', 'qmail prefix', 'envelopeheader', 'ssl', 'keep')
    all_required = True

    def get_widget_options(self, udm_property):
        descr = complex.get_widget_options(self, udm_property)
        descr['rowLabelsVisibility'] = 'allRows'
        return descr

    @classmethod
    def parse(cls, texts, minn=None):
        if texts and not any(texts):
            return None
        return super(cls, cls).parse(texts, minn)
