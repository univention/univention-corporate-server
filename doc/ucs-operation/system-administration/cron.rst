.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration-cron:

Run recurring actions with cron
===============================

Use the cron service to start recurring actions such as processing log files
at a defined time.
This page refers to such an action as a cron job
and describes three ways to define cron jobs:

* Predefined cron directories
* Local cron jobs in :file:`/etc/cron.d/`
* Cron jobs through Univention Configuration Registry

.. _system-administration-cron-predefined-dirs:

Predefined cron directories
---------------------------

Each Nubus for UCS system includes these directories:

* :file:`/etc/cron.hourly/`
* :file:`/etc/cron.daily/`
* :file:`/etc/cron.weekly/`
* :file:`/etc/cron.monthly/`

Executable shell scripts in these directories
run hourly, daily, weekly, or monthly.

.. _system-administration-cron-local:

Define local cron jobs in :file:`/etc/cron.d/`
----------------------------------------------

.. index:: cron; syntax
   :name: cron-syntax

Use one line with seven columns to define a cron job:

* Minute (0-59)

* Hour (0-23)

* Day (1-31)

* Month (1-12)

* Weekday (0-7); 0 and 7 both mean Sunday

* Name of the user who runs the job, for example ``root``

* Command to run

Specify the time in different ways.
Enter a particular minute, hour, or other value,
or use ``*`` to run an action every minute, hour, or other interval.
You can also define intervals.
For example, :samp:`*/2` in the minute field runs an action every two minutes.

Example:

.. code-block::

   30 * * * * root /usr/sbin/jitter 600 /usr/share/univention-samba/slave-sync

.. _system-administration-cron-ucr:

Define cron jobs in Univention Configuration Registry
-----------------------------------------------------

You can also define cron jobs in *Univention Configuration Registry*.
Use this approach when you set cron jobs through a *UDM policy*
and apply them to multiple computers.

Each cron job uses at least two UCR variables.
Replace :samp:`{JOBNAME}` with a unique identifier for the cron job.
This placeholder appears in the variable names in the following lists.

Required variables:

* :samp:`cron/{JOBNAME}/command` specifies the command.

* :samp:`cron/{JOBNAME}/time` specifies the execution time.
  For the time format, see :ref:`system-administration-cron-local`.

Optional variables and defaults:

* By default, cron runs the job as root.
  Use :samp:`cron/{JOBNAME}/user` to specify a different user.

* Use :samp:`cron/{JOBNAME}/mailto` to send command output by email.

* Use :samp:`cron/{JOBNAME}/description` to add a description.
