.. _introduction:

************
Introduction
************

.. _introduction-what-is-ucs:

What is Univention Corporate Server?
====================================

Univention Corporate Server (UCS) is a Linux-based server operating
system for the operation and administration of IT infrastructures for
companies and authorities. UCS implements an integrated, holistic
concept with consistent, central administration and can ensure the
operation of all the components in an interrelated security and trust
context, the so-called UCS domain. At the same time, UCS supports a wide
range of open standards and includes extensive interfaces to
infrastructure components and management tools from other manufacturers,
meaning it can be easily integrated in existing environments.

UCS consists of reliable Open Source software tried and tested in
organizations of different sizes. These software components are
integrated together via the |UCSUMS|. This allows the easy integration and
administration of the system in both simple and complex distributed or
virtualized environments.

The central functions of UCS are:

* Flexible and extensive identity/infrastructure management for the
  central administration of servers, workstations, users and their
  permissions, server applications and web services

* Services for integrating the management of existing Microsoft Active
  Directory domains or even the provision of such services as an
  alternative for Microsoft-based server systems

* App Center for simple installation and management of extensions and
  applications

* Comprehensive features for the operation of virtualized systems (e.g.
  running a Windows or Linux operating systems) in either the cloud of
  on locally running UCS systems

* Network and intranet services for administration of DHCP and DNS

* File and print services

* Computer administration and monitoring

* Mail services

These functions are provided by different software packages in
Univention Corporate Server and are handled in detail in the course of
this handbook. Basically, the software packages contained in UCS can be
assigned to the following three main categories:

1. Base system

2. UCS management system with |UCSUMC| modules

3. Univention App Center, allowing the installation of further
   components and applications of other software vendors

The *base system* encompasses the operating system of the UCS Linux distribution
maintained by Univention and based on Debian GNU/Linux. It largely includes the
same software selection as Debian GNU/Linux as well as additional tools for the
installation, updating and configuration of clients and servers.

The |UCSUMS| realizes a single point of
administration where the accounts of all domain members (users, groups,
and hosts) and services such as DNS and DHCP are managed in a single
directory service. Core components of the management system are the
services OpenLDAP (directory service), Samba (provision of domain, file
and print services for Windows), Kerberos (authentication and single
sign on), DNS (network name resolution) and SSL/TLS (secure transmission
of data between systems). It can be used either via a web interface
(|UCSUMC| modules) or in the command line and in individual scripts. The
UCS management system can be extended with APIs (application programming
interfaces) and provides a flexible client-server architecture which
allows changes to be transferred to the involved systems and be
activated there.

Additional components from Univention and other manufacturers can easily
be installed using the App Center. They expand the system with numerous
functions such as groupware, document management and services for
Windows, meaning that they can also be run from a UCS system and
administrated via the UCS management system.

.. _introduction-overview-ucs:

Overview of UCS
===============

Linux is an operating system which always had a focus on stability,
security and compatibility with other operating systems. Therefore Linux
is predestined for being used in server operating systems that are
stable, secure and highly available.

Built on that base, UCS is a server operating system which is optimized
for the simple and secure operation and management of applications and
infrastructure services in enterprises and public authorities. For
efficient and secure management such applications rely on the tight
integration in the user and permission management of the |UCSUMS|.

UCS can be employed as the basis for the IT infrastructure in companies
and authorities and provide the central control for it. This makes a
considerable contribution to secure, efficient and cost-effective IT
operation. The business-critical applications are integrated in a
uniform concept, adapted to each other and pre-configured for
professional utilization. Alternatively it can be operated as part of an
existing Microsoft Active Directory domain.

.. _introduction-commissioning:

Commissioning
-------------

The use of UCS begins either with a classic operating system
installation on a physical server or as a virtual machine. Further
information can be found in :ref:`installation:chapter`.

.. _introduction-domain-concept:

Domain concept
--------------

In an IT infrastructure managed with UCS, all servers, clients and users
are contained in a common security and trust context, referred to as the
UCS domain. Every UCS system is assigned a so-called server role during
the installation. Possible system roles are Directory Node,
|UCSMANAGEDNODE| and client.

.. _introduction-domain:

.. figure:: /images/domainconcept.*
   :alt: UCS domain concept

   UCS domain concept

Depending on the system role within the domain, such services as
Kerberos, OpenLDAP, Samba, modules for domain replication or a Root CA
(certification authority) are installed on the computer. These are
automatically configured for the selected system role. The manual
implementation and configuration of every single service and application
is therefore not required. Due to the modular design and extensive
configuration interfaces, tailor-made solutions to individual
requirements can nevertheless be realized.

The integration of Samba, which provides the domain service for clients
and servers operated with Microsoft Windows, makes Univention Corporate
Server compatible with Microsoft Active Directory (AD), whereby the
system acts as an Active Directory server for Windows-based systems.
Consequently, for example, group policies for Microsoft Windows systems
can be administrated in the usual way.

UCS can also be operated as part of an existing Microsoft Active
Directory domain. This way, users and groups of the Active Directory
domain can access applications from the Univention App Center.

Ubuntu or macOS clients can be integrated in a UCS environment, as well
(see :ref:`computers-ubuntu`).

.. _introduction-expandability-with-components:

Expandability with the Univention App Center
--------------------------------------------

The Univention App Center offers additional UCS components and
extensions and a broad selection of business IT software, e.g.,
groupware and collaboration, file exchange, CRM or backup. These
applications can be installed in existing environments with a few clicks
and are usually ready to use. In most cases they are directly integrated
into the |UCSUMS| such that they are available as |UCSUMC| modules. This
provides a central management of data on the domain level and obsoletes
the separate management of, e.g., user data in multiple places.

.. _introduction-ldap-directory-service:

LDAP directory service
----------------------

With the |UCSUMS|, all the components of the UCS domain can be centrally
administrated across computer, operating system and site boundaries. It
thus provides a single point of administration for the domain. One
primary element of the UCS management system is an LDAP directory in
which the data required across the domain for the administration are
stored. In addition to the user accounts and similar elements, the data
basis of services such as DHCP is also saved there. The central data
management in the LDAP directory avoids not only the repeated entry of
the same data, but also reduces the probability of errors and
inconsistencies.

An LDAP directory has a tree-like structure, the root of which forms the
so-called basis of the UCS domain. The UCS domain forms the common
security and trust context for its members. An account in the LDAP
directory establishes the membership in the UCS domain for users.
Computers receive a computer account when they join the domain.
Microsoft Windows systems can also join the domain such that users can
log in there with their domain passport.

UCS utilizes OpenLDAP as a directory service server. The directory is
provided by the |UCSPRIMARYDN| and replicated on all UCS Directory Nodes
in the domain. The complete LDAP directory is also replicated on a
|UCSBACKUPDN| as this can replace the |UCSPRIMARYDN| in an emergency. In
contrast, the replication on |UCSREPLICADN| can be restricted to certain
areas of the LDAP directory using ACLs (access control lists) in order
to realize a selective replication. For example, this may be desirable
if data should only be stored on as few servers as possible for security
reasons. For secure communication of all systems within the domain, UCS
integrates a root CA (certification authority).

Further information can be found in :ref:`domain-ldap`.

.. _introduction-domain-administration:

Domain administration
---------------------

.. _introduction-umc:

.. figure:: /images/umc-favorites-tab.*
   :alt: |UCSUMC| modules

   |UCSUMC| modules

Access to the LDAP directory is performed via a web-based user interface
through |UCSUMC| (UMC) modules. In addition to this, |UCSUDM| allows the
realization of all domain-wide administrative tasks via a command line
interface. This is particularly suitable for the integration in scripts
or automated administrative steps.

|UCSUMC| modules allows to display, edit, delete, and search the data in
the LDAP directory via various filter criteria. The web interface offers
a range of wizards for the administration of user, groups, networks,
computers, directory shares and printers. The administration of
computers also comprises comprehensive functions for distributing and
updating software. The integrated LDAP directory browser can be used to
make further settings and add customer-specific object classes or
attributes.

Further information can be found in :ref:`central-general`.

.. _introduction-computer-administration:

Computer administration
-----------------------

|UCSUMC| modules allows not only the access to the LDAP directory, but
also the web-based configuration and administration of individual
computers. These include the adaptation of configuration data, the
installation of software as well as the monitoring and control of
services and the operating system itself. With the |UCSUMS|, domain
administration as well as computer and server configuration is possible
from any place via a comfortable graphic web interface.

.. _introduction-policy-concept:

Policy concept
--------------

The tree-like structure of LDAP directories is similar to that of a file
system It ensures that objects (such as users, computers, etc.) are in
one container which itself can be adopted by other containers. The root
container is also called the LDAP base object.

Policies describe certain administrative settings which are applied to
more than one object. Linked to containers, they facilitate the
administration as they are effective for all objects in the container in
question as well as the objects in subfolders.

For example, users can be organized in different containers or
organizational units (which are a form of containers) depending on which
department they belong to. Settings such as the desktop background or
accessible programs can then be connected to these organizational units
using policies. Subsequently, they apply for all users within the
organizational unit in question.

Further information can be found in :ref:`central-policies`.

.. _introduction-listener-notifier-replication:

Listener/notifier replication
-----------------------------

The listener/notifier mechanism is an important technical component of
the |UCSUMS|. With this, the creation, editing or deleting of entries in
the LDAP directory triggers defined actions on the computers in
question. For example, the creation of a directory share with the UMC
module :guilabel:`Shares` leads to the share firstly being
entered in the LDAP directory. The listener/notifier mechanism then
ensures that the NFS and Samba configuration files are also expanded
accordingly on the selected server and that the directory is created in
the file system of the selected server if it does not already exist.

The listener/notifier mechanism can be easily expanded with modules for
further - also customer-specific - procedures. Consequently, it is used
by numerous technology partners for the integration of their products in
the LDAP directory service and the |UCSUMS| for example.

Further information can be found in :ref:`domain-listenernotifier`.

.. _introduction-further-documentation:

Further documentation
=====================

This manual addresses just a small selection of the possibilities in
UCS. Among other things, UCS and solutions based on UCS provide:

* Comprehensive support for complex server environments and replication
  scenarios

* Advanced capabilities for Windows environments

* Central network management with DNS and DHCP

* Monitoring systems and networks

* Print server functionalities

* Proxy server

Further documentation related to UCS and further issues is published under `UCS
documentation overview <ucs-documentation-overview_>`_ and in the `Univention
Wiki <univention-wiki_>`_).

.. _introduction-symbols-and-conventions-used-in-this-manual:

Symbols and conventions used in this manual
===========================================

The manual uses the following symbols:

.. caution::

   Warnings are highlighted.

.. note::

   Notes are also highlighted.

This table describes the functionality of a UMC module:

.. table:: Tab DHCP service

   +-----------------------+-----------------------------------------------+
   | Attribute             | Description                                   |
   +=======================+===============================================+
   | Name                  | The unique name of a DHCP service.            |
   +-----------------------+-----------------------------------------------+
   | Description           | An arbitrary description of the service.      |
   +-----------------------+-----------------------------------------------+

Menu entries, button labels, and similar details with actions are printed in
:guilabel:`this font face`.

*Names* are highlighted.

``Computer names, LDAP DNs``, :command:`program
names`, :file:`file names, file paths`,
`internet addresses <https://example.com>`_ and ``options`` are
also optically accented.

``Commands and other keyboard input`` is accented optically.

::

   In addition, excerpts from configuration files, screen output, etc. are
   printed as code block.

A backslash (``\``) at the end of a line signifies that the subsequent line
feed is not to be understood as an *end of line*.
This circumstance may occur, for example, where commands cannot be
represented in one line in the manual, yet have to be entered in the
command line in one piece without the backslash or with the backslash
and a subsequent :kbd:`Enter`.

The path to a function is represented in a similar way to a file path.
:menuselection:`Users --> Add` means for example, you have to click
:guilabel:`Users` in the main menu and :guilabel:`Add` in the submenu.
