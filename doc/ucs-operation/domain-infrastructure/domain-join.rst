.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _domain-infrastructure-join:

Domain join
===========

.. highlight:: console

A Nubus for UCS system must and Ubuntu, or Windows system can join the domain after installation.
You can also add any other Unix systems to the domain.
See :cite:t:`ext-doc-domain` for details.

.. _domain-infrastructure-join-process:

Domain join process
-------------------

The :term:`Primary Directory Node` should run the latest version.
A UCS system joining the domain must use the same version or an older version.
Because this causes compatibility errors, don't join a domain with a newer version.
When a computer joins a domain, the primary system:

* Creates a computer account.
* Synchronizes the TLS certificates.
* Copies LDAP data if needed.

After that, the *join scripts* run.
Installed software packages use them
to add objects to the directory service.
For more information, see :ref:`domain-infrastructure-join-ucs-joinscripts`.

The UCS system records the domain join on the client in
:file:`/var/log/univention/join.log`.
To analyze errors, review this file.
The Primary Directory Node stores related join actions in
:file:`/home/{<Join-Account>}/.univention-server-join.log`.

You can repeat the domain join process at any time.
You may need to rejoin a system after major changes on the Primary Directory Node,
such as changes to key system settings.

.. _domain-infrastructure-join-ucs:

How UCS systems join domains
----------------------------

A UCS system can join an existing domain in three ways:

* During installation in the *Univention Installer*, see
  :ref:`deployment-domain-setup-join-ucs`.

* After installation with the command :command:`univention-join`, see
  :ref:`domain-infrastructure-join-univention-join`.

* Through the *Domain Join* management module in the *Management UI*, see
  :ref:`domain-infrastructure-join-ucs-umc`.

.. _domain-infrastructure-join-univention-join:

Subsequent domain joins with :spelling:word:`univention`-join
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :command:`univention-join` command joins a Nubus for UCS system to a Nubus for UCS domain.
It accepts command-line arguments or interactive prompts.
After installation and before the domain join is complete, run this command.
The command asks for required settings interactively,
or pass them as command-line options instead.
This works well for automated or remote setups.

.. program:: univention-join

The following options are available.
Most are optional.
The command asks for any missing values.

.. option:: -dcname <HOSTNAME>

   The system automatically detects the Primary Directory Node through DNS.
   If automatic detection fails, for example, when a :term:`Replica Directory Node`
   has a different DNS domain,
   you can specify the Primary Directory Node hostname directly using this parameter.
   Enter the hostname as a fully qualified name, for example ``primary.example.com``.

.. option:: -dcaccount <ACCOUNTNAME>

   The join account is the user account used to add systems to the UCS domain.
   By default, you use the ``Administrator`` user or a member of the ``Domain Admins``
   or ``DC Backup Hosts`` groups.
   You can specify a different join account using this parameter.

.. option:: -dcpwd <FILE>

   Specify the password using this parameter.
   The command reads the password from the specified file.

.. option:: -verbose

   This parameter adds additional debug output to the log files.
   You can review this output to analyze errors.

.. _domain-infrastructure-join-ucs-umc:

Join a domain through the management module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can also join a Nubus for UCS domain through the *Domain join* management module.
The ``Administrator`` user doesn't exist yet on a system that hasn't joined.
Sign in to the *Management UI* as user ``root`` instead.
For information about the password, see :ref:`deployment-initial-system-configuration-password`.

As with the command-line join,
enter the username and password of an account that's member of the ``Domain Admins`` group.
The system finds the Primary Directory Node through DNS.
You can also enter it by hand.

Use the :guilabel:`Rejoin` option to repeat the domain join at any time.

.. _domain-infrastructure-join-ucs-joinscripts:

Join scripts and unjoin scripts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The system runs scripts during the domain join and during software removal:

Join scripts
   The UCS system runs *join scripts* during the domain join.
   They can register a print server in the domain,
   adapt DNS entries,
   or perform other configuration changes.
   The system stores them in :file:`/usr/lib/univention-install/`.

Unjoin scripts
   *Unjoin scripts* reverse changes that join scripts applied.
   The UCS system runs them when you uninstall software components
   and stores them in :file:`/usr/lib/univention-uninstall/`.

Each script belongs to a software package and has a version number.
When a new package version needs an updated setup, the script version goes up too.

.. note::

   Join scripts and unjoin scripts are specific to UCS systems.
   Windows, Ubuntu, and macOS systems don't use this mechanism during domain join.

.. rubric:: Checking and running scripts

Use :command:`univention-check-join-status` to check
whether any scripts need to run.
This command identifies scripts that haven't run yet or have an older version.

If pending scripts are present,
the *Domain join* management module displays a warning message when you open it.
To run all pending join scripts, click :guilabel:`Execute all pending join scripts`.

To run all scripts from the command line,
use :command:`univention-run-join-scripts`.
The system automatically checks whether it has already run each script.
When you run :command:`univention-run-join-scripts` on a system other than
the Primary Directory Node, the command asks for a username and password.
When you run this command on the Primary Directory Node,
to sign in, use the ``--ask-pass`` option.

The system records each script name and its output
in :file:`/var/log/univention/join.log`.

.. _domain-infrastructure-join-windows:

Windows domain joins
--------------------

Microsoft Windows systems can join a Nubus for UCS domain.
The join uses Samba with Active Directory support.

.. _domain-infrastructure-join-windows-overview:

Windows domain join overview and requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Samba enables Nubus for UCS to support Microsoft Windows systems.
This section describes the join procedure for Windows 11 as an example.
The process is similar for other Windows versions and for Windows Server systems,
which you can also join as member servers.
UCS doesn't support Windows systems as domain controllers.
For more information about Windows in a Nubus for UCS domain,
see :external+uv-ucs-manual:ref:`windows-services-for-windows`
in :cite:t:`ucs-manual`.

.. TODO: Replace the cross-reference to Windows Services after they're available in the UCS Operation Manual.

.. important::

   Only domain-compatible Windows versions can join the Nubus for UCS domain.
   Windows Home editions can't join a domain.

When a Windows client joins, Nubus for UCS creates a host account for it.
For more information,
see :external+uv-nubus-manual:ref:`nubus-computer-management`
in :cite:t:`uv-nubus-manual`.
You can configure the MAC address, IP address, network, DHCP, and DNS
through management modules before or after the join.

To join the domain, use the local ``Administrator`` account.

Domain joins take some time.
Don't cancel the process prematurely.
After successful joining, a confirmation window appears with the message
*Welcome to the domain <your domain name>*.
To confirm the join, click :guilabel:`OK`.
To apply the changes, restart the Windows computer.

For Windows client domain name rules,
see :ref:`deployment-domain-setup-naming-domain`.

.. important::

   For a domain join against a domain controller based on Samba/AD,
   configure the DNS settings on the client to resolve entries from the Nubus for UCS domain.
   Verify that the system time on the client matches the time on the domain controller.

.. _domain-infrastructure-join-windows-versions:

Supported Windows versions
~~~~~~~~~~~~~~~~~~~~~~~~~~

Nubus for UCS supports the following Microsoft Windows versions to join a UCS domain:

* Windows 10
* Windows 11
* Windows Server in the versions 2012, 2016, 2019, 2022, and 2025

.. _domain-infrastructure-join-windows-11:

Windows 11
~~~~~~~~~~

To join Windows 11 to a Nubus for UCS domain, you need the *Pro*, *Education*, or
*Enterprise* edition.
Follow these steps:

#. Open the *Start* menu or press the Windows key.
   Search for ``Control Panel`` in the *Search* field.

#. Navigate to :menuselection:`System and Security --> System`.
   Scroll down and click :guilabel:`Domain or workgroup`.
   Select :menuselection:`Change settings --> Change`.

#. Enable the :guilabel:`Domain` option.

#. Enter the domain name in the input field.
   Use the full domain name, for example ``mydomain.intranet``.
   Click :guilabel:`OK`.

#. Enter the username and password of an account that's member in the ``Domain Admins`` group.
   The default domain username for administrator accounts is ``Administrator``.

#. To start the domain join, click :guilabel:`OK`.

.. _domain-infrastructure-join-windows-10:

Windows 10
~~~~~~~~~~

Only the *Pro* and *Enterprise* editions of Windows 10 can join a domain.
To join Windows 10 to a Nubus for UCS domain, follow the steps in :ref:`domain-infrastructure-join-windows-11`.

.. _domain-infrastructure-join-windows-server:

Windows Server 2012 / 2016 / 2019 / 2022 / 2025
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To join Windows Server to a Nubus for UCS domain,
follow these steps:

#. Open the *Start* menu.

#. Navigate to :menuselection:`System and Security --> System`.
   Click :menuselection:`Change settings --> Network ID`.

#. Enable the *Domain* option.
   Enter the domain name in the input field for the domain join.
   Click :guilabel:`OK`.

#. In the *Name* field, enter ``Administrator``.
   In the *Password* field, enter the password from :samp:`uid=Administrator,cn=users,{LDAP base DN}`.

#. To start the domain join, click :guilabel:`OK`.

.. warning::

   Univention doesn't support joining Microsoft Active Directory Domain Controllers into the Nubus for UCS domain.
   Use the :program:`Active Directory Connection` app
   from the :ref:`lifecycle-app-center` as an alternative.

   For more information,
   see :external+uv-ucs-manual:ref:`ad-connector-general`
   in :cite:t:`ucs-manual`.

.. _domain-infrastructure-join-ubuntu:

Ubuntu domain joins
-------------------

Univention provides the :program:`Univention Domain Join Assistant`,
a GUI and command-line tool for adding Ubuntu and Linux Mint clients to a Nubus for UCS domain.
The assistant sets up LDAP, DNS, Kerberos, and login (PAM/SSSD) for you.
You don't need to set up anything manually.

For installation steps, supported versions, and usage details,
see the `Univention Domain Join Assistant documentation <https://github.com/univention/univention-domain-join>`_.

.. _domain-infrastructure-join-macos:

macOS domain joins
------------------

To join the macOS client to a Nubus for UCS domain, follow these steps:

#. In *System Preferences*, open :guilabel:`Users & Groups`.

#. Click the lock icon and enter the credentials for a local *Administrator* account.

#. From the menu, open the *Directory Utility*,
   as you can see in :numref:`domain-infrastructure-join-macos-gui-figure`.

.. _domain-infrastructure-join-macos-gui-figure:

.. figure:: /images/macosx-bind.*
   :alt: Domain join of a macOS system

   Domain join of a macOS system

4. In the *Advanced options* section, enable *Create mobile account at login*.
   A mobile account lets you sign in to the macOS system with your domain account
   even when the domain isn't available.

#. Enter the domain name in the *Active Directory Domain* field.

#. Enter the macOS client hostname in the *Computer ID* field.

#. To start the domain join, click :guilabel:`Bind…`.
   Enter the username and password for an account in the ``Domain Admins`` group,
   for example ``Administrator``.

.. _domain-infrastructure-join-macos-cli:

Domain join on the command line
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can also use :command:`dsconfigad` on the command line.
See :numref:`domain-infrastructure-join-macos-cli-listing` for the full command.
For more options, run :command:`dsconfigad -help`.

.. code-block::
   :caption: Join a Nubus for UCS domain through CLI on macOS
   :name: domain-infrastructure-join-macos-cli-listing

   $ dsconfigad -a <MAC HOSTNAME> \
     -domain <FQDN> \
     -ou "CN=Computers,<LDAP base DN>" \
     -u <Domain Administrator> \
     -mobile enable

.. _domain-infrastructure-join-macos-mount-shares:

Optional: Mount CIFS shares
~~~~~~~~~~~~~~~~~~~~~~~~~~~

After the domain join, you can automatically mount CIFS shares
to subfolders in :file:`/Volumes` when signing in with a domain user.
To do this, follow these steps:

#. Add the line in :numref:`domain-infrastructure-join-macos-mount-shares-volumes-listing`
   to the :file:`/etc/auto_master` file.

   .. code-block:: text
      :caption: Configure ``auto-custom`` for volumes
      :name: domain-infrastructure-join-macos-mount-shares-volumes-listing

      /Volumes	auto_custom

#. Create the file :file:`/etc/auto_custom`
   and list the shares you want to mount using the pattern shown in :numref:`domain-infrastructure-join-macos-mount-shares-pattern-listing`.

   .. code-block:: text
      :caption: Pattern for share definition
      :name: domain-infrastructure-join-macos-mount-shares-pattern-listing

      <SUBFOLDER_NAME>    -fstype=smbfs    ://<FQDN>/<SHARE_NAME>

.. note::

   The :program:`Finder` doesn't show auto-mounted shares in the sidebar.
