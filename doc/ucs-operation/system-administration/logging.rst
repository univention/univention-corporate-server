.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration-logging:

Log files and log rotation
==========================

This page describes where Nubus for UCS stores log files
and how the system rotates them.
It also covers the separate log rotation settings
for Univention Directory Listener modules.

.. _computers-log-files:

Log file locations
------------------

All UCS-specific log files (e.g., for the listener/notifier replication) are
stored in the :file:`/var/log/univention/` directory. Services write log messages their own
standard log files: for example, Apache to the file
:file:`/var/log/apache2/error.log`.

.. _computers-log-rotation:

Log rotation
------------

The log files are managed by :program:`logrotate`. It ensures that log files are
named in series in intervals (can be configured in weeks using the :term:`UCR variable`
:envvar:`log/rotate/weeks`, with the default setting being 12) and older log
files are then deleted. For example, the current log file for the *Univention Directory Listener* is
found in the :file:`listener.log` file; the one for the previous week in
:file:`listener.log.1`, etc.

Alternatively, log files can also be rotated only once they have reached a
certain size. For example, if they are only to be rotated once they reach a size
of 50 MB, the UCR variable :envvar:`logrotate/rotates` can be set to ``size 50M``.

The UCR variable :envvar:`logrotate/compress` is used to configure whether the
older log files are additionally zipped with :command:`gzip`.

.. _computers-log-listener-module:

Listener module log files
-------------------------

Log files located in the directory :file:`/var/log/univention/listener_modules`
each have their own Logrotate configuration. These log files have global and
specific Logrotate settings. The UCR variable :samp:`logrotate/listener-modules/{<directive>}`
configures the global settings.
The `logrotate(8) <https://manpages.debian.org/bookworm/logrotate/logrotate.8.en.html>`_
documentation describes the functionality in detail.

.. _computers-log-listener-module-rotation-settings:

Global listener module logrotate settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

UCS supports the following directives:

.. envvar:: logrotate/listener-modules/rotate

   Default value: ``weekly``

.. envvar:: logrotate/listener-modules/rotate/count

   Default value: ``12``

.. envvar:: logrotate/listener-modules/create

   Default value: ``640 listener adm``

.. envvar:: logrotate/listener-modules/missingok

   Default value: ``missingok``

.. envvar:: logrotate/listener-modules/compress

   Default value: ``compress``

.. envvar:: logrotate/listener-modules/notifempty

   Default value: ``notifempty``

.. _computers-log-listener-module-rotation-settings-overrides:

Per-logfile overrides
~~~~~~~~~~~~~~~~~~~~~

If a configuration only applies to a specific log file, compose the UCR variable as
follows: :samp:`logrotate/listener-modules/{<logfile-name>}/{<directive>}`. Use
the log filename without the file suffix :file:`.log`.
