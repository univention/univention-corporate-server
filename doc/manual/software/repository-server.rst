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

.. _software-config-repo:

Configuration of the repository server for updates and package installations
============================================================================

Package installations and updates can either be performed from the Univention
update server or from a locally maintained repository. A local repository is
practical if there are a lot of UCS systems to update as the updates only need
to be downloaded once in this case. As repositories can also be updated offline,
a local repository also allows the updating of UCS environments without internet
access.

A local repository can require a lot of disk space.

Using the registered settings, APT package sources are automatically generated
in the :file:`/etc/apt/sources.list.d/` directory for release and errata updates
as well as add-on components. If further repositories are required on a system,
these can be entered in the :file:`/etc/apt/sources.list` file.

By default the Univention repository ``updates.software-univention.de`` is used
for a new installation.

The Univention repository contains all packages provided by Univention and
Debian. A distinction is made between maintained and unmaintained packages.

* All packages in the standard package scope are in *maintained* status.
  Security updates are provided in a timely manner only for *maintained*
  packages. The list of *maintained* packages can be viewed on a UCS system in
  :file:`univention-errata-level/maintained-packages.txt`.

* *unmaintained* packages are not covered by security updates or other
  maintenance. To check if *unmaintained* packages are installed, the command
  :command:`univention-list-installed-unmaintained-packages` can be executed.

For additional repositories the installation of *unmaintained* packages is not
possible by default. To enable installation, the |UCSUCRV|
:envvar:`repository/online/component/.*/unmaintained` must be set to ``yes``.

.. _computers-configuration-via-the-univention-management-console:

Configuration via |UCSUMC| module
---------------------------------

The :guilabel:`Repository server` can be specified in the UMC
module :guilabel:`Repository Settings`.

.. _computers-configuration-via-univention-configuration-registry:

Configuration via Univention Configuration Registry
---------------------------------------------------

The repository server to be used can be entered in the |UCSUCRV|
:envvar:`repository/online/server` and is preset to
``updates.software-univention.de`` for a new installation.

.. _computers-policy-based-configuration-of-the-repository-server:

Policy-based configuration of the repository server
---------------------------------------------------

The repository server to be used can also be specified using the *Repository
server* policy in the |UCSUMC| module :guilabel:`Computers`. Only UCS server
systems for which a DNS entry has been configured are shown in the selection
field (see :ref:`central-policies`).

.. _software-create-repo:

Creating and updating a local repository
----------------------------------------

Package installations and updates can either be performed from the Univention
update server or from a locally maintained repository. A local repository is
practical if there are a lot of UCS systems to update as the updates only need
to be downloaded once in this case. As repositories can also be updated offline,
a local repository also allows the updating of UCS environments without internet
access.

The local repository can be activated/deactivated using the |UCSUCRV|
:envvar:`local/repository`.

There is also the possibility of synchronizing local repositories, which means,
for example, a main repository is maintained at the company headquarters and
then synchronized to local repositories at the individual locations.

To set up a repository, the :command:`univention-repository-create` command must
be run as the ``root`` user.

The packages in the repository can be updated using the
:command:`univention-repository-update` tool. With
:command:`univention-repository-update net` the repository is synchronized with
another specified repository server. This is defined in the |UCSUCRV|
:envvar:`repository/mirror/server` and typically points to
``updates.software-univention.de``.

An overview of the possible options is displayed with the following command:

.. code-block:: console

   $ univention-repository-update -h


The repository is stored in the :file:`/var/lib/univention-repository/mirror/`
directory.
