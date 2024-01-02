.. SPDX-FileCopyrightText: 2021-2024 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

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
