.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _iam-user-lockout:

User account lockout after failed sign-in attempts
==================================================

By default, there is no limit on failed password attempts.
To prevent brute force attacks,
you can configure an automatic lockout for user accounts
after a set number of failed sign-in attempts.

Nubus for UCS supports multiple authentication methods.
Each method has its own way to configure and count failed sign-in attempts.

.. _iam-user-lockout-samba:

Configure lockout for Samba and Active Directory
------------------------------------------------

Samba provides services in Active Directory environments, such as Kerberos.
To lock out users after too many failed sign-in attempts,
use :command:`samba-tool`.

#. Show the currently configured values:

   .. code-block:: console
      :name: samba-show-password-settings
      :caption: Show Samba password lockout settings

      $ samba-tool domain passwordsettings show

#. Set the number of failed sign-in attempts before locking the account:

   .. code-block:: console
      :name: samba-set-lockout-threshold
      :caption: Set the sign-in attempt limit before lockout

      $ samba-tool domain passwordsettings set --account-lockout-threshold=5

#. Set the number of minutes that the account locks
   after a user enters too many incorrect passwords:

   .. code-block:: console
      :name: samba-set-lockout-duration
      :caption: Set the account lockout duration in minutes

      $ samba-tool domain passwordsettings set --account-lockout-duration=3

#. Set the number of minutes after which the counter resets:

   .. code-block:: console
      :name: samba-set-lockout-reset-interval
      :caption: Set the lockout counter reset interval in minutes

      $ samba-tool domain passwordsettings set --reset-account-lockout-after=5

To unlock a locked account,
see :ref:`iam-user-lockout-unlock`.

.. important::

   After the lockout duration expires,
   Nubus for UCS unlocks the account
   but doesn't reset the counter immediately.
   Until the counter resets,
   a single failed sign-in attempt locks the account again.

.. _iam-user-lockout-pam:

Configure lockout for the PAM stack
-----------------------------------

To automatically lock users in the PAM stack after failed sign-in attempts,
set the :term:`UCR variable` :envvar:`auth/faillog` to ``yes``.
Set the limit of failed sign-in attempts that triggers a lockout
in :envvar:`auth/faillog/limit`.
The counter resets each time the user enters the password correctly.

By default, the lockout is per system.
A user locked out on one system can still sign in on another.
Set :envvar:`auth/faillog/lock_global` to ``yes``
to apply the lockout globally
and register it in the LDAP directory.
You can set the global lock only on
:term:`Primary Directory Node` or :term:`Backup Directory Node` systems,
because other system roles lack write permissions
in the LDAP directory.
On these systems,
the listener module automatically activates or deactivates
the local lockout depending on the lock state in the LDAP directory.

By default, the lockout has no time limit,
and you must reset the lockout manually.
However, Nubus for UCS can also reset the lockout automatically after a configured period.
Specify the period in seconds in :envvar:`auth/faillog/unlock_time`.
If the value is ``0``, Nubus for UCS resets the lockout counter immediately.

By default, the ``root`` user is exempt from the lockout.
You can apply the lockout to ``root`` by setting :envvar:`auth/faillog/root` to ``yes``.

If the lockout applies only locally,
you can unlock a user account
by running the command in :numref:`pam-faillock-reset`.

.. code-block:: console
   :name: pam-faillock-reset
   :caption: Reset a locally locked user account

   $ faillock --reset --user USERNAME

If Nubus for UCS locks the account globally in the LDAP directory,
see :ref:`iam-user-lockout-unlock`.

.. _iam-user-lockout-openldap:

Configure lockout for OpenLDAP
------------------------------

This feature is available on :term:`Primary Directory Node` and :term:`Backup Directory Node` systems.
To enable it,
set :envvar:`ldap/ppolicy/enabled` to ``yes``
and restart the OpenLDAP server,
as shown in :numref:`openldap-enable-ppolicy`.

.. code-block:: console
   :name: openldap-enable-ppolicy
   :caption: Enable OpenLDAP password policy and restart the server

   $ ucr set ldap/ppolicy/enabled=yes
   $ systemctl restart slapd

By default, five failed LDAP sign-in attempts
within five minutes trigger the lockout.
To unlock a locked account,
see :ref:`iam-user-lockout-unlock`.

In the configuration object with the ``objectClass`` ``pwdPolicy``,
you can adjust the number of failed LDAP sign-in attempts
that trigger a lockout.

The ``pwdPolicy`` object has these attributes:

``pwdMaxFailure``
   The number of failed LDAP sign-in attempts before the account locks.

``pwdMaxFailureCountInterval``
   The time interval in seconds during which Nubus for UCS counts failed sign-in attempts.
   Nubus for UCS ignores failed sign-in attempts outside this time interval.

To list the current values,
run the following command:

.. code-block:: console
   :name: openldap-search-pwdpolicy
   :caption: List the ``pwdPolicy`` configuration object

   $ univention-ldapsearch objectclass=pwdPolicy

To set ``pwdMaxFailure`` to 10,
run the following command:

.. code-block:: console
   :name: openldap-set-pwdmaxfailure
   :caption: Set the maximum sign-in failure count to 10

   $ LB="$(ucr get ldap/base)"
   $ ldapmodify -x -D "cn=admin,$LB" -y /etc/ldap.secret <<__EOT__
   dn: cn=default,cn=ppolicy,cn=univention,$LB
   changetype: modify
   replace: pwdMaxFailure
   pwdMaxFailure: 10
   __EOT__

.. _iam-user-lockout-unlock:

Unlock a locked user account
----------------------------

The unlock method depends on which lockout mechanism locked the account.

If Samba or OpenLDAP locked the account:

#. Open the *Users* management module.
#. Open the :guilabel:`Account` tab.
#. Select :guilabel:`Unlock account`.
#. Save the changes.

If the PAM stack locked the account globally,
Nubus for UCS also deactivates the user account:

#. Open the *Users* management module.
#. Open the :guilabel:`Account` tab.
#. Clear the :guilabel:`Account is deactivated` checkbox.
#. Save the changes.
