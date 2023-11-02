.. _domain:

***********
Domain join
***********

This section covers aspects of the domain join that administrators of Debian
GNU/Linux or Ubuntu systems need to be aware of regarding |UCS|.

|UCS| aims for multi-server environments. The first system takes the server role
of the *Primary Directory Node* in a UCS domain. A domain is a single trust
context that groups one or more entities such as computer systems or users. The
domain provides domain services to systems and users.

.. seealso::

   For more information in :cite:t:`ucs-architecture`:

   * :ref:`uv-architecture:concept-domain` about the most important concept in
     UCS.

   * :ref:`uv-architecture:concept-role` about the different roles of UCS
     systems in a UCS domain.

   * :ref:`uv-architecture:concept-permission` about the different permissions
     of default user groups.

   For more information in :cite:t:`ucs-manual`:

   * :ref:`uv-manual:system-roles`
   * :ref:`uv-manual:domain-ldap-primary-directory-node`

.. _domain-join:

Join UCS systems
================

To join a |UCS| system to an existing UCS domain, use the possibilities outlined
in :ref:`uv-manual:linux-domain-join`.

.. _rule-5:

.. admonition:: Rule #5

   Don't run :command:`univention-join` on a *Primary Directory Node*. It just
   skips.

.. _domain-join-scripts:

Join scripts
============

Services and apps that integrate with the domain, provide so-called *join
scripts*. A service's join script requires the credentials of a domain
administrator to write data to the domain database so that the administrator can
manage it.

Installing UCS components through the App Center ensures that the join
scripts run after the installation. If administrators install the same
component using the package manager, the join scripts don't run and the
administrator must run them manually afterwards.

.. _rule-6:

.. admonition:: Rule #6

   Install UCS components through the App Center.

.. seealso::

   For more information about join scripts, see the following resources in
   :cite:t:`ucs-manual`:

   * :ref:`uv-manual:linux-domain-join`
   * :ref:`uv-manual:linux-domain-join-umc`
   * :ref:`uv-manual:domain-ldap-joinscripts`

Consequences of unfinished join scripts
=======================================

Services won't work properly, or administrators can't manage them, if the join
scripts didn't run during the package installation or upgrade.

.. _rule-7:

.. admonition:: Rule #7

   Verify status and version of the join scripts in the following situations:

   * After installing software or apps.
   * After software or app updates.
   * When services aren't running as expected.

To verify status and version of join scripts, run the command
:command:`univention-check-join-status`.

To run pending join scripts, use the command
:command:`univention-run-join-scripts` as described in
:ref:`uv-manual:domain-ldap-joinscripts-execlater`. However, be careful with the
``--force`` option and the |UCS| server role on which you run the command.

.. _rule-8:

.. admonition:: Rule #8

   Never run :command:`univention-run-joinscripts --force` on a *Primary
   Directory Node*.

   The LDAP server doesn't work properly anymore and the repair is a lot of
   effort.
