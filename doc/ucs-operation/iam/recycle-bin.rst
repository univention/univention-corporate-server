.. SPDX-FileCopyrightText: 2025-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _management-interface-recycle-bin:

Recycle Bin
===========

.. versionadded:: 5.2-3-erratum-298

   Since :uv:erratum:`5.2x298`,
   Univention Corporate Server (UCS) supports a *Recycle Bin* feature
   for user and group objects in Univention Directory Manager (UDM).

The *Recycle Bin* temporarily stores deleted directory objects in UDM.
Administrators who accidentally remove UDM objects
can restore them with the data preserved in the *Recycle Bin*.

When you activate a *Recycle Bin* policy,
UDM moves deleted objects to the *Recycle Bin* container
before removing them from the LDAP directory.
UDM preserves the original object data
and metadata about the deletion.
You can view existing *Recycle Bin* entries
in Univention Management Console (UMC), UDM,
and the *UDM HTTP REST API*.
You can restore entries before UDM purges them
after the configured retention time.

This section describes how to activate, configure,
and manage the *Recycle Bin*.
It also provides information about automatically purging entries,
configuration, and logging.

.. _management-interface-recycle-bin-limitations:

Limitations
-----------

The *Recycle Bin* has the following limitations:

* The *Recycle Bin* supports only the UDM types ``users/user``
  and ``groups/group``.

* The *Recycle Bin* is available only in Nubus for UCS.

.. _management-interface-recycle-bin-activate:

Activate the Recycle Bin
------------------------

To activate the *Recycle Bin*,
you need administrator privileges and access to the
:term:`Primary Directory Node` and all
:term:`Backup Directory Nodes <Backup Directory Node>`.

#. On the Primary Directory Node and all
   Backup Directory Nodes,
   set the :term:`UCR variable`
   :envvar:`listener/module/recyclebin/deactivate` to ``false``.
   For instructions about setting UCR variables,
   see :ref:`system-administration-ucr`.

#. Restart the *Univention Directory Listener* on the
   Primary Directory Node with the command in
   :numref:`udm-recyclebin-policy-restart-listener-listing`.

   .. code-block:: console
      :caption: Restart the *Univention Directory Listener*
      :name: udm-recyclebin-policy-restart-listener-listing

      $ systemctl restart univention-directory-listener

   .. important::

      If you activate the *Recycle Bin* after creating user or group objects,
      the *Recycle Bin* doesn't include them
      because the listener cache has no association with those objects.
      Deleting those objects **doesn't** add them to the *Recycle Bin*.

#. To include user and group objects
   that existed before you activated the *Recycle Bin*,
   run the command in
   :numref:`udm-recyclebin-activate-re-initialize-listener-listing`
   on the Primary Directory Node.
   The command restarts the *Univention Directory Listener*
   and :spelling:word:`reinitializes` only the *Recycle Bin*.

   .. important::

      Reinitialization doesn't change objects or create entries in the *Recycle Bin*.
      While reinitialization runs,
      the *Univention Directory Listener* doesn't process other directory changes
      on the Primary Directory Node.
      The *Univention Directory Listener* processes pending directory changes
      after reinitialization.

      Reinitialization can't recover deleted objects
      that existed before you activated the *Recycle Bin*.

   .. important::

      In large environments, reinitialization can take longer.
      Schedule it during a period of low load or a maintenance window.

   .. code-block:: console
      :caption: Restart *Univention Directory Listener* to reinitialize only the *Recycle Bin*
      :name: udm-recyclebin-activate-re-initialize-listener-listing

      $ univention-directory-listener-ctrl resync recyclebin

#. To verify that reinitialization is complete,
   run the command in :numref:`udm-recyclebin-activate-listener-status-listing`.
   Confirm that the ``recyclebin`` listener module has state ``3``.
   State ``3`` indicates that the module is fully initialized and ready.
   If the module has a different state,
   verify that :envvar:`listener/module/recyclebin/deactivate` is set to ``false``
   and read :file:`/var/log/univention/listener.log`.
   You can restart the *Univention Directory Listener*
   with the command in :numref:`udm-recyclebin-policy-restart-listener-listing`.

   .. code-block:: console
      :caption: Check the listener status
      :name: udm-recyclebin-activate-listener-status-listing

      $ univention-directory-listener-ctrl status

.. _management-interface-recycle-bin-policy:

Recycle Bin policy
------------------

Administrators can configure the *Recycle Bin* with one or more
``Recycle Bin`` policies.
For instructions about creating and linking policies,
see :ref:`management-interface-udm-command-examples-policies`.

After you create a *Recycle Bin* policy
and link it to a container object in the LDAP directory,
the *Recycle Bin* configuration applies to all objects within the container.
Before removing an object,
UDM checks whether a policy applies and moves the object to the *Recycle Bin*.

The *Recycle Bin* policy has the following configuration properties:

.. _management-interface-recycle-bin-policy-enabled:

Recycle Bin enabled
   Defines whether the *Recycle Bin* is active for objects.
   Even if a container has a linked *Recycle Bin* policy,
   you can deactivate it.

.. _management-interface-recycle-bin-policy-udm-modules:

UDM modules to recycle
   Defines a list of UDM module types
   that the *Recycle Bin* policy applies to,
   such as ``users/user`` or ``groups/group``.

.. _management-interface-recycle-bin-policy-ignored-object-classes:

Ignored object classes
   Defines a list of LDAP object classes
   that are exceptions for the *Recycle Bin*.
   If an administrator deletes an object
   and the object matches any of these object classes,
   UDM doesn't move the object to the *Recycle Bin* container.

.. _management-interface-recycle-bin-policy-retention-days:

Retention days
   Defines the retention time in days
   that UDM keeps objects in the *Recycle Bin*
   before permanently removing them.
   Set the retention time to a value between the values of the
   :term:`UCR variables <UCR variable>`
   :envvar:`ldap/database/internal/overlay/dds/min-ttl`
   and :envvar:`ldap/database/internal/overlay/dds/max-ttl`.

.. _management-interface-recycle-bin-management:

Manage objects in the Recycle Bin
---------------------------------

Administrators can manage entries in the *Recycle Bin*
with the *Recycle Bin* management module
or with the command-line tool :program:`udm`
and the UDM module ``recyclebin/removedobject``.
For instructions about UDM operations,
see :ref:`management-interface-udm-command`.

The following actions are available:

* :option:`List <udm list>` all existing entries in the *Recycle Bin*.
* :option:`Delete <udm delete>` entries permanently.
* :option:`Restore <udm restore>` entries.

Restoring an entry from the *Recycle Bin*
adds it to the LDAP database with the data preserved in the *Recycle Bin*.
For user objects, this data includes passwords and group memberships.

.. _management-interface-recycle-bin-purge:

Automatically purge entries in the Recycle Bin
----------------------------------------------

UDM creates entries in the *Recycle Bin*
if an administrator removes a UDM object
and the *Recycle Bin* policy applies to it.

The policy defines the retention time.
The *Recycle Bin* entry inherits this value as its ``time-to-live`` property.
The value must be within the range that
:envvar:`ldap/database/internal/overlay/dds/min-ttl`
and :envvar:`ldap/database/internal/overlay/dds/max-ttl` define.
UDM purges *Recycle Bin* entries when their ``time-to-live`` value expires.
You can't restore purged entries.

In Nubus for UCS, the Dynamic Directory Services (DDS) overlay
of the OpenLDAP server purges expired entries.

.. _management-interface-recycle-bin-configuration:

Configuration through UCR
-------------------------

The following reference shows the available settings for the *Recycle Bin*.
You need to change these settings on the :term:`Primary Directory Node`.

.. envvar:: listener/module/recyclebin/deactivate

   Controls whether the *Recycle Bin* is active.
   The default value is ``true``.

   To activate the *Recycle Bin*,
   see :ref:`udm-recyclebin-activate`.

.. envvar:: ldap/database/internal/overlay/dds/min-ttl

   Defines the minimum time to live (TTL) in seconds
   for entries in the *Recycle Bin*.
   The default is ``86400`` seconds (1 day).

   After you change the value,
   restart the LDAP server with the command in
   :numref:`udm-recyclebin-ucr-configuration-restart-ldap-server`.

.. envvar:: ldap/database/internal/overlay/dds/max-ttl

   Defines the maximum time to live (TTL) in seconds
   for entries in the *Recycle Bin*.
   The default is ``31536000`` seconds (365 days).

   After you change the value,
   restart the LDAP server with the command in
   :numref:`udm-recyclebin-ucr-configuration-restart-ldap-server`.

.. important::

   To restart the LDAP service, complete the following steps:

   #. Verify that the UCS domain meets the following conditions:

      * No mass import of user data is in progress,
        for example through UCS\@school,
        or connector initialization with the *Active Directory Connection*
        or the *S4 Connector*.

      * No UCS system is joining the domain.

      * No system or app upgrades are running.

      * Listeners and connectors are idle.

   #. Restart the LDAP server on the :term:`Primary Directory Node`
      with the command in
      :numref:`udm-recyclebin-ucr-configuration-restart-ldap-server`.

      .. code-block:: console
         :caption: Restart the LDAP server
         :name: udm-recyclebin-ucr-configuration-restart-ldap-server

         $ systemctl restart slapd.service

   #. Verify that the LDAP server is active
      with the command in
      :numref:`udm-recyclebin-ucr-configuration-verify-ldap-server`.

      .. code-block:: console
         :caption: Verify that the LDAP server is active
         :name: udm-recyclebin-ucr-configuration-verify-ldap-server

         $ systemctl is-active slapd.service

.. _management-interface-recycle-bin-logging:

Logging information
-------------------

The following log files contain entries about creating *Recycle Bin* entries
and restoring objects:

:file:`/var/log/univention/listener.log` on the Primary Directory Node
   Contains entries about creating *Recycle Bin* entries.

:file:`/var/log/univention/management-console-module-udm.log`
   Contains entries about restoring objects with UMC.

:file:`/var/log/univention/directory-manager-rest.log`
   Contains entries about restoring objects with the *UDM HTTP REST API*.
