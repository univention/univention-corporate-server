# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2023 Univention GmbH
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

from univention.admin.syntax import IMAP_POP3, boolean, complex, select, string, userPasswd


class FetchMailSingle(complex):
    """Syntax for single drop fetchmail configuration."""

    subsyntaxes = [
        ('Remote Server', string), ('Protocol', IMAP_POP3),
        ('Remote Username', string), ('Password', userPasswd),
        ('Use SSL', boolean), ('Keep in server', boolean),
    ]

    subsyntax_names = ('server', 'protocol', 'remote username', 'password', 'ssl', 'keep')
    all_required = True
    subsyntax_key_value = True

    def get_widget_options(self, udm_property):
        descr = super(FetchMailSingle, self).get_widget_options(udm_property)
        descr['rowLabelsVisibility'] = 'allRows'
        return descr


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
        ('Remote Server', string), ('Protocol', IMAP_POP3),
        ('Remote Username', string), ('Password', userPasswd),
        ('Local Domain Names', string), ('Virtual qmail Prefix', string),
        ('Envelope Header', FetchmailEnvelope), ('Use SSL', boolean), ('Keep in remote server', boolean),
    ]

    subsyntax_names = ('server', 'protocol', 'remote username', 'password', 'Local Domain Name', 'qmail prefix', 'envelopeheader', 'ssl', 'keep')
    all_required = True
    subsyntax_key_value = True

    def get_widget_options(self, udm_property):
        descr = super(FetchMailMulti, self).get_widget_options(udm_property)
        descr['rowLabelsVisibility'] = 'allRows'
        return descr
