.. SPDX-FileCopyrightText: 2021-2023 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _services-ucs-portal:

UCS portal service
==================

.. index::
   single: ucs portal; architecture model
   single: ucs portal
   single: model; ucs group cache
   single: model; ucs portal tiles cache
   single: model; ucs portal
   single: model; ucs portal frontend
   single: model; ucs portal backend

This section describes the technical architecture of the UCS portal service.
For a general overview, see :ref:`component-portal`.

Every UCS system role installs the UCS portal and its dependencies per default.
The UCS portal generates structured data in the JSON format. The data
persistence layer consists of cache files with structured data in the JSON
format. The UCS portal needs information about the tiles on the portal and about
user memberships in user groups. Portal frontend and backend use HTTP for
communication.

You find the source code at :uv:src:`management/univention-portal/`.

:numref:`services-ucs-portal-architecture-model` shows the architecture of the
UCS Portal and the description below.

.. _services-ucs-portal-architecture-model:

.. figure:: /images/UCS-portal-architecture.*
   :alt: Architecture of the UCS portal consisting of frontend and backend
   :width: 650 px

   Architecture of the UCS Portal

The *User* uses the *UCS Portal* through a web browser with HTTP/HTTPS. The
:ref:`services-ucs-portal-front-end` and the *backend* together realize the
*UCS portal*. The :ref:`services-ucs-portal-back-end` validates the user login
with the *UMC server* and uses structured data from the *UCS Portal tile
cache* and the *UCS group cache*.

The UCS Portal uses the following technology:

.. index::
   single: technology; http request handler for Python
   single: technology; tornado
   pair: tornado; ucs portal

HTTP request handler
   The UCS Portal backend uses *Tornado* to handle the HTTP requests from the
   frontend and to serve the data to the frontend. `Tornado <tornado_>`_ is a
   Python web framework and asynchronous networking library.

.. index::
   single: technology; vue.js
   single: technology; single page application
   pair: vue.js; ucs portal

Single-page application
   *Vue.js* with *TypeScript* is the technology behind the web frontend of the
   portal. It serves the single-page application of the portal to the user.
   `Vue.js <vuejs_>`_ is a versatile JavaScript framework for building web user
   interfaces. The decision came to *Vue.js*, because it's flexible, painless,
   and not owned by a company. The implementation began with *Vue.js* 3, because
   it has full *TypeScript* support and many improvements compared to *Vue.js*
   2.

.. index::
   single: technology; typescript
   pair: typescript; ucs portal

TypeScript
   `TypeScript <typescript_>`_ is the programming language of choice for the
   frontend, because it helps to achieve a unified codebase through typing and
   linting features. Furthermore, *TypeScript* avoids common JavaScript mistakes
   and helps software developers to write cleaner code.

.. _services-ucs-portal-front-end:

Portal frontend
---------------

.. index::
   single: ucs portal; frontend

The portal frontend is a `single-page application <w-spa_>`_ and renders the
UCS portal in the users' web browser. Users see for example the portal header,
background image, a menu and various tiles consisting of logo, title, and
description.

.. index:: files; portal.json

The portal requests the structured data in :file:`portal.json` about what to
render from the :ref:`services-ucs-portal-back-end`.

.. _services-ucs-portal-back-end:

Portal backend
--------------

.. index::
   single: ucs portal; backend
   single: ucs portal; architecture model backend

The portal backend generates the data about what portal the frontend renders
for the user.

The portal backend delegates the user authentication to the UMC server. It
maintains internal caches for the portal content and the user group memberships.
It doesn't request LDAP or :ref:`services-udm` directly.

.. TODO : Add reference, once LDAP is ready.
   It doesn't request :ref:`services-ldap` or :ref:`services-udm` directly.

:numref:`services-ucs-portal-back-end-architecture-model` shows the architecture
of the portal backend. A description about the elements and their responsibility
follows.

.. _services-ucs-portal-back-end-architecture-model:

.. figure:: /images/UCS-portal-back-end-architecture.*

   Architecture of the UCS Portal backend

.. index:: ucs portal; tiles cache

UCS Portal tiles cache
   Provides structured data about the tiles configured for every portal in the
   domain. Every tile has assignments to user groups.

.. index::
   single: ucs portal; ucs group cache
   single: ucs group cache
   single: cache; group cache

UCS group cache
   Provides structured data to resolve a user and its group memberships
   including nested groups.

UMC server
   Validates user authentication for a given user.

.. index::
   pair: directory listener; ucs portal

Univention Directory Listener
   In the context of the UCS Portal, the Univention Directory Listener triggers
   the update of the :ref:`services-ucs-portal-back-end-portal-tile-cache` and
   the :ref:`services-ucs-portal-back-end-group-cache`.

.. TODO : Add reference, once Univention Directory Listener is ready.
   In the context of the UCS Portal, the :ref:`services-listener` triggers the
   update of the :ref:`services-ucs-portal-back-end-portal-tile-cache` and the
   :ref:`services-ucs-portal-back-end-group-cache`.

.. _services-ucs-portal-back-end-user-identification:

User identification
~~~~~~~~~~~~~~~~~~~

.. index::
   single: ucs portal; user identification
   single: ucs portal; identification flow
   single: role; user

:numref:`services-ucs-portal-back-end-user-identification-model` shows the basic
model of the user identification. The description follows below.

.. _services-ucs-portal-back-end-user-identification-model:

.. figure:: /images/UCS-portal-user-identification.*

   User identification in the UCS Portal

#. The user is either an anonymous user or has user information from a login.

#. The portal frontend sends an HTTP request with user information to the portal
   backend.

#. The portal backend delegates the user validation to the UMC server.

#. The UMC server returns the login status.

#. Based on the login status the portal backend generates the structured data
   for the portal frontend.

.. _services-ucs-portal-back-end-structured-data:

Structured data for portal content
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   single: ucs portal; portal.json
   single: files; portal.json
   single: ucs portal; data
   single: JSON; portal.json

The structured data in :file:`portal.json` for the portal frontend has
information for example about folders in the menu, categories in the portal main
area, portal design, the entries for the menu and the portal tiles. For example,
the `anonymous portal data from the UCS demo system <ucs-demo-portal-json_>`_.

The content depends on the user login status:

Anonymous users
   Anonymous users see portal content that's publicly available.

Signed in users
   Signed in users see public content and content depending on their group
   memberships. One user may also see different tiles than another user.

The portal backend uses the caches in the following sections to generate the
structured data.

.. _services-ucs-portal-back-end-portal-tile-cache:

UCS portal tile cache
"""""""""""""""""""""

.. index::
   single: ucs portal; tile cache

The portal tile cache has information about the content of every tile like name,
description, logo, and category. Furthermore, it knows the group assignment for
every tile.

When administrators create or modify a portal in the |UMC| module *LDAP
directory*, the Univention Directory Listener reacts on this change and triggers
the listener module responsible for the portal tile cache. The module then uses
|UDM| and recreates the portal tile cache.

.. TODO : Add reference, once Univention Directory Listener is ready.
   When administrators create or modify a portal in the |UMC| module *LDAP
   directory* the :ref:`services-listener` reacts on this change and triggers
   the listener module responsible for the portal tile cache. The module then
   uses |UDM| and recreates the portal tile cache.

.. index:: JSON; portal tile cache

The portal tile cache uses structured data, as well. The listener module saves it
in a JSON file in the file system of the UCS system.

.. _services-ucs-portal-back-end-group-cache:

UCS group cache
"""""""""""""""

.. index::
   single: ucs portal; group cache

The :ref:`services-ucs-portal-back-end-user-identification` returns information
about the user without data about the users' group memberships and nested
groups. The group cache steps in and provides a mapping for users to their
groups.

Running the user's group resolution on the fly is an expensive operation
especially for large environments.

To mitigate the expensive operation, the Univention Directory Listener triggers
the respective listener module in the *post-run* when no more changes happen to
user groups for 15 seconds. The group cache retrieves the necessary information
from the key-value store of the UCS group membership cache.

.. TODO : Add reference, once Univention Directory Listener is ready.
   To mitigate the expensive operation, the :ref:`services-listener` triggers
   the respective listener module in the *post-run* when no more changes happen
   to user groups for 15 seconds. The group cache retrieves the necessary
   information from the key-value store of the UCS group membership cache.

.. _services-ucs-portal-dependencies:

Dependencies for UCS portal
---------------------------

.. index::
   pair: ucs portal; dependency

The UCS portal depends on the Univention Directory Listener,
:ref:`services-udm`, the *UCS group membership cache*, and the *UCS Portal tile
cache*. :numref:`services-ucs-portal-dependencies-table` lists the depending
services and their packages:

.. TODO : Add reference, once Univention Directory Listener is ready.
   The UCS portal depends on the :ref:`services-listener`, :ref:`services-udm`,
   the *UCS group membership cache*, and the *UCS Portal tile cache*.
   :numref:`services-ucs-portal-dependencies-table` lists the depending services
   and their packages:

.. _services-ucs-portal-dependencies-table:

.. list-table:: Dependencies for UCS portal
   :header-rows: 1
   :widths: 6 6

   * - Service
     - Package name

   * - UCS configuration manager
     - :program:`univention-config`

   * - Univention Directory Listener
     - :program:`univention-directory-listener`

   * - UCS command-line based administration tools
     - :program:`univention-directory-manager-tools`

   * - UCS group membership cache
     - :program:`univention-group-membership-cache`

   * - :ref:`UCS management console server <services-umc>`
     - :program:`univention-management-console-server`
