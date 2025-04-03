.. SPDX-FileCopyrightText: 2025 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _da-start:

#####################################################################
Univention Corporate Server - Delegative administration documentation
#####################################################################

.. warning::

   Delegative administration is an experimental feature.
   Don't use it in production yet.
   There are still many shortcomings
   and in particular things like configuration can and will change in the future.

This document describes the concepts, setup, and configuration
of delegative administration for Univention Nubus
and wants to enable experienced Nubus administrators
to test this experimental feature.

With delegative administration Univention Nubus provides a mechanism
that enables organizations to implement a decentralized model of managing the LDAP directory through UMC.

It's possible to assign roles to user objects.
The roles define what an user object can do to the LDAP directory,
which objects the user can read, modify, create, or delete.

A common use case is a manager or administrator for an organizational unit within the directory.
Users with such an assigned role are able to manage other user and group objects of a specific position in the directory,
such as ``ou=bremen,dc=ldap,dc=base``.
However, depending on the exact configuration,
users with such a role can't manage or even see objects from other positions.

The Univention development team is happy to receive feedback
to improve the experimental version of delegative administration
and to make it a useful and supported addition to the Nubus product.
For general feedback, use the `feedback form <https://www.univention.com/feedback/?ext-delegative-administration=generic>`_.

.. toctree::
   :numbered: 4
   :caption: Contents

   intro
   setup
   concepts
   troubleshooting
   configuration
   bibliography
