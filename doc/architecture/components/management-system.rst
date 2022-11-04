.. _component-management-system:

UCS management system
=====================

The UCS management system is the central administration interface for users with
administrative tasks to operate a UCS domain and maintain the UCS systems. It
provides different interfaces, for example for web browsers, command-line and
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

* :ref:`component-domain-management` to centrally administer the domain
  settings and objects in the domain database.

* :ref:`component-system-management` to administer UCS systems, services and
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
   pair: domain management; udm
   pair: domain management; univention directory manager
   pair: udm; univention directory manager
   single: udm; identities
   single: udm; devices
   single: udm; services

Domain management covers all administrative areas related to identities,
devices, and services across the domain.

Identities
   *Identities* include users and their collection in user groups. A user can be
   member of different groups.

Devices
   *Devices* include computers like for example other UCS systems, user clients
   like notebooks or printers. Furthermore, it also includes device monitoring.

Services
   *Services* include basic infrastructure services like networks with DHCP and
   DNS, infrastructure for applications and users like email and file shares and
   other domain services like domain join, directory manager, and policies.

In |UCS| the |UDM| is responsible for domain management. You can imagine |UDM|
as abstraction layer to the domain database. |UDM| provides modules for each
area. Services and apps can extend the domain management.

As abstraction layer the purposes of |UDM| are the following:

.. index::
   single: udm; purposes

Data aggregation
   Return multiple objects from the domain database as one object in |UDM|.

Data consistency
   Ensure data consistency between different objects in the domain database, for
   example references between different objects and make sure the references
   always are valid.

Data presentation
   Enhance the data from the domain database for appropriate presentation to
   the user on the command-line and in the web interface.

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
   The process logic ensures that |UDM| automatically applies default values on
   properties when users don't set values for properties. Furthermore, process
   logic prevents inconsistent state of data.

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

   :ref:`users-general`
      for identity management of users in :cite:t:`ucs-manual`

   :ref:`groups`
      for identity management of user groups in :cite:t:`ucs-manual`

.. _component-system-management:

System management
-----------------

.. _component-configuration-registry:

Configuration management
------------------------

