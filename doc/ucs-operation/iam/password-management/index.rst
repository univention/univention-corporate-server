.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _password-management:

*******************
Password management
*******************

This chapter covers password management in Nubus for UCS.

.. important::

   If your domain has Samba installed through the *Active Directory Domain Controller* app,
   you have two password policy systems, UDM and Samba domain.
   Univention recommends configuring them identically.

:ref:`password-management-policies`
   It describes the different policy types in Nubus for UCS:
   the UDM password policy and the Samba domain password policy.
   It explains when each policy applies
   and how users can change their password through the *Portal*,
   *End User Self Service*, Microsoft Windows, or Kerberos.
   It also covers the available password policy settings
   and the UCR variables for password quality checks.

:ref:`password-management-windows-client`
   It describes the Samba domain object
   for configuring password requirements in a Samba-enabled domain,
   including password length, history, age, and complexity settings.

:ref:`password-management-hashes`
   It describes how Nubus for UCS stores and hashes user passwords.
   It covers the default SHA-512 hashing method
   and the optional bcrypt hashing method,
   including its activation requirements and tuning parameters.

:ref:`end-user-self-service`
   It describes the installation, configuration, and features of the *End User Self Service*,
   including contact information management, user self-registration with email verification,
   and user deregistration.

.. toctree::
   :caption: Contents

   policies
   samba-policies
   password-hashes
   user-self-service
