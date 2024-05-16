.. SPDX-FileCopyrightText: 2021-2024 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _users-passwords:

User password management
========================

Most internet users find it difficult to choose the right password.
The password is the key to accessing user accounts, even in a UCS domain.
Passwords that are difficult to guess and regular passwords changes
are an essential element of the system security of a UCS domain.
To prevent users from choosing passwords that are too easy,
administrators can configure several properties in a *password policy*.

This section describes how to define password policies,
such as a minimum password length and an expiration time interval.
UCS applies the password policy when users change their passwords.

UCS stores the user password for every user as hash
in different attributes of the corresponding LDAP user account object:

:``krb5Key``: stores the Kerberos password.

:``userPassword``: stores the Unix password.
  Other Linux distributions store it in :file:`/etc/shadow`.

:``sambaNTPassword``: stores the NT password hash used by Samba.

.. seealso::

   `Creating Secure Passwords <bsi-secure-password_>`_ by German Federal Office of Information Security
      for more information and tips about creating a secure and good password.

.. _users-passwords-policy-types:

Password policy types
---------------------

UCS has several types of password policy settings as outlined in this section.
What policy applies depends on who runs the password change
and if the UCS domain has Samba installed
through the app :program:`Active Directory Domain Controller`.

Password Policy in UDM
   The *Password Policy* is a UDM policy
   that applies to user password changes done through UMC modules
   which in turn use UDM in the backend.
   The *Password Policy* applies, when an **administrator** changes a user's password through UMC or UDM.
   It also applies, when a **user** changes their password and if the UCS domain **hasn't** Samba installed.

   UCS defines a default password policy.
   :ref:`users-passwords-policy-settings-umc` describes the available settings for the *Password Policy*.

   You can enhance the *Password quality check* with |UCSUCRVs| mentioned in :ref:`users-passwords-policy-settings-umc`.

   You can create additional password policies
   and assign them to user account objects in the LDAP directory tree.
   For more information about policies, see :ref:`central-policies`.

   .. important::

      When you have Samba installed,
      design the password requirement settings of the user password policy
      identical to the Samba domain object as described in :ref:`users-password-samba`.

      .. Same note exists in password-settings-windows-clients.rst

Password policy for the Samba domain
   When you have Samba installed in your UCS domain,
   the Samba domain has it's own password policy.
   The Samba password policy **always** applies, when a **user** changes their password,
   regardless of the used service,
   through Univention Portal, User Self Service, Microsoft Windows, or Kerberos.

   To configure the password policy for the Samba domain, see :ref:`users-password-samba`.

   .. seealso::

      :ref:`windows-setup4` of Samba
         for more information about the installation of Samba.

      :ref:`windows-services-for-windows`
         for general information about Samba providing Services for Windows.

.. _users-passwords-change:

Change the user password
------------------------

Changing the user password has the following triggers:

#. The systems requires the user to change their password,
   for example, because the password reached the expiration interval.

#. Through a setting at the user account,
   an administrator requests the user to change their password upon next sign-in.

#. The user decides to change their password.

When a user decides to change their password,
they can use the following ways:

Univention Portal
   Every UCS domain has the *Portal* installed.
   To change the password, use the following steps:

   #. Sign in to the *Univention Portal*.

   #. Navigate to the user menu. It's the *"burger menu"* in top right corner.

   #. Select :menuselection:`User settings --> Change your password`.

   #. Provide your current password and set a new password.
      Retype it and confirm.

User Self Service
   The :ref:`user-management-password-changes-by-users` is a dedicated app in the :ref:`software-appcenter`.
   It offers a direct link to the password change
   so that administrators can add a prominent tile to the Univention Portal
   for the password change.
   Furthermore, the app offers a way to reset the user password when they forgot it.

Microsoft Windows
   Users can change their user password through their Microsoft Windows client
   that's joined in the UCS domain through Samba.

Kerberos
   Users can change their user password through clients
   that have joined in the UCS domain through Kerberos.
   They can use the default features of those clients to change the password.

   For more information about joining Ubuntu and Linux systems to a UCS domain
   and the integration with Kerberos,
   see :cite:t:`ext-doc-domain`.

.. _users-passwords-policy-settings-umc:

Password policy settings in UMC
-------------------------------

With the password policy settings in UMC administrators can define
the minimum password length, the expiry interval and the password history length.
:numref:`password-policy` shows the password policy settings in UMC.
Following the figure, you find a reference of the available settings.

.. _password-policy:

.. figure:: /images/users_policy_password.*
   :alt: Configuring a password policy

   Configuring a password policy

On the *General* tab of a password policy, you can configure the following settings.

History length
   The password history saves the last used password hashes.
   The *History length* determines the length of that history,
   for example if the history stores the last three or the last seven passwords.
   Users can't reuse passwords from the password history for setting a new password.
   UCS doesn't store the passwords retroactively.

   To deactivate the validation for the password history, set the value to ``0``.

   Example
      If UCS stored ten passwords, and you reduce the value for the password history length to ``3``,
      UCS deletes the oldest seven passwords from the password history during the next password change.
      If you then change the password history length,
      the number of stored passwords stays at three and increases by each password change.

Password length
   The *Password length* is the minimum length in characters that a user
   password must comply with.
   If you don't set a value, UCS applies the minimum length of ``8`` characters.

   The default value always applies if you don't set a policy
   and you activated the *Override password check* checkbox.
   This means it even applies if you deleted the *default-settings* password policy.

   To deactivate the validation for the password length, set the value to ``0``.

   You can configure a default value per UCS system through the |UCSUCRV|
   :envvar:`password/quality/length/min`.
   The setting applies to users that aren't subject to a *UDM password policy*.

Password expiry interval
   A *Password expiry interval* demands regular password changes.
   UCS requires a user to change their password during sign-in to |UCSWEB|\ s,
   to Kerberos, and on UCS systems when the expiry interval in days passed.
   UCS displays the remaining validity of the user password in the user management module
   at *Password expiry date* in the *Account* tab.

   To deactivate the *Password expiry interval*, leave the value blank.

Password quality check
   If you activate the option *Password quality check*,
   UCS runs additional password checks, including dictionary checks,
   for password changes in UMC and Kerberos.

   You configure the quality checks through the following |UCSUCR| variables.
   For more information, refer to linked variable descriptions.

   You can enforce the following checks:

   * :envvar:`password/quality/credit/digits`
   * :envvar:`password/quality/credit/upper`
   * :envvar:`password/quality/credit/lower`
   * :envvar:`password/quality/credit/other`
   * :envvar:`password/quality/forbidden/chars`
   * :envvar:`password/quality/required/chars`
   * :envvar:`password/quality/mspolicy`

   .. important::

      To apply the *password quality check* on all UCS sign-in systems,
      you need to set the |UCSUCRVs| on **all** UCS sign-in servers.
