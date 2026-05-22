.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration-system-services:

Service management and system integration
=========================================

This page describes service-related configuration tasks on Nubus for UCS systems.
It covers service startup behavior, selected integration settings,
and the name service cache daemon.

.. _system-administration-service-management:

Manage system services
----------------------

The UMC module :guilabel:`System services` can be used to check the current
status of a system service and to start or stop it as required.

.. _system-administration-system-services-figure:

.. figure:: /images/umc-systemservices.*
   :alt: Overview of system services

   Overview of system services

In this list of all the services installed on the system, the current running
runtime status and a *Description* are displayed under *Status*. The service can
be started, stopped or restarted under :guilabel:`more`.

By default every service is started automatically when the system is started. In
some situations, it can be useful not to have the service start directly, but
instead only after further configuration. The action *Start manually* is used so
that the service is not started automatically when the system is started, but
can still be started subsequently. The action *Start never* also prevents
subsequent service starts.

.. _system-administration-ldap-server:

Configuration of the LDAP server in use
---------------------------------------

Several LDAP servers can be operated in a UCS domain. The primary one used is
specified with the :term:`UCR variable` :envvar:`ldap/server/name`, further servers can be
specified via the UCR variable :envvar:`ldap/server/addition`.

Alternatively, the LDAP servers can also be specified via a *LDAP server*
policy. The order of the servers determines the order of the computer's requests
to the server if a LDAP server cannot be reached.

By default only :envvar:`ldap/server/name` is set following the installation or
the domain join. If there is more than one LDAP server available, it is
advisable to assign at least two LDAP servers using the *LDAP server* policy in
order to improve redundancy. In cases of an environment distributed over
several locations, preference should be given to LDAP servers from the local
network.

.. _system-administration-print-server:

Configuration of the print server in use
----------------------------------------

The print server to be used can be specified with the :term:`UCR variable`
:envvar:`cups/server`.

Alternatively, the server can also be specified via the *Print server* policy in
the UMC module :guilabel:`Computers`.

.. _system-administration-nscd:

Name service cache daemon
-------------------------

Data of the NSS service is cached by the *Name Server Cache Daemon* (NSCD) in
order to speed up frequently recurring requests for unchanged data. Thus, if a
repeated request occurs, instead of a complete LDAP request to be processed, the
data are simply drawn directly from the cache.

Since UCS 3.1, the groups are no longer cached via the NSCD for performance and
stability reasons; instead they are now cached by a local group cache, see
:ref:`groups-cache`.

Since UCS 5.2-0, the user information (``passwd``) is no longer cached via
NSCD. Instead the *System Security Services Daemon* (SSSD) is used to get and
cache user information, see `SSSD documentation <https://sssd.io/docs/introduction.html>`_.

The central configuration file of the (:file:`/etc/nscd.conf`) is managed by
*Univention Configuration Registry*.

The access to the cache is handled via a hash table. The size of the hash table
can be specified in Univention Configuration Registry, and should be higher than the number of
simultaneously used users/hosts. For technical reasons, a prime number should be
used for the size of the table. The following table shows the standard values of
the variables:

.. list-table:: Default size of the hash table
   :header-rows: 1
   :widths: 30 70

   * - Variable
     - Default size of the hash table

   * - :envvar:`nscd/hosts/size`
     -  ``6007``

With very big caches it may be necessary to increase the size of the cache
database in the system memory. This can be configured through the UCR
variable :envvar:`nscd/hosts/maxdbsize`.

As standard, five threads are started by NSCD. In environments with many
accesses it may prove necessary to increase the number via the :term:`UCR variable`
:envvar:`nscd/threads`.

In the basic setting, a resolved hostname is kept in cache for one
hour.
With the UCR variable :envvar:`nscd/hosts/positive_time_to_live` this
period can be extended or diminished (in seconds).

From time to time it might be necessary to manually invalidate the cache of the
NSCD. This can be done individually for each cache table with the following
commands:

.. code-block:: console

   $ sss_cache -U
   $ nscd -i hosts

The verbosity of the log messages can be configured through the UCR variable
:envvar:`nscd/debug/level`.
