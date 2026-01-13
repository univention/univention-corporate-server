.. SPDX-FileCopyrightText: 2024 - 2025 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

**********************
UCR variable reference
**********************

This section provides a reference for UCR variables.

.. envvar:: directory/manager/user_group/uniqueness

   If activated with the value ``true``
   or the variable isn't set,
   usernames and group names must be distinct.
   That means if there is a username ``test``,
   then Nubus doesn't allow a group with the name ``test``.

   For information where to this variable applies,
   see :ref:`ucs-operation-groups-management-tab-general-name`
   in :ref:`ucs-operation-groups-creation-assignment`.

   :Default value: not set
   :Possible values: ``yes``, ``no``, not set
   :Type: boolean

.. envvar:: directory/manager/web/modules/groups/group/checks/circular_dependency

   If activated with the value ``yes``
   or the variable isn't set,
   Nubus automatically detects cyclic dependencies of nested groups
   and refuses to create them.
   To deactivate the check,
   set it to the value ``no``.

   For information about where this variable applies,
   see :ref:`ucs-operation-groups-management-nested`.

   :Default value: not set
   :Possible values: ``yes``, ``no``, not set
   :Type: boolean

.. envvar:: nss/group/cachefile

   If activated,
   Nubus exports all group data to a cache file.
   The NSS module *extrausers* includes the exported data.
   This results to significant performance improvements in large environments.
   If the variable isn't set, the cache file is activated.

   For information about where this variable applies,
   see :ref:`ucs-operation-groups-management-cache`.

   :Default value: ``yes``
   :Possible values: ``yes``, ``no``, not set
   :Type: boolean

.. envvar:: nss/group/cachefile/check_member

   If activated, the group cache export verifies
   whether the exported group members are still present in the LDAP directory.
   If you only use user management methods through the *Users* and *Groups* management module,
   this validation isn't necessary and you can deactivate it.

   For information about where this variable applies,
   see :ref:`ucs-operation-groups-management-cache`.

   :Possible values: ``true``, ``false``, not set
   :Type: boolean

.. envvar:: nss/group/cachefile/invalidate_interval

   If Nubus uses the group cache file, see :envvar:`nss/group/cachefile` UCR variable,
   Nubus exports the group data to the cache file in the interval specified here.
   The interval is in cron format, see :command:`man 5 crontab`
   or `crontab(5) <https://manpages.debian.org/bookworm/cron/crontab.5.en.html>`_.

   For information about where this variable applies,
   see :ref:`ucs-operation-groups-management-cache`.

   :Type: cron

.. envvar:: nss/group/cachefile/invalidate_on_changes

   If Nubus has this variable activated and the group cache file has been enabled,
   see the :envvar:`nss/group/cachefile` UCR variable,
   the Nubus automatically regenerates the cache file
   whenever a domain administrator edits a group in the *Management UI*.
   If this variable isn't set, the functionality is enabled.

   For information about where this variable applies,
   see :ref:`ucs-operation-groups-management-cache`.

   :Default value: not set
   :Possible values: ``yes``, ``no``, not set
   :Type: boolean

.. envvar:: password/quality/credit/digits

   Defines the minimum required number of digits for passwords.
   A newly defined password must include at least this many digits.

   If the password policy has the option *Password quality check* activated,
   Nubus runs additional checks including dictionary checks,
   for password changes in *Management UI* (UMC), Samba, and Kerberos.

   For more information,
   see :ref:`password-management-policies`.

   :Default value: not set
   :Type: integer

.. envvar:: password/quality/credit/lower

   Defines the minimum required number of lowercase letters for passwords.
   A newly defined password must include at least this many lowercase letters.

   If the password policy has the option *Password quality check* activated,
   Nubus runs additional checks, including dictionary checks,
   for password changes in *Management UI* (UMC), Samba, and Kerberos.

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
   for password changes in *Management UI* (UMC), Samba, and Kerberos.

   For more information,
   see :ref:`password-management-policies`.

   :Default value: not set
   :Type: integer

.. envvar:: password/quality/credit/upper

   Defines the minimum required number of uppercase letters for passwords.
   A newly defined password must include at least this many uppercase letters.

   If the password policy has the option *Password quality check* activated,
   Nubus runs additional checks including dictionary checks,
   for password changes in *Management UI* (UMC), Samba, and Kerberos.

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
   for password changes in *Management UI* (UMC), Samba, and Kerberos.

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
   *Directory Manager* or Kerberos without Samba,
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
   for password changes in *Management UI* (UMC), Samba, and Kerberos.

   For more information,
   see :ref:`password-management-policies`.

   :Default value: not set
   :Type: string

.. envvar:: portal/auth-mode

   Specifies the mechanism
   that the *Portal* uses to authenticate a user
   when clicking the :guilabel:`Login` in the *Portal* sidebar.
   For the values ``saml`` and ``oidc``
   the clients have to resolve the name of the single sign-on server
   and retrieve a trustworthy and valid certificate.

   :Default value: ``ucs``
   :Type: string
   :Possible values: ``saml``, ``oidc``, ``ucs``


.. envvar:: portal/reload-tabs-on-logout

   If activated,
   the *Management UI* sets up a persistent connection
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
   created by user accounts from the ``Domain Admins`` group.

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
   through SAML single sign-on
   before using a regular sign-in.

   :Default value: not set
   :Type: boolean
