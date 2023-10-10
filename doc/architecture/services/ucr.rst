.. SPDX-FileCopyrightText: 2021-2023 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _services-ucr:

Univention Configuration Registry (UCR)
=======================================

.. index::
   see: univention configuration registry; ucr

This section describes the architecture of |UCR|. For a general overview about
system management and the role of UCR, refer to
:ref:`component-system-management`.

You find the source code for UCR at
:uv:src:`base/univention-config-registry/`.

Every UCS system installs UCR per default, regardless of the system role. UCR
stores all configuration settings of a UCS system, and also some other
information for quick lookup, for example the validity of certificates.
Administrators set values for configuration settings. Also, packages set
configuration values with default values during their installation. UCR is an
important component used everywhere, for example by UCS packages and also apps.

.. _services-ucr-architecture:

UCR architecture
----------------

.. index::
   single: ucr; architecture
   single: model; ucr python api
   single: model; ucr c api
   single: model; scripts
   single: model; apps
   single: model; services
   single: http; ucr
   single: https; ucr
   single: model; univention configuration registry
   single: interfaces; terminal / ssh
   single: interfaces; http/https

:numref:`services-ucr-architecture-model` shows the architecture overview of
UCR.

.. _services-ucr-architecture-model:

.. figure:: /images/UCR-architecture.*
   :width: 650 px

   Architecture overview of UCR

UCR provides configuration values to *Scripts*, *Apps* and *Services* with its
various configuration values from the UCR variables. Users use UCR through the
web interface of :ref:`services-umc` with *HTTP/HTTPS* and through the command
line with *Terminal / SSH*. And *UCR Python API* offers a programming interface
for UCS components and other Python programs. *UCR C API* is a small API in C
for only getting and setting UCR variables.

.. seealso::

   Administrators, refer to :cite:t:`ucs-manual`:

   * :ref:`computers-using-the-univention-management-console-web-interface`

   * :ref:`computers-using-the-command-line-front-end`

.. seealso::

   Software developers and system engineers, refer to
   :cite:t:`developer-reference`:

   * :ref:`uv-dev-ref:ucr-usage-shell`

   * :ref:`uv-dev-ref:ucr-usage-python`

   From :cite:t:`ucs-python-api`:

   * :py:mod:`univention.config_registry` for *UCR Python API*

.. _services-ucr-persistence-layer:

UCR persistence layer
---------------------

.. index::
   single: ucr; persistence layer
   single: ucr; variables
   single: ucr; templates
   single: ucr; service restart
   single: model; ucr variables
   single: model; ucr templates
   single: model; system configuration
   single: model; ucr commit
   single: model; ucr set / unset
   single: model; univention configuration registry
   single: model; ucr variable priority

:numref:`services-ucr-persistence-layer-model` shows the relation between the
active *Univention Configuration Registry (UCR) [application component]* and the
passive *UCR variables*, *UCR templates* and *System configuration files*.

.. _services-ucr-persistence-layer-model:

.. figure:: /images/UCR-architecture-persistence-layer.*
   :width: 650 px

   Architecture of Univention configuration registry persistence layer

.. index::
   single: ucr; base*.conf

UCR variables
   |UCR| is independent from any LDAP directory service. Instead, UCR uses plain
   text files as its storage backend for UCR variables and saves them in
   :file:`/etc/univention/base*.conf`. Most UCR commands read UCR variables. The
   *UCR set / unset* command changes UCR variables.

   The variables don't follow a hierarchy. The separator slash (``/``) exists
   for readability.

.. index::
   single: directory; /etc/univention/templates/files
   single: directory; /etc/univention/templates/info

UCR templates
   *UCR templates* are file templates for configuration files of various
   services in UCS. They include placeholders for the UCR variables.
   Additionally, they can include Python code for algorithms and more complex
   use cases.

   The template files locate at :file:`/etc/univention/templates/files/`.

   The mapping between which UCR template uses which UCR variables locates at
   :file:`/etc/univention/templates/info/`.

System configuration files
   When UCR variables change or administrators run the :option:`UCR commit <ucr
   commit>` command, the *UCR configuration manager* determines the affected
   system configuration files. The manager reads the respective *UCR templates*,
   parses them, replaces the variable placeholders with the values from the *UCR
   variables*, and writes *System configuration files*. UCR commands like
   :command:`ucr set` and :command:`ucr unset` automatically trigger *UCR
   commit* on all affected *System configuration files* referencing the changed
   *UCR variables*.

   UCR usually doesn't reload the affected services, because only the
   administrator knows when configuration tasks are complete and safe for
   restart.

   Exceptions to this behavior exist. For example changes to UCR variables
   starting with ``interfaces/`` trigger a restart of the networking service,
   unless you set UCR variable :envvar:`interfaces/restart/auto`\ ``=no``. Also,
   the Docker service restarts when UCR variables starting with
   ``proxy/*`` change.

   .. caution::

      Beware that UCR overwrites any manual changes to configuration files that
      are under control of UCR. Such configuration files include a header with a
      warning. Overwriting can happen during system updates or other events that
      trigger a rewriting of configuration files.

:numref:`services-ucr-workflow-set-variable` shows this general workflow after
an administrator sets a UCR variable.

.. index::
   single: role; administrator

.. _services-ucr-workflow-set-variable:

.. figure:: /images/UCR-set-variable.*

   Workflow after setting a UCR variable

   The *Administrator* triggers the event *UCR set variable* by using the UCR
   command. *UCR set / unset* writes one of the *UCR variables* and triggers a
   *UCR commit*. The *UCR commit* uses the *UCR variable priority*, the *UCR
   variables*, and the *UCR templates* to write and update the *System
   configuration*. After *UCR commit* finished, it triggers the *Configuration
   written* event.

.. seealso::

   :ref:`computers-administration-of-local-system-configuration-with-univention-configuration-registry`
      for more information about using UCR in :cite:t:`ucs-manual`.

.. seealso::

   Software developers and system engineers, refer to
   :cite:t:`developer-reference`:

   * :ref:`uv-dev-ref:ucr-usage` for more information about how to extend or develop with UCR

   * :ref:`uv-dev-ref:ucr-conffiles` for more information about writing UCR template files

   For more information about how to run code or programs when specific UCR
   variables change, refer to the following documentation:

   * :ref:`uv-dev-ref:ucr-script` for more information about how to call external programs

   * :ref:`uv-dev-ref:ucr-module` for more information about how to run Python modules

   * :ref:`uv-dev-ref:ucr-file`, refer to ``Preinst``, ``Postinst``, and
     :file:`/etc/univention/templates/scripts/`.

.. _services-ucr-priorities:

UCR variable priorities
-----------------------

.. index::
   single: ucr; variable priorities
   single: ucr; priority default
   single: ucr; priority normal
   single: ucr; priority LDAP
   single: ucr; priority scheduled
   single: ucr; priority forced
   single: ucr; priority custom

UCR uses priority layers to determine what value actually becomes effective. The
following layers from low priority to high priority exist:

Default
   The lowest priority represents the default value for UCR variables. The
   package that introduces the UCR variable sets the default value. This
   priority layer avoids default values scattered across the program code in
   UCS.

   .. versionadded:: 5.0 *Default* layer added to UCR

      Packages must explicitly register a default value in its UCR info file, so
      that the UCR variables uses the *Default* layer.

      The package's :file:`postinst` may still set the default value of UCR
      variables using :command:`ucr set name?value`. This command stores the UCR
      variable in the *Normal* layer.

      Changing a UCR variable default value the "old way" without the *Default*
      layer requires updates in multiple code locations resulting in a major
      drawback with increased effort.

.. index::
   single: role; administrator

Normal
   The priority layer *normal* becomes effective after an administrator, a
   package installation or something else explicitly sets a value for a UCR
   variable. UCR uses this layer by default, when a role like administrator or
   script uses none of the options ``--force``, ``--schedule``, or
   ``--ldap-policy`` to explicitly use another layer.

LDAP
   By default each UCS system has its own independent UCR. For managing multiple
   UCS systems, administrators can define the same *UCR policies* in LDAP and
   apply them to several UCS systems consistently. UCS stores the values of
   these settings in the priority layer *LDAP*, which takes precedence over both
   previous layers.

   By default, UCS systems apply *UCR policies* once per hour, but not at a
   fixed minute to avoid load peaks on the LDAP server. You can change the
   default value of *once per hour* with the UCR variable
   :envvar:`ldap/policy/cron`.

Scheduled
   The priority layer *scheduled* is specific to UCS\@school. It temporarily
   overwrites UCR variables.

Forced
   The priority layer *forced* has the highest priority for a regular UCS system
   by default. It applies to UCR variables set with the option ``--force``.

Custom
   The priority layer *custom* is an internal detail and not used by default.
   This layer applies **only** when the environment variable
   :envvar:`UNIVENTION_BASECONF` has a value and points to a file. Then the
   *custom* layer has the highest priority for those processes only.

.. seealso::

   System administrators refer to :cite:t:`ucs-manual`:

   * :ref:`ucr-templates-policy` for more information about how to set UCR
     variables with a policy

   * :ref:`central-policies` for more information about *Policies* in UCS

.. seealso::

   Software developers and system engineers, refer to
   :cite:t:`developer-reference`:

   * :ref:`uv-dev-ref:ucr-info` for more information about the UCR info file.

.. _services-ucr-limitations:

UCR limitations
---------------

.. index::
   single: ucr; limitations
   single: ucr; variable names
   single: ucr; ascii
   single: ucr; read access
   single: ucr; write access
   single: ucr; variable length

|UCR| has the following limitations:

#. UCR variables store and return string values.

#. Values must not contain newlines (``\n``, ``\r``) or zero bytes (``\0``).

#. UCR variable names should be restricted to alpha-numeric characters from the
   ASCII alphabet.

   UCR commands validate the variable name using the function
   :py:func:`validate_key`, that prohibits using many shell control characters.
   For more information, refer to
   :uv:src:`base/univention-config-registry/python/univention/config_registry/misc.py#L131`.

#. It's recommended, that UCR variables shouldn't exceed the length of ``1024``
   characters counting the length of the key and the length of the value plus 3:
   :math:`key.length + value.length + 3 <= 1024`

   The underlying C implementation of UCR is the reason for the limitation. The
   limit isn't enforced in the implementation.

   .. This is indeed a should as in a recommendation.

#. Access management:

   Write
      On the command line, only the user ``root`` can change UCR variables.
      UMC policies can grant proper rights to users, so that a *normal* user
      can also set UCR variables through :ref:`services-umc`.

      .. seealso::

         See also the note about the path and access rights in
         :ref:`uv-dev-ref:ucr-usage-shell` in :cite:t:`developer-reference`.

   Read
      Any user or process on a UCS system can read UCR variables, because
      :file:`/etc/univention/base*.conf` are world-readable.

      .. warning::

         Don't access UCR variables directly from the files. Always use the
         interfaces such as:

         * For administrators, see :cite:t:`ucs-manual`:

           * :ref:`web interface <computers-using-the-univention-management-console-web-interface>`
           * :ref:`command line interface <computers-using-the-command-line-front-end>`

         * For developers, see :cite:t:`developer-reference`:

           * :ref:`uv-dev-ref:shell scripts <ucr-usage-shell>`
           * :ref:`uv-dev-ref:Python interface <ucr-usage-python>`
