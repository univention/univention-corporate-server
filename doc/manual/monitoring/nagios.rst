.. _nagios-general:

Nagios
======

With UCS 5.0 support for the Nagios server component has been
discontinued. Yet, the systems can still be monitored, e.g. by UCS 4.4
Nagios servers, as described in the UCS 4.4 manual.

.. _nagios-installation:

Installation
------------

In addition to the standard plugins provided with the installation of
the :program:`univention-nagios-client` package, additional
plugins can be subsequently installed with the following packages:

* :program:`univention-nagios-raid`: Monitoring of the software RAID status

* :program:`univention-nagios-smart`: Test of the S.M.A.R.T. status of hard
  drives

* :program:`univention-nagios-opsi`: Test of software distribution OPSI

* :program:`univention-nagios-ad-connector`: Test of the AD Connector

Some of the packages are automatically set up during installation of the
respective services. For example, if the UCS AD connector is set up, the
monitoring plugin is included automatically.

.. _nagios-preconfigured-checks:

Preconfigured Nagios checks
---------------------------

During the installation, basic Nagios tests are set up automatically for
UCS systems.

.. list-table:: Preconfigured Nagios checks
   :header-rows: 1
   :widths: 4 8

   * - Nagios service
     - Description

   * - ``UNIVENTION_PING``
     - Tests the availability of the monitored UCS system with the command
       :command:`ping`. By default an error status is attained if the response
       time exceeds 50 ms or 100 ms or package losses of 20% or 40%
       occur.

   * - ``UNIVENTION_DISK_ROOT``
     - Monitors how full the :file:`/` partition is. An error status is raised
       if the remaining free space falls below 25% or 10% by default.

   * - ``UNIVENTION_DNS``
     - Tests the function of the local DNS server and the accessibility of the
       public DNS server by querying the hostname ``www.univention.de``. If no
       DNS forwarder is defined for the UCS domain, this request fails. In this
       case, ``www.univention.de`` can be replaced with the FQDN of the
       |UCSPRIMARYDN| for example, in order to test the function of the name
       resolution.

   * - ``UNIVENTION_LDAP``
     - Monitors the LDAP server running on UCS Directory Nodes.

   * - ``UNIVENTION_LOAD``
     - Monitors the system load.

   * - ``UNIVENTION_NTP``
     - Requests the time from the NTP service on the monitored UCS system. If
       this deviates by more than ``60`` or ``120`` seconds, the error status is
       attained.

   * - ``UNIVENTION_SMTP``
     - Tests the mail server.

   * - ``UNIVENTION_SSL``
     - Tests the remaining validity period of the UCS SSL certificates. This
       plugin is only suitable for |UCSPRIMARYDN| and |UCSBACKUPDN| systems.

   * - ``UNIVENTION_SWAP``
     - Monitors the utilization of the swap partition. An error status is raised
       if the remaining free space falls below the threshold (40% or 20% by
       default).

   * - ``UNIVENTION_REPLICATION``
     - Monitors the status of the LDAP replication and recognizes the creation
       of a :file:`failed.ldif` file and the standstill of the replication and
       warns of large differences between the transaction IDs.


   * - ``UNIVENTION_NSCD``
     - Tests the availability of the name server cache daemon (NSCD). If there
       is no NSCD process running, a CRITICAL event is triggered; if more than
       one process is running, a WARNING.

   * - ``UNIVENTION_WINBIND``
     - Tests the availability of the Winbind service. If no process is running,
       a CRITICAL event is triggered.

   * - ``UNIVENTION_SMBD``
     - Tests the availability of the Samba service. If no process is running, a
       CRITICAL event is triggered.

   * - ``UNIVENTION_NMBD``
     - Tests the availability of the NMBD service, which is responsible for the
       NetBIOS service in Samba. If no process is running, a CRITICAL event is
       triggered.

   * - ``UNIVENTION_JOINSTATUS``
     - Tests the join status of a system. If a system has yet to join, a
       CRITICAL event is triggered; if non-run join scripts are available, a
       WARNING event is returned.

   * - ``UNIVENTION_KPASSWDD``
     - Tests the availability of the Kerberos password service (only available
       on Primary/|UCSBACKUPDN|\ s). If fewer or more than one process is running,
       a CRITICAL event is triggered.

   * - ``UNIVENTION_CUPS``
     - Monitors the CUPS daemon. If there is no :program:`cupsd` process running
       or the web interface on port 631 is not accessible, the CRITICAL status
       is returned.

   * - ``UNIVENTION_SQUID``
     - Monitors the Squid proxy. If no squid process is running or the Squid
       proxy is not accessible, the CRITICAL status is returned.

The following Nagios services are only available on the respective Nagios client
once additional packages have been installed (see :ref:`nagios-installation`):


.. list-table:: Additional Nagios checks
   :header-rows: 1
   :widths: 4 8

   * - Nagios service
     - Description

   * - ``UNIVENTION_OPSI``
     - Monitors the OPSI Daemon. If no OPSI process is running or the OPSI proxy
       is not accessible, the CRITICAL status is returned.

   * - ``UNIVENTION_SMART_SDA``
     - Tests the S.M.A.R.T. status of the hard drive :file:`/dev/sda`.
       Corresponding Nagios services exist for the hard drives :file:`sdb`,
       :file:`sdc` and :file:`sdd`.

   * - ``UNIVENTION_RAID``
     - Tests the status of the software RAID via :file:`/proc/mdadm` and returns
       CRITICAL if one of the hard drives in the RAID association has failed or
       WARNING if a recovery procedure is in progress.

   * - ``UNIVENTION_ADCONNECTOR``
     - Checks the status of the AD connector:

       * If no connector process is running, CRITICAL is reported.
       * If more than one process is running per connector instance, a WARNING is given.
       * If rejects occur, a WARNING is given.
       * If the AD server cannot be reached, a CRITICAL status occurs.

       The plugin can also be used in multi-connector instances; the name of the
       instance must be passed on as a parameter.
