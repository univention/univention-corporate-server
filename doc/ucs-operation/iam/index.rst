.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _iam:

******************************
Identity and Access Management
******************************

This chapter covers Identity and Access Management (IAM) configuration tasks
for technical administrators in Nubus for UCS.
It addresses how users authenticate, how administrators govern passwords,
how they structure and synchronize groups, and how they create user accounts.

Password management
   Configure password policies that control password length, complexity, history, and age.
   Nubus for UCS supports two policy systems—UDM and Samba domain—
   which Univention recommends keeping aligned in Samba-enabled domains.
   This section covers the *End User Self Service*,
   which lets users manage their own contact information,
   register, and reset their passwords.
   See :ref:`password-management`.

Group management
   Create and manage groups in your Nubus for UCS domain,
   including nested groups, group caching, and Active Directory group synchronization.
   See :ref:`ucs-operation-groups`.

User creation wizard
   Configure the user creation wizard for functional administrators,
   including requiring a primary email address, controlling which account properties appear,
   and deactivating the wizard when you don't need it.
   See :ref:`iam-user-create-wizard`.

User activation for apps
   Activate and deactivate users or groups for *App Center* apps directly from the user account
   in the *Management UI*,
   including app-specific settings per user.
   See :ref:`iam-user-activation-apps`.

Track last sign-in time to detect inactive accounts
   Identify inactive user accounts by recording when each account last signed in.
   Activate the OpenLDAP ``lastbind`` overlay module,
   collect sign-in timestamps from all LDAP servers in the domain,
   and schedule automatic updates to keep the timestamps current.
   See :ref:`iam-last-bind`.

.. toctree::
   :caption: Contents

   password-management/index
   group-management
   user-create-wizard
   http-api
   user-activation-apps
   user-lockout
   last-bind
