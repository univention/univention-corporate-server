.. SPDX-FileCopyrightText: 2024 - 2025 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

**********************
UCR variable reference
**********************

This section provides a reference for UCR variables.

.. envvar:: password/quality/credit/digits

   Defines the minimum required number of digits for passwords.
   A newly defined password must include at least this many digits.

   If the password policy has the option *Password quality check* activated,
   Nubus runs additional checks including dictionary checks,
   for password changes in Management UI (UMC), Samba, and Kerberos.

   For more information,
   see :ref:`password-management-policies`.

   :Default value: not set
   :Type: integer

.. envvar:: password/quality/credit/lower

   Defines the minimum required number of lowercase letters for passwords.
   A newly defined password must include at least this many lowercase letters.

   If the password policy has the option *Password quality check* activated,
   Nubus runs additional checks, including dictionary checks,
   for password changes in Management UI (UMC), Samba, and Kerberos.

   For more information,
   see :ref:`password-management-policies`.

   :Default value: not set
   :Type: integer

.. envvar:: password/quality/credit/other

   Defines the minimum required number of characters in the user password
   that are neither letters nor digits.
   A newly defined password must include at least this many characters.

   If the password policy has the option *Password quality check* activated,
   Nubus runs additional checks including dictionary checks,
   for password changes in Management UI (UMC), Samba, and Kerberos.

   For more information,
   see :ref:`password-management-policies`.

   :Default value: not set
   :Type: integer

.. envvar:: password/quality/credit/upper

   Defines the minimum required number of uppercase letters for passwords.
   A newly defined password must include at least this many uppercase letters.

   If the password policy has the option *Password quality check* activated,
   Nubus runs additional checks including dictionary checks,
   for password changes in Management UI (UMC), Samba, and Kerberos.

   For more information,
   see :ref:`password-management-policies`.

   :Default value: not set
   :Type: integer

.. envvar:: password/quality/forbidden/chars

   Defines the characters and digits
   that aren't allowed in passwords.
   A newly defined password must not contain these characters.

   If the password policy has the option *Password quality check* activated,
   Nubus runs additional checks including dictionary checks,
   for password changes in Management UI (UMC), Samba, and Kerberos.

   For more information,
   see :ref:`password-management-policies`.

   :Default value: not set
   :Type: string

.. envvar:: password/quality/mspolicy

   Defines the standard Microsoft password complexity criteria.

   The values ``yes``, ``1``, or ``true``
   activate the standard Microsoft password complexity criteria
   in addition to the other criteria validated with :program:`python-cracklib`.
   The value ``sufficient`` only applies the standard Microsoft password complexity criteria
   without :program:`python-cracklib`.
   The default value is unset and corresponds to the value ``false``.

   For more information,
   see :ref:`password-management-policies`.

   :Default value: not set
   :Type: string

.. envvar:: password/quality/length/min

   When changing passwords through *Univention Portal*, *Management UI*,
   *Directory Manager* or Kerberos without Samba/AD,
   UCS checks whether the new password meets the minimum length requirement.

   You can define the minimum length through the following approaches:

   * Use this UCR variable to define the minimum password length locally per Nubus for UCS node.
     The value applies to all user accounts.

   * You can use *Policy: Passwords*, type ``policies/pwhistory``,
     to override the value defined in this UCR variable.
     The values of the policy apply to user accounts
     that are subject to the policy.
     The policy takes precedence over the UCR variable.

     If the policy has *Password quality check* activated,
     :program:`python-cracklib` demands a minimum password length of 4 characters.

   The UCR variable can have the following values:

   * Integer to define the minimum password length as number of characters.

   * The value ``yes`` applies checks from :program:`python-cracklib`.

   * The value ``sufficient`` doesn't include :program:`python-cracklib` checks.

   :Default value: not set
   :Type: string

   .. seealso::

      :ref:`password-management-policies`
         for context information about password policies in Nubus for UCS.

      :external+uv-nubus-manual:ref:`nubus-user-password-management-module`
         in :cite:t:`uv-nubus-manual`
         for information about *Policy: Passwords* in the *Policies module* in the *Management UI*.

.. envvar:: password/quality/required/chars

   Defines individual characters as required for passwords.
   A newly defined password must include the specified characters.

   If the password policy has the option *Password quality check* activated,
   Nubus runs additional checks including dictionary checks,
   for password changes in Management UI (UMC), Samba, and Kerberos.

   For more information,
   see :ref:`password-management-policies`.

   :Default value: not set
   :Type: string

.. envvar:: portal/auth-mode

   Specifies the mechanism
   that the *Portal* uses to authenticate a user
   when clicking the login button in the *Portal* sidebar.
   For the values ``saml`` and ``oidc``
   the clients have to resolve the name of the SSO server
   and retrieve a trustworthy and valid certificate.

   :Default value: ``ucs``
   :Type: string
   :Possible values: ``saml``, ``oidc``, ``ucs``


.. envvar:: portal/reload-tabs-on-logout

   If activated,
   the Management UI sets up a persistent connection
   to the user's web browser.
   It notifies all Univention Portal browser tabs of a sign-out
   and causes them to reload.

   :Default value: ``false``
   :Type: boolean

.. envvar:: saml/idp/selfservice/check_email_verification

   If activated,
   users that have registered themselves
   through the :program:`Self Service` app
   need to verify their email address first
   before they can sign in.

   You must set this UCR variable
   on the :term:`UCS Primary Directory Node`
   and all :term:`UCS Backup Directory Node`\s.
   The variable has no effect on accounts
   created by user accounts in the ``Domain Admins`` group.

   For more information,
   see :ref:`end-user-self-service-registration-account-activation`.

   :Default value: ``false``
   :Type: boolean

.. envvar:: umc/http/processes

   Defines the number of *UMC Server* processes
   that Nubus for UCS starts in parallel.

   :Default value: ``1``
   :Type: Unsigned integer


.. envvar:: umc/http/session/timeout

   The web browser automatically closes the browser session
   after the defined time period in seconds.
   A new session requires a new sign-in

   :Default value: ``300``
   :Type: Unsigned integer


.. envvar:: umc/oidc/issuer

   Defines the OpenID provider issuer of this relying party entry.

   :Default value: not set
   :Type: string


.. envvar:: umc/oidc/rp/server

   Defines the fully qualified domain name of the relying party for the *UMC Server*.
   If the variable is unset,
   Nubus for UCS uses the fully qualified domain name of the UCS system and all IP addresses.

   :Default value: not set
   :Type: string


.. envvar:: umc/web/oidc/enabled

   If activated, the *UMC Server* tries the sign-in
   through OpenID Connect single sign-on
   before using a regular sign-in.

   :Default value: ``true``
   :Type: boolean


.. envvar:: umc/web/sso/enabled

   If activated, the *UMC Server* tries the sign-in
   through single sign-on
   before using a regular sign-in.

   :Default value: not set
   :Type: boolean
