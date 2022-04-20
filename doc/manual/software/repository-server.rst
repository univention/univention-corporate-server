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
