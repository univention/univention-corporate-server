.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
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

The content of this section moved to
:external+uv-ucs-operation:ref:`password-management-policies-types`
in :cite:t:`uv-ucs-operation`.

.. _users-passwords-policy-settings-umc:

Password policy settings in UMC
-------------------------------

The content of this section moved to
:external+uv-ucs-operation:ref:`password-management-policies-settings`
in :cite:t:`uv-ucs-operation`.
