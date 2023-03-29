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

.. _mail-clients:

Configuration of mail clients for the mail server
=================================================

The use of IMAP is recommended for using a mail client with the UCS mail
server. STARTTLS is used to switch to a TLS-secured connection after an
initial negotiation phase when using SMTP (for sending mail) and IMAP
(for receiving/synchronizing mail). *Password (plain
text)* should be used in combination with
*STARTTLS* as the authentication method. The
method may have a different name depending on the mail client. The
following screenshot shows the setup of Mozilla Thunderbird as an
example.

.. _mail-clients-thunderbird:

.. figure:: /images/thunderbird.*
   :alt: Setup of Mozilla Thunderbird

   Setup of Mozilla Thunderbird
