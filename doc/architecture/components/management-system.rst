.. SPDX-FileCopyrightText: 2021-2023 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _component-management-system:

UCS management system
=====================

The UCS management system is the central administration interface for users with
administrative tasks to operate a UCS domain and maintain the UCS systems. It
provides different interfaces, for example for web browsers, command line and
programming, although the term *UCS management system* generally refers to the
web interface. Administrators usually open the management system in their web
browser through the :ref:`component-portal` after they sign in.

The UCS management system provides for the following purposes:

#. Intuitive, easy to use, and central web application for all administrative
   tasks around identity and IT infrastructure management

#. Low entrance barrier for system administrators

#. Aggregation and representation of data stored in the domain database

#. Management of UCS systems through a web based interface

It consists of the following parts as shown in
:numref:`management-system-model`:

.. _management-system-model:

.. figure:: /images/management-system.*
   :alt: Model for the UCS managementsystem including Univention
         Directory Manager (UDM), Univention Management Console (UMC) and Univention
         Configuration Registry (UCR)

   Parts of the UCS management system

* :ref:`component-domain-management` to centrally manage the domain
  settings and objects in the domain database.

* :ref:`component-system-management` to manage UCS systems, services and
  apps.

* :ref:`component-configuration-registry` to store configuration settings for
  each UCS system.

Talking about the UCS management system comprises all previously mentioned
parts. Administrators rely on the UCS management system, because it simplifies
their daily work and improves the usability of |UCS|.

.. _component-domain-management:

Domain management
-----------------

.. index::
   pair: udm; domain management
   see: univention directory manager; udm
   single: udm; identities
   single: udm; devices
   single: udm; services

Domain management covers all administrative areas related to identities,
devices, and services across the domain.

Identities
   *Identities* include users and their collection in user groups. A user can be
   member of different groups.

Devices
   *Devices* include computers such as other UCS systems, user clients such as
   notebooks or printers. Furthermore, it also includes device monitoring.

Services
   *Services* include basic infrastructure services such as networking with DHCP
   and DNS, infrastructure for applications and users such as email and file
   shares, and other domain services such as domain join, directory manager, and
   policies.

In |UCS|, |UDM| is responsible for domain management. You can imagine |UDM| as
abstraction layer to the domain database. |UDM| provides modules for each area.
Services and apps can extend the domain management.

As abstraction layer the purposes of |UDM| are the following:

.. index::
   single: udm; purposes

Data aggregation
   Return multiple objects from the domain database as one object in |UDM|.

Data consistency
   Ensure data consistency between different objects in the domain database,
   such as references between different objects and ensure that the references
   are always valid.

Data presentation
   Enhance the data from the domain database for appropriate presentation to
   the user on the command line and in the web interface.

Atomic operations
   Provide a locking mechanism so that operations with multiple actions run as
   atomic operation. The domain database doesn't support transactions. For
   example, creating a user with a unique primary email address requires the
   reservation of username and email address before |UDM| can create the user
   object.

Input value validation
   Validate user input to ensure correct and consistent data in the domain
   database. |UDM| is the interaction layer between the user and the domain
   database.

Process logic
   Process logic ensures that |UDM| automatically applies default values to
   properties when users don't set values for properties. In addition, the
   process logic prevents inconsistent state of data.

.. index::
   single: extended attributes
   single: extended options

User interface enhancements
   |UDM| provides an interface for enhancement with additional properties in
   UDM. *Extended attributes* and *extended options* provide the interfaces.

Usability
   |UDM| enhances the usability when working with data from the domain database.
   For example, the domain database maintains group memberships at the group
   only. In contrast, in |UDM| administrators can maintain group memberships at
   the group and at the user alike.

.. admonition:: Continue reading

   :ref:`services-udm` for description of the architecture of UDM.

.. seealso::

   Administrators refer to :cite:t:`ucs-manual`:

   * :ref:`users-general` for identity management of users

   * :ref:`groups` for identity management of user groups

.. seealso::

   Software developers refer to :cite:t:`developer-reference`:

   * :ref:`uv-dev-ref:udm-ea`
   * :ref:`uv-dev-ref:udm-ea-option`

.. _component-system-management:

System management
-----------------

.. index::
   pair: system management; umc
   see: univention management console; umc
   single: umc; administration
   pair: umc; software updates
   pair: umc; system updates
   pair: umc; web interface
   single: umc modules
   single: umc; technology stack

System management includes all administrative tasks related to the underlying
UCS system. These tasks include, for example, UCS system updates, management of
apps such as lifecycle, configuration, and certificate handling. The purpose of
system management is to simplify the daily tasks of administrators when managing
multiple UCS systems.

The component *Univention Management Console (UMC)* provides the capabilities
for system management on UCS and is part of the UCS management system. It offers
the technology stack for the web interface of the UCS management system. |UMC|
consists of modules for various management tasks. Apps and software packages can
provide custom UMC modules and extend the UCS management system.

|UMC| is a central component in UCS for the following reasons:

* UMC provides the technology stack for the web interface of the UCS management
  system.

* UMC provides user authentication interface to the UCS management system and
  :ref:`services-ucs-portal`.

* UMC allows extension of the UCS management system with custom UMC modules.

As component serving the web interface for the UCS management system, |UMC|
involves a web frontend and a backend as shown in
:numref:`component-system-management-umc-model`.

.. _component-system-management-umc-model:

.. figure:: /images/UMC-architecture-product-component.*
   :width: 250 px

   *UMC web frontend* and *UMC backend* realize Univention Management Console

.. admonition:: Continue reading

   :ref:`services-umc` for description of the architecture of UMC

.. seealso::

   System administrators refer to :cite:t:`ucs-manual`:

   * :ref:`central-user-interface` for details about |UMC| modules

   * :ref:`central-extended-attrs` for details about how to enhance with
     *extended attributes*

   Software developers and system engineers refer to
   :cite:t:`developer-reference`:

   * :ref:`uv-dev-ref:chap-umc` for technical details about |UMC| for software developers

.. _component-configuration-registry:

Configuration management
------------------------

.. index::
   pair: ucr; configuration management
   see: univention configuration variable; ucr
   single: ucr; configuration setting
   single: ucr; write configuration files
   single: ucr; trigger write
   single: ucr; services
   single: ucr; scripts
   single: ucr; apps
   single: ucr; plain text

Configuration management is a collection of tasks used to configure software
systems. For example, changing the system's mail relay server requires updates
to several configuration text files. With configuration management, an
administrator changes the configuration setting in one place. The change then
triggers updates to the associated configuration files.

The component *Univention Configuration Registry (UCR)* covers the local
configuration management on all Univention Corporate Server systems. Services,
scripts, and apps use UCR as a central configuration store. And administrators
use UCR to adapt their UCS system to their needs.

UCR consists of a non-hierarchical key-value store called *UCR variables*. It
provides a common interface to system settings. UCR decouples configuration
settings from specific file formats such as plain text, XML, or JSON. UCR also
consists of a template system and mechanisms to generate configuration files
from templates and UCR variables.

UCS uses UCR variables for all configuration settings on a system. And UCS
provides many templates for service configuration files.

.. admonition:: Continue reading

   :ref:`services-ucr` for description of the architecture of UCR

.. seealso::

   :ref:`computers-administration-of-local-system-configuration-with-univention-configuration-registry`
      For information about how to use UCR in :cite:t:`ucs-manual`

   :ref:`uv-dev-ref:chap-umc`
      For detailed information about UCR in :cite:t:`developer-reference`
