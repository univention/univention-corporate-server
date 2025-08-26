.. SPDX-FileCopyrightText: 2025 Univention GmbH
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

:file:`/var/log/univention/directory-manager-rest.log`
   Contains log information for the UDM REST API.

You may also want to increase the log level for the UMC server, module process and UDM REST API
as shown in :numref:`da-troubleshooting-log-level-listing`.

.. code-block:: console
   :caption: Increase log levels
   :name: da-troubleshooting-log-level-listing

   $ ucr set \
     umc/server/debug/level='4' \
     umc/module/debug/level='4' \
     directory/manager/rest/debug/level='4'
   $ systemctl restart \
     univention-management-console-server \
     univention-directory-manager-rest
