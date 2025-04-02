.. SPDX-FileCopyrightText: 2025 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _da-intro:

************
Introduction
************

.. _da-technical-requirements:

Technical requirements
======================

The current implementation has the following technical requirements:

* You need a UCS system with version 5.2-1 and the latest errata updates.
* Delegative administration only supports the UCS system roles |UCSPRIMARYDN| and |UCSBACKUPDN|.

.. _da-limits:

Limits and known issues
=======================

As already said,
delegative administration is in an early development stages
and many things are still missing or not fully implemented.
Beware the following limitations:

* This is a minimal viable product without an update path, just for testing.
  Don't use it in production, yet.

* Use it only in UCS environments with up to 2,000 directory objects.

* The configuration and customization may break any time.

* Delegative administration is only available for the UDM modules in UMC.
  In particularly, this has no effect
  on what modules users can see and use in UMC,
  just what they can do with these modules.
  You have to separately configure
  which user can see and use which UMC module.

  .. FIXME: This item has a mixture of UDM modules, UMC modules, and UDM modules in the UDM module for UMC. It's confusing. We need to be more specific here.

  .. TODO: Refer to reader to content about how they configure which user sees which UMC module. Otherwise, we leave them alone here.

.. _da-features:

Features
========

* Administrators can define roles
  and added to user objects and group objects to them.
  Group members inherit the roles from the group object.
  Therefore, you can implement authorization based on group membership.

  .. FIXME: Is it really about authorization?

* Every role defines a list of permissions.
  Permissions define what a role can do in the directory.

* The backend of the UMC UDM modules checks the authorization for the roles of the signed-in user
  before accessing the directory database
  or returning directory objects from the database.

* Delegative administration provides the following default roles:

  ``domainadmins``
    Can manage every object.

  ``ouadmins``
    Can manage a particular position in the directory.
