.. _computers-softwaremanagement-installsoftware:

Installation of further software
================================

The initial selection of the software components of a UCS system is performed
within the scope of the installation. The software components are selected
relative to the functions, whereby e.g. the *Proxy server* component is
selected, which then procures the actual software packages via a meta package.
The administrator does not need to know the actual package names. However,
individual packages can also be specifically installed and removed for further
tasks. When installing a package, it is sometimes necessary to install
additional packages, which are required for the proper functioning of the
package. These are called package dependencies. All software components are
loaded from a repository (see :ref:`software-configrepo`).

Software which is not available in the Debian package format should be installed
into the :file:`/opt/` or :file:`/usr/local/` directories. These directories are
not used for installing UCS packages, thus a clean separation between UCS
packages and other software is ensured.

There are several possibilities for installing further packages subsequently on
an installed system, as the following sections describe.

.. _computers-softwareselection:

Installation/uninstallation of UCS components in the Univention App Center
--------------------------------------------------------------------------

All software components offered in the Univention Installer can also be
installed and removed at a later point in time via the Univention App Center.
This is done by selecting the *UCS components* package category. Further
information on the Univention App Center can be found in
:ref:`software-appcenter`.

.. _appcenter-ucscomponents:

.. figure:: /images/appcenter-ucs.*
   :alt: Selection of UCS components in the App Center

   Selection of UCS components in the App Center

.. _computers-installation-removal-of-individual-packages-in-the-univention-management-console:

Installation/removal of individual packages via |UCSUMC| module
---------------------------------------------------------------

The UMC module :guilabel:`Package Management` can be used to
install and uninstall individual software packages.

.. _software-umcinstall:

.. figure:: /images/software_install.*
   :alt: Installing the package univention-squid via |UCSUMC| module 'Package management'

   Installing the package :program:`univention-squid` via |UCSUMC| module
   'Package management'

A search mask is displayed on the start page in which the user can
select the package category or a search filter (name or description).
The results are displayed in a table with the following columns:

* Package name

* Package description

* Installation status

Clicking an entry in the result list opens a detailed information page
with a comprehensive description of the package.

In addition, one or more buttons will be displayed. They have the following
meanings:

Install
   is displayed if the software package is not installed yet.

Uninstall
   is displayed if the software package is installed.

Upgrade
   is displayed if the software package is installed but not updated.

Close
   can be used for returning to the previous search request.

.. _computers-installation-removal-of-individual-packages-in-the-command-line:

Installation/removal of individual packages in the command line
---------------------------------------------------------------

The following steps must be performed with ``root`` user rights.

Individual packages are installed using the command:

.. code-block:: console

   $ univention-install PACKAGENAME


Packages can be removed with the following command:

.. code-block:: console

   $ univention-remove PACKAGENAME

If the name of a package is unknown, the command :command:`apt-cache search` can
be used to search for the package. Parts of the name or words which appear in
the description of the package are listed, for example:

.. code-block:: console

   $ apt-cache search fax


.. _computers-installation-and-remove-hooks:

Hook scripts for administrators
-------------------------------

Custom scripts can be called after each app installation, -upgrade or -removal.
Such scripts can be used to automate repeating administrative tasks.

To use this feature custom scripts can be placed in one of the directories
listed below. If such a directory does not yet exist, it can be manually
created:

* :file:`/var/lib/univention-appcenter/apps/{{appid}}/local/hooks/post-install.d/`
* :file:`/var/lib/univention-appcenter/apps/{{appid}}/local/hooks/post-upgrade.d/`
* :file:`/var/lib/univention-appcenter/apps/{{appid}}/local/hooks/post-remove.d/`

Where ``{appid}`` is the name of the app for which the scripts should be
executed.

Script file names are only allowed to consist of lower case letters and numbers
(``^[a-z0-9]+$``). Additionally scripts have to be marked as executable
(:command:`chmod +x [filename]`), because they are internally called by
:program:`run-parts`. As a consequence :command:`run-parts --test [directory]`
can be used to verify if and which files would be executed. Further information
can be found in the manual with :command:`man run-parts`.

The :file:`/var/log/univention/appcenter.log` contains
possible scripting error messages and further hints.

.. _computers-softwaremanagement-packagelists:

Policy-based installation/uninstallation of individual packages via package lists
---------------------------------------------------------------------------------

Package lists can be used to install and remove software using policies. This
allows central software deployment for a large number of computer systems.

Each system role has its own package policy type.

Package policies are managed in the UMC module :guilabel:`Policies` with the
*Policy: Packages + system role*.

.. list-table:: 'General' tab
   :header-rows: 1

   * - Attribute
     - Description

   * - Name
     - An unambiguous name for this package list, e.g., *mail server*.

   * - Package installation list
     - A list of packages to be installed.

   * - Package removal list
     - A list of packages to be removed.

The software packages defined in a package list are installed/uninstalled at the
time defined in the :guilabel:`Maintenance` policy (for the configuration see
:ref:`computers-softwaremanagement-maintenancepolicy`).

The software assignable in the package policies are also registered in the LDAP.
