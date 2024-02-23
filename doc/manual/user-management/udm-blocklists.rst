.. SPDX-FileCopyrightText: 2021-2024 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _udm-blocklists:

Prevent reuse of user property values
=====================================

.. TODO : Add version of the erratum

.. versionadded:: 5.0-6-erratum-...

   Since :uv:erratum:`5.0x...`, UCS supports block lists to prevent the reuse of user or group
   property values.

Block lists is a module in UDM.  It allows to configure block lists for UDM
properties.  When an administrator or software modifies or removes a UDM
property on a UDM object, the block list automatically adds an entry about
this property with its value to the block list.  The entry in the block list
prevents that another UDM object can use the same value of the UDM property.
Block lists operate on the UDM level.

For example, you want to prevent that UCS reuses values of the UDM property
``mailPrimaryAddress`` of the UDM objects *user*.  You configure a block list
for the UDM property ``mailPrimaryAddress``.  If you then remove the value
``chef@example.com`` for the UDM property ``mailPrimaryAddress`` from a UDM
user object, the UDM block list creates an entry for that value.  If you
change the value from ``james@example.com`` to ``john@example.com`` for the
UDM property ``mailPrimaryAddress``, the UDM block list creates another
entries for ``james@example.com``.

UDM block lists now prevents reusing the values ``chef@example.com`` and
``james@example.com``.  You can't use them on other UDM user objects for the
UDM property ``mailPrimaryAddress``.

.. _udm-blocklists-activate:

Activate block lists
--------------------

Before you can activate the block lists, you first need to update the UCS
systems, where you manage UDM objects, to at least :uv:erratum:`5.0x...`.

Second, you need to set the |UCSUCRV|
:envvar:`directory/manager/blocklist/enabled` to ``true`` with :option:`ucr
set` on all UCS systems, where you manage UDM objects.

.. _udm-blocklists-configure:

Configure block lists
---------------------

Block lists can be created, listed and removed in the UMC module
:guilabel:`Blocklists` or with the command line tool ``udm blocklists/list``.

On every block list you need to define the following properties:

Name
   Provide a human-readable name for the block list for later identification.

Retention time
   Defines the retention time for entries in this block list.  The retention
   time is the time period that needs to expire to automatically remove entries
   from the block list.
   Use the following scheme to set the retention time:
   For example ``1m 20d`` which results in one month and twenty days.

Properties to block
   Defines the UDM modules and their properties that the block list prevents
   from reuse.

The following example for :program:`udm blocklists/list` shows how to create a
block list.  The block lists prevents the reuse of the UDM property
``mailPrimaryAddress`` for ``users/user`` objects and the UDM property
``mailAddress`` for ``groups/group`` objects.

.. code-block:: console

   $ udm blocklists/list create \
     --set name=user-and-group-emails \
     --set retentionTime=40d \
     --append blockingProperties="users/user mailPrimaryAddress" \
     --append blockingProperties="groups/group mailAddress"


.. _udm-blocklists-entry-manage:

Manage block list entries
-------------------------

You can manage block list entries in the UMC module *Blocklists*,
or through the command line tool :program:`udm blocklists/list`.

When you activated block lists,
UDM automatically creates entries in the configured block list,
when you remove a value from a UDM property of a UDM object.
UDM automatically deletes expired entries from the block list.

Every block list entry has the following properties:


Value
   A SHA-256 hash representing the value that the block list is blocking from
   reuse.  The UDM property value is a clear text value.  Before UDM creates
   the block list entry, it converts the value to lowercase text.  All
   uppercase and lowercase variants of the value then match the block list
   entry when validated by UDM.

Blocked until
   The block list entry expires after this
   `GeneralizedTime-LDAP-Syntax <ldap-generalized-time_>`_
   timestamp.

   When UDM creates a block list entry, it takes the current date and time,
   adds the configured retention time of the corresponding block list and
   writes the result to *Blocked until*.

   Changing the retention time of the block list doesn't update the *Blocked
   until* property of the block list entry.

Origin ID
   The ID of the UDM object that caused the block list entry.
   You can still use the value of the block list entry on this UDM object.

.. important::

   Listing block list entries gives you only the hashes of the blocked values.

   Nevertheless, you can search for the clear text value of a particular entry,
   for example, in case you want to delete that entry.

   .. code-block:: console

      $ udm blocklists/entry list
      DN: cn=sha256:a859cd5964b6ac...,cn=emails,cn=blocklists
      DN: cn=sha256:b859cd5964b6ac...,cn=emails,cn=blocklists
      DN: cn=sha256:c859cd5964b6ac...,cn=emails,cn=blocklists

      $ udm blocklists/entry list --filter value=blocked_email@example.com
      DN: cn=sha256:c859cd5964b6ac...,cn=emails,cn=blocklists


.. _udm-blocklists-expired-entries:

Expired block list entries
--------------------------

Every entry in a block list has a ``Blocked until`` property. Block list
entries are only valid until this time stamp expires. A cron job on the
|UCSPRIMARYDN| deletes expired block list entries. How often this cron job is
executed can be configured with the
:envvar:`directory/manager/blocklist/cleanup/cron`.  The log file
:file:`/var/log/univention/blocklist-clean-expired-entries.log` lists the
expired entries that UDM deleted.

.. _udm-blocklists-ldap-acl:

LDAP ACLs for block lists
-------------------------

By default every UCS node in the domain and every member of the ``Domain
Admins`` group can write block list entries. And everybody can read.  You can
configure the permissions on the |UCSPRIMARYDN| and the |UCSBACKUPDN|\ s with
the following |UCSUCRVs|:

* :envvar:`ldap/database/internal/acl/blocklists/groups/read`
* :envvar:`ldap/database/internal/acl/blocklists/groups/write`

For example, if you want to give a user the permission to delete block list
entries who isn't member of the ``Domain Admins`` group, you need to create a
group with that user as member and add the LDAP DN of this group to
:envvar:`ldap/database/internal/acl/blocklists/groups/write`.
