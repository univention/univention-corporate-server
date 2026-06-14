.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _monitoring:

Monitoring
==========

UCS monitoring collects metrics from managed systems and evaluates them against predefined alert conditions.
This helps administrators detect system issues early and respond to them in a timely manner.

This page describes the monitoring-specific setup and administration tasks in Nubus for UCS.
It covers the required monitoring components, the configuration of alerts,
the assignment of alerts to computers, the available preconfigured checks, and the creation of custom alerts.

For information about installing and using the *UCS Dashboard*,
see :ref:`infrastructure-monitoring-ucs-dashboard`.

.. _monitoring-installation:

Installation
------------

For installation of the *UCS Dashboard* components,
see :ref:`infrastructure-monitoring-ucs-dashboard-installation`.

In addition to the *UCS Dashboard* components,
you need to install the *Prometheus Alertmanager* app and the package :program:`univention-monitoring-client`.

For monitored Nubus for UCS systems, install the *UCS Dashboard Client* app.
The package :program:`univention-monitoring-client`
depends on the *UCS Dashboard Client* app
and is installed by default for alert functionality.

Prometheus Alertmanager
   The *Prometheus Alertmanager* app sends notifications for firing alerts,
   for example by email.
   Configure its app settings so that it can deliver notifications.

.. figure:: /images/alertmanager-appsettings.*
    :alt: Alertmanager Settings

The settings include the recipients of the email alert notifications.
Furthermore, the app settings need a value for a SMTP server to send email
notifications. The Alertmanager supports the SMTP authentication methods
``PLAIN``, ``LOGIN``, and ``CRAM-MD5`` as well as communication with TLS. No
authentication will be used, if you leave all authentication related fields of
the app settings empty.

:program:`univention-monitoring-client`
   The package :program:`univention-monitoring-client` provides standard alert
   plugins for checking the system health.

Administrators can install plugins with the following packages, that add alerts
beyond the standard plugins provided with the
:program:`univention-monitoring-client` package:

* :program:`univention-monitoring-raid`: Monitoring of the software RAID status

* :program:`univention-monitoring-smart`: Test of the S.M.A.R.T. status of hard
  drives

* :program:`univention-monitoring-opsi`: Test of software distribution OPSI

* :program:`univention-monitoring-cups`: Test of CUPS printing system

* :program:`univention-monitoring-squid`: Test of Squid proxy server

* :program:`univention-monitoring-samba`: Test of the Samba 4 services

* :program:`univention-monitoring-s4-connector`: Test of the S4 Connector

* :program:`univention-monitoring-ad-connector`: Test of the AD Connector

Some services already automatically setup their respective package
during installation. For example, if administrators setup the
:program:`UCS AD Connector`, it automatically includes the
monitoring plugin.

.. _monitoring-configuration:

Configuration
-------------

Use the *Management UI* and *Prometheus Alertmanager*
to configure alerts and alert handling.

.. _monitoring-alert-configuration:

Configure monitoring alerts
~~~~~~~~~~~~~~~~~~~~~~~~~~~

An alert defines the monitoring of a service or a status, for example free disk
space. Administrators can assign any number of computers to such an alert
object.

Administrators manage monitoring alerts in the UMC module :guilabel:`Monitoring`
with the object type *Alert*, see
:ref:`computers-management-table-monitoring-alert`. Prometheus has no LDAP
interface for the monitoring configuration. Instead, a listener module generates
the configuration files when administrators add, edit, or remove alerts.

.. figure:: /images/alert_umc.*
   :alt: Configuring an alert

   Configuring an alert

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 4 8

   * - Attribute
     - Description

   * - ``Name``
     - An unambiguous name for the alert.

   * - ``Alert group``
     - Defines the group that includes the alert. Multiple alarms can belong to
       the same group.

   * - ``Query expression``
     - Prometheus query expression, which triggers the alert. The alert triggers
       when the given query returns a non-empty vector.

       For details about the syntax, see the `Prometheus documentation
       <prometheus-query-expression_>`_.

   * - ``For clause``
     - Defines the time that the query expression result is non-empty until the
       alert triggers.

   * - ``Summary template``
     - The title of the alert, shown in alert dashboard and alert email
       notifications.

   * - ``Description template``
     - The description of the alert, shown in alert dashboard and alert email
       notifications.

   * - ``Labels``
     - *Prometheus* attaches labels to alerts. Labels help in queries for
       alerts. For example: *severity* with the value ``critical`` or
       ``warning``.

   * - ``Template Values``
     - Query expressions, descriptions and summaries can use variable values.
       For example: Reference ``max`` through ``%max%``.

.. list-table:: *Hosts* tab
   :header-rows: 1
   :widths: 4 8

   * - Attribute
     - Description

   * - ``Assigned hosts``
     - *Prometheus* executes the query on the computers referenced here. The
       listener module runs the tests for the alert. It replaces the term
       ``%instance%`` in the query expression with a regular expression that
       matches the assigned hosts.

.. _monitoring-assign-alerts:

Assign monitoring alerts to computers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*Prometheus* can monitor all computers administered with the *Management UI*.

Navigate in the *Management UI* to :guilabel:`Computers` and choose the computer you want
to activate alerts on. Choose and add all alerts you like in the tab
*Advanced settings* under *Alerts* and save your changes.

.. figure:: /images/monitoring-alerts.*
   :alt: Assigning alert to a host

   Assigning alert to a host

.. list-table:: *Advanced settings* tab
   :header-rows: 1
   :widths: 4 8

   * - Attribute
     - Description

   * - ``Assigned monitoring alerts``
     - Lists all assigned monitoring alerts for the current computer. Add or
       remove alerts.

.. _monitoring-silence-alerts:

Silence alerts
~~~~~~~~~~~~~~

To silence firing alerts for a defined time,
use the *Prometheus Alertmanager* web interface.

For more information, see the `Prometheus Alertmanager documentation
<https://prometheus.io/docs/alerting/latest/alertmanager/#silences>`_.

.. _monitoring-preconfigured-checks:

Preconfigured monitoring checks
-------------------------------

The installation automatically sets up basic monitoring tests for UCS systems.
All alerts have label *severity* with value ``critical`` or ``warning``.

.. list-table:: Preconfigured alerts
   :header-rows: 1
   :widths: 4 8

   * - Alert
     - Description

   * - ``UNIVENTION_DISK_ROOT`` and ``UNIVENTION_DISK_ROOT_WARNING``
     - Monitors how full the :file:`/` partition is. An error status is raised
       if the remaining free space falls below 25% or 10% by default.

   * - ``UNIVENTION_DNS``
     - Tests the function of the local DNS server and the accessibility of the
       public DNS server by querying the hostname ``www.univention.de``. If no
       DNS forwarder is defined for the UCS domain, this request fails. In this
       case, ``www.univention.de`` can be replaced with the FQDN of the
       :term:`Primary Directory Node` for example, in the :envvar:`monitoring/dns/lookup-domain`
       to test the function of the name resolution.

   * - ``UNIVENTION_LDAP_AUTH``
     - Monitors the LDAP server running on UCS Directory Nodes.

   * - ``UNIVENTION_LOAD`` and ``UNIVENTION_LOAD_WARNING``
     - Monitors the system load.

   * - ``UNIVENTION_NTP`` and ``UNIVENTION_NTP_WARNING``
     - Requests the time from the NTP service on the monitored UCS system. If
       this deviates by more than ``60`` or ``120`` seconds, the error status is
       attained.

   * - ``UNIVENTION_SMTP``
     - Tests if the SMTP server is reachable. The alert fires if it is not reachable.

   * - ``UNIVENTION_SSL`` and ``UNIVENTION_SSL_WARNING``
     - Tests the remaining validity period of the UCS SSL certificates. This
       plugin is only suitable for :term:`Primary Directory Node` and :term:`Backup Directory Node` systems.

   * - ``UNIVENTION_SWAP`` and ``UNIVENTION_SWAP_WARNING``
     - Monitors the utilization of the swap partition. An error status is raised
       if the remaining free space falls below the threshold (40% or 20% by
       default).

   * - ``UNIVENTION_REPLICATION`` and ``UNIVENTION_REPLICATION_WARNING``
     - Monitors the status of the LDAP replication and recognizes the creation
       of a :file:`failed.ldif` file and the standstill of the replication and
       warns of large differences between the transaction IDs.


   * - ``UNIVENTION_NSCD`` and ``UNIVENTION_NSCD2``
     - Tests the availability of the name server cache daemon (NSCD). If there
       is no NSCD process running, a *critical* alert is fired; if more than
       one process is running, a *warning* alert is fired.

   * - ``UNIVENTION_WINBIND``
     - Tests the availability of the Winbind service. If no process is running,
       a *critical* alert is fired.

   * - ``UNIVENTION_SMBD``
     - Tests the availability of the Samba service. If no process is running, an
       alert is fired.

   * - ``UNIVENTION_NMBD``
     - Tests the availability of the NMBD service, which is responsible for the
       NetBIOS service in Samba. If no process is running, an alert is fired.

   * - ``UNIVENTION_JOINSTATUS`` and ``UNIVENTION_JOINSTATUS_WARNING``
     - Tests the join status of a system. If a system has yet to join, a *critical*
       alert is fired; if non-run join scripts are available, a *warning* alert is fired.

   * - ``UNIVENTION_KPASSWDD``
     - Tests the availability of the Kerberos password service (only available
       on the :term:`Primary Directory Node` and :term:`Backup Directory Nodes <Backup Directory Node>`). If fewer or more than one process is running,
       an alert is fired.

   * - ``UNIVENTION_PACKAGE_STATUS``
     - Monitors the status of installed debian packages. If any package has status *half-installed*
       an alert is fired.

   * - ``UNIVENTION_SLAPD_MDB_MAXSIZE`` and ``UNIVENTION_SLAPD_MDB_MAXSIZE_WARNING``
     - Monitors the share of free memory pages of the *mdb* backend of SLAPD for multiple directories.

   * - ``UNIVENTION_LISTENER_MDB_MAXSIZE`` and ``UNIVENTION_LISTENER_MDB_MAXSIZE_WARNING``
     - Monitors the share of free memory pages of the *mdb* backend of SLAPD for multiple directories regarding the Univention listener.

The following monitoring alerts are only available
once additional packages have been installed (see :ref:`Monitoring installation <monitoring-installation>`).


.. list-table:: Additional alerts
   :header-rows: 1
   :widths: 4 8

   * - Alert
     - Description

   * - ``UNIVENTION_OPSI``
     - Monitors the OPSI daemon. If no OPSI process is running or the OPSI proxy
       is not accessible, the alert is fired.

   * - ``UNIVENTION_SMART_SDA``
     - Tests the S.M.A.R.T. status of the hard drive :file:`/dev/sda`.
       Corresponding alerts exist for the hard drives :file:`sdb`,
       :file:`sdc` and :file:`sdd`.

   * - ``UNIVENTION_ADCONNECTOR`` and ``UNIVENTION_ADCONNECTOR_WARNING``
     - Checks the status of the AD connector:

       * If no connector process is running, the alert is fired.
       * If more than one process is running per connector instance, a *warning* is fired.
       * If rejects occur, a *warning* alert is fired.
       * If the AD server can't be reached, an alert is fired.

       The plugin can also be used in multi-connector instances.

   * - ``UNIVENTION_CUPS``
     - Monitors the CUPS daemon. If there is no :program:`cupsd` process running
       or the web interface is not accessible, a *critical* alert is fired.

   * - ``UNIVENTION_SQUID``
     - Monitors the Squid proxy. If no squid process is running or the Squid
       proxy is not accessible, the alert is fired.

   * - ``UNIVENTION_RAID`` and ``UNIVENTION_RAID_WARNING``
     - Monitors the status of present raid devices.
       The *warning* alert is fired in case of the following RAID statuses:

       * ``Rebuilding``
       * ``Reconstruct``
       * ``Replaced Drive``
       * ``Expanding``
       * ``Warning``
       * ``Verify``

       The *critical* alert is fired in case of the following RAID statuses:

       * ``Degraded``
       * ``Dead``
       * ``Failed``
       * ``Error``
       * ``Missing``

   * - ``UNIVENTION_S4CONNECTOR`` and ``UNIVENTION_S4CONNECTOR_WARNING``
     - Monitors the status of Samba 4 server. A *warning* alert is fired if the Samba 4 is reachable and if any rejects are present.
       A *critical* alert is fired, if the server is not reachable.

   * - ``UNIVENTION_SAMBA_REPLICATION``
     - Monitors the status of the samba replication. the alert is fired if any replication failures are present.

.. _monitoring-extend:

Extend monitoring
-----------------

Use custom alert checks to collect additional metrics and define alerts for them.

.. _monitoring-add-alerts:

Create new alerts
~~~~~~~~~~~~~~~~~

This section describes how to add a custom script to collect new metrics and create new alerts.

As administrator, you can complement the preconfigured alerts supplied with UCS
with additional alerts. An alert check script exports metrics about the machine
it runs on to *Prometheus*. A *PromQL* query on metrics defines an alert in
*Prometheus*. For more information about how to write custom checks, see
`Querying basis <prometheus-query-expression_>`_.

Copy the custom alert check script into the directory
:file:`/usr/share/univention-monitoring-client/scripts/` on the UCS system that
shall export the custom metrics. Change the file mode to *executable* with
:command:`chmod a+x PLUGIN`.

All alert checks delivered by UCS use Python. Custom checks can use Perl,
Python, or Shell and don't require any external libraries or programs. All UCS
systems always provide the needed interpreters.

In contrast, if the custom alert check uses external programs or libraries,
ensure you install them on all UCS systems that use the custom alert check.

The alert check script exports one or multiple metrics by writing them to a text
file. It must write valid *Prometheus* metrics into a :file:`.prom` file in the
:file:`/var/lib/prometheus/node-exporter/` directory. *Prometheus* imports this
file.

You need to configure the custom alert in the *Management UI*, see
:ref:`monitoring-alert-configuration`. You must enter a
Prometheus expression for the metric of the script to the *Query
expression* field. To assign the custom alert to UCS systems, see
:ref:`monitoring-assign-alerts`.

.. seealso::

   Prometheus naming conventions
      `Metric and label naming <https://prometheus.io/docs/practices/naming/>`_

   Text-based format of a :file:`.prom` file
      `Exposition formats
      <https://prometheus.io/docs/instrumenting/exposition_formats/>`_

.. _prometheus-query-expression: https://prometheus.io/docs/prometheus/latest/querying/basics/
