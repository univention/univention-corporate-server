.. SPDX-FileCopyrightText: 2021-2024 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _mail-fetchmail:

Integration of Fetchmail for retrieving mail from external mailboxes
====================================================================

Usually, the UCS mail service accepts mails for the users of the UCS domain
directly via SMTP. UCS also offers optional integration of the software
*Fetchmail* for fetching emails from external POP3 or IMAP mailboxes.

Fetchmail can be installed via the Univention App Center; simply select the
:program:`Fetchmail` application and then click on :guilabel:`Install`.

After the installation, the :menuselection:`Advanced settings --> Remote mail retrieval (single)`
and :menuselection:`Remote mail retrieval (multi)` tabs in the user administration provide
additional input fields. Use them to configure the retrieval of emails from a remote mail server.

Fetchmail delivers emails to the inboxes of the corresponding users. The user account must have
the primary email address configured for this. Before using multi-drop configurations, read
`THE USE AND ABUSE OF MULTIDROP MAILBOXES <fetchmail-multidrop_>`_ in the Fetchmail manual.

The mail is fetched every twenty minutes once at least one email address is
configured for mail retrieval. After the initial configuration of a user
Fetchmail needs to be started in the UMC module :guilabel:`System services`. In
that module the fetching can also be disabled (alternatively by setting the
|UCSUCRV| :envvar:`fetchmail/autostart` to ``false``).

.. list-table:: *Remote mail retrieval (single)* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Username
     - The username to connect to the email server for fetching emails.

   * - Password
     - The password for the user to connect to the email server for fetching mail.

   * - Protocol
     - The protocol that Fetchmail uses for fetching emails. Choose either ``IMAP`` or ``POP3``.

   * - Remote mail server
     - The hostname of the email server that Fetchmail uses to fetch emails.

   * - Use SSL
     - This option enables encrypted mail fetching. For it to work, this feature has to be
       supported by the mail server.

   * - Keep mail on remote server
     - By default, Fetchmail deletes fetched email from the remote server after
       the transfer. To keep the emails on the remote server, enable this option.

.. list-table:: *Remote mail retrieval (multi)* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Username
     - The username to connect to the email server for fetching emails.

   * - Password
     - The password for the user to connect to the email server for fetching mail.

   * - Protocol
     - The protocol that Fetchmail uses for fetching emails. Choose either ``IMAP`` or ``POP3``.

   * - Remote mail server
     - The hostname of the email server that Fetchmail uses to fetch emails.

   * - Local Domain Names
     - A space-separated list of local domain names. Leave it empty to use all
       local domains.

   * - Virtual *qmail* prefix
     - Fetchmail removes the defined string prefix from the email address found in the header
       specified with the envelope header option. For example, if the value is
       ``example-prefix-`` and Fetchmail retrieves an email whose header matches an address
       such as ``example-prefix-info@remotedomain.com``, Fetchmail forwards the email as
       ``info@localdomain.com``.

   * - Envelope Header
     - The value of this field sets the header that Fetchmail expects to appear
       as a copy of the mail envelope address. Fetchmail uses it for mail rerouting.

   * - Use SSL
     - This option enables encrypted mail fetching. For it to work, this feature has to be
       supported by the mail server.

   * - Keep mail on remote server
     - By default, Fetchmail deletes fetched email from the remote server after
       the transfer. To keep the emails on the remote server, enable this option.
