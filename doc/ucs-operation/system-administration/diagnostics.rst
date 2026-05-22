.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration-diagnostics:

System diagnostics
==================

This page describes the tools that help you inspect the current state of a Nubus for UCS system
and identify common problems.
It covers command-line system status logging
and diagnostic functions in Univention Management Console.

.. _system-administration-diagnostics-cli:

Command-line diagnostics
------------------------

:command:`univention-system-stats` can be used to document the current system
status in the :file:`/var/log/univention/system-stats.log` file. The following
values are logged:

* The free disk space on the system partitions (:command:`df
  -lhT`)

* The current process list (:command:`ps auxf`)

* Two :command:`top` lists of the current processes and
  system load (:command:`top -b -n2`)

* The current free system memory (:command:`free`)

* The time elapsed since the system was started
  (:command:`uptime`)

* Temperature, fan and voltage indexes from
  :program:`lm-sensors`
  (:command:`sensors`)

* A list of the current Samba connections
  (:command:`smbstatus`)

The runtime in which the system status should be logged can be defined in Cron
syntax via the :term:`UCR variable` :envvar:`system/stats/cron`, e.g., ``0,30 * * * *``
for logging every half and full hour. The logging is activated by setting the
UCR variable :envvar:`system/stats` to ``yes``. This is the default since UCS 3.0.

.. _system-administration-diagnostics-umc:

Diagnostics in Management UI
----------------------------

The Management UI provides modules for inspecting running processes
and diagnosing known system problems.

.. _system-administration-diagnostics-processes:

Process overview through management module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The UMC module :guilabel:`Process overview` displays a table of the current
processes on the system. The processes can be sorted based on the following
properties by clicking on the corresponding table header:

* CPU utilization in percent

* The username under which the process is running

* Memory consumption in percent

* The process ID

The menu item *more* can be used to terminate processes. Two different types of
termination are possible:

Terminate
   The action :guilabel:`Terminate` sends the process a ``SIGTERM`` signal; this
   is the standard method for the controlled termination of programs.

Force terminate
   Sometimes, it may be the case that a program - e.g., after crashing - can no
   longer be terminated with this procedure. In this case, the action
   :guilabel:`Force terminate` can be used to send the signal ``SIGKILL`` and
   force the process to terminate.

As a general rule, terminating the program with ``SIGTERM`` is preferable as
many programs then stop the program in a controlled manner and, for example,
save open files.

.. _system-administration-diagnostics-management-module:

System diagnostic through management module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The UMC module :guilabel:`System diagnostic` offers a corresponding user
interface to analyze a UCS system for a range of known problems.

The module evaluates a range of problem scenarios known to it and suggests
solutions if it is able to resolve the identified solutions automatically. This
function is displayed via ancillary buttons. In addition, links are shown to
further articles and corresponding UMC modules.
