.. Like what you see? Join us!
.. https://www.univention.com/about-us/careers/vacancies/
..
.. Copyright (C) 2021-2023 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only
..
.. https://www.univention.com/
..
.. All rights reserved.
..
.. The source code of this program is made available under the terms of
.. the GNU Affero General Public License v3.0 only (AGPL-3.0-only) as
.. published by the Free Software Foundation.
..
.. Binary versions of this program provided by Univention to you as
.. well as other copyrighted, protected or trademarked materials like
.. Logos, graphics, fonts, specific documentations and configurations,
.. cryptographic keys etc. are subject to a license agreement between
.. you and Univention and not subject to the AGPL-3.0-only.
..
.. In the case you use this program under the terms of the AGPL-3.0-only,
.. the program is provided in the hope that it will be useful, but
.. WITHOUT ANY WARRANTY; without even the implied warranty of
.. MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
.. Affero General Public License for more details.
..
.. You should have received a copy of the GNU Affero General Public
.. License with the Debian GNU/Linux or Univention distribution in file
.. /usr/share/common-licenses/AGPL-3; if not, see
.. <https://www.gnu.org/licenses/agpl-3.0.txt>.

.. _computers-softwaremanagement-maintenance-policy:

Specification of an update point using the package maintenance policy
=====================================================================

A *Maintenance* policy (see :ref:`central-policies`) in the UMC modules for
computer and domain management can be used to specify a point at which the
following steps should be performed:

* Check for available release updates to be installed (see
  :ref:`computers-softwaremanagement-release-policy`) and, if applicable,
  installation.

* Installation/deinstallation of package lists (see
  :ref:`computers-softwaremanagement-package-lists`)

* Installation of available errata updates

Alternatively, the updates can also be performed when the system is booting or
shut down.

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Perform maintenance after system startup
     - If this option is activated, the update steps are performed when the
       computer is started up.

   * - Perform maintenance before system shutdown
     - If this option is activated, the update steps are performed when the
       computer is shut down.

   * - Use Cron settings
     - If this flag is activated, the fields *Month*, *Day of week*, *Day*,
       *Hour* and *Minute* can be used to specify an exact time when the update
       steps should be performed.

   * - Reboot after maintenance
     - This option allows you to perform an automatic system restart after
       release updates either directly or after a specified time period of
       hours.
