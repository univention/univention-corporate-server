.. _mail-general:

*************
Mail services
*************

|UCSUCS| provides mail services that users can access via standard mail clients
such as Thunderbird.

Postfix is used for sending and receiving mails. In the basic installation, a
configuration equipped for local mail delivery is set up on every UCS system. In
this configuration, Postfix only accepts mails from the local server and they
can also only be delivered to local system users.

The installation of the mail server component implements a complete mail
transport via SMTP (see :ref:`mail-installation`). Postfix is reconfigured
during the installation of the component so that a validity test in the form of
a search in the LDAP directory is performed for incoming emails. That means
that emails are only accepted for email addresses defined in the LDAP
directory or via an alias.

The IMAP service Dovecot is also installed on the system along with the mail
server component. It provides email accounts for the domain users and offers
corresponding interfaces for access via email clients. Dovecot is
preconfigured for the fetching of emails via ``IMAP`` and ``POP3``. Access via
POP3 can be deactivated by setting the |UCSUCRV| :envvar:`mail/dovecot/pop3` to
``no``. The same applies to IMAP and the |UCSUCRV| :envvar:`mail/dovecot/imap`.
The further configuration of the mail server is performed via |UCSUCR|, as well,
see :ref:`mail-serverconfig-general`.

The management of the user data of the mail server (e.g., email addresses or
mailing list) is performed via UMC modules and is documented in
:ref:`mail-management-general`. User data are stored in LDAP. The authentication
is performed using a user's primary email address, i.e., it must be entered as
the username in mail clients. As soon as a primary email address is assigned
to a user in the LDAP directory, a listener module creates an IMAP mailbox on
the mail home server. By specifying the mail home server, user email accounts
can be distributed over several mail servers, as well, see
:ref:`mail-homeserver`.

Optionally, emails received via Postfix can be checked for spam content and
viruses before further processing by Dovecot. Spam emails are detected by the
classification software SpamAssassin (:ref:`mail-spam`); ClamAV is used for the
detection of viruses and other malware (:ref:`mail-virus`).

By default emails to external domains are delivered directly to the responsible
SMTP server of that domain. Its location is performed via the resolution of the
MX record in the DNS. Mail sending can also be taken over by the relay host,
e.g., on the internet provider (see :ref:`mail-serverconfig-relay`).

The UCS mail system does not offer any groupware functionality such as shared
calendars or invitations to appointments. However, there are groupware systems
based on UCS which integrate in the UCS management system such as Kopano and
Open-Xchange. Further information can be found in the :ref:`software-appcenter`.

.. toctree::
   :caption: Chapter contents:

   install
   management
   spam
   virus
   dnsbl
   fetchmail
   configuration-server
   configuration-client
   ox-connector
