.. SPDX-FileCopyrightText: 2024 - 2025 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _password-management-policies:

*****************
Password policies
*****************

This section describes the behavior specific to Nubus for UCS
and the configuration for the user password management.
For a general introduction to user password management in Nubus,
first read :external+uv-nubus-manual:ref:`nubus-user-password-management`
in :cite:t:`uv-nubus-manual`.

.. _password-management-policies-types:

Password policy types
---------------------

Nubus has various types of password policy settings.
Which policy applies depends on who initiates the password change
and if the domain of Nubus for UCS has Samba installed
through the :program:`Active Directory Domain Controller` app.

Password Policy in UDM
   For the description,
   see :external+uv-nubus-manual:ref:`nubus-user-password-management-policy-types-policy-udm`
   in :cite:t:`uv-nubus-manual`.

   .. important::

      If you have Samba installed in your domain of Nubus for UCS,
      configure the password requirement settings of the user password policy
      to match the Samba domain object as described in
      :ref:`password-management-windows-client`.

      UDM policies apply when administrators change passwords through administrative tools.
      Samba domain policies apply when users change their own passwords through any service.
      Because these are separate services,
      Univention recommends configuring them identically
      to ensure consistent behavior.

      If the policies are inconsistent, the services use the policies as configured.
      However, the different settings may confuse users.
      Identical settings in both policies reduce user confusion.

      .. A similar warning locates in password-management/windows.rst

Password policy for the Samba domain
   If you have Samba installed in your domain of Nubus for UCS,
   the Samba domain has its own password policy.
   The Samba password policy **always** applies when a **user** changes their password,
   regardless of which service they use:
   *Portal*, *End User Self Service*, *Microsoft Windows*, or *Kerberos*.

   To configure the password policy for the Samba domain, see :ref:`password-management-windows-client`.

   .. seealso::

      :external+uv-ucs-manual:ref:`windows-setup4`
         in :cite:t:`ucs-manual`
         for more information about installing Samba.

      :external+uv-ucs-manual:ref:`windows-services-for-windows`
         in :cite:t:`ucs-manual`
         for general information about Samba providing Services for Windows.

.. _password-management-policies-change:

Change the user password
------------------------

This section amends
:external+uv-nubus-manual:ref:`nubus-user-password-management-change`
in :cite:t:`uv-nubus-manual`
with content specific to Nubus for UCS.

*Portal*
   See :external+uv-nubus-manual:ref:`nubus-user-password-management-change-portal`
   in :cite:t:`uv-nubus-manual`.

*End User Self Service*
   See :external+uv-nubus-manual:ref:`nubus-user-password-management-change-end-user-self-service`
   in :cite:t:`uv-nubus-manual`.

Microsoft Windows
   Users can change their user password through their Microsoft Windows client
   that's joined to the domain of Nubus for UCS through Samba.

Kerberos
   Users can change their user password
   through Kerberos-joined clients in the domain of Nubus for UCS
   using the client's built-in password change feature.

.. _password-management-policies-settings:

Password policy settings
------------------------

For the password policy settings,
first read :external+uv-nubus-manual:ref:`nubus-user-password-management-module`
in :cite:t:`uv-nubus-manual`.
Some settings have additional options in Nubus for UCS as outlined in the following.

Password length
   See :external+uv-nubus-manual:ref:`nubus-user-password-management-module`
   in :cite:t:`uv-nubus-manual`.

   You can configure a default value per Nubus for UCS system
   through the UCR variable
   :envvar:`password/quality/length/min`.

   The password policy for the affected user account
   takes precedence over the UCR variable.

.. _nubus-user-password-management-module-password-quality-check:

Password quality check
   See :external+uv-nubus-manual:ref:`nubus-user-password-management-module-password-quality-check`
   in :cite:t:`uv-nubus-manual`.

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
