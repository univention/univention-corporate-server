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
with Univention Corporate Server (UCS). It allows administrators to map their
organization's structure to the IT environment.

An IT environment consists of systems and users. Systems offer services and
provide functionality. Users use functionality.

A domain is a form of a computer network. It incorporates one or more systems
and users into one single trust context. The domain offers special services to
systems and users, called domain services.

An identity represents an account for a user in a domain. It holds information
like for example username and password for login. Furthermore, it contains
various data associated to the user like for example group memberships,
permissions, and different attributes used by services.

User accounts are organized in groups. Users groups help administrators to apply
permissions for domain services to users. Users can belong to multiple groups.

A central database registers all objects of the domain, like for example user
identities, computer systems, printers and file shares. The database stores the
objects in a hierarchical tree-like structure. One or more central systems store
the central database and are called *domain controller*.

UCS is such a system that operates the central database for the domain. For the
distinct roles of UCS systems in a domain, see the :ref:`concept-role`.
