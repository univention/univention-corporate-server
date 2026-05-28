.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration-system-services:

Service management and system integration
=========================================

This page describes service-related configuration tasks
on systems running Nubus for UCS.
It covers service startup behavior, selected integration settings,
and the name service cache daemon.

.. _system-administration-service-management:

Manage system services
----------------------

To manage system services:

#. To open the :guilabel:`System services` management module,
   in the *Univention Portal* go to :menuselection:`System --> System services`.

#. Check the current status of a system service.

#. Start or stop the service when needed.

.. figure:: /images/umc-systemservices.*
   :alt: The System services management module shows installed services, their status, and available actions.

   Overview of system services

The list shows all services installed on the system.
Under :guilabel:`Status`,
you can see the current status and a description.
Select one or more services
and use the :guilabel:`More` menu
to start, stop, or restart a service.

By default, the system starts every service automatically.
Sometimes,
you may want to prevent a service from starting automatically
until you complete additional configuration.

* Use :guilabel:`Start manually`
  to prevent automatic startup
  while still allowing you to start the service later.

* Use :guilabel:`Start never`
  to prevent automatic and manual service starts.

.. _system-administration-ldap-server:

Configure the LDAP server
-------------------------

You can operate several LDAP servers in a Nubus for UCS domain.
Set the primary server
with the :term:`UCR variable` :envvar:`ldap/server/name`.
Set additional servers
through the :term:`UCR variable` :envvar:`ldap/server/addition`.

Alternatively, specify LDAP servers
through the *LDAP server* policy.
If a system can't reach one LDAP server,
it contacts the servers in the configured order.

By default, the installation or the domain join only sets :envvar:`ldap/server/name`.
If more than one LDAP server is available,
assign at least two LDAP servers
through the *LDAP server* policy
to improve redundancy.
In environments that span several locations,
prefer LDAP servers in the local network.

.. _system-administration-print-server:

Configure the print server
--------------------------

Specify the print server
with the :term:`UCR variable` :envvar:`cups/server`.

Alternatively, specify the server
through the *Print server* policy
in the :guilabel:`Computers` management module.

.. seealso::

   :external+uv-nubus-manual:ref:`nubus-computer-management`
      in :cite:t:`uv-nubus-manual`
      for information about the :guilabel:`Computers` management module

.. _system-administration-nscd:

Name service cache daemon
-------------------------

The *Name Service Cache Daemon* (NSCD) caches
Name Service Switch (NSS) data
to speed up repeated requests for unchanged data.
If the same request occurs again,
the system reads the data from the cache
instead of processing a complete LDAP request.

Groups are no longer cached through NSCD
for performance and stability reasons.
Instead, a local group cache stores them.
For more information, see :ref:`ucs-operation-groups-management-cache`.

Since UCS 5.2-0,
the system no longer caches user information (``passwd``) through NSCD.
Instead, the *System Security Services Daemon* (SSSD)
retrieves and caches user information.
For more information, see the `SSSD documentation <https://sssd.io/docs/introduction.html>`_.

*Univention Configuration Registry*
manages the :file:`/etc/nscd.conf` configuration file.

A hash table handles access to the cache.
Specify the hash table size
with the UCR variable :envvar:`nscd/hosts/size`.
Set the value higher than the number
of users and hosts that access the cache at the same time.
For technical reasons,
use a prime number.

With large caches,
increase the cache database size in system memory
through the UCR variable :envvar:`nscd/hosts/maxdbsize`.

By default, NSCD starts five threads.
If the system handles many accesses,
increase the number
through the :term:`UCR variable` :envvar:`nscd/threads`.

By default, the system caches a resolved hostname
for one hour.
Use the :envvar:`nscd/hosts/positive_time_to_live` UCR variable
to increase or decrease the cache period in seconds.

You may need to invalidate the NSCD cache manually.
Run the commands in :numref:`system-administration-nscd-invalidate-cache-listing`
for the relevant cache table.
Use the :term:`UCR variable` :envvar:`nscd/debug/level`
to set the verbosity of log messages.

.. code-block:: console
   :caption: Commands to manually invalidate the NSCD cache
   :name: system-administration-nscd-invalidate-cache-listing

   $ sss_cache -U
   $ nscd -i hosts
