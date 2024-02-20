.. SPDX-FileCopyrightText: 2021-2024 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _udm-blocklists:

Prevent reuse of user property values
=====================================

Since version TODO UCS supports block lists to prevent the reuse of user or
group property values.

This feature allows to configure block lists for UDM properties. When this
property is modified or removed from an UDM object a block list entry for the
old value of this property is created automatically. This block list entry
prevents setting this value to the property of another UDM object.

As an example imagine we want to block old values of the property
``mailPrimaryAddress`` of UDM user objects from being reused. First you have
to configure a block list for the property ``mailPrimaryAddress``. If we now
remove a user object with the ``mailPrimaryAddress`` of ``chef@mail.test`` and
change the ``mailPrimaryAddress`` of another user from ``james@mail.test`` to
``john@mail.test``, block list entries for both old values are created. These
values, ``chef@mail.test`` and ``james@mail.test``, are now blocked and can
not be set as ``mailPrimaryAddress`` on other user objects.

.. note::

   The block lists feature operates on the UDM level.

.. _udm-blocklists-activate:

Activate block lists
--------------------

Requirement for the use of block lists is UCS version TODO (at least on all
server where UDM object are managed).

On all UCS servers in the domain the |UCSUCRV|
:envvar:`directory/manager/blocklist/enabled` has to be set to ``true``.

.. _udm-blocklists-configure:

Configure block lists
---------------------

Block lists can be created, listed and removed in the UMC module
:guilabel:`Blocklists` or with the command line tool ``udm blocklists/list``.

On every block list you need to define the following properties:

.. _udm-blocklists-configure-table:

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Name
     - A free selectable name for the block list.

   * - Retention time
     - Retention time for entries in this block list (expired block list
       entries will be removed). The retention period is set using the
       following schema "1y6m3d" (which equals one year, six months and three
       days).

   * - Properties to block
     - Defines the UDM modules and properties for which this block list
       blocks values from being reused.

An example for creating a block list  on the command line would be:

.. code-block::

   $ udm blocklists/list create \
     --set name=user-and-group-emails \
     --set retentionTime=20241212000000Z \
     --append blockingProperties="users/user mailPrimaryAddress" \
     --append blockingProperties="groups/group mailAddress"

Entries in this block list block values from being reused as values for the
user property ``mailPrimaryAddress`` and the group property ``mailAddress``.


.. _udm-blocklists-entry-manage:

Manage block list entries
-------------------------

Block list entries can be managed in the UMC module :guilabel:`Blocklists`
or with the command line tool ``udm blocklists/entry``. When block lists are
activated and configured entries are created automatically when a value is
removed from an UDM object. Expired entries are automatically deleted.

Every block list entry has the following properties:

.. _udm-blocklists-entry-configure-table:

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Value
     - A ``sha256`` hash representing the value to block. When creating an
       entry this is the clear text value. Before creating the hash
       the value is converted to lower case, so that all versions, regardless
       of case, match the block list entry when it is checked.

   * - Blocked until
     - The block list entry expired after this
       `GeneralizedTime-LDAP-Syntax <ldap-generalized-time_>`_ time stamp.
       When an entry is create this is set to now + the retention time
       of the corresponding block list.

   * - Origin ID
     - The ID of the UDM object that lead to this block list entry. The value
       of this block list entry can still be used on that UDM object.

.. _udm-blocklists-expired-entries:

.. note::

   Listing block list entries gives you only the hashes of the blocked values.
   But you can search for the clear text value of a particular entry, e.g. in
   case you want to delete that entry.

   .. code-block::

      $ udm blocklists/entry list
      DN: cn=sha256:a859cd5964b6ac...,cn=emails,cn=blocklists
      DN: cn=sha256:b859cd5964b6ac...,cn=emails,cn=blocklists
      DN: cn=sha256:c859cd5964b6ac...,cn=emails,cn=blocklists

      $ udm blocklists/entry list --filter value=blocked_email@mail.test
      DN: cn=sha256:c859cd5964b6ac...,cn=emails,cn=blocklists

Expired block list entries
--------------------------

Every entry in a block list has a ``Blocked until`` property. Block list
entries are only valid until this time stamp expires. A cron job on the
|UCSPRIMARYDN| deletes expired block list entries. How often this cron job
is executed can be configured with the
:envvar:`directory/manager/blocklist/cleanup/cron`.

.. _udm-blocklists-ldap-acl:

LDAP ACLs for block lists
-------------------------

By default every UCS node in the domain and every member of the
``Domain Admins`` group can write block list entries. And everybody can read.

This can be configured on the |UCSPRIMARYDN| (and |UCSBACKUPDN|\ s)
with :envvar:`ldap/database/internal/acl/blocklists/groups/read` and
:envvar:`ldap/database/internal/acl/blocklists/groups/write`.

For example, if you want to give a user that is not member of the
``Domain Admins`` group the permission to delete block list entries, you need
to create a group with that user as member and add the LDAP DN of this group
to :envvar:`ldap/database/internal/acl/blocklists/groups/write`.
