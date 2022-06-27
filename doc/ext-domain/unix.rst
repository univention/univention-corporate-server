.. _ext-dom-unix:

***************************************************
Integration of Linux/Unix systems into a UCS domain
***************************************************

These are general instructions for the integration of Unix/Linux-based
non-UCS systems - referred to in the following simply as Unix systems -
in the trust context of the UCS domain.

The integration of Ubuntu clients is documented with example
step-by-step instructions in :ref:`ext-dom-ubuntu`.

The integration of macOS clients is documented with :ref:`example step-by-step
instructions <uv-manual:macos-domain-join>` in the UCS manual. macOS systems use
a deviating domain integration based on Samba 4.

Not all integration steps need to be performed. In this way, for
example, a Unix system can merely be integrated in the IP management and
access the NTP server without integrating the system in the UCS user
management (e.g., if it is a database server on which no user login is
performed anyway).

.. _unix-umc:

Managing the systems in the |UCSUMC|
====================================

A *Computer: Linux* object can be created in the UMC computer management. This
allows the integration of the Unix system in the DNS/DHCP and network
administration of the |UCSUMC|

If the Nagios support is enabled under *[Options]*, remote Nagios
checks can also be applied against the system.

.. _ext-dom-time:

Configuration of the name resolution
====================================

The Unix system should use a name server from the UCS domain: All UCS
Directory Nodes (i.e., |UCSPRIMARYDN|, |UCSBACKUPDN| and |UCSREPLICADN|)
operate a DNS server. One or more of these UCS system should be entered
in the :file:`/etc/resolv.conf`, e.g.:

.. code-block::

   domain example.com
   nameserver 192.0.2.08
   nameserver 192.0.2.9

.. _unix-time:

Configuration of the time server
================================

All UCS Directory Nodes (i.e., |UCSPRIMARYDN|, |UCSBACKUPDN| and
|UCSREPLICADN|) operate a NTP server.

The configuration differs depending on the NTP software used, but is set
under :file:`/etc/ntp.conf` on most Linux systems, e.g.:

.. code-block::

   server primary.example.com
   server backup.example.com

.. _unix-domain:

Access to user and group information of the UCS domain
======================================================

The *Name Service Switch* (NSS) is an interface for configuring the data sources
for users, groups and computers. NSS is present on all Linux versions and most
Unix systems.

If the Unix system used provides support for an NSS module for LDAP access - as
is the case in most Linux distributions - user and group information can be read
out of the UCS LDAP directory.

The configuration files of the NSS LDAP module differ depending on the
Linux/Unix version.

As a general rule, the following settings must be set there:

* The DN of the LDAP base of the UCS domain (saved in the |UCSUCRV|
  :envvar:`ldap/base` on UCS servers) needs to be configured on the system.

* The LDAP server, ports and authentication credentials to be used. The fully
  qualified domain names of one or more UCS Directory Nodes should be entered
  here. By default UCS LDAP servers only allow authenticated LDAP access.

* In the standard setting, only TLS-secured access is possible on UCS-LDAP
  servers. The accessing Unix system must therefore use the root certificate of
  the UCS-CA. The certificate can be found on the |UCSPRIMARYDN| in the file
  :file:`/etc/univention/ssl/ucsCA/CAcert.pem` and can be copied into any
  directory, e.g., :file:`/etc/ucs-ssl/`. The UCS root certificate must then be
  configured in the LDAP configuration files. If the Unix system uses OpenLDAP
  as the LDAP implementation, it is usually the file
  :file:`/etc/openldap/ldap.conf` or :file:`/etc/ldap/ldap.conf`. The line for
  OpenLDAP is as follows:

  .. code-block::

     TLS_CACERT /etc/ucs-ssl/CAcert.pem

If the NSS LDAP service has been set up correctly, the following two commands
should output all users and groups:

.. code-block:: console

   getent passwd
   getent group

.. _unix-kerberos:

Integrating into Kerberos
=========================

UCS employs the Kerberos implementation Heimdal. For this reason, Heimdal should
also be used to access the Kerberos realm on the Unix system. Only the Heimdal
client libraries need to be installed on the Unix system.

Kerberos requires correct time synchronization, see :ref:`ext-dom-time`.

The configuration is performed in the :file:`/etc/krb5.conf` file on most
systems. Here is an example configuration:

* :samp:`KERBEROSREALM` must be replaced by the name of
  the UCS Kerberos realm (saved in the |UCSUCRV| :envvar:`kerberos/realm`).

* :samp:`PRIMARYIP` must be replaced by the IP address of
  the |UCSPRIMARYDN|.

* :samp:`PRIMARYFQDN` must be replaced by the fully
  qualified domain name of the |UCSPRIMARYDN|.

.. code-block::

   [libdefaults]
       default_realm = KERBEROSREALM
       default_tkt_enctypes = arcfour-hmac-md5 des-cbc-md5 des3-hmac-sha1 \
          des-cbc-crc des-cbc-md4 des3-cbc-sha1 aes128-cts-hmac-sha1-96   \
          aes256-cts-hmac-sha1-96
       permitted_enctypes = des3-hmac-sha1 des-cbc-crc des-cbc-md4 \
          des-cbc-md5 des3-cbc-sha1 arcfour-hmac-md5               \
          aes128-cts-hmac-sha1-96 aes256-cts-hmac-sha1-96
       allow_weak_crypto=true
       kdc_timesync = 1
       ccache_type = 4
       forwardable = true
       proxiable = true

   [realms]
   KERBEROSREALM = {
      kdc = PRIMARYIP PRIMARYFQDN
      admin_server = PRIMARYIP PRIMARYFQDN
      kpasswd_server = PRIMARYIP PRIMARYFQDN
   }

The Heimdal PAM module then needs to be installed. In general, the installation
of the module should adapt the PAM configuration automatically.

Then Kerberos authentication during login should work via PAM and password
changes should be possible via :command:`kpasswd`.

To allow SSH logins via Kerberos, the options ``GSSAPIAuthentication`` and
``GSSAPIKeyExchange`` should be set to ``yes`` in the configuration file of the
SSH daemon (typically :file:`/etc/ssh/sshd_config`).

.. _unix-print:

Accessing a UCS print server
============================

UCS uses the *Common Unix Printing System* (CUPS)
to implement print services. The Unix system can use the UCS print
servers by installing the CUPS client programs. In addition the CUPS
server needs to be configured for the clients, typically in the
configuration file :file:`/etc/cups/client.conf`, e.g.:

.. code-block::

   ServerName printserver.example.com

