.. _domaenenkonzept:

********************************
Domain services / LDAP directory
********************************

Univention Corporate Server offers a cross platform domain concept with a common
trust context between Linux and/or Windows systems. Within this domain a user is
known to all systems via their username and password stored in the |UCSUMS| and
can use all services which are authorized for them. The management system keeps
the account synchronized for the windows login, Linux/POSIX systems and
Kerberos. The management of user accounts is described in :ref:`users-general`.

All UCS and Windows systems within a UCS domain have a host domain account. This
allows system-to-system authentication. Domain joining is described in
:ref:`domain-join`.

The certificate authority (CA) of the UCS domain is operated on the
|UCSPRIMARYDN|. A SSL certificate is generated there for every system that has
joined the domain. Further information can be found in :ref:`domain-ssl`.

Every computer system which is a member of a UCS domain has a system role. This
system role represents different permissions and restrictions, which are
described in :ref:`system-roles`.

All domain-wide settings are stored in a directory service on the basis of
OpenLDAP. :ref:`domain-ldap` describes how to expand the managed attributes with
LDAP scheme expansions, how to set up an audit-compliant LDAP documentation
system and how to define access permissions to the LDAP directory.

Replication of the directory data within a UCS domain occurs via the Univention
Directory Listener / Notifier mechanism. Further information can be found in
:ref:`domain-listener-notifier`.

Kerberos is an authentication framework the purpose of which is to permit secure
identification in the potentially insecure connections of decentralized
networks. Every UCS domain operates its own Kerberos trust context (realm).
Further information can be found in :ref:`domain-kerberos`.

.. toctree::
   :caption: Chapter contents

   domain-join
   system-roles
   ldap-directory
   listener-notifier
   ssl
   kerberos
   password-hashes
   saml
   oidc
   backup2master
   fault-tolerant-setup
   admin-diary
