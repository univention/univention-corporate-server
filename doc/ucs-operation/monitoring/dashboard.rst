.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _infrastructure-monitoring-ucs-dashboard:

UCS Dashboard
=============

The *UCS Dashboard* app gives administrators a clear, up-to-date view
of the domain and individual servers.
You can access the dashboards in a web browser
to view live reports on specific aspects.

.. _infrastructure-monitoring-ucs-dashboard-installation:

Installation
------------

The UCS Dashboard consists of the following three apps:

UCS Dashboard
   Visualizes data from the central database using
   `Grafana <https://grafana.com/>`_ [1]_.

UCS Dashboard Database
   Stores metrics in a time series database using *Prometheus*.

UCS Dashboard Client
   Collects metrics from server systems using the *Prometheus Node Exporter*.

You can install the *UCS Dashboard* app from the *Univention App Center*
on any server in the domain with one of the following roles:

* :term:`Primary Directory Node`
* :term:`Backup Directory Node`
* :term:`Replica Directory Node`

The *App Center* automatically installs
the *UCS Dashboard Database* and *UCS Dashboard Client* apps
on the same server.

.. [1]
   Grafana Labs and its affiliates don't endorse, sponsor,
   or have any affiliation with Univention.

.. seealso::

   :ref:`lifecycle-app-center`
      for information about *Univention App Center*.

.. _infrastructure-monitoring-ucs-dashboard-access:

Accessing the UCS Dashboard
---------------------------

After installing the *UCS Dashboard* app,
the portal includes a link to the *UCS Dashboard*.
Alternatively, you can access the *UCS Dashboard* directly through
:samp:`https://{SERVERNAME-OR-IP}/ucs-dashboard/`.

By default, only users in the ``Domain Admins`` group can access the dashboard.
For example, the ``Administrator`` user has access by default.
To enable other users to access the *UCS Dashboard*,
add those users to the ``Domain Admins`` group.

.. _infrastructure-monitoring-ucs-dashboard-dashboards:

Dashboards
----------

The *UCS Dashboard* app provides three dashboards by default,
each showing a different aspect of your domain.

.. _infrastructure-monitoring-ucs-dashboard-domain:

Domain dashboard
~~~~~~~~~~~~~~~~

After you sign in, the *Domain Dashboard* opens by default,
as shown in :numref:`infrastructure-monitoring-ucs-dashboard-domain-figure`.
This dashboard displays general information about the domain,
such as the number of servers and users in the environment.
The dashboard also lists all servers in a table,
including the server role, installed apps,
and whether an update is available.
It shows CPU usage, memory usage, free disk space,
and the LDAP replication status across all servers.

.. _infrastructure-monitoring-ucs-dashboard-domain-figure:

.. figure:: /images/dashboard-domain.*
   :alt: Domain dashboard

   Domain dashboard

.. _infrastructure-monitoring-ucs-dashboard-server:

Server dashboard
~~~~~~~~~~~~~~~~

The *Server Dashboard* is also available by default,
as shown in :numref:`infrastructure-monitoring-ucs-dashboard-server-figure`.
This dashboard displays detailed information about individual servers,
such as CPU usage, memory usage, and network throughput.

Select a server from the *Server* drop-down.
The dashboard updates to show the metrics for the selected server.

.. _infrastructure-monitoring-ucs-dashboard-server-figure:

.. figure:: /images/dashboard-server.*
   :alt: Server dashboard

   Server dashboard

.. _infrastructure-monitoring-ucs-dashboard-alert:

Alert dashboard
~~~~~~~~~~~~~~~

The *UCS Dashboard* app includes the *Alert Dashboard* by default,
as shown in :numref:`infrastructure-monitoring-ucs-dashboard-alert-figure`.
It displays the status of all alerts configured in UCS.

.. _infrastructure-monitoring-ucs-dashboard-alert-figure:

.. figure:: /images/dashboard-alert.*
   :alt: Alert dashboard

   Alert dashboard

.. _infrastructure-monitoring-ucs-dashboard-custom:

Custom dashboards
~~~~~~~~~~~~~~~~~

You can't change the three built-in dashboards *Domain Dashboard*,
*Server Dashboard*, and *Alert Dashboard*,
because Univention provides updates for them.

Instead, you can create your own custom dashboards in Grafana.
Click :guilabel:`+` in the Grafana navigation menu
to create a dashboard and add elements to it.
