.. _mail-fetchmail:

Integration of Fetchmail for retrieving mail from external mailboxes
====================================================================

Usually, the UCS mail service accepts mails for the users of the UCS domain
directly via SMTP. UCS also offers optional integration of the software
*Fetchmail* for fetching emails from external POP3 or IMAP mailboxes.

Fetchmail can be installed via the Univention App Center; simply select the
:program:`Fetchmail` application and then click on :guilabel:`Install`.

Once the installation is finished, there are additional input fields in the
:menuselection:`Advanced settings --> Remote mail retrieval` tab of the user
administration which can be used to configure the collection of mails from an
external server. The mails are delivered to the inboxes of the respective users.
The primary email address must be configured for that.

The mail is fetched every twenty minutes once at least one email address is
configured for mail retrieval. After the initial configuration of a user
Fetchmail needs to be started in the UMC module :guilabel:`System services`. In
that module the fetching can also be disabled (alternatively by setting the
|UCSUCRV| :envvar:`fetchmail/autostart` to ``false``).

.. list-table:: *Remote mail retrieval* tab
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

   * - Encrypt connection (SSL/TLS)
     - If this option is enabled, the mail is fetched in an encrypted form (when
       this is supported by the mail server).

   * - Keep mails on the server
     - By default the fetched mails are deleted from the server following the
       transfer. If this option is enabled, it can be suppressed.
