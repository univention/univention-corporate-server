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
delegative administration is in an early development stage
and many things are still missing or not fully implemented,
with several missing or incomplete features.
Beware the following limitations:

* This is a minimal viable product intended for testing purposes only,
  without a stable update path for setup or configuration.
  Don't use it in production, yet.

* Use it only in UCS environments with up to 2,000 directory objects.

* The configuration and customization may break any time.

* Delegative administration is currently only implemented for authorization between UMC and the LDAP directory.
  In particularly, this has no effect on what modules a users can see and use in UMC,
  like the user or group management modules,
  just what they can do with these modules.
  You have to separately configure
  which module a user can see and use in UMC, see :external+uv-manual:ref:`delegated-administration`.

.. _da-features:

Features
========

* Role-based authorization checks when accessing the LDAP directory through the UMC user and group management modules.

* Administrators can define roles
  and assign them to user and group objects.
  Group members inherit the roles assigned to their group.
  Therefore, you can implement authorization based on group membership.

* Every role defines a list of permissions.
  Permissions define what a role can do in the directory.

* The backend of the UMC modules checks the authorization for the roles of the signed-in user
  before accessing the directory database
  or returning directory objects from the database.

* Delegative administration provides the following default roles:

  ``domainadmins``
    Can manage every object.

  ``ouadmins``
    Can manage a particular position in the directory.
