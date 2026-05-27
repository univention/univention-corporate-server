.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration-diagnostics:

System diagnostics
==================

This page describes tools that help you inspect the current state
of a system running Nubus for UCS
and identify common problems.
It covers command-line system status logging
and diagnostic functions in the *Management UI*.

.. _system-administration-diagnostics-cli:

Command-line diagnostics
------------------------

Run :command:`univention-system-stats`
to write the current system status
to the :file:`/var/log/univention/system-stats.log` file.
The command logs the following values:

* The free disk space on the system partitions: :command:`df -lhT`.

* The current process list: :command:`ps auxf`.

* Two :command:`top` lists of the current processes and system load,
  :command:`top -b -n2`.

* The current free system memory: :command:`free`.

* The time elapsed since the system started: :command:`uptime`.

* Temperature, fan, and voltage indexes from :program:`lm-sensors` with the command
  :command:`sensors`.

* A list of the current Samba connections: :command:`smbstatus`.

To configure system status logging:

#. Set the :term:`UCR variable` :envvar:`system/stats/cron`
   to the required cron expression.
   For example, use ``0,30 * * * *``
   to log the status every 30 minutes.

#. Set the :term:`UCR variable` :envvar:`system/stats` to ``yes``.

.. _system-administration-diagnostics-umc:

Diagnostics in the Management UI
--------------------------------

The *Management UI* provides modules
to inspect running processes
and diagnose known system problems.

View processes in the Management UI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Open the :guilabel:`Process overview` management module
to view the current processes on the system.
To sort the processes,
click the corresponding table header
for one of the following properties:

* CPU utilization in percent

* The username under which the process runs

* Memory consumption in percent

* The process ID

To terminate a process,
open the :guilabel:`More` menu
and choose one of the following actions:

Terminate
   The :guilabel:`Terminate` action sends the process the ``SIGTERM`` signal.
   Use this action for controlled program termination.

Force terminate
   A program can sometimes stop responding,
   for example after a crash.
   In this case,
   use :guilabel:`Force terminate`
   to send the ``SIGKILL`` signal
   and force the process to stop.

In general,
use ``SIGTERM`` first
because many programs can then shut down in a controlled way
and save open files.

.. seealso::

   `POSIX signals in Signal (IPC) - Wikipedia <https://en.wikipedia.org/wiki/Signal_(IPC)#POSIX_signals>`_
      for information about POSIX signals for inter-process communication.

.. _system-administration-diagnostics-management-module:

Run system diagnostics in the Management UI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Open the :guilabel:`System diagnostics` management module
to analyze a system running Nubus for UCS
for known problems.

The module checks known problem scenarios.
If the module can fix a detected problem automatically,
it shows an additional button for that action.
It also links to related articles
and corresponding management modules.
