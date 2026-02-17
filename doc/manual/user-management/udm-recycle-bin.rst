.. SPDX-FileCopyrightText: 2025 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _udm-recyclebin:

Recycle Bin
===========

.. versionadded:: 5.2-3-erratum-298

   Since :uv:erratum:`5.2x298`, UCS supports a *Recycle Bin* feature for
   user and group objects in UDM.

The *Recycle Bin* is a feature in UDM
that provides a way to temporarily store deleted directory objects.
The *Recycle Bin* allows administrators
who accidentally removed UDM objects
to restore these objects to their original state.

When activated through a *Recycle Bin* policy,
UDM moves deleted objects to the *Recycle Bin* container
before it removes them from the LDAP directory.
UDM preserves the original object data along with metadata about the deletion.
You can view all existing entries in the *Recycle Bin* within UMC, UDM, and the UDM HTTP REST API.
You can restore these entries to their original state before the deletion.
UDM purges entries in the *Recycle Bin* after a configurable retention time.

This section describes how to activate, define a policy for, and manage the *Recycle Bin*.
It also provides information about automatic purge of entries, configuration,
and logging.

.. _udm-recyclebin-limitations:

Limitations
-----------

The implementation of the *Recycle Bin* has the following technical limitations:

* The *Recycle Bin* only supports the UDM types ``users/user`` and ``groups/group``.

* The *Recycle Bin* is only available for Nubus for UCS.

.. _udm-recyclebin-activate:

Activate Recycle Bin
--------------------

To activate the *Recycle Bin*,
set the |UCSUCRV| :envvar:`listener/module/recyclebin/deactivate` to ``false`` on the |UCSPRIMARYDN| and all |UCSBACKUPDN|\ s.

Then, restart the *Directory Listener* on the |UCSPRIMARYDN| with the command in
:numref:`udm-recyclebin-policy-restart-listener-listing`.

.. code-block:: console
   :caption: Restart the *Directory Listener*
   :name: udm-recyclebin-policy-restart-listener-listing

   $ systemctl restart univention-directory-listener

.. _udm-recyclebin-policy:

Recycle Bin policy
------------------

Administrators can configure the *Recycle Bin* with one or more
``Recycle Bin`` policies, see :ref:`central-policies`.

After you create a *Recycle Bin* policy
and link it to a container object in the LDAP directory,
the *Recycle Bin* configuration applies to all objects within the container.
Before removing an object, UDM checks if such a policy applies and moves the
object to the *Recycle Bin*.

The *Recycle Bin* policy has the following configuration properties:

.. _udm-recyclebin-policy-enabled:

Recycle Bin enabled
   Defines whether the *Recycle Bin* is active for objects.
   Even if a container has a linked *Recycle Bin* policy,
   you can deactivate it.

.. _udm-recyclebin-policy-udm-modules:

UDM modules to recycle
   Defines a list of UDM module types
   that the *Recycle Bin* policy applies to,
   such as ``users/user`` or ``groups/group``.

.. _udm-recyclebin-policy-ignored-object-classes:

Ignored object classes
   Defines a list of LDAP object classes
   that are exceptions for the *Recycle Bin*.
   If an administrator deletes an object
   and the object matches any of these object classes,
   UDM doesn't move the object to the *Recycle Bin* container.

.. _udm-recyclebin-policy-retention-days:

Retention days
   Defines the retention time in days
   that UDM keeps objects in the *Recycle Bin* before permanently removing them.
   You need to ensure
   that the value of the retention time is between the value of the
   :envvar:`ldap/database/internal/overlay/dds/min-ttl`
   and the
   :envvar:`ldap/database/internal/overlay/dds/max-ttl` |UCSUCRV|\ s.
   You set both variables on the |UCSPRIMARYDN|.

.. _udm-recyclebin-management:

Manage objects in the Recycle Bin
---------------------------------

Administrators can manage entries in the *Recycle Bin* with the UMC module *Recycle Bin*,
or with the command line tool :program:`udm` and the UDM module ``recyclebin/removedobject``.

You have the following actions available:

* *List* or view all existing entries in the *Recycle Bin*.
* *Delete* objects permanently.
* *Restore* objects.

Restoring objects from the *Recycle Bin*
adds them to the LDAP database in the object state
that they had before the deletion.
For example, this includes passwords and group memberships for user objects.

.. _udm-recyclebin-purge:

Automatic purge of entries in the Recycle Bin
---------------------------------------------

UDM creates entries in the *Recycle Bin*
if an administrator removes a UDM object
and the *Recycle Bin* policy applies to it.

The policy also defines a retention time,
see :ref:`udm-recyclebin-policy-retention-days`.
The *Recycle Bin* entry inherits this retention time from its policy
as a ``time-to-live`` property.
UDM automatically purges *Recycle Bin* entries that reach their ``time-to-live`` retention time.
You can no longer restore purged entries.

In Nubus, the feature *Dynamic Directory Services*
of the OpenLDAP server takes care of the cleanup.

.. _udm-recyclebin-ucr-configuration:

Configuration through UCR
-------------------------

The following reference shows the available settings for the *Recycle Bin*.
You need to change these settings on the |UCSPRIMARYDN|.

.. envvar:: listener/module/recyclebin/deactivate

   Controls whether the *Recycle Bin* is active.
   The default value is ``true``.

   To activate the *Recycle Bin*,
   see :ref:`udm-recyclebin-activate`.

.. envvar:: ldap/database/internal/overlay/dds/min-ttl

   Defines the minimum time to live (TTL) in seconds for entries in the *Recycle Bin*.
   Default is 86400 seconds, so one day.

   After you change the value, you need to restart the LDAP server,
   see :numref:`udm-recyclebin-ucr-configuration-restart-ldap-server`.

.. envvar:: ldap/database/internal/overlay/dds/max-ttl

   Defines the maximum time to live (TTL) in seconds for entries in the *Recycle Bin*.
   Default is 31536000 seconds, so 365 days.

   After you change the value, you need to restart the LDAP server,
   see :numref:`udm-recyclebin-ucr-configuration-restart-ldap-server`.

.. important::

   To restart the LDAP service, use the following steps:

   #. Validate that the UCS domain meets the following conditions:

      * No mass import of user data is in progress,
        for example through UCS\@school,
        or connector initialization with the *AD Connector* or the *S4 Connector*.

      * No UCS system is joining the domain.

      * No system or app upgrades are running.

      * Listeners and connectors are idle.

   #. Restart the LDAP server on the |UCSPRIMARYDN| with the command in
      :numref:`udm-recyclebin-ucr-configuration-restart-ldap-server`.

      .. code-block:: console
         :caption: Restart LDAP Server
         :name: udm-recyclebin-ucr-configuration-restart-ldap-server

         $ systemctl restart slapd

.. _udm-recyclebin-logging:

Logging information
-------------------

The following files contain information about the creation of entries in the *Recycle Bin*
and the restoration process.

:file:`/var/log/univention/listener.log` on the |UCSPRIMARYDN|
   Contains log information about creating entries in the *Recycle Bin*.

:file:`/var/log/univention/management-console-module-udm.log`
   Contains log information about the restoration of objects with UMC.

:file:`/var/log/univention/directory-manager-rest.log`
   Contains log information about the restoration of objects with the *UDM HTTP REST API*.
