.. SPDX-FileCopyrightText: 2024 - 2025 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _password-management:

*******************
Password management
*******************

This chapter covers password management in Nubus for UCS
with the following sections.

.. important::

   If your domain has Samba installed through the *Active Directory Domain Controller* app,
   you have two password policy systems, UDM and Samba domain.
   Univention recommends configuring them identically.

:ref:`password-management-policies`
   Describes the different policy types in Nubus for UCS:
   the UDM password policy and the Samba domain password policy.
   Explains when each policy applies
   and how users can change their password through the Portal,
   End User Self Service, Microsoft Windows, or Kerberos.
   Also covers the available password policy settings
   and the UCR variables for password quality checks.

:ref:`password-management-windows-client`
   Describes the Samba domain object
   for configuring password requirements in a Samba-enabled domain,
   including password length, history, age, and complexity settings.

.. toctree::

   policies
   samba-policies
   user-self-service
