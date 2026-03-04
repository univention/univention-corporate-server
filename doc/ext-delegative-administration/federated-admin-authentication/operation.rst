.. SPDX-FileCopyrightText: 2025-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _fed-auth-manage-administrators:

Manage administrators for federated authentication
==================================================

After you configure and test federated authentication,
you must maintain the system as users and roles change.
This section covers common operational tasks.

.. _fed-auth-manage-add:

Add a new administrator
-----------------------

To grant administrative access to a new user,
you don't need to make any configuration changes in Nubus.

#. Create the user account in your upstream IAM, not in Nubus.

#. Assign the user to groups that correspond to guardian roles.

   Or add the user to the attribute containing guardian roles.

#. When the user signs in to the *Management UI* for the first time,
   Nubus creates a federated account object automatically.
   For more information the data that Nubus creates for the object,
   see :ref:`fed-auth-data-protection`.

#. Verify the user can access the expected management modules.

.. _fed-auth-manage-update-role:

Update administrative roles
---------------------------

.. note::

   You don't need to make any configuration changes in Nubus.

To change which administrative tasks a user can perform:

#. Update the user's group memberships or role attributes in the upstream IAM.

#. When the user signs in to the *Management UI* again,
   their permissions reflect the new roles.

To revoke administrative access for a user account:

#. Remove the user from all administrative groups in the upstream IAM.

#. Or remove the guardian roles attribute from the user.

.. important::

   The user can still sign in, but has no administrative permissions.

.. _fed-auth-manage-emergency:

Prepare emergency access
------------------------

This feature depends on upstream IAM availability.
If your upstream IAM becomes unavailable,
you can't create new administrator accounts in Nubus.

Prepare for upstream IAM outages before you enable federated authentication:

#. Create a break-glass local administrator account in Nubus.

#. Store the credentials securely in a password manager or vault.

#. Keep this account active but don't use it for normal administration.

#. If your upstream IAM becomes unavailable,
   sign in with this break-glass account to restore access.

#. Rotate the credentials of this account after you restore upstream IAM access.

.. warning::

   A break-glass account is essential for disaster recovery.
   Without it, you have no access if the upstream IAM is unavailable.
