.. SPDX-FileCopyrightText: 2025 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _da-troubleshooting:

***************
Troubleshooting
***************

When you encounter problems or errors,
consult the following files:

:file:`/var/log/univention/management-console-server.log`
   Contains log information for the UMC server.

:file:`/var/log/univention/management-console-module-udm.log`
   Contains log information for the UMC user and group management modules.

You may also want to increase the log level for the UMC server and module process
as shown in :numref:`da-troubleshooting-log-level-listing`.

.. code-block:: console
   :caption: Increase log levels
   :name: da-troubleshooting-log-level-listing

   $ ucr set umc/server/debug/level='4'
   $ ucr set umc/module/debug/level='4'
   $ service univention-management-console-server restart


