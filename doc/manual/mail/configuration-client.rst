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
