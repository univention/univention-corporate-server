************
|UCSUCRV|\ s
************

This appendix lists the |UCSUCRV|\ s mentioned in the document.

.. envvar:: backup/clean/max_age

   Defines how long a UCS system keeps old backup files of the LDAP data.
   Allowed values are integer numbers and they define days. The system doesn't
   delete backup files when the variable is not set. See
   :ref:`domain-ldap-nightly-backup`.


.. envvar:: directory/reports/logo

   Defines the path and name to an image file for usage as logo in a Univention
   Directory report PDF file. For more information see
   :ref:`central-management-umc-adjustment_expansion_of_directory_reports`.

.. envvar:: kerberos/adminserver

   Defines the system that provides the Kerberos admin server. See
   :ref:`domain-kerberos-admin-server`.


.. envvar:: kerberos/kdc

   Contains the reference to the KDC. Typically, a UCS system selects the KDC to
   be used from a DNS service record. With this variable administrators can
   configure an alternative KDC.

.. TODO Ask SME: What kind of value is expected?


.. envvar:: kerberos/realm

   Contains the name of the Kerberos realm. See :ref:`domain-kerberos`.


.. envvar:: ldap/acl/read/anonymous

   Controls if the LDAP server allows anonymous access to the LDAP directory.
   In the default configuration the LDAP server doesn't allow ananymous access
   to the LDAP directory.


.. envvar:: ldap/acl/read/ips

   A list of IP addresses for which the LDAP server allows anonymous access. See
   :ref:`domain-ldap-acls`.


.. envvar:: ldap/acl/nestedgroups

   Controls if nested groups are allowed. Per default nested groups are
   activated. See :ref:`domain-ldap-acls`.


.. envvar:: ldap/acl/user/passwordreset/accesslist/groups/dn

   Use a different group from the default ``User Password Admins`` group to
   reset user passwords. The value is a distinguished name (DN) to a user group.
   See :ref:`domain-ldap-delegation-of-the-priviledge-to-reset-user-passwords`.


.. envvar:: ldap/idletimeout

   Configures a time period in seconds after which the LDAP connection is cut
   off on the server side. See
   :ref:`domain-ldap-timeout-for-inactive-ldap-connections`.


.. envvar:: ldap/logging/exclude1

   Exclude individual areas of the directory service from logging. See
   :ref:`domain-ldap-directory-logger`.


.. envvar:: ldap/logging/excludeN

   See :envvar:`ldap/logging/exclude1`.


.. envvar:: ldap/logging/id-prefix

   Adds the transaction ID of an entry to the directory log. Possible values are
   the default ``yes`` and ``no``. See :ref:`domain-ldap-directory-logger`.

.. envvar:: ldap/master

   TBD

.. TODO : Define UCRV server/role


.. envvar:: ldap/pw-bcrypt

   Activates :program:`bcrypt` as password hashing method when set to ``true``.
   See :ref:`domain-password-hashes`.


.. envvar:: ldap/server/addition

   Additional LDAP server a UCS system can query for information in the
   directory service.


.. envvar:: ldap/server/name

   The LDAP server the system queries for information in the directory service.


.. envvar:: listener/debug/level

   Defines the detail level for log messages of the listener to
   :file:`/var/log/univention/listener.log`. The possible values are from 0
   (only error messages) to 4 (all status messages). Once the debug level has
   been changed, the |UCSUDL| must be restarted.


.. envvar:: notifier/debug/level

   Defines the detail level for log messages of the notifier to
   :file:`/var/log/univention/notifier.log`. The possible values are from 0
   (only error messages) to 4 (all status messages). Once the debug level has
   been changed, the |UCSUDN| must be restarted.


.. envvar:: nssldap/bindpolicy

   Controls the measures that the UCS system takes when the LDAP server cannot
   be reached. See :ref:`domain-ldap-name-service-switch-ldap-nss-module`.

.. TODO Ask SME: What is the default value and what values are possible?


.. envvar:: password/hashing/bcrypt

   Activates :program:`bcrypt` as password hashing method when set to ``true``.
   See :ref:`domain-password-hashes`.


.. envvar:: password/hashing/bcrypt/cost_factor

   Defines the :program:`bcrypt` cost factor and defaults to ``12``. See
   :ref:`domain-password-hashes`.


.. envvar:: password/hashing/bcrypt/prefix

   Defines the :program:`bcrypt` prefix and defaults to ``2b``. See
   :ref:`domain-password-hashes`.


.. envvar:: password/hashing/method

   Defines the hashing method for the password hashes. The default is
   ``SHA-512``. See :ref:`domain-password-hashes`.


.. envvar:: portal/auth-mode

   Defines the authentication mode for the UCS portal. Set it to ``saml``, if
   you want to activate SAML for single sign-on login. For more information see
   :ref:`central-management-umc-login`.

.. envvar:: saml/idp/authsource

   Allows Kerberos authentication at the SAML identity provider. Change to
   ``univention-negotiate`` to activate. The default is ``univention-ldap``. For
   more information, see :ref:`domain-saml`.

.. envvar:: saml/idp/entityID/supplement/[identifier]

   Activates additional local identity providers for SAML on a UCS system
   serving as UCS Identity provider. To activate set the value to ``true``. For
   more information see :ref:`domain-saml-extended-configuration`.


.. envvar:: saml/idp/negotiate/filter-subnets

   Allows to restrict the Kerberos authentication at the SAML identity provider
   to certain IP subnets in the `CIDR notation
   <https://en.wikipedia.org/wiki/Classless_Inter-Domain_Routing>`_, for example
   ``127.0.0.0/16,192.168.0.0/16``. For more information, see
   :ref:`domain-saml`.


.. envvar:: server/role

   TBD

.. TODO : Define UCRV server/role


.. envvar:: ssl/validity/host

   Records the expiry date of the local computer certificate on each UCS system.
   The value reflects the number of days since the 1970-01-01.


.. envvar:: ssl/validity/root

   Records the expiry date of the root certificate on each UCS system. The value
   reflects the number of days since the 1970-01-01.


.. envvar:: ssl/validity/warning

   Defines the warning period for the expiration check of the SSL/TLS root
   certificate. The default value is ``30`` days. See :ref:`domain-ssl`.


.. envvar:: ucs/web/theme

   Select the theme for |UCSWEB|. The value corresponds to a CSS file under
   :file:`/usr/share/univention-web/themes/` with the same name without filename
   extension.
