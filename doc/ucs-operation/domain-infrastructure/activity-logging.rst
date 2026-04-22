.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _domain-activity-logging:

Domain activity logging
=======================

The :program:`Admin Diary` app from *Univention App Center* records important events in the domain.
It includes the following capabilities:

* Creation, movement, modification, and deletion of user objects and other objects
  through the Univention Directory Manager.

* Installation, update, and removal of apps.

* Server password changes.

* Start, end, and possible failures of domain joins.

* Start and end of Nubus for UCS updates.

.. _domain-activity-logging-admin-diary-components:

Admin Diary components
----------------------

The app consists of the following components:

.. _domain-activity-logging-admin-diary-backend:

Admin Diary backend
   The backend includes a customization for :program:`rsyslog`
   and writes to a central database, which defaults to PostgreSQL.
   If you have MariaDB or MySQL already installed on the target system,
   the backend uses it instead of PostgreSQL.

.. _domain-activity-logging-admin-diary-frontend:

Admin Diary frontend
   The frontend provides the *Admin Diary* management module
   to view and comment on diary entries.

.. _domain-activity-logging-view-and-search:

View and search diary entries
-----------------------------

:numref:`domain-activity-logging-figure` shows events in the *Admin Diary* management module.
By default, the module groups entries by week.
You can also filter them using the search field.

.. _domain-activity-logging-figure:

.. figure:: /images/admindiary-list.*
   :alt: Events view in the Admin Diary management module

   Events view in the *Admin Diary* management module

To view additional details about who triggered an event and when it occurred,
select the entry from the list.
A dialog similar to :numref:`domain-activity-logging-detail-figure` appears.
You can also add a comment to each event.

.. _domain-activity-logging-detail-figure:

.. figure:: /images/admindiary-detail.*
   :alt: Detail view in Admin Diary management module

   Detail view in *Admin Diary* management module

.. _domain-activity-logging-setup:

Set up Admin Diary
------------------

Install both components through *Univention App Center*.

.. _domain-activity-logging-setup-backend:

Install the backend
~~~~~~~~~~~~~~~~~~~

Use *Univention App Center* to install the *Admin Diary backend* app on exactly one Nubus for UCS system in the domain.
Complete this step before installing the frontend.

.. _domain-activity-logging-setup-frontend:

Install the frontend
~~~~~~~~~~~~~~~~~~~~

Use *Univention App Center* to install the *Admin Diary frontend* app on at least one Nubus for UCS system.

If you install the frontend on the same host as the backend,
you don't need any additional configuration.
If you install it on a different host,
see :ref:`domain-activity-logging-setup-separate-hosts`.

.. _domain-activity-logging-setup-separate-hosts:

Configure database access for separate hosts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When the frontend and backend run on different hosts,
configure the database access of the frontend manually.
The backend stores its data in a central database,
which defaults to PostgreSQL on the backend host.

For the configuration steps,
see :uv:kb:`Admin Diary - How to separate frontend and backend <11331>`.
