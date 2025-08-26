.. SPDX-FileCopyrightText: 2025 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _da-intro:

************
Introduction
************

.. warning::

   Delegative administration is an experimental feature.
   Don't use it in production yet.
   There are still many shortcomings
   and in particular things like configuration can and will change in upcoming releases.

This document describes the concepts, setup, and configuration
of delegative administration for Univention Nubus
and wants to enable experienced Nubus administrators
to test this experimental feature.

With delegative administration Univention Nubus provides a mechanism
that enables organizations to implement a decentralized model of managing the LDAP directory through UMC and UDM HTTP REST.
It's possible to assign roles to user objects.
The roles define what a user can do to the LDAP directory through their user object,
which objects the user can read, modify, create, or delete.

A common use case is a manager or administrator for an organizational unit within the directory.
Users with such an assigned role can manage other user objects and group objects of a specific position in the directory,
for example ``ou=bremen,dc=example,dc=org``.
However, depending on the exact configuration,
users with such a role can't manage or even see objects from other positions.

..
  TODO: After the section introduction, we need some more short sections:

  Although it's in the lines in the second paragraph, we should have an
  explicit section about the audience and the required knowledge and skills.

.. _da-feedback:

Feedback
========

The Univention development team is happy to receive feedback
to improve the experimental version of the delegative administration feature
and to make it a helpful and supported addition to the Nubus product.
For general feedback, use the `feedback form <https://www.univention.com/feedback/?ext-delegative-administration=generic>`_.
For feedback on explicit sections,
use the section feedback
that appears to the right of the section heading when you mouse over it.

.. _da-technical-requirements:

Technical requirements
======================

The current implementation has the following technical requirements:

* You need a UCS system with version 5.2-2 and the latest errata updates.
* Delegative administration only supports the UCS system roles |UCSPRIMARYDN| and |UCSBACKUPDN|.

.. _da-limits:

Limits and known issues
=======================

.. note::

   Delegated administration is supported for the UMC and UDM HTTP REST API services.
   However, it is currently not available for the UDM command-line interface.


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

* Delegative administration only supports authorization between the UMC,
  the UDM HTTP REST API, and the LDAP directory.
  Specifically, it has no effect on which modules
  users can see or use in the UMC or UDM HTTP REST API,
  such as the user or group management modules.
  Rather, it only affects what users can do with these modules.
  You must configure which modules users can see and use separately.
  For information about UMC,
  see :external+uv-manual:ref:`delegated-administration`.
  For information about the UDM HTTP REST API,
  see :external+uv-nubus-kubernetes-customization:ref:`customization-api-udm-rest`.

.. _da-features:

Features
========

Delegative administration offers the following features:

* Role-based authorization checks when accessing the LDAP directory through the UMC user and group management modules.

* Administrators can define roles
  and assign them to user and group objects.
  Group members inherit the roles assigned to their group.
  Therefore, you can implement authorization based on group membership.

* Every role defines a list of permissions.
  Permissions define what a role can do in the directory.

* The UDM library checks the authorization for the roles of the signed-in user
  before accessing the directory database
  or returning directory objects from the database.

.. _da-roles:

Roles for delegative administration
===================================

UCS provides the following default roles for delegative administration:

``udm:default-roles:domain-administrator``
  Can perform CRUD operations for every object on every position in the directory.

``udm:default-roles:organizational-unit-admin``
  Can perform CRUD operations on user and group objects
  on a particular position in the directory.

``udm:default-roles:linux-ou-client-manager``
  Can perform CRUD operations on objects of type ``computers/linux``
  on a particular position in the directory.

``udm:default-roles:helpdesk-operator``
  Can reset the password for user objects
  in a particular position in the directory.

``udm:default-roles:domain-user``
  Can read his own object.
