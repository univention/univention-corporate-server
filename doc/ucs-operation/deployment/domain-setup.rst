.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _deployment-domain-setup:

Domain setup
============

.. _deployment-installation-physical-domain-settings:

Set up the domain
~~~~~~~~~~~~~~~~~

You start the final configuration step of the Nubus for UCS system by selecting a domain mode.
:numref:`deployment-installation-physical-domain-settings-role-figure`
shows the domain modes.
They influence the next configuration steps.
The following domain modes are available:

.. _deployment-installation-physical-domain-settings-new:

Create a new UCS domain
   The *Create a new UCS domain* configures the first system in a UCS domain,
   a Nubus for UCS system with the :term:`UCS Primary Directory Node` system role.
   The subsequent steps request required information
   to set up the directory service, authentication service, and the DNS server.
   A Nubus for UCS domain can consist of one single or several Nubus for UCS systems.
   You can add additional Nubus for UCS systems at a later point in time
   using the :ref:`deployment-installation-physical-domain-settings-join` mode.
   For more information, see
   :ref:`deployment-installation-physical-domain-settings-new-domain`.

.. _deployment-installation-physical-domain-settings-join-ad:

Join into an existing Active Directory domain
   This mode operates Nubus for UCS as a member of a Windows Active Directory domain.
   The configuration is suitable for expanding an Active Directory domain with applications available on Nubus for UCS.
   Apps installed on Nubus for UCS are then available for the users of the Active Directory domain to use.
   The subsequent steps request information for joining the Active Directory domain
   and configure Nubus for UCS accordingly.
   For more information, see
   :ref:`deployment-installation-physical-domain-settings-ad-member`.

.. _deployment-installation-physical-domain-settings-join:

Join into an existing UCS domain
   This mode configures the Nubus for UCS system to join an existing Nubus for UCS domain.
   At a later step, the system setup asks for what system role it assigns.
   For more information, see
   :ref:`deployment-installation-physical-domain-settings-join-ucs`.

.. _deployment-installation-physical-domain-settings-role-figure:

.. figure:: /images/installer-domainrole.*
   :alt: Domain settings

   Domain settings

.. _deployment-installation-physical-domain-settings-naming:

Naming convention for hostnames
"""""""""""""""""""""""""""""""

.. index::
   single: hostname; naming convention
   single: hostname
   single: hostname; length
   single: hostname; allowed characters

During Nubus for UCS installation,
the domain setup asks for a hostname and a domain name as *fully qualified domain name*.
For compatibility reasons with Samba and Active Directory domains,
the hostname must adhere to the following naming convention:

* Length from 1 to 13 alphanumeric characters.

* Only lower case letters (``a-z``) and numerals (``0-9``).

* Start and end with an alphanumeric character and can contain a hyphen (``-``) in between.

The naming convention has the regular expression in
:numref:`deployment-installation-physical-domain-settings-naming-listing`.

.. code-block::
   :caption: Regular expression for the naming convention for the hostname
   :name: deployment-installation-physical-domain-settings-naming-listing

   ^[a-z0-9][a-z0-9-]{0,11}[a-z0-9]?$

.. _deployment-installation-physical-domain-settings-new-domain:

Mode: Create a new UCS domain
"""""""""""""""""""""""""""""

.. index::
   single: hostname; Create new UCS domain

After you selected :ref:`deployment-installation-physical-domain-settings-new`,
system setup asks for the following information,
see :numref:`deployment-installation-physical-domain-settings-new-domain-figure`:

.. _deployment-installation-physical-domain-settings-new-domain-organization:

Organization name
   You can *optionally* specify an organization name.
   The system setup uses the organization name
   to automatically generate a
   :ref:`domain name <deployment-installation-physical-domain-settings-new-domain-fqdn>`
   and the :ref:`LDAP base <deployment-installation-physical-domain-settings-new-domain-ldap-base>`.

.. _deployment-installation-physical-domain-settings-new-domain-email:

Email address
   If you provide a valid email address,
   system setup activates a personalized license
   and sends it to the address.
   Univention App Center requires the license to install apps.
   Univention automatically generates the license
   and immediately sends it to the specified email address.
   You import the license through the *Welcome* management module,
   see :external+uv-ucs-manual:ref:`central-license`
   in :cite:t:`ucs-manual`.

   .. TODO: Replace link to license management module after it's available in the document.

.. _deployment-installation-physical-domain-settings-new-domain-fqdn:

Fully qualified domain name
   Provide the fully qualified domain name for the system, including hostname and domain name.
   System setup derives the name of the Nubus for UCS system
   and the DNS domain from it.
   System setup automatically generates a suggestion if you provided an
   :ref:`deployment-installation-physical-domain-settings-new-domain-organization`.
   For the naming convention of the hostname,
   see :ref:`deployment-installation-physical-domain-settings-naming`.

   .. important::

      Recommendation: don't use publicly available DNS domains for your DNS domain,
      as this can result in name resolution problems.

.. _deployment-installation-physical-domain-settings-new-domain-ldap-base:

LDAP base
   You must specify an LDAP base to initialize the directory service.
   System setup automatically creates a suggestion from the
   :ref:`deployment-installation-physical-domain-settings-new-domain-fqdn`.
   You can usually accept the suggestion without changes.

.. _deployment-installation-physical-domain-settings-new-domain-figure:

.. figure:: /images/installer-hostname.*
   :alt: Specify of hostname and LDAP base

   Specify of hostname and LDAP base

.. _deployment-installation-physical-domain-settings-ad-member:

Mode: Join an existing Active Directory domain
""""""""""""""""""""""""""""""""""""""""""""""

.. index::
   single: hostname; Join existing Active Directory domain

If you configured the DNS server of an Active Directory domain during the
:ref:`network configuration <deployment-installation-physical-network-configuration>`,
system setup automatically suggest the name of the Active Directory domain controller in the *Active Directory account information* step,
see :numref:`deployment-installation-physical-domain-settings-ad-member-figure`.
If the suggestion is incorrect,
you can provide the name of another Active Directory domain controller or another Active Directory domain.

You need to provide an Active Directory account and its corresponding password
to enable your Nubus for UCS system to join the Active Directory domain.
The user account must have the permission to join new systems in the Active Directory domain.

In addition, you need to define a hostname for the Nubus for UCS system.
You can adopt the suggested hostname or provide a different one.
For the naming convention of the hostname,
see :ref:`deployment-installation-physical-domain-settings-naming`.

System setup automatically derives the system's domain name from the domain DNS server.
However, in some scenarios such as hosting a public mail server,
you may need to use a different fully qualified domain name.
The Nubus for UCS system joins the Active Directory domain with the specified hostname.

.. important::

   After the configuration is complete, you **can't** change the domain.

In a Nubus for UCS domain, you can install systems in different system roles.
The first Nubus for UCS system that joins an Active Directory domain,
automatically has the :term:`UCS Primary Directory Node` system role.
If you select this mode during the installation of addition Nubus for UCS system,
system setup shows the selection dialog for the system role.
For the system role selection,
see :ref:`deployment-installation-physical-domain-settings-join-ucs`.

.. _deployment-installation-physical-domain-settings-ad-member-figure:

.. figure:: /images/installer-adjoin.*
   :alt: Information on the Active directory domain

   Information on the Active directory domain

.. _deployment-installation-physical-domain-settings-join-ucs:

Mode: Join an existing UCS domain
"""""""""""""""""""""""""""""""""

.. index::
   single: hostname; Join existing UCS domain

To join an existing Nubus for UCS domain,
you need to process the following steps:

#. Select the system role.

   In a Nubus for UCS domain, you can install systems in different system roles.
   The first system in a Nubus for UCS domain always has the :term:`UCS Primary Directory Node` system role.
   Additional Nubus for UCS systems can join the domain at a later point in time.
   You can assign them one of the following system roles.

   .. TODO: Make system roles more concise and use the glossary to collect information there.

   Backup Directory Node
      The :term:`Backup Directory Node` is the fallback system for the UCS Primary Directory Node.
      If the Primary Directory Node fails,
      a Backup Directory Node can adopt the role of the UCS Primary Directory Node permanently.
      Backup Directory Nodes have all the domain data and SSL security certificates saved as read-only copies.

   Replica Directory Node
      Servers with the :term:`Replica Directory Node` role have all the domain data saved as read-only copies.
      In contrast to the Backup Directory Node, however, they don't have all security certificates.
      Services running on a Replica Directory node access LDAP directory data through the local LDAP directory service.
      Replica Directory Node systems are ideal for site servers and the distribution of high-load services.

   Managed Node
      :term:`Managed Node`\ s are Nubus for UCS systems without a local LDAP directory service.
      They access domain data through other servers in the domain.
      They're suitable for services that don't require a local database for authentication,
      for example, print and file servers.

#. After you selected the system role for Nubus for UCS,
   the system setup asks for more information to join the domain,
   see :numref:`deployment-installation-physical-domain-settings-join-ucs-figure`.

   Start join at the end of the installation
      If you don't intend to let the system setup run the domain join automatically during the installation,
      deactivate the option *Start join at the end of the installation*.

   Search Primary Directory Node in DNS
      System setup automatically determines the name of the UCS Primary Directory Node
      if you provided it as DNS server during
      :ref:`deployment-installation-physical-network-configuration`.

      .. TODO: Clarify: What's the reason? Why have the detection and why deactivate it?

      If you decide to join another Nubus for UCS domain,
      you can deactivate *Search Primary Directory Node in DNS*
      and provide the fully qualified domain name of the preferred UCS Primary Directory Node.

   .. _deployment-installation-physical-domain-settings-join-ucs-credentials:

   Credentials for domain administrator
      The domain join process needs to access information about the domain.
      To grant system setup the appropriate permission,
      you need to provide the credentials for an *Administrator* account of the domain.

#. Finally, provide a hostname for the Nubus for UCS system.
   You can adopt the suggested hostname or change it.
   For the naming convention of the hostname,
   see :ref:`deployment-installation-physical-domain-settings-naming`.
   The system setup automatically derives the domain name of the computer from the domain DNS server.
   In some scenarios, such as a public mail server, it may be necessary to use a certain fully qualified domain name.

   .. important::

      After the configuration is complete, you **can't** change the domain.

.. _deployment-installation-physical-domain-settings-join-ucs-figure:

.. figure:: /images/installer-join.*
   :alt: Information on the domain join

   Information on the domain join

.. _deployment-installation-physical-confirm-settings:

Confirm the installation settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*Confirm configuration settings* shows a summary of your settings,
see :numref:`deployment-installation-physical-confirm-settings-summary-figure`.

Update system after installation
   The *Update system after installation* option allows the automatic installation of available errata updates.

   .. TODO: Add glossary entry for errata updates.

   In addition,
   the :term:`UCS Primary Directory Node` installs all available patch level updates and errata updates.
   All other system roles update their patch level version
   to match the patch level version of the UCS Primary Directory Node.
   You need to sign in to the UCS Primary Directory Node
   to check the installation status.
   For sign-in, use the same administrator credentials
   that you provided in :ref:`deployment-installation-physical-domain-settings-join-ucs-credentials`.

.. TODO: Clarify. Is that true with the updates on the Primary? I don't think all of this happens during a join of an additional system to the domain. It would require major planning of maintenance windows when adding one system to a large domain. I can't imagine that our product requires that.

If the settings match your intention,
click :guilabel:`Configure System`
to start the configuration of the Nubus for UCS system.

System setup shows the progress during the system configuration.
It saves the installation protocol in the following files:

* :file:`/var/log/installer/syslog`
* :file:`/var/log/univention/management-console-module-setup.log`

After you confirm the completion of the system setup,
your Nubus for UCS system is ready for the first full boot procedure.
You can restart it.
The system then boots from the hard drive.
After the boot procedure completes,
continue with :ref:`deployment-after-installation`.

.. _deployment-installation-physical-confirm-settings-summary-figure:

.. figure:: /images/installer-overview.*
   :alt: Installation overview

   Installation overview

