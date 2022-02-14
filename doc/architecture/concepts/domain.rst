.. _concept-domain:

Domain concept
==============

.. index::
   single: user
   pair: group; user group
   single: identity management; system
   single: service
   single: trust context
   single: domain; service

The domain concept is the most important concept in an IT environment operated
with Univention Corporate Server (UCS). The domain concept offers a way to
centrally manage an IT environment where administrators can map their
organization's structure to the IT environment.

Simplified, an IT environment consists of systems and users. Systems offer
services that provide functionality. Users use functionality. A domain is a form
of a computer network. It incorporates one or more systems and users into one
single trust context. The domain offers special services called domain services
to systems and users. The figure :ref:`fig-concepts-domain-systems-users` shows
the relationship between the actors systems, services and users.

.. _fig-concepts-domain-systems-users:

.. figure:: /images/Systems-and-users-in-domain.*

   Relationship of the actors *systems*, *services* and *users* in a domain

A trust context uses roles, permissions and cryptographic certificates to ensure
secure communication between the domain participants. Only participants
known to the domain can interact with domain services.

One key participant in a domain is the identity, a digital representation for
persons.  An identity represents an account for a user in a domain. It holds
information like for example username and password for login. Furthermore, it
contains various data associated to the user like for example group memberships,
permissions, and different attributes used by services.

User accounts are organized in groups and users can belong to multiple groups.
Users groups help administrators to apply permissions for domain services to
users and are essential to the organization's structure to the domain
administration.

All the objects in a domain need to be managed and organized. In a domain a
central database called domain database registers all objects, like for example
user identities, computer systems, printers and file shares. See figure
:ref:`fig-concepts-domain-database` for a graphical interpretation. The database
stores the objects in a hierarchical tree-like structure. One or more central
systems store the central database and are called domain node.

.. _fig-concepts-domain-database:

.. figure:: /images/Domain-database.*

   Central domain database with different objects

UCS is a system that operates the central database for the domain. UCS is the
central platform the implements to domain concept and helps administrators to
manage and organize the IT environment for their organization. For the distinct
roles of UCS systems in a domain, see the :ref:`role concept <concept-role>`.
