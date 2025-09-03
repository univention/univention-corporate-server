.. SPDX-FileCopyrightText: 2024 - 2025 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _users-password-management:

************************
User password management
************************

This section describes the UCS appliance specific behavior
and configuration
for the user password management.
It amends :external+uv-nubus-manual:ref:`nubus-user-password-management`.
For a general introduction to user password management in Nubus,
read that section first.

.. _users-password-management-policy-types:

Password policy types
---------------------

Nubus has various types of password policy settings as outlined in this section.
What policy applies depends on who runs the password change
and if the UCS domain of UCS appliances has Samba installed
through the :program:`Active Directory Domain Controller` app.

Password Policy in UDM
   For the description,
   see :external+uv-nubus-manual:ref:`nubus-user-password-management-policy-types-policy-udm`.

   .. important::

      If you have Samba installed in your UCS domain of UCS appliances,
      design the password requirement settings of the user password policy
      identical to the Samba domain object as described in :external+uv-ucs-manual:ref:`users-password-samba`.

Password policy for the Samba domain
   If you have Samba installed in your UCS domain of UCS appliances,
   the Samba domain has its own password policy.
   The Samba password policy **always** applies, when a **user** changes their password,
   regardless of the used service,
   through the *Portal*, *End User Self Service*, *Microsoft Windows*, or *Kerberos*.

   To configure the password policy for the Samba domain, see :external+uv-ucs-manual:ref:`users-password-samba`.

   .. seealso::

      :external+uv-ucs-manual:ref:`windows-setup4` of Samba
         for more information about the installation of Samba.

      :external+uv-ucs-manual:ref:`windows-services-for-windows`
         for general information about Samba providing Services for Windows.

.. _users-password-management-change:

Change the user password
------------------------

This section amends
:external+uv-nubus-manual:ref:`nubus-user-password-management-change`
with UCS appliance specific content.

*Portal*
   See :external+uv-nubus-manual:ref:`nubus-user-password-management-change-portal`.

*End User Self Service*
   See :external+uv-nubus-manual:ref:`nubus-user-password-management-change-end-user-self-service`.

Microsoft Windows
   Users can change their user password through their Microsoft Windows client
   that's joined in the UCS domain of UCS appliances through Samba.

Kerberos
   Users can change their user password through clients
   that have joined in the UCS domain of UCS appliances through Kerberos.
   They can use the default features of those clients to change the password.

.. _users-password-management-change-policy-settings:

Password policy settings
------------------------

For the password policy settings,
first see :external+uv-nubus-manual:ref:`nubus-user-password-management-module`.
Some settings have additional options on a UCS appliance as outline in the following.

Password length
   See :external+uv-nubus-manual:ref:`nubus-user-password-management-module`.

   You can configure a default value per UCS appliance system
   through the UCR variable
   :envvar:`password/quality/length/min`.
   The setting applies to users that aren't subject to a *UDM password policy*.

.. _nubus-user-password-management-module-password-quality-check:

Password quality check
   See :external+uv-nubus-manual:ref:`nubus-user-password-management-module-password-quality-check`.

   You configure the quality checks through the following Univention Configuration Registry variables.
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
      you need to set the Univention Configuration Registry variables on **all** UCS sign-in servers.
