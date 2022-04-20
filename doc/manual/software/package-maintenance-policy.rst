.. _computers-softwaremanagement-maintenance-policy:

Specification of an update point using the package maintenance policy
=====================================================================

A *Maintenance* policy (see :ref:`central-policies`) in the UMC modules for
computer and domain management can be used to specify a point at which the
following steps should be performed:

* Check for available release updates to be installed (see
  :ref:`computers-softwaremanagement-release-policy`) and, if applicable,
  installation.

* Installation/deinstallation of package lists (see
  :ref:`computers-softwaremanagement-package-lists`)

* Installation of available errata updates

Alternatively, the updates can also be performed when the system is booting or
shut down.

.. list-table:: *General* tab
   :header-rows: 1

   * - Attribute
     - Description

   * - Perform maintenance after system startup
     - If this option is activated, the update steps are performed when the
       computer is started up.

   * - Perform maintenance before system shutdown
     - If this option is activated, the update steps are performed when the
       computer is shut down.

   * - Use Cron settings
     - If this flag is activated, the fields *Month*, *Day of week*, *Day*,
       *Hour* and *Minute* can be used to specify an exact time when the update
       steps should be performed.

   * - Reboot after maintenance
     - This option allows you to perform an automatic system restart after
       release updates either directly or after a specified time period of
       hours.
