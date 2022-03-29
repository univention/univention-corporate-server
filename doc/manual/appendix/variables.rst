************
|UCSUCRV|\ s
************

This appendix lists the |UCSUCRV|\ s mentioned in the document.

.. envvar:: auth/faillog

   Configures the automatic locking of users after failed login attempts in the
   PAM stack. To activate, set the value to ``yes``. For more information, see
   :ref:`users-faillog-pam`.


.. envvar:: auth/faillog/limit

   Configures the upper limit of failed login attempts for a user account
   lockout. For more information, see :ref:`users-faillog-pam`.

.. envvar:: auth/faillog/lock_global

   Configure on |UCSPRIMARYDN| and |UCSBACKUPDN| to create a failed login
   account lockout globally and store it in the LDAP directory. For more
   information, see :ref:`users-faillog-pam`.


.. envvar:: auth/faillog/root

   To make the user account ``root`` subject of the PAM stack account lockout,
   set the value to ``yes``. It defaults to ``no``. For more information, see
   :ref:`users-faillog-pam`.


.. envvar:: auth/faillog/unlock_time

   Configure a time interval to unlock an account lockout. The value is defined
   in seconds. The value ``0`` resets the lock immediately. For more
   information, see :ref:`users-faillog-pam`.


.. envvar:: backup/clean/max_age

   Defines how long a UCS system keeps old backup files of the LDAP data.
   Allowed values are integer numbers and they define days. The system doesn't
   delete backup files when the variable is not set. See
   :ref:`domain-ldap-nightly-backup`.

.. envvar:: directory/manager/templates/alphanum/whitelist

   Define an allowlist of characters that are not removed by the ``:alphanum``
   option for the value definition in user templates. For more information, see
   :ref:`users-templates`.

.. envvar:: directory/manager/user_group/uniqueness

   Controls if UCS prevents users with the same username as existing groups. To
   deactivate the check for uniqueness, set the value to ``false``. For more
   information see :numref:`users-management-table-general-tab`.

.. envvar:: directory/manager/web/modules/groups/group/checks/circular_dependency

   Controls the check for circular dependencies regarding nested groups. To
   disable, set the value to ``no``. For more information, see
   :ref:`groups-nested`.


.. envvar:: directory/manager/web/modules/users/user/wizard/disabled

   Deactivates the simplified wizard to create users when the value is set to
   ``true``. In the default setting the wizard is activated. For more
   information see :ref:`users-management`.

.. envvar:: directory/reports/logo

   Defines the path and name to an image file for usage as logo in a Univention
   Directory report PDF file. For more information see
   :ref:`central-management-umc-adjustment-expansion-of-directory-reports`.

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

.. envvar:: ldap/overlay/lastbind

   To activate the ``lastbind`` overlay module for the LDAP server, set the
   value to ``yes``. For more information, see
   :ref:`users-lastbind-overlay-module`.

.. envvar:: ldap/overlay/lastbind/precision

   Configures the time in seconds that has to pass before the ``authTimestamp``
   is updated again by the ``lastbind`` overlay. For more information, see
   :ref:`users-lastbind-overlay-module`.


.. envvar:: ldap/overlay/memberof/memberof

   Configures the attribute at user objects that shows the group membership.
   Default value is ``memberOf``. For more information, see
   :ref:`groups-memberof`.

.. envvar:: ldap/ppolicy

   To enable automatic account locking, set the value to ``yes``. Also set
   :envvar:`ldap/ppolicy/enabled`. For more information, see
   :ref:`users-faillog-openldap`.


.. envvar:: ldap/ppolicy/enabled

   To enable automatic account locking, set the value to ``yes``. Also set
   :envvar:`ldap/ppolicy`. For more information, see
   :ref:`users-faillog-openldap`.


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


.. envvar:: local/repository

   Activates and deactivates the local repository. For more information see
   :ref:`software-createrepo`.


.. envvar:: notifier/debug/level

   Defines the detail level for log messages of the notifier to
   :file:`/var/log/univention/notifier.log`. The possible values are from 0
   (only error messages) to 4 (all status messages). Once the debug level has
   been changed, the |UCSUDN| must be restarted.

.. envvar:: nss/group/cachefile/check_member

   When activated with ``true``, the cron job script for exporting the local
   group cache also checks, if the group members are still present in the LDAP
   directory. For more information, see :ref:`groups-cache`.


.. envvar:: nss/group/cachefile/invalidate_interval

   Defines the invalidation interval to control when the local group cache is
   considered invalid and a new export is run. For more information, see
   :ref:`groups-cache`.


.. envvar:: nss/group/cachefile/invalidate_on_changes

   Activates or deactivates the listener to invalidate the local group cache. To
   activate the listener, set the value to ``true``. Else, set it to ``false``.
   For more information, see :ref:`groups-cache`.


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


.. envvar:: password/quality/credit/digits

   Defines the minimum number of digits for a new password. For more
   information, see :ref:`users-passwords`. For more information, see
   :ref:`users-passwords`.


.. envvar:: password/quality/credit/lower

   Defines the minimum number of lowercase letters in the new password. For more
   information, see :ref:`users-passwords`.


.. envvar:: password/quality/credit/other

   Defines the minimum number of characters in the new password which are
   neither letters nor digits. For more information, see :ref:`users-passwords`.


.. envvar:: password/quality/credit/upper

   Defines the minimum number of uppercase letters in the new password. For more
   information, see :ref:`users-passwords`.


.. envvar:: password/quality/forbidden/chars

   Defines the characters and digits that are not allowed for passwords. For
   more information, see :ref:`users-passwords`.


.. envvar:: password/quality/length/min

   Sets the minimum length default for a password on a per UCS system basis for
   users not subject to a UDM password policy. The value ``yes`` applies checks
   from the :program:`python-cracklib`. The value ``sufficient`` does not
   include :program:`python-cracklib` checks. For more information, see
   :ref:`users-passwords`.


.. envvar:: password/quality/mspolicy

   Defines the standard Microsoft password complexity criteria. For more
   information, see :ref:`users-passwords`.

.. envvar:: password/quality/required/chars

   Defines individual characters/figures that are compulsory for passwords. For
   more information, see :ref:`users-passwords`.


.. envvar:: pkgdb/scan

   Controls if a UCS system stores installation processes in the software
   monitor. To turn it off, set the value ``no``. For more information see
   :ref:`computers-softwaremonitor`.

.. envvar:: portal/auth-mode

   Defines the authentication mode for the UCS portal. Set it to ``saml``, if
   you want to activate SAML for single sign-on login. For more information see
   :ref:`central-management-umc-login`.


.. envvar:: repository/mirror/server

   Defines another repository server as source for the local mirror. Default
   value: ``updates.software-univention.de``. For more information see
   :ref:`software-createrepo`.


.. envvar:: repository/online/component/.*/unmaintained

   Defines how to deal with unmaintained packages from additional repositories.
   To activate, set the value to ``yes``. For more information see
   :ref:`software-configrepo`.


.. envvar:: repository/online/server

   The repository server used to check for updates and download packages.
   Default value: ``updates.software-univention.de``. For more information see
   :ref:`computers-configuration-via-univention-configuration-registry`.


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

.. envvar:: saml/idp/selfservice/account-verification/error-descr

   Configures the error message description text for the :program:`Self
   Service`. The text shows up for users that login through SSO with an
   unverified and self registered user account. For more information, see
   :ref:`user-management-password-changes-by-users-selfregistration-account-verification`.


.. envvar:: saml/idp/selfservice/account-verification/error-title

   Configures the error message title for the :program:`Self Service`. The title
   shows up for users that login through SSO with an unverified and self
   registered user account. For more information, see
   :ref:`user-management-password-changes-by-users-selfregistration-account-verification`.


.. envvar:: saml/idp/selfservice/check_email_verification

   Controls if the SSO login denies logins from unverified and self registered
   user accounts. For more information, see
   :ref:`user-management-password-changes-by-users-selfregistration-account-verification`.

.. envvar:: self-service/backend-server

   Defines the UCS system where the backend of the :program:`Self Service` app
   is installed. For more information, see
   :ref:`user-management-password-changes-by-users-self-service`.

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


.. envvar:: umc/self-service/account-deregistration/enabled

   To activate the :program:`Self Service` deregistration, set the variable to
   ``True``. For more information, see
   :ref:`user-management-password-changes-by-users-selfderegistration`.


.. envvar:: umc/self-service/account-verification/backend/enabled

   Enables or disables the account verification and request of new verification
   tokens for the :program:`Self Service`. For more information, see
   :ref:`user-management-password-changes-by-users-selfregistration-account-verification`.
