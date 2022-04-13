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
support for DNSBLs <http://www.postfix.org/postconf.5.html#reject_rbl_client>`_.

DNSBLs from various projects and companies are available on the internet. Please
refer to the corresponding websites for further information on conditions and
prices.

The |UCSUCRV| :envvar:`mail/postfix/smtpd/restrictions/recipient` with a
key-value pair :samp:`{SEQUENCE}={RULE}` must be set to be able to use DNSBLs
with Postfix:
:samp:`mail/postfix/smtpd/restrictions/recipient/{SEQUENCE}={RULE}`.

It can be used to configure recipient restrictions via the Postfix option
``smtpd_recipient_restrictions`` (see
http://www.postfix.org/postconf.5.html#smtpd_recipient_restrictions). The
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

.. spelling::

   Blackhole
