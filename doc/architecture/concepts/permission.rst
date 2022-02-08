.. _concept-permission:

Permission concept
==================

The permission concept in Univention Corporate Server (UCS) specifies who can
read and write domain data. Permissions apply to objects like users and systems
alike. Policies assign custom permissions to objects. UCS applies default
permissions for systems and pre-defined users and groups.

System roles
------------

Only UCS systems in the system role Primary Directory Node can write data to the
domain database. All other system roles have read-only access. Nevertheless,
write operations happen on the Primary Directory Node on behalf of other systems
or users, for example a new UCS system joins the domain or an administrator
installs an app.

Administrator and root
----------------------

A UCS system knows two administrative user accounts: *Administrator* and *root*.

Administrator
   The user account *Administrator* is the first domain user and has all domain
   permissions. The *Administrator* user account can join new systems to the
   domain and can work with all modules in the UCS management system.

   The *Administrator* account is only defined once per domain during the
   installation of the Primary Directory Node. The account password is set
   during installation.

   Think of *Administrator* as the primary administrative account for the UCS
   domain.

root
   The user account *root* is the superuser on the local UCS system and has the
   user ID of ``0``. It has all permissions and is equivalent to the *root*
   account known from other GNU Linux systems.

   The *root* account is defined and the password set during installation of
   every UCS system. The account is only for the local UCS system. On other UCS
   systems administrators should of course define other passwords for the *root*
   account.

   Think of *root* as the primary administrative account for the local UCS
   system.

Domain users and admins
-----------------------

UCS has two default user groups in the domain that differ fundamentally: *Domain
Users* and *Domain Admins*.

Domain Users
   UCS assigns every user to the user group *Domain Users* per default. The
   group identifies the user account as belonging to a person. The user account
   only has a minimal set of permissions in the domain.

   .. TODO : Ask SME: What permissions have user accounts in the Domain Users group per default?

Domain Admins
   UCS creates one user account called *Administrator* during the installation
   of the first UCS system (Primary Directory Node) in a domain. It is the first
   user account and has all permissions for the domain. The *Administrator*
   user account is member of the *Domain Admins* group. Users in *Domain Admins*
   group have all domain permissions. To join a UCS system to the domain
   administrators need a user account in the group *Domain Admins*.

Machine account
---------------

UCS systems are actors in a domain like users. Each UCS system has its
own account in the domain database. The account is called *machine account*.

UCS systems can read data from the domain database with their machine account.
Every machine account has assigned the following default permissions in the UCS
domain:

.. TODO : Ask SME: Check for the correct listing. The manual only mentions the machine account two times.

* The UCS system can read all object information from the domain database.
* The UCS system can write only information to the domain database that is
  associated with its account.

Policies
--------

Policies are administrative settings to help administrators with infrastructure
management that can be assigned to objects in the domain database. Policies use
the inheritance principle as it is known from object oriented software
programming. Inheritance allows to set policies to one object in the structured
domain database. The policy then applies to all objects that are organized in
the structure below.
