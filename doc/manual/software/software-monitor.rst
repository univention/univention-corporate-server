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

.. _computers-software-monitor:

Central monitoring of software installation statuses with the software monitor
==============================================================================

.. index:: DNS record; _pkgdb._tcp

The software monitor is a database in which information is stored concerning the
software packages installed across all UCS systems. This database offers an
administrator an overview of which release and package versions are installed in
the domain and offers information for the step-by-step updating of a UCS domain
and for use in identifying problems.

The software monitor can be installed from the Univention App Center with the
application :program:`Software installation monitor`. Alternatively, the
software package :program:`univention-pkgdb` can be installed. Additional
information can be found in :ref:`computers-softwaremanagement-install-software`.

UCS systems update their entries automatically when software is installed,
uninstalled or updated. The system on which the software monitor is operated is
located by the DNS service record ``_pkgdb._tcp``.

The software monitor brings its own UMC module :guilabel:`Software monitor`. The
following functions are available:

Systems
   allows to search for the version numbers of installed systems. It is possible
   to search for system names, UCS versions and system roles.

Packages
   allows to search in the installation data tracked by the package status
   database. Besides searching for a *Package name* there are various search
   possibilities available for the installation status of packages:

   Selection state
      The *selection state* influences the action taken when updating a package.
      ``Install`` is used to select a package for installation. If a package is
      configured to ``Hold`` it will be excluded from further updates. There are
      two possibilities for uninstalling a package: A package removed with
      ``DeInstall`` keeps locally created configuration data, whilst a package
      removed with ``Purge`` is completely deleted.

   Installation state
      The *installation state* describes the status of an installed package in
      relation to upcoming updates. The normal status is ``Ok``, which leads to a
      package being updated when a newer version exists. If a package is configured
      to ``Hold`` it will be excluded from the update.

   Package state
      The *package state* describes the status of a setup package. The normal status
      here is ``Installed`` for installed packages and ``ConfigFiles`` for removed
      packages. All other statuses appear when the package's installation was
      canceled in different phases.

.. _software-monitor:

.. figure:: /images/software_softwaremonitor.*
   :alt: Searching for packages in the software monitor

   Searching for packages in the software monitor

If you do not wish UCS systems to store installation processes in the software
monitor (e.g., when there is no network connection to the database), this can be
arranged by setting the |UCSUCRV| :envvar:`pkgdb/scan` to ``no``.

Should storing be reactivated at a later date, the command
:command:`univention-pkgdb-scan` must be executed to ensure that package
versions installed in the meanwhile are also adopted in the database.

The following command can be used to remove a system's program inventory from
the database again:

.. code-block:: console

   $ univention-pkgdb-scan --remove-system [HOSTNAME]
