.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _deployment-primary-dn-resilience:

Redundancy and failover for the Primary Directory Node
======================================================

The Primary Directory Node is the central writing instance
for the directory service in a Nubus for UCS domain.
For an overview of system roles, see :ref:`domain-infrastructure-system-roles`.

A disruption to this single system represents a critical risk with significant consequences:

* Users can't authenticate to the domain.
* Administrators can't create or modify users and groups.
* Password resets and account management operations fail.
* New systems can't join the domain.
* Mail services, file sharing, and other integrated applications can't serve domain users.
* All domain members lose their ability to modify critical directory data and manage domain resources.

This page describes two complementary strategies to mitigate this risk:

Redundancy
   Distribute directory data across Backup and Replica Directory Nodes
   to ensure read access continues if the Primary becomes unavailable.

Failover
   Promote a Backup Directory Node to Primary,
   restoring write capability when the current Primary becomes unavailable.

Whether you are planning infrastructure from scratch
or recovering from an outage,
this page guides you through building
and maintaining a resilient directory service.

.. _deployment-primary-dn-resilience-fault-tolerant-setup:

Fault-tolerant domain setup
---------------------------

A Nubus for UCS domain relies on critical services
such as LDAP, DNS, Kerberos, DHCP, and Active Directory-compatible domain controllers.
To ensure these services remain available during hardware failures or maintenance,
distribute them across multiple Directory Nodes.

Consider the following when planning redundancy:

At least one Backup Directory Node
   Provides full data replication and promotion capability to a Primary Directory Node.
   Essential for production environments.

Geographic distribution
   Place Backup and Replica Directory Nodes in different locations
   for disaster recovery and local access.

Network connectivity
   Ensure all systems can reliably communicate with the Primary Directory Node.

Service distribution
   Plan which services run on which systems,
   such as LDAP, DNS, Kerberos, DHCP, and Samba.

Building a fault-tolerant domain requires two steps:

#. Install redundant Directory Nodes

   Add Backup and Replica Directory Nodes to your domain.
   For more information,
   see :external+uv-ucs-manual:ref:`domain-join`
   in :cite:t:`ucs-manual`.

#. Configure service redundancy

   Configure LDAP, Kerberos, DNS, DHCP, and Samba to use multiple servers.

The article :uv:kb:`Fail-safe domain setup <6682>` in the Univention Support database
provides detailed configuration instructions for each service.
Follow the procedures in the article after installing your Backup and Replica Directory Nodes
to complete your fault-tolerant domain configuration.

LDAP server failover
   Configure additional LDAP servers with UCR variables,
   so clients automatically fail over if the Primary Directory Node becomes unavailable.

Kerberos Key Distribution Centers
   Set up multiple Kerberos KDCs for authentication redundancy.

DNS name servers
   Configure multiple name servers to ensure name resolution continues
   during maintenance or failures.

DHCP redundancy
   Install the DHCP server app on additional systems
   to ensure network configuration remains available.

Active Directory-compatible Domain Controllers
   If you need Active Directory functionality,
   deploy the Samba component on Backup and Replica Directory Nodes
   to provide redundant domain controller functionality.

.. _deployment-primary-dn-resilience-backup-primary-promotion:

Backup to Primary promotion
---------------------------

.. highlight:: console

A Nubus for UCS domain consists of only one Primary Directory Node,
but has no limit in the number of Backup Directory Nodes.
In contrast to the Primary Directory Node,
the Backup Directory Node can't write changes to the domain data.
For descriptions about the system roles, see the following sections:

* :ref:`domain-infrastructure-system-roles-primary-directory-node`
* :ref:`domain-infrastructure-system-roles-backup-directory-node`

You can promote any Backup Directory Node to a Primary Directory Node.
The following promotion scenarios exist:

Emergency
   In an emergency, for example if the hardware of the Primary Directory Node fails.

Replacement
   To replace a fully functional Primary Directory Node with modern hardware.

.. _deployment-primary-dn-resilience-backup-primary-promotion-prepare:

Prepare backup to primary promotion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The promotion primarily involves transferring authentication-related services
such as LDAP, DNS, Kerberos, and Samba.
You need to manually adjust the installed software
through the management modules *App Center* and *Package Management*.

For example,
if the previous Primary Directory Node has the mail component installed,
the promotion process doesn't install the app on the promoted Primary Directory Node.
To minimize manual changes after the promotion,
consider :ref:`deployment-primary-dn-resilience-fault-tolerant-setup`.

.. caution::

   The promotion of a Backup Directory Node to a Primary Directory Node
   is a serious and **irreversible** configuration change.

   Before promoting:

   * Shut down the Primary Directory Node and keep it powered off during and after the promotion.
   * Compare installed packages, see :ref:`deployment-primary-dn-resilience-backup-primary-promotion-prepare-sync-ldap-schema`, and configuration, see :ref:`deployment-primary-dn-resilience-backup-primary-promotion-prepare-compare-ucr`, between Primary and Backup Directory Nodes.
   * If the Primary is unavailable in an emergency, use a file backup for comparison.

   After promoting, see :ref:`deployment-primary-dn-resilience-backup-primary-promotion-validate`:

   * Remove or update all references to the old Primary Directory Node across the domain.

To prepare the backup to primary promotion, follow these steps:

.. _deployment-primary-dn-resilience-backup-primary-promotion-prepare-sync-ldap-schema:

Synchronize LDAP schema packages
   If the Primary Directory Node has additional LDAP schema packages installed,
   you need to install them on the Backup Directory Node before you run the promotion.

   #. Save the package list from the Primary Directory Node

      To create the package list, run the command in
      :numref:`deployment-primary-dn-resilience-backup-primary-promotion-package-listing`.

      .. code-block:: console
         :caption: Save the package list
         :name: deployment-primary-dn-resilience-backup-primary-promotion-package-listing

         $ dpkg --get-selections \* > dpkg.selection

   #. List packages with LDAP schema on the Primary Directory Node

      To list all packages on the Primary Directory Node with an LDAP schema,
      run the command in
      :numref:`deployment-primary-dn-resilience-backup-primary-promotion-package-ldap-schema-listing`.

      .. code-block:: console
         :caption: List of packages with an LDAP schema
         :name: deployment-primary-dn-resilience-backup-primary-promotion-package-ldap-schema-listing

         $ dpkg -S /etc/ldap/schema/*.schema \
           /usr/share/univention-ldap/schema/*.schema

   #. Compare the package lists on the Backup Directory Node

      Compare the :file:`dpkg.selection` file with the output from the same command on the Backup Directory Node.
      Ensure that the package list only differs in the packages
      :program:`univention-server-master` and :program:`univention-server-backup`.

      If the comparison reveals other missing packages,
      you need to install them on the Backup Directory Node.
      Packages that install an LDAP schema are especially important.

   #. Install the same packages on the Backup Directory Node

      Use the :file:`dpkg.selection` file created
      on the Primary Directory Node in
      :numref:`deployment-primary-dn-resilience-backup-primary-promotion-package-listing`
      and run the command in
      :numref:`deployment-primary-dn-resilience-backup-primary-promotion-package-install-same-listing`
      on the Backup Directory Node.

      .. code-block:: console
         :caption: Install the same packages on the Backup Directory Node
         :name: deployment-primary-dn-resilience-backup-primary-promotion-package-install-same-listing

         $ dpkg --set-selections < dpkg.selection
         $ apt-get dselect-upgrade

.. _deployment-primary-dn-resilience-backup-primary-promotion-prepare-compare-ucr:

Compare Univention Configuration Registry
   You need to save the Univention Configuration Registry inventory
   so that you can compare the configuration adjustments on the promoted Primary Directory Node.

   #. Compare the following files on the Primary Directory Node with those on the Backup Directory Node:

      * :file:`/etc/univention/base.conf`
      * :file:`/etc/univention/base-forced.conf`

   #. UCS saves a copy of those files every night to
      :file:`/var/univention-backup/ucr-backup_{%Y%m%d}.tgz`.

.. _deployment-primary-dn-resilience-backup-primary-promotion-run:

Run the backup to primary promotion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To promote a Backup Directory Node to the Primary Directory Node,
run the :command:`/usr/lib/univention-ldap/univention-backup2master` command on the Backup Directory Node.
The Backup Directory Node system must reboot after the promotion.
The promotion process logs to the :file:`/var/log/univention/backup2master.log` log file.

The :command:`univention-backup2master` command runs the following steps:

#. Verify the environment:

   * The system must be a Backup Directory Node
     that has already joined the domain.

   * The Backup Directory Node can resolve the Primary Directory Node through DNS
     and reaches the repository server.

   * The Primary Directory Node is offline and not reachable anymore.

   .. TODO: Clarify, how does that work? What's verified here? How can DNS resolution be verified if the system is powered off?

#. Run component scripts in the :file:`/usr/lib/univention-backup2master/pre` directory **before** the promotion begins.
   The directory contains executable scripts for components
   that require custom handling for the Primary Directory Node.

#. Reconfigure the critical services:

   * Stop the most important services OpenLDAP, Samba, Kerberos, Univention Directory Notifier,
     and Directory Listener.

   * Change important UCR variables,
     such as :envvar:`ldap/master` and :envvar:`server/role`.

   * Make the UCS Root CA certificate available through the web server on the Backup Directory Node.

   * Start the services OpenLDAP, Samba, Kerberos, Univention Directory Notifier,
     and Listener.

#. Update the DNS service record ``kerberos-adm`` from the old Primary Directory Node
   to the promoted Primary Directory Node.

#. If present,
   remove the Univention
   :external+uv-ucs-manual:ref:`windows-s4-connector`
   from the computer object of the old Primary Directory Node
   and schedule it for re-configuration on the promoted Primary Directory Node.

   .. TODO: Update reference to S4 Connector.

#. Change the server role of the promoted Primary Directory Node
   to ``domaincontroller_master`` in the OpenLDAP directory service.
   Adjust the DNS service record ``_domaincontroller_master._tcp`` accordingly.

#. If present,
   remove all entries of the old Primary Directory Node
   from the local Samba directory service.
   Additionally, transfer the FSMO roles to the promoted Primary Directory Node.

#. Delete the computer object of the old Primary Directory Node from the OpenLDAP directory.

#. Search the OpenLDAP directory service for any remaining references
   to the old Primary Directory Node.
   Show all found references, such as DNS records,
   and suggest fixing them.

   You need to verify and confirm the suggested fixes one by one.

#. Finally, replace the package :program:`univention-server-backup`
   with :program:`univention-server-master`.

#. Run component scripts in the :file:`/usr/lib/univention-backup2master/post` directory **after** the promotion completed.
   The directory contains executable scripts for components
   that require custom handling for the Primary Directory Node.

.. _deployment-primary-dn-resilience-backup-primary-promotion-validate:

Validate the promotion
~~~~~~~~~~~~~~~~~~~~~~

After the promotion completes,
remove or update all references to the old Primary Directory Node across the domain.

The article :uv:help:`How To: backup2master <19514>` provides detailed validation procedures for:

* Checking UCR variables on all domain systems for old hostname and IP references.
* Verifying and updating DNS host entries in LDAP.
* Reviewing and updating domain policies in the *Managment UI*.

Test regular domain operations after validation to ensure correct functionality.
