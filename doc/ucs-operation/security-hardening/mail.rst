.. SPDX-FileCopyrightText: 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _security-hardening-mail:

Harden mail transport
=====================

Postfix and Dovecot handle SMTP, IMAP, and POP3 traffic.
Encryption protects mail in transit, but the remote mail system and the mail
client must also support the selected policy.

.. _security-hardening-mail-postfix:

Configure Postfix TLS
---------------------

The Postfix SMTP client uses opportunistic TLS by default through
:envvar:`mail/postfix/tls/client/level` set to ``may``.
This encrypts a connection when the remote server offers TLS, but it doesn't
require encryption.

For destinations that require encrypted transport, define a destination-
specific TLS policy.
Don't set a global mandatory policy until you have verified that every remote
mail system supports it.

Restrict protocol versions for mandatory and opportunistic TLS connections:

.. code-block:: console

   $ ucr set mail/postfix/tls/client/mandatory_protocols='>=TLSv1.2'
   $ ucr set mail/postfix/tls/client/protocols='>=TLSv1.2'

Exclude obsolete ciphers from the Postfix SMTP client:

.. code-block:: console

   $ ucr set mail/postfix/tls/client/exclude_ciphers='RC4, aNULL, MD5, DES'

Test delivery to internal and external destinations after changing these
settings.

.. _security-hardening-mail-submission:

Restrict the submission service
-------------------------------

Port 587 is intended for authenticated mail submission.
Configure the Postfix submission service to require TLS and authentication
through the ``mail/postfix/mastercf/options/submission/`` UCR variables.
The following options express the intended policy:

.. code-block:: text

   smtpd_tls_security_level=encrypt
   smtpd_sasl_auth_enable=yes
   smtpd_client_restrictions=permit_sasl_authenticated,reject
   smtpd_recipient_restrictions=reject_non_fqdn_recipient,reject_unknown_recipient_domain,permit_sasl_authenticated,reject_unauth_destination

The exact UCR variable names include the option name, for example
``mail/postfix/mastercf/options/submission/smtpd_tls_security_level``.
Check the generated Postfix configuration after setting them.
Without explicit submission restrictions, the service can inherit behavior
that is intended for port 25 rather than authenticated submission.
Check the generated configuration on the installed UCS release because the
package defaults can provide some submission restrictions already.

.. _security-hardening-mail-dovecot:

Configure Dovecot TLS
---------------------

Set the minimum protocol version for IMAP and POP3 TLS connections:

.. code-block:: console

   $ ucr set mail/dovecot/ssl/min_protocol=TLSv1.2
   $ ucr set mail/dovecot/ssl/prefer_server_ciphers=yes

This excludes clients that support only TLS 1.0 or TLS 1.1.
Test every supported mail client and mobile application before applying the
change.

Regenerate the Dovecot SSL parameters regularly through
:envvar:`mail/dovecot/ssl/parameters_regenerate`.
The default interval is 168 hours.

.. _security-hardening-mail-disclosure:

Reduce mail service disclosure
------------------------------

Review SMTP banners and service responses so that they don't disclose the
fully qualified hostname or unnecessary product details.
If you customize :envvar:`mail/postfix/smtpd/banner`, retain only the identity
information that your mail policy requires.
For example, ``$myhostname ESMTP`` omits the Postfix product name while still
providing a usable SMTP greeting.
