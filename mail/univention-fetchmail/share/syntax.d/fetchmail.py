# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2023-2024 Univention GmbH
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

import univention.admin.localization
from univention.admin.syntax import IMAP_POP3, boolean, complex, select, string, userPasswd


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
