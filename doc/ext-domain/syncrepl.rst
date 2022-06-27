.. _ext-dom-syncrepl:
.. _syncrepl-intro:

***************************************************
Connecting an external OpenLDAP server via syncrepl
***************************************************

This chapter describes the read-only integration of an external OpenLDAP server
via a :program:`syncrepl` proxy. This allows the external system to access the LDAP data of
the UCS domain without being a member of the domain itself. This guide
principally applies to any Unix system with OpenLDAP. The guide has been tested
with Debian 7 Wheezy. Syncrepl is part of OpenLDAP starting with version 2.2.

The external OpenLDAP server is described as ``extldap.univention.test`` below
and synchronizes with the |UCSPRIMARYDN|, which uses the LDAP base
``dc=univention,dc=test``.

The following steps must be run on the OpenLDAP system and the UCS system as the
``root`` user.

.. _syncrepl-account:

Creating a computer account
===========================

For ``extldap.univention.test``, a *Linux* computer object must be created in
the |UCSUMC| computer management and a DNS forward and reverse zone assigned to
the computer.

.. _syncrepl-primary:

Activation of syncrepl on the Primary Directory Node
====================================================

Now a syncrepl proxy needs to be set up on the |UCSPRIMARYDN|. The required
configuration files are downloaded from
https://updates.software-univention.de/download/syncrepl/ucs5-syncrepl-proxy-setup.tar.bz2
as a TAR archive.

The downloaded archive must firstly be extracted on the |UCSPRIMARYDN|:

.. code-block:: console

   $ tar -xvf ucs4-syncrepl-proxy-setup.tar.bz2


The subdirectory :file:`UCS_Primary_Directory_Node` contains two |UCSUCR|
sub-file templates for the LDAP server configuration file
(:file:`/etc/ldap/slapd.conf`). Sub-files are a mechanism in |UCSUCR| which can
be used to generate a configuration file from several individual templates. More
detailed information can be found in the UCS manual. The two sub-files are now
copied into the template directory:

.. code-block:: console

   $ mv UCS_Primary_Directory_Node/8*.conf /etc/univention/templates/files/etc/ldap/slapd.conf.d/
   $ mv UCS_Primary_Directory_Node/syncrepl-proxy.conf /etc/univention/templates/files/etc/ldap/

The info file now needs to be copied. It registers the sub-file templates
and the |UCSUCR| variables used:

.. code-block:: console

   $ mv UCS_Primary_Directory_Node/syncrepl-proxy.info /etc/univention/templates/info/


Then the :file:`slapd.conf` is regenerated from the template:

.. code-block:: console

   $ ucr commit /etc/ldap/slapd.conf
   $ ucr commit /etc/ldap/syncrepl-proxy.conf


.. _syncrepl-init:

Initial transfer of the LDAP data
=================================

Now an initial copy of the UCS data is created and transferred to the external
system. In addition, an initial configuration file for the OpenLDAP service is
copied onto the external system (:file:`slapd.conf`).

.. code-block:: console

   $ slapcat > data.ldif
   $ cat remote_system/template-slapd.conf | ucr filter > remote_system/slapd.conf
   $ scp remote_system/slapd.conf data.ldif extldap.univention.test:
   $ rm data.ldif

The LDAP schema data and the SSL certificates from the UCS |UCSPRIMARYDN| are
now passed to the external LDAP server:

.. code-block:: console

   $ rsync -aR /usr/share/univention-ldap/schema extldap.univention.test:/
   $ rsync -aR /var/lib/univention-ldap/local-schema extldap.univention.test:/
   $ rsync -aR /etc/univention/ssl/extldap.univention.test extldap.univention.test:/
   $ rsync -aR /etc/univention/ssl/ucsCA/CAcert.pem extldap.univention.test:/


.. _syncrepl-3rd:

Configuration of the LDAP service on the third-party system
===========================================================

The configuration of the external LDAP server is now adapted. It must be noted
that only a minimal :file:`slapd.conf` is installed here, which should be
expanded with local adaptations as necessary:

.. code-block:: console

   $ systemctl stop slapd
   $ cp /etc/ldap/slapd.conf /root/backup-slapd.conf
   $ cp /root/slapd.conf /etc/ldap


A number of settings now need to be adapted in the provided
:file:`/etc/ldap/slapd.conf` template:

* ``extldap.univention.test`` must be replaced with the fully qualified domain
  name of the external LDAP server

* ``dc=univention,dc=test`` must be replaced with the LDAP base actually used

* :samp:`REMOTE_UPDATE_PASSWORD` must be replaced with the password used to
  access the LDAP database

.. _syncrepl-init2:

Importing the initial LDAP copy
===============================

The initial copy of the UCS directory data is now imported and the LDAP server
restarted. The file permissions of the :file:`/var/lib/ldap/` directory and the
:file:`/etc/ldap/slapd.conf` file differ depending on the Linux/Unix version:

.. code-block:: console

   $ mkdir /root/ldap_backup_dir
   $ mv /var/lib/ldap/*.* /root/ldap_backup_dir
   $ slapadd -f /etc/ldap/slapd.conf -l /root/data.ldif
   $ chown openldap.openldap /var/lib/ldap/*.*
   $ chgrp openldap /etc/ldap/slapd.conf
   $ chgrp -R openldap /etc/univention/ssl
   $ systemctl start slapd

The configuration of the external LDAP server is now complete. The following
command (performed on the |UCSPRIMARYDN|) can be used to check whether the
external LDAP server can be reached via the ``LDAPS`` protocol:

.. code-block:: console

   $ ldapsearch -x -H ldaps://extldap.univention.test -b cn=Subschema -s base

Whenever schema files are added on the UCS |UCSPRIMARYDN|, the following steps
have to be repeated. First an updated :file:`slapd.conf` needs to be generated
for the remote LDAP server which includes all UCS schema files. Then all
required files need to be copied to the remote LDAP server:

.. code-block:: console

   $ cat remote_system/template-slapd.conf | ucr filter > remote_system/slapd.conf
   $ scp remote_system/slapd.conf extldap.univention.test:
   $ rsync -aR /usr/share/univention-ldap/schema extldap.univention.test:/
   $ rsync -aR /var/lib/univention-ldap/local-schema extldap.univention.test:/


And after that the following steps need to be repeated on the external LDAP
server:

.. code-block:: console

   $ systemctl stop slapd
   $ cp /etc/ldap/slapd.conf /root/backup-slapd.conf
   $ cp /root/slapd.conf /etc/ldap
   $ chgrp openldap /etc/ldap/slapd.conf
   $ systemctl start slapd

If the external system is a Debian system, the ``SLAPD_SERVICES`` variable may
need to be adapted in :file:`/etc/default/slapd`. In addition, the
``SLAPD_CONF`` variable can be used to specify the
:file:`/etc/ldap/slapd.conf` file as the configuration file for the ``slapd``,
if this is not the standard for the OpenLDAP version used.

.. _syncrepl-proxy:

Activation of the syncrepl proxy
================================

If the LDAP connection works, the configuration of the syncrepl proxy can be
activated on the |UCSPRIMARYDN|. This is done by saving the
:samp:`REMOTE_UPDATE_PASSWORD` password configured above in the
:file:`/etc/replica-001.secret` file and entering the address of the external
LDAP server in the form of a LDAP-URI in the |UCSUCRV|
:envvar:`ldap/replica/target/uri`:

.. code-block:: console

   $ echo -n 'REMOTE_UPDATE_PASSWORD' >/etc/replica-001.secret
   $ chmod 600 /etc/replica-001.secret
   $ ucr set ldap/replica/target/uri=ldaps://extldap.univention.test/
   $ ucr commit /etc/ldap/syncrepl-proxy.conf
   $ systemctl restart slapd

If several systems are connected, the corresponding LDAP-URIs can be entered in
the variable separated with commas and additional replica password files
created. The number in the name of the password files is incremented by one for
each additional system.

The replication originates from the |UCSPRIMARYDN| and is performed via
``LDAPS`` to the host name of the external LDAP server system. This requires
working name resolution (typically via DNS). The host name must be specified as
a fully qualified domain name to allow checking of the SSL certificate.

To allow convenient LDAP search via :command:`ldapsearch -x expression` on the
external LDAP server the file :file:`/etc/ldap/ldap.conf` may be configured like
this:

.. code-block:: console

   TLS_CACERT /etc/univention/ssl/ucsCA/CAcert.pem
   HOST FQDN
   BASE LDAPBASE

.. _syncrepl-test:

Testing the replication
=======================

The replication via :program:`syncrepl` can be tested by changing the description
of an existing user for example. When an LDAP search is performed on the
external server, the changed description should then be displayed.

