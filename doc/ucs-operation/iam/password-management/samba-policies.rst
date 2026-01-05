.. SPDX-FileCopyrightText: 2024 - 2025 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _password-management-windows-client:

****************************
Samba domain password policy
****************************

With the Samba domain object,
you can set the requirements for user account passwords in a Samba domain.

You can manage the Samba domain object through the *LDAP directory module* in the *Management UI*.
For more information,
see :external+uv-nubus-manual:ref:`nubus-domain-ldap`
in :cite:t:`uv-nubus-manual`.

.. important::

   Univention recommends configuring the Samba domain object's password requirements
   to match the user password policy
   as described in :ref:`password-management-policies`.

   UDM policies apply when administrators change passwords through administrative tools.
   Samba domain policies apply when users change their own passwords through any service.
   Because these are separate systems,
   Univention recommends configuring them identically
   to ensure consistent behavior.

   If the policies are inconsistent, the services use the policies as configured.
   However, the different settings may confuse users.
   Identical settings in both policies reduce user confusion.

   .. A similar warning locates in password-management/policies.rst

In the LDAP directory,
navigate to the ``samba`` container underneath the LDAP base DN
and select the Samba object.
The Samba object has the domain's NetBIOS name.

In the *Password* section on the *General* tab of the *Samba Domain* object,
you can configure the following settings.

Password length
   The minimum number of characters for a user password.

   :Default value: ``8``

Password history
   Nubus stores password changes as hashes.
   Users can't use passwords from the password history when setting a password.
   For example, with a password history value of ``5``,
   users must set five other passwords before they can reuse a password from the history.

   :Default value: No value set.

Minimum password age
   Defines how long users must wait before changing their password.
   You can configure the value as seconds, minutes, hours, or days.

   :Default value: No value set.

Maximum password age
   Defines the maximum password age.
   When this period expires,
   Nubus requires the user to change their password upon next sign-in.
   You can configure the value as seconds, minutes, hours, or days.

   To deactivate password expiration, leave the value empty.

   :Default value: No value set.

Password must meet complexity requirements
   Activate the checkbox to enable
   `Microsoft Password complexity requirements <https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/security-policy-settings/password-must-meet-complexity-requirements>`_.
   A tool tip shows the required characters in a password.
   The library :file:`Passfilt.dll` enforces the complexity requirements.
   Administrators can't change them.

   :Default value: ``activated``.
