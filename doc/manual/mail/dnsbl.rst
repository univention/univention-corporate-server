.. Like what you see? Join us!
.. https://www.univention.com/about-us/careers/vacancies/
..
.. Copyright (C) 2021-2023 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only
..
.. https://www.univention.com/
..
.. All rights reserved.
..
.. The source code of this program is made available under the terms of
.. the GNU Affero General Public License v3.0 only (AGPL-3.0-only) as
.. published by the Free Software Foundation.
..
.. Binary versions of this program provided by Univention to you as
.. well as other copyrighted, protected or trademarked materials like
.. Logos, graphics, fonts, specific documentations and configurations,
.. cryptographic keys etc. are subject to a license agreement between
.. you and Univention and not subject to the AGPL-3.0-only.
..
.. In the case you use this program under the terms of the AGPL-3.0-only,
.. the program is provided in the hope that it will be useful, but
.. WITHOUT ANY WARRANTY; without even the implied warranty of
.. MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
.. Affero General Public License for more details.
..
.. You should have received a copy of the GNU Affero General Public
.. License with the Debian GNU/Linux or Univention distribution in file
.. /usr/share/common-licenses/AGPL-3; if not, see
.. <https://www.gnu.org/licenses/agpl-3.0.txt>.

.. _mail-dnsbl:

Identification of Spam sources with DNS-based Blackhole Lists
=============================================================

Another means of combating spam is to use a *DNS-based Blackhole List* (DNSBL)
or *Real-time Blackhole List* (RBL). DNSBLs are lists of IP addresses that the
operator believes to be (potential) sources of spam. The lists are checked by
DNS. If the IP of the sending email server is known to the DNS server, the
message is rejected. The IP address is checked quickly and in a comparatively
resource-friendly manner. The check is performed *before* the message is
accepted. The extensive checking of the content with SpamAssassin and anti-virus
software is only performed once it has been received. Postfix has `integrated
support for DNSBLs <postfix-reject-rbl-client_>`_.

DNSBLs from various projects and companies are available on the internet. Please
refer to the corresponding websites for further information on conditions and
prices.

The |UCSUCRV| :envvar:`mail/postfix/smtpd/restrictions/recipient` with a
key-value pair :samp:`{SEQUENCE}={RULE}` must be set to be able to use DNSBLs
with Postfix:
:samp:`mail/postfix/smtpd/restrictions/recipient/{SEQUENCE}={RULE}`.

It can be used to configure recipient restrictions via the Postfix option
``smtpd_recipient_restrictions`` (see `Postfix setting
smtpd_recipient_restrictions <postfix-smtp-recipient-restrictions_>`_). The
sequential number is used to sort multiple rules alphanumerically, which can be
used to influences the ordering.

.. tip::

   Existing ``smtpd_recipient_restrictions``
   regulations can be listed as follows:

   .. code-block:: console

      $ ucr search --brief mail/postfix/smtpd/restrictions/recipient

In an unmodified |UCSUCS| Postfix installation, the DNSBL should be added
to the end of the ``smtpd_recipient_restrictions``
rules. For example:

.. code-block:: console

   $ ucr set mail/postfix/smtpd/restrictions/recipient/80="reject_rbl_client ix.dnsbl.manitu.net"
