.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration-cron:

Run recurring actions with cron
===============================

Regularly recurring actions (e.g., the processing of log files) can be
started at a defined time with the Cron service. Such an action is known
as a cron job.
This page describes three ways to define cron jobs:
predefined cron directories,
local cron jobs in :file:`/etc/cron.d/`,
and cron jobs through Univention Configuration Registry.

.. _system-administration-cron-predefined-dirs:

Predefined cron directories
---------------------------

Four directories are predefined on every UCS system, :file:`/etc/cron.hourly/`,
:file:`/etc/cron.daily/`, :file:`/etc/cron.weekly/` and
:file:`/etc/cron.monthly/`. Shell scripts which are placed in these directories
and marked as executable are run automatically every hour, day, week or month.

.. _system-administration-cron-local:

Defining local cron jobs in :file:`/etc/cron.d/`
------------------------------------------------

.. index:: cron; syntax
   :name: cron-syntax

A cron job is defined in a line, which is composed of a total of seven columns:

* Minute (0-59)

* Hour (0-23)

* Day (1-31)

* Month (1-12)

* Weekday (0-7) (0 and 7 both stand for Sunday)

* Name of user executing the job (e.g., ``root``)

* The command to be run

The time specifications can be set in different ways. One can specify a specific
minute/hour/etc. or run an action every minute/hour/etc. with a ``*``. Intervals
can also be defined, for example :samp:`*/2` as a minute specification runs an
action every two minutes.

Example:

.. code-block::

   30 * * * * root /usr/sbin/jitter 600 /usr/share/univention-samba/slave-sync

.. _system-administration-cron-ucr:

Defining cron jobs in Univention Configuration Registry
-------------------------------------------------------

Cron jobs can also be defined in *Univention Configuration Registry*. This is particularly useful if
they are set via a *UDM policy* and are thus used on more than one
computer.

Each cron job is composed of at least two UCR variables.
:samp:`{JOBNAME}` is a general description.

* :samp:`cron/{JOBNAME}/command` specifies the command to be run (required)

* :samp:`cron/{JOBNAME}/time` specifies the execution time (see
  :ref:`cron-local`) (required)

* As standard, the cron job is run as a user ``root``.
  :samp:`cron/{JOBNAME}/user` can be used to specify a different user.

* If an email address is specified under :samp:`cron/{JOBNAME}/mailto`, the
  output of the cron job is sent there per email.

* :samp:`cron/{JOBNAME}/description` can be used to provide a description.
