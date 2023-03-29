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

.. _computers-softwaremanagement:

*******************
Software deployment
*******************

The software deployment integrated in UCS offers extensive possibilities for the
rollout and updating of UCS installations. Security and version updates can be
installed via the UMC module :guilabel:`Software update`, a command line tool or
based on policies. This is described in the section :ref:`software-ucs-updates`.
The UCS software deployment does not support the updating of Microsoft Windows
systems. An additional Windows software distribution is required for this.

For larger installations, there is the possibility of establishing a local
repository server from which all further updates can be performed, see
:ref:`software-config-repo`.

The UCS software deployment is based on the underlying Debian package management
tools, which are expanded through UCS-specific tools. The different tools for
the installation of software are introduced in
:ref:`computers-softwaremanagement-install-software`. The installation of version
and errata updates can be automated via policies, see
:ref:`computers-softwaremanagement-maintenance-policy`.

The software monitor provides a tool with which all package installations
statuses can be centrally stored in a database, see
:ref:`computers-software-monitor`.

The initial installation of UCS systems is not covered in this chapter, but is
documented in :ref:`installation-chapter` instead.

.. toctree::
   :caption: Chapter contents:

   ucs-versions
   app-center
   updates
   repository-server
   further-software
   package-maintenance-policy
   software-monitor
