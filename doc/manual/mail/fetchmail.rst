.. _mail-fetchmail:

Integration of Fetchmail for retrieving mail from external mailboxes
====================================================================

Usually, the UCS mail service accepts mails for the users of the UCS domain
directly via SMTP. UCS also offers optional integration of the software
*Fetchmail* for fetching emails from external POP3 or IMAP mailboxes.

Fetchmail can be installed via the Univention App Center; simply select the
:program:`Fetchmail` application and then click on :guilabel:`Install`.

Once the installation is finished, there are additional input fields in the
:menuselection:`Advanced settings --> Remote mail retrieval (single)` and
:menuselection:`Remote mail retrieval (multi)` tab of the user administration
which can be used to configure the collection of mails from an external server.
The mails are delivered to the inboxes of the respective users. The primary
email address must be configured for that. Before using multi-drop
configurations it is recommended to read `THE USE AND ABUSE OF MULTIDROP MAILBOXES <fetchmail-multidrop_>`_
in the Fetchmail manual.

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
     - The username to be provided to the mail server for fetching mail.

   * - Password
     - The password to be used for fetching mail.

   * - Protocol
     - The mail can be fetched via the IMAP or POP3 protocols.

   * - Remote mail server
     - The name of the mail server from which the emails are to be fetched.

   * - Use SSL
     - If this option is enabled, the mail is fetched in an encrypted form (when
       this is supported by the mail server).

   * - Keep mails on remote server
     - By default the fetched mails are deleted from the server following the
       transfer. If this option is enabled, it can be suppressed.

.. list-table:: *Remote mail retrieval (multi)* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Username
     - The username to be provided to the mail server for fetching mail.

   * - Password
     - The password to be used for fetching mail.

   * - Protocol
     - The mail can be fetched via the IMAP or POP3 protocols.

   * - Remote mail server
     - The name of the mail server from which the emails are to be fetched.

   * - Local Domain Names
     - A space-separated list of local domain names. Leave it empty to use all
       local domains.

   * - Virtual *qmail* prefix
     - The string prefix assigned to this field will be removed from the address
       found in the header which is specified with the envelope header option.
       E.g. if the value is set to `example-prefix-` and Fetchmail retrieves an
       email whose header matches with an address like `example-prefix-info@remotedomain.com`
       the mail will be forwarded as `info@localdomain.com.`

   * - Envelope Header
     - The value of this field sets the header that Fetchmail expects to appear
       as a copy of the mail envelope address. It is used for mail rerouting.

   * - Use SSL
     - If this option is enabled, the mail is fetched in an encrypted form (when
       this is supported by the mail server).

   * - Keep mails on remote server
     - By default the fetched mails are deleted from the server following the
       transfer. If this option is enabled, it can be suppressed.
