.. SPDX-FileCopyrightText: 2025 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _udm-recyclebin:

Recycle bin
===========

.. versionadded:: 5.2-3-erratum-298

   Since :uv:erratum:`5.2x298`, UCS supports a recycle bin feature for
   user and group objects in the IDM.

*Recycle bin* is a feature in UDM that provides a way to temporarily store deleted objects.
The recycle bin allows administrators, who accidentally removed UDM objects, to restore these objects to their original state.

When activated through a recycle bin policy configuration,
UDM moves deleted objects to the recycle bin container before removing them from the LDAP directory.
UDM preserves the original object data along with metadata about the deletion.

You can view all the existing entries in the recycle bin within UMC, UDM and UDM-REST
with the option to restore them to their original state before the deletion.

Entries in the recycle bin will be purged after a configurable retention time.

.. _udm-recyclebin-limitations:

Limitations
-----------

The current implementation of the recycle bin has the following technical limitations:

* The recycle bin feature supports only the UDM type ``users/user`` and ``groups/group``.

* Restoring objects in a setup with the AD/S4 Connector is not yet fully implemented.

* The recycle bin feature is not yet available for ``nubus@k8s``.

.. _udm-recyclebin-policy:

Configuration of the recycle bin
--------------------------------

To initially activate the recycle bin
you have to set the |UCSUCRV| :envvar:`listener/module/recyclebin/deactivate` to ``false`` on the |UCSPRIMARYDN| and |UCSBACKUPDN|\ s.

Afterwards the Listener needs to be restarted:

.. code-block::

   $ systemctl restart univention-directory-listener

Configuration
~~~~~~~~~~~~~

Administrators can configure the recycle bin with one or more
``Recyclebin policy`` policies, see :ref:`central-policies`.

After you created such a policy and linked it to a container object in the
LDAP directory the recycle bin configuration applies to all objects within the
container.

Before removing an object UDM checks if such a policy applies and moves the
object to the recycle bin.

The recycle bin policy has the following configuration properties:

``enabled``
   Controls whether the recycle bin is active for objects.
   So even if the policy is linked to a container, you can disable the recycle bin.

``udm_modules``
   List of UDM module types that this policy applies to, for example ``users/user`` or ``groups/group``.

``ignored_object_classes``
   This list of LDAP object classes allows you to define exceptions for the recycle bin.
   If the object that is to be removed has one of these object classes,
   the object is not moved to the recycle bin container.

``retention_time``
   Defines the retention time in days that UDM keeps objects in the recycle bin before permanently removing it.
   The value here can not be lower than the value of the |UCSUCRV| :envvar:`ldap/database/internal/overlay/dds/min-ttl` on the |UCSPRIMARYDN|.
   The value here can not be higher than the value of the |UCSUCRV| :envvar:`ldap/database/internal/overlay/dds/max-ttl` on the |UCSPRIMARYDN|.

.. _udm-recyclebin-management:

Manage objects in the recycle bin
---------------------------------

Administrators can manage entries in the recycle bin with the UMC module *Recyclebin*,
or with the command line tool :program:`udm recyclebin/removedobject`.

You can

* *list* or view all existing entries in the recycle bin.
* You can permanently *delete* entries.
* And you can *restore* objects.

Restoring objects from the recycle bin adds these objects to the LDAP database
in the state they had before the deletion. This includes for example passwords
and group membership for user objects.

Automatic purge of entries in the recycle bin
---------------------------------------------

Entries in the recycle bin are created when an UDM object is removed and a recycle bin policy applies to the UDM object.

The policy also defines a retention time.
This retention time is set on the recycle bin entry as a "time-to-live" property, by default 180 days.

Entries in the recycle bin will be automatically purged after this time has elapsed.

Configuration options
---------------------

The following references shows the available settings for recycle bin.
You need to change these settings on the |UCSPRIMARYDN|.

.. envvar:: listener/module/recyclebin/deactivate

   Activate or deactivate recycle bin listener handler (default ``true``)

   Possible values:
      ``true`` or ``false``.

   After modification you need to re-start the Listener.

.. envvar:: ldap/database/internal/overlay/dds/min-ttl

   Minimum TTL (Time To Live) in seconds for entries in the recycle bin.

   After modification you need to re-start the LDAP server.

.. envvar:: ldap/database/internal/overlay/dds/max-ttl

   Maximum TTL (Time To Live) in seconds for entries in the recycle bin.

   After modification you need to re-start the LDAP server.

Log information
---------------

The following files contain information about the creation of entries in the recycle bin and the restore.

:file:`/var/log/univention/listener.log` on the |UCSPRIMARYDN|
   Contains log information about creating entries in the recycle bin.

:file:`/var/log/univention/management-console-module-udm.log`
   Contains log information about the restore of objects with UMC.

:file:`/var/log/univention/directory-manager-rest.log`
   Contains log information about the restore of objects with UDM-REST.
