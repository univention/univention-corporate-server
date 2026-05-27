.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration-logging:

Log files and log rotation
==========================

Use this page to learn which log files
Nubus for UCS stores
and how the system rotates them.
It also covers separate log rotation settings
for Univention Directory Listener modules.

.. _computers-log-files:

Log file locations
------------------

Nubus for UCS stores its product-specific log files
in the :file:`/var/log/univention/` directory,
for example log files for listener and notifier replication.
Services write their log messages
to their own standard log files.
For example,
Apache writes log messages to the :file:`/var/log/apache2/error.log` file.

.. _computers-log-rotation:

Log rotation
------------

:program:`logrotate` manages the log files.
It creates numbered log file archives at configured intervals
and deletes older archives.
The :term:`UCR variables <UCR variable>` :envvar:`logrotate/rotate`
and :envvar:`logrotate/rotate/count`
control log rotation.
The :envvar:`logrotate/rotate` variable
specifies the rotation criterion,
for example ``weekly`` or :samp:`size 50M`.
The :envvar:`logrotate/rotate/count` variable
specifies how many rotated log file archives the system keeps.
By default,
the system rotates log files weekly
and keeps ``12`` archives.

For example,
the current log file for *Univention Directory Listener*
is the :file:`listener.log` file.
The archive for the previous rotation
is the :file:`listener.log.1` file.

Use the :envvar:`logrotate/compress` UCR variable
to control whether :command:`gzip` compresses older log files.

.. _computers-log-listener-module:

Listener module log files
-------------------------

Each log file in the :file:`/var/log/univention/listener_modules` directory
has its own :program:`logrotate` configuration.
Listener module log files use global settings by default
and can also use per-log-file overrides.
The :samp:`logrotate/listener-modules/{DIRECTIVE}` UCR variable
configures the global settings.
For a complete list of supported directives,
see the `logrotate manual page <https://manpages.debian.org/bookworm/logrotate/logrotate.8.en.html>`_.

.. _computers-log-listener-module-rotation-settings:

Global listener module logrotate settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use these settings
when you want to apply the same logrotate behavior
to all listener module log files.
Nubus for UCS supports the following directives
for listener module log files:

.. envvar:: logrotate/listener-modules/rotate

   Defines how often the system rotates listener module log files.

   :Default value: ``weekly``

.. envvar:: logrotate/listener-modules/rotate/count

   Defines how many rotated log files the system keeps.

   :Default value: ``12``

.. envvar:: logrotate/listener-modules/create

   Defines the permissions and ownership for newly created log files.

   :Default value: ``640 listener adm``

.. envvar:: logrotate/listener-modules/missingok

   Defines whether logrotate continues
   when a log file is missing.

   :Default value: ``missingok``

.. envvar:: logrotate/listener-modules/compress

   Defines whether logrotate compresses rotated log files.

   :Default value: ``compress``

.. envvar:: logrotate/listener-modules/notifempty

   Defines whether logrotate skips empty log files.

   :Default value: ``notifempty``

.. _computers-log-listener-module-rotation-settings-overrides:

Per-log-file overrides
~~~~~~~~~~~~~~~~~~~~~~

Use the following UCR variable pattern
to configure settings for a specific log file:
:samp:`logrotate/listener-modules/{LOG_FILE_NAME}/{DIRECTIVE}`.
Use the log filename without the :file:`.log` filename extension.
You can override the same directives
that the global settings section lists.
For example,
to configure the rotation interval for :file:`example.log`,
use :samp:`logrotate/listener-modules/example/rotate`.
