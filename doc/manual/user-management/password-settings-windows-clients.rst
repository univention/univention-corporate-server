.. SPDX-FileCopyrightText: 2021-2024 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _users-password-samba:

Password settings for Windows clients when using Samba
======================================================

With the Samba domain object,
you can set the requirements for user account passwords in a Samba domain.

You can manage the Samba domain object through the UMC module :guilabel:`LDAP directory`.
The Samba domain object locates in the ``samba`` container and has the domain's NetBIOS name.
You find the ``samba`` container under the LDAP base.

.. important::

   It's a strong recommendation to design the password requirement settings of the Samba domain object
   identical to the user password policy as described in :ref:`users-passwords`.

   .. Same note exists in password-management.rst

In the *Password* section on the *General* tab of the *Samba Domain* object,
you can configure the following settings.

Password length
   The minimum number of characters for a user password.

Password history
   UCS stores password changes in the form of hashes.
   Users can't use passwords from history when setting a password.
   For example, with a password history value of ``5``,
   user must set five other passwords before they can reuse a password from the history.

Minimum password age
   Defines the period of time that must elapse,
   before users can change their password.

Maximum password age
   Defines the maximum age for a password.
   When the period of time is over,
   UCS requires the user to change their password upon next sign-in.

   To define an infinite period of time, leave the value empty.

Password must meet complexity requirements
   Activating the checkbox activates `Microsoft Password complexity requirements <microsoft-password-complexity-requirements_>`_.
   A tooltip shows the required characters in a password.
   The library :file:`Passfilt.dll` enforces the complexity requirements.
   Administrators can't change them.
