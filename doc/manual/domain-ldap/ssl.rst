.. _domain-ssl:

SSL certificate management
==========================

In UCS, sensitive data are always sent across the network encrypted, e.g., via
the use of SSH for the login to systems or via the use of protocols based on
SSL/TLS. (*Transport Layer Security (TLS)* is the current protocol name, the
name of the previous protocol *Secure Socket Layer (SSL)*, however, is still
more common and is also used in this documentation).

For example, SSL/TLS is employed in the listener/notifier domain
replication or for HTTPS access to |UCSWEB|\ s.

Both communication partners must be able to verify the authenticity of the key
used for encrypted communication between two computers. To this end, each
computer also features a so-called *host certificate*, which is issued and
signed by a certification authority (CA).

UCS provides its own CA, which is automatically set up during installation of
the |UCSPRIMARYDN| and from which every UCS system automatically procures a
certificate for itself and the CA's public certificate when joining the domain.
This CA appears as the root CA, signs its own certificate and can sign
certificates for other certification authorities.

The properties of the CA are generated automatically during the installation
based on system settings such as the locale. These settings can be subsequently
adapted on the |UCSPRIMARYDN| in the UMC module :guilabel:`Certificate
settings`.

.. caution::

   If the UCS domain contains more than one system, all other host certificates
   need to be reissued after changing the root certificate! The procedure
   required for this is documented in :uv:kb:`Renewing the SSL certificates <37>`.

The UCS-CA is always found on the |UCSPRIMARYDN|. A copy of the CA is stored on
every |UCSBACKUPDN|, which is synchronized with the CA on the |UCSPRIMARYDN| by
a Cron job every 20 minutes.

.. caution::

   The CA is synchronized from the |UCSPRIMARYDN| to the |UCSBACKUPDN| and not
   vice-versa. For this reason, only the CA on the |UCSPRIMARYDN| should be
   used.

If a |UCSBACKUPDN| is promoted to the |UCSPRIMARYDN| (see
:ref:`domain-backup2master`), the CA on the new |UCSPRIMARYDN| can be used
directly.

The UCS root certificate has a specified validity period - as do the
computer certificates created with it.

.. caution::

   Once this period of time elapses, services which encrypt their
   communication with SSL (e.g., LDAP or domain replication) no longer
   function.

It is thus necessary to verify the validity of the certificate regularly
and to renew the root certificate in time. A Nagios plugin is provided
for the monitoring of the validity period. In addition, a warning is
shown when opening a UMC module if the root certificate is going to
expire soon (the warning period can be specified with the |UCSUCRV|
:envvar:`ssl/validity/warning`; the standard value is 30 days).

The renewal of the root certificate and the other host certificates is
documented in :uv:kb:`Renewing the SSL certificates <37>`.

On UCS systems, a Cron job verifies the validity of the local computer
certificate and the root certificate daily and records the expiry date in the
|UCSUCR| variables :envvar:`ssl/validity/host` (host certificate) and
:envvar:`ssl/validity/root` (root certificate). The values entered there
reflect the number of days since the 1970-01-01.

In |UCSUMC|, the effective expiry date of the computer and root certificate can
be accessed via the upper right menu and the entry :menuselection:`License -->
License information`.
