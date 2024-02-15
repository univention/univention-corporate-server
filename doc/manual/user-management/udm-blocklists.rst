.. SPDX-FileCopyrightText: 2021-2024 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _udm-blocklists:

Prevent reuse of user property values
=====================================

Since version TODO UCS supports blocklists to prevent the reuse of user or
group property values.

This feature allows to configure blocklists for UDM properties. When this
property is modified or removed from an UDM object a blocklist entry for the
old value of this property is created automatically. This blocklist entry
prevents setting this value to the property of another UDM object.

As an example imagine we want to block old values of the property
``mailPrimaryAddress`` of UDM user objects from being reused. First you have
to configure a blocklist for the property ``mailPrimaryAddress``. If we now
remove a user object with the ``mailPrimaryAddress`` of ``chef@mail.test`` and
change the ``mailPrimaryAddress`` of another user from ``james@mail.test`` to
``john@mail.test``, blocklist entries for both old values are created. These
values, ``chef@mail.test`` and ``james@mail.test``, are now blocked and can
not be set as ``mailPrimaryAddress`` on other user objects.

.. _udm-blocklists-activate:

Activate UDM blocklists
---------------------------

Requirement for the use of blocklists is UCS version TODO (at least on all
server where UDM object are managed).

On all UCS servers in the domain the |UCSUCRV|
:envvar:`directory/manager/blocklist/enabled` has to be set to ``true``.

.. _udm-blocklists-configure:

Configure blocklists
------------------------

Blocklists can be managed in the UMC module :guilabel:`Blocklists` or with the
command line tool ``udm blocklists/list``.

On every blocklist you need to define the following properties:

.. _udm-blocklists-configure-table:

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Name
     - A free selectable name for the blocklist.

   * - Retention time
     - Retention time in `GeneralizedTime-LDAP-Syntax <ldap-generalized-time_>`_
       for entries in this blocklist (expired blocklist entries will be removed).

   * Properties to block
     - Defines the UDM modules and properties entries in the blocklist block from
       beeing reused.

An example for creating a blocklist  on the command line would be:

.. code-block::

   $ udm blocklists/list create \
     --set name=user-and-group-emails \
     --set retentionTime=20241212000000Z \
     --append blockingProperties="users/user mailPrimaryAddress" \
     --append blockingProperties="groups/group mailAddress"

Entries in this blocklist block values from being reused as values for the
user property ``mailPrimaryAddress`` and the group property ``mailAddress``.


.. _udm-blocklists-entry-manage:

Manage blocklist entries
----------------------------

.. _udm-blocklists-expired-entries:

Expired blocklist entries
-------------------------

.. _udm-blocklists-ldap-acl:

LDAP ACLs for blocklists
------------------------
