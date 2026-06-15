.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _monitoring:

Monitoring
==========

Monitoring in Nubus for UCS collects metrics from managed systems
and compares them with predefined alert conditions.
This helps administrators detect system issues early
and respond promptly.

This page describes monitoring setup and administration tasks
for Nubus for UCS.
It covers the required monitoring components,
how to configure alerts,
how to assign alerts to computers,
which preconfigured checks are available,
and how to create custom alerts.

For information about installing and using the *UCS Dashboard*,
see :ref:`infrastructure-monitoring-ucs-dashboard`.

.. _monitoring-installation:

Installation
------------

To install the *UCS Dashboard* components,
see :ref:`infrastructure-monitoring-ucs-dashboard-installation`.

In addition to the *UCS Dashboard* components,
install the *Prometheus Alertmanager* app
on the system that sends alert notifications.
Install the :program:`univention-monitoring-client` package
on each monitored Nubus for UCS system.

On each monitored Nubus for UCS system,
install the *UCS Dashboard Client* app.
The :program:`univention-monitoring-client` package
depends on the *UCS Dashboard Client* app.
Nubus for UCS installs the :program:`univention-monitoring-client` package
by default for alert functionality.

Prometheus Alertmanager
   The *Prometheus Alertmanager* app sends notifications for firing alerts,
   for example by email.
   Configure the app settings so it can deliver them.

.. figure:: /images/alertmanager-appsettings.*
    :alt: The figure shows the Alertmanager app settings for SMTP and email recipients.

   *Alertmanager* app settings for SMTP and email recipients

Before you configure *Alertmanager*,
make sure that a reachable SMTP server
and the recipient email addresses are available.
The settings include the recipients for email alert notifications.
The app settings also require an SMTP server
for sending email notifications.
*Alertmanager* supports the SMTP authentication methods
``PLAIN``, ``LOGIN``, and ``CRAM-MD5``,
and it supports TLS communication.
If you leave all authentication-related fields empty,
*Alertmanager* doesn't use SMTP authentication.
After you save the settings,
send a test alert to verify that email notifications work.

:program:`univention-monitoring-client`
   The package :program:`univention-monitoring-client` provides standard alert
   plugins for checking the system health.

Administrators can install the following packages
to add alerts beyond the standard checks from the
:program:`univention-monitoring-client` package:

* :program:`univention-monitoring-raid`: Monitoring of the software RAID status.

* :program:`univention-monitoring-smart`: Test of the S.M.A.R.T. status of hard drives.

* :program:`univention-monitoring-opsi`: Test of software distribution OPSI.

* :program:`univention-monitoring-cups`: Test of CUPS printing system.

* :program:`univention-monitoring-squid`: Test of Squid proxy server.

* :program:`univention-monitoring-samba`: Test of the Samba 4 services.

* :program:`univention-monitoring-s4-connector`: Test of the S4 Connector.

* :program:`univention-monitoring-ad-connector`: Test of the AD Connection.

Some services already set up their required package
during installation.
For example, when you set up the
:program:`AD Connection`,
Nubus for UCS also installs the monitoring plugin.

.. _monitoring-configuration:

Configuration
-------------

Use the *Management UI* and *Alertmanager*
to configure alerts and alert handling.

.. _monitoring-alert-configuration:

Configure monitoring alerts
~~~~~~~~~~~~~~~~~~~~~~~~~~~

An alert defines the monitoring of a service or status.
For example, administrators can monitor free disk space.
Administrators can assign any number of computers to an alert object.

Administrators manage monitoring alerts
in the *Monitoring* module of the *Management UI*
with the object type *Alert*.
For more information, see
:ref:`computers-management-table-monitoring-alert`.
Note that Prometheus doesn't provide an LDAP interface
for monitoring configuration.
Instead, a listener module generates the configuration files
when administrators add, edit, or remove alerts.

.. figure:: /images/alert_umc.*
   :alt: The figure shows the Monitoring module in the Management UI with the configuration of an alert.

   Configuring an alert

.. TODO: Replace tables with description lists and use headings for cross-references

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 4 8

   * - Attribute
     - Description

   * - ``Name``
     - An unambiguous name for the alert.

   * - ``Alert group``
     - Defines the group that includes the alert.
       Multiple alerts can belong to the same group.

   * - ``Query expression``
     - Defines the Prometheus query expression that triggers the alert.
       The alert triggers when the query returns a non-empty vector.

       For details about the syntax, see the `Prometheus documentation
       <prometheus-query-expression_>`_.

   * - ``For clause``
     - Defines how long the query expression must return a non-empty result
       before the alert triggers.

   * - ``Summary template``
     - Specifies the alert title for the alert dashboard
       and for alert email notifications.

   * - ``Description template``
     - Specifies the alert description for the alert dashboard
       and for alert email notifications.

   * - ``Labels``
     - *Prometheus* attaches labels to alerts.
       These labels help you query alerts.
       For example, you can use the label *severity*
       with the value ``critical`` or ``warning``.

   * - ``Template Values``
     - Query expressions, descriptions, and summaries can use variables.
       For example, use ``%max%`` to reference the value ``max``.

.. list-table:: *Hosts* tab
   :header-rows: 1
   :widths: 4 8

   * - Attribute
     - Description

   * - ``Assigned hosts``
     - *Prometheus* runs the query on the computers listed here.
       The listener module runs the tests for the alert.
       It replaces ``%instance%`` in the query expression
       with a regular expression that matches the assigned hosts.

.. _monitoring-assign-alerts:

Assign monitoring alerts to computers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*Prometheus* can monitor all computers
that you administer through the *Management UI*.

To assign monitoring alerts to a computer,
do the following:

#. In the *Management UI*,
   go to :guilabel:`Computers`
   and select the computer.

#. On the *Advanced settings* tab,
   under *Alerts*,
   add the monitoring alerts that you want to assign.

#. Save your changes.

#. Verify that the assigned alerts appear
   in the *Assigned monitoring alerts* list.

.. figure:: /images/monitoring-alerts.*
   :alt: The figure shows the assignment of monitoring alerts to a computer.

   Assigning alert to a host

.. list-table:: *Advanced settings* tab
   :header-rows: 1
   :widths: 4 8

   * - Attribute
     - Description

   * - ``Assigned monitoring alerts``
     - Lists the monitoring alerts assigned to the current computer.
       You can add or remove alerts here.

.. _monitoring-silence-alerts:

Silence alerts
~~~~~~~~~~~~~~

To silence firing alerts for a specific period,
use the *Alertmanager* web interface.

For more information about silences,
see the `Prometheus Alertmanager documentation
<https://prometheus.io/docs/alerting/latest/alertmanager/#silences>`_.

.. _monitoring-preconfigured-checks:

Preconfigured monitoring checks
-------------------------------

Nubus for UCS sets up basic monitoring tests automatically.
All alerts use the *severity* label
with the value ``critical`` or ``warning``.

.. list-table:: Preconfigured alerts
   :header-rows: 1
   :widths: 4 8

   * - Alert
     - Description

   * - ``UNIVENTION_DISK_ROOT`` and ``UNIVENTION_DISK_ROOT_WARNING``
     - Monitors how full the :file:`/` partition is.
       The alert fires if the remaining free space falls below 25% or 10%
       by default.

   * - ``UNIVENTION_DNS``
     - Tests the local DNS server
       and checks whether the public DNS server resolves the hostname
       ``www.univention.de``.
       If the UCS domain has no DNS forwarder, the request fails.
       In that case, you can use the FQDN of the
       :term:`Primary Directory Node`,
       for example, by setting the :envvar:`monitoring/dns/lookup-domain`
       variable, to test name resolution.

   * - ``UNIVENTION_LDAP_AUTH``
     - Monitors the LDAP server on UCS Directory Nodes.

   * - ``UNIVENTION_LOAD`` and ``UNIVENTION_LOAD_WARNING``
     - Monitors the system load.

   * - ``UNIVENTION_NTP`` and ``UNIVENTION_NTP_WARNING``
     - Requests the time from the NTP service on the monitored UCS system.
       If the time differs by more than ``60`` or ``120`` seconds,
       the alert fires.

   * - ``UNIVENTION_SMTP``
     - Tests whether the SMTP server is reachable.
       The alert fires if the server isn't reachable.

   * - ``UNIVENTION_SSL`` and ``UNIVENTION_SSL_WARNING``
     - Tests how long the Nubus for UCS TLS certificates remain valid.
       Use this plugin only on :term:`Primary Directory Node`
       and :term:`Backup Directory Node` systems.

   * - ``UNIVENTION_SWAP`` and ``UNIVENTION_SWAP_WARNING``
     - Monitors the utilization of the swap partition.
       The alert fires if the remaining free space falls below the threshold
       of 40% or 20% by default.

   * - ``UNIVENTION_REPLICATION`` and ``UNIVENTION_REPLICATION_WARNING``
     - Monitors LDAP replication.
       The alert detects a :file:`failed.ldif` file,
       replication standstills,
       and large differences between transaction IDs.

   * - ``UNIVENTION_NSCD`` and ``UNIVENTION_NSCD2``
     - Tests the availability of the nameserver cache daemon (NSCD).
       If no NSCD process runs, the check triggers a *critical* alert.
       If more than one process runs,
       the check triggers a *warning* alert.

   * - ``UNIVENTION_WINBIND``
     - Tests the availability of the Winbind service.
       If no process runs, the check triggers a *critical* alert.

   * - ``UNIVENTION_SMBD``
     - Tests the availability of the Samba service.
       If no process runs, the check triggers an alert.

   * - ``UNIVENTION_NMBD``
     - Tests the availability of the NMBD service,
       which handles the NetBIOS service in Samba.
       If no process runs, the check triggers an alert.

   * - ``UNIVENTION_JOINSTATUS`` and ``UNIVENTION_JOINSTATUS_WARNING``
     - Tests the join status of a system.
       If the system hasn't joined yet,
       the check triggers a *critical* alert.
       If join scripts haven't run,
       the check triggers a *warning* alert.

   * - ``UNIVENTION_KPASSWDD``
     - Tests the availability of the Kerberos password service.
       Use this check only on :term:`Primary Directory Node`
       and :term:`Backup Directory Nodes <Backup Directory Node>`.
       If the service doesn't run exactly one process,
       the check triggers an alert.

   * - ``UNIVENTION_PACKAGE_STATUS``
     - Monitors the status of installed Debian packages.
       If any package has the status *half-installed*,
       the check triggers an alert.

   * - ``UNIVENTION_SLAPD_MDB_MAXSIZE`` and ``UNIVENTION_SLAPD_MDB_MAXSIZE_WARNING``
     - Monitors the proportion of free memory pages
       in the *mdb* backend of SLAPD
       across multiple directories.

   * - ``UNIVENTION_LISTENER_MDB_MAXSIZE`` and ``UNIVENTION_LISTENER_MDB_MAXSIZE_WARNING``
     - Monitors the proportion of free memory pages
       in the *mdb* backend of SLAPD
       across multiple directories that the Listener uses.

Additional monitoring alerts are available
after you install the required packages.
For installation details,
see :ref:`monitoring-installation`.

.. list-table:: Additional alerts
   :header-rows: 1
   :widths: 4 8

   * - Alert
     - Description

   * - ``UNIVENTION_OPSI``
     - Monitors the OPSI daemon.
       If no OPSI process runs
       or the OPSI proxy isn't accessible,
       the alert fires.

   * - ``UNIVENTION_SMART_SDA``
     - Tests the S.M.A.R.T. status of the hard drive :file:`/dev/sda`.
       Corresponding alerts are available for the hard drives
       :file:`sdb`, :file:`sdc`, and :file:`sdd`.

   * - ``UNIVENTION_ADCONNECTOR`` and ``UNIVENTION_ADCONNECTOR_WARNING``
     - Monitors the status of the Active Directory Connection:

       * If no connector process runs, the alert fires.
       * If more than one process runs per connector instance,
         the check triggers a *warning* alert.
       * If rejects occur, the check triggers a *warning* alert.
       * If the AD server isn't reachable, the alert fires.

       You can use this plugin in multi-connector instances.

   * - ``UNIVENTION_CUPS``
     - Monitors the CUPS daemon.
       If no :program:`cupsd` process runs
       or the web interface isn't accessible,
       the check triggers a *critical* alert.

   * - ``UNIVENTION_SQUID``
     - Monitors the Squid proxy.
       If no Squid process runs
       or the Squid proxy isn't accessible,
       the alert fires.

   * - ``UNIVENTION_RAID`` and ``UNIVENTION_RAID_WARNING``
     - Monitors the status of existing RAID devices.
       The check triggers a *warning* alert
       for the following RAID statuses:

       * ``Rebuilding``
       * ``Reconstruct``
       * ``Replaced Drive``
       * ``Expanding``
       * ``Warning``
       * ``Verify``

       The check triggers a *critical* alert
       for the following RAID statuses:

       * ``Degraded``
       * ``Dead``
       * ``Failed``
       * ``Error``
       * ``Missing``

   * - ``UNIVENTION_S4CONNECTOR`` and ``UNIVENTION_S4CONNECTOR_WARNING``
     - Monitors the Samba 4 server.
       If the server is reachable and rejects are present,
       the check triggers a *warning* alert.
       If the server isn't reachable,
       the check triggers a *critical* alert.

   * - ``UNIVENTION_SAMBA_REPLICATION``
     - Monitors Samba replication.
       The alert fires if replication failures occur.

.. _monitoring-extend:

Extend monitoring
-----------------

Use custom alert checks to collect additional metrics
and define alerts for them.

.. _monitoring-add-alerts:

Create new alerts
~~~~~~~~~~~~~~~~~

Create a custom alert
when you want to collect additional metrics
and monitor them in *Prometheus*.

Before you begin, make sure that:

* you have administrative access to the target Nubus for UCS system
* the target system includes the required monitoring components
* every target system includes the external programs or libraries
  that your custom check uses

Custom alert checks export metrics from the local system to *Prometheus*.
A *PromQL* query uses these metrics to define the alert.
For more information about writing custom checks,
see the `Prometheus documentation <prometheus-query-expression_>`_.

To create a custom alert, do the following:

#. Copy the custom alert check script to
   :file:`/usr/share/univention-monitoring-client/scripts/`
   on the target Nubus for UCS system.

#. Replace ``PLUGIN`` with the filename of your custom alert check script.
   Then make the script executable:

   :command:`chmod a+x PLUGIN`

#. Write valid *Prometheus* metrics
   to a :file:`.prom` file in
   :file:`/var/lib/prometheus/node-exporter/`.

#. In the *Management UI*,
   configure the custom alert.
   For details, see :ref:`monitoring-alert-configuration`.

#. Enter the Prometheus expression for the script metric
   in the *Query expression* field.

#. Assign the custom alert to the required systems.
   For details, see :ref:`monitoring-assign-alerts`.

#. Verify that *Prometheus* reads the exported metrics.
   For example, confirm that the metric appears in Prometheus
   and that the alert is available in the alert configuration.

All alert checks that Nubus for UCS provides use Python.
Custom checks can use Perl, Python, or Shell.
They don't require external libraries or programs
unless your script uses them.

.. seealso::

   Prometheus naming conventions
      `Metric and label naming <https://prometheus.io/docs/practices/naming/>`_

   Text-based format of a :file:`.prom` file
      `Exposition formats
      <https://prometheus.io/docs/instrumenting/exposition_formats/>`_

.. _prometheus-query-expression: https://prometheus.io/docs/prometheus/latest/querying/basics/
